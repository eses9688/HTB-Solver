const https = require('https');

const TOKEN = 'github_pat_[REDACTED]';
const REPO = 'drkim-dev/private-test';

function api(path) {
  return new Promise((resolve, reject) => {
    https.get({
      hostname: 'api.github.com',
      path,
      headers: {
        'Authorization': `Bearer ${TOKEN}`,
        'User-Agent': 'pentest-recon',
        'Accept': 'application/vnd.github+json'
      }
    }, (res) => {
      let data = '';
      res.on('data', (c) => data += c);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); } catch (e) { resolve(data); }
      });
    }).on('error', reject);
  });
}

const mode = process.argv[2];

(async () => {
  if (mode === 'tags') {
    const tags = await api(`/repos/${REPO}/tags`);
    console.log(JSON.stringify(tags.map(t => ({ name: t.name, sha: t.commit.sha })), null, 2));
  } else if (mode === 'tree') {
    const sha = process.argv[3];
    const tree = await api(`/repos/${REPO}/git/trees/${sha}?recursive=1`);
    if (tree.tree) {
      tree.tree.forEach(f => console.log(f.type, f.path));
    } else {
      console.log(JSON.stringify(tree, null, 2));
    }
  } else if (mode === 'file') {
    const sha = process.argv[3];
    const path = process.argv[4];
    const blob = await api(`/repos/${REPO}/contents/${path}?ref=${sha}`);
    if (blob.content) {
      console.log(Buffer.from(blob.content, 'base64').toString('utf8'));
    } else {
      console.log(JSON.stringify(blob, null, 2));
    }
  } else if (mode === 'commit') {
    const sha = process.argv[3];
    const c = await api(`/repos/${REPO}/commits/${sha}`);
    console.log(JSON.stringify(c, null, 2));
  } else {
    console.log('usage: node gh_tags_explore.js [tags|tree <sha>|file <sha> <path>|commit <sha>]');
  }
})();
