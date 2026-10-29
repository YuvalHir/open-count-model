const S = window.__occ; if (!S) return {error: 'watcher not running (page was navigated away?)'};
const out = {snaps: S.snaps.splice(0), polls: S.polls.splice(0), running: S.running, started: S.started, now: new Date().toISOString()};
return out;
