const crypto = require('crypto');

const TARGET = '179ad45c6ce2cb97cf1029e212046e81';

const candidates = [
  'testuser', 'test123', 'password', 'password123', 'test', 'Test1234',
  'testuser123', 'roundcube', 'rainloop', 'webmail', 'webmail123',
  'nginx-config-relay-mail', 'relay123', 'relay2023', 'cjwebmail',
  'stage3', 'Stage3!', 'changeme', 'temp123', 'testpass', 'letmein',
  'admin', 'admin123', 'welcome1', 'qwerty123', 'test1234', 'testuser1',
  'cjtest', 'testaccount', 'novise', 'svc-monitor', 'monitor123',
  'CJinternal2026', 'cj123456', 'internal2026', '12345678', 'password1',
  'test@123', 'Passw0rd', 'P@ssw0rd', 'roundcube123', 'mailtest',
  'mail1234', 'edge-relay', 'edgerelay', 'relay-legacy-2023',
  'nginx123', 'config123', 'guest', 'guest123', 'demo', 'demo123'
];

for (const c of candidates) {
  const h = crypto.createHash('md5').update(c).digest('hex');
  if (h === TARGET) {
    console.log('MATCH:', c);
    process.exit(0);
  }
}
console.log('no match in wordlist of', candidates.length, 'candidates');
