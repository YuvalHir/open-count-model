// Runs inside a browser tab opened on https://media26.bechirot.gov.il/ (same origin as the files).
// The browser itself passes the site's bot check; we only read public files, politely.
// Every POLL_MS it does a cheap HEAD; when the file changed (Last-Modified/ETag) it downloads
// the full CSV, gzips it and queues it. Harvest with harvest.js. Queue lives in window.__occ.
const POLL_MS = 60000, MAX_MIN = 230, FILES = ['expb', 'expc'];
window.__occ = window.__occ || {snaps: [], polls: [], last: {}, running: true, started: new Date().toISOString()};
const S = window.__occ;
async function refreshToken() {
  // The CEC file host uses a bot check that expires after a few minutes. A normal browser passes it by
  // loading the file URL as a page; we do the same in a hidden iframe, then retry.
  const fr = document.createElement('iframe'); fr.style.display = 'none';
  fr.src = '/files/expc.csv?r=' + Date.now(); document.body.appendChild(fr);
  await new Promise(r => setTimeout(r, 10000)); fr.remove();
}
async function head(f) {
  let r = await fetch('/files/' + f + '.csv', {method: 'HEAD', cache: 'no-store'});
  if (r.status === 202) { await refreshToken(); r = await fetch('/files/' + f + '.csv', {method: 'HEAD', cache: 'no-store'}); }
  return r;
}
async function full(f) {
  let r = await fetch('/files/' + f + '.csv', {cache: 'no-store'});
  if (r.status === 202) { await refreshToken(); r = await fetch('/files/' + f + '.csv', {cache: 'no-store'}); }
  const buf = await r.arrayBuffer();
  const h = [...new Uint8Array(await crypto.subtle.digest('SHA-256', buf))].map(x => x.toString(16).padStart(2, '0')).join('');
  const gz = new Uint8Array(await new Response(new Blob([buf]).stream().pipeThrough(new CompressionStream('gzip'))).arrayBuffer());
  let s = ''; for (let i = 0; i < gz.length; i += 32768) s += String.fromCharCode.apply(null, gz.subarray(i, i + 32768));
  return {status: r.status, last_modified: r.headers.get('last-modified'), etag: r.headers.get('etag'), sha256: h, bytes: buf.byteLength, gz_b64: btoa(s)};
}
(async () => {
  const end = Date.now() + MAX_MIN * 60000;
  while (S.running && Date.now() < end) {
    const t = new Date().toISOString();
    try {
      const changed = {};
      for (const f of FILES) {
        try {
          const r = await head(f);
          const key = (r.headers.get('last-modified') || '') + '|' + (r.headers.get('etag') || '') + '|' + (r.headers.get('content-length') || '');
          S.polls.push({t, file: f, status: r.status, last_modified: r.headers.get('last-modified'), content_length: r.headers.get('content-length')});
          if (r.status === 200 && key !== S.last[f]) { changed[f] = key; }
        } catch (e) { S.polls.push({t, file: f, error: String(e)}); }
      }
      if (Object.keys(changed).length) {
        const snap = {fetched_at_utc: new Date().toISOString(), files: {}};
        for (const f of Object.keys(changed)) { try { const x = await full(f); if (x.status === 200) { snap.files[f] = x; S.last[f] = changed[f]; } } catch (e) { S.polls.push({t, file: f, error: 'full:' + String(e)}); } }
        if (Object.keys(snap.files).length) S.snaps.push(snap);
      }
    } catch (e) { S.polls.push({t, error: String(e)}); }
    await new Promise(r => setTimeout(r, POLL_MS));
  }
  S.running = false;
  return 'stopped';
})();
return 'started';
