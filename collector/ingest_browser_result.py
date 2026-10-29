#!/usr/bin/env python3
"""Save snapshots returned by the browser-side collector (collector/watch.js).

Input: the JSON printed by the browser harvest call (--json output of execute-js).
Each snapshot entry becomes data-raw/live/<UTC stamp>/<name>.csv.gz plus a meta.json,
and one line is appended to data-raw/live/polls.jsonl.
Usage: ingest_browser_result.py HARVEST.json OUT_DIR
"""
import base64, json, os, re, sys

def main(src, out):
    outer = json.load(open(src, encoding="utf8"))
    data = json.loads(outer["content"]) if "content" in outer else outer
    if isinstance(data, dict) and "result" in data and not data.get("snaps"):
        data = data["result"]
    os.makedirs(os.path.join(out, "live"), exist_ok=True)
    n = 0
    for s in data.get("snaps", []):
        stamp = re.sub(r"[^0-9TZ]", "", s["fetched_at_utc"].split(".")[0]) + "Z"
        d = os.path.join(out, "live", stamp)
        os.makedirs(d, exist_ok=True)
        meta = {k: v for k, v in s.items() if k not in ("files",)}
        for name, f in s.get("files", {}).items():
            with open(os.path.join(d, name + ".csv.gz"), "wb") as fh:
                fh.write(base64.b64decode(f["gz_b64"]))
            meta[name] = {k: v for k, v in f.items() if k != "gz_b64"}
        json.dump(meta, open(os.path.join(d, "meta.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
        n += 1
    with open(os.path.join(out, "live", "polls.jsonl"), "a", encoding="utf8") as fh:
        for p in data.get("polls", []):
            fh.write(json.dumps(p, ensure_ascii=False) + "\n")
    print(f"saved {n} snapshots, {len(data.get('polls', []))} poll records")

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
