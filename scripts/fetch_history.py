#!/usr/bin/env python3
"""Download official CEC station-level results (Knesset 18-25) from data.gov.il.

Dataset: https://data.gov.il/dataset/votes-knesset  (publisher: Central Elections Committee,
license shown on the portal: "Other (Open)"; terms: https://data.gov.il/terms).
Files are not committed to this repo; run this script to fetch them into data-raw/cec_history/.
"""
import csv, io, json, os, sys, urllib.request

UA = "Mozilla/5.0 (X11; Linux x86_64) Chrome/120 Safari/537.36"
OUT = os.path.join(os.path.dirname(__file__), "..", "data-raw", "cec_history")

def get(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=120).read()

def main():
    os.makedirs(OUT, exist_ok=True)
    pkg = json.loads(get("https://data.gov.il/api/3/action/package_show?id=votes-knesset"))["result"]
    for r in pkg["resources"]:
        name = r.get("name", "")
        if "קלפיות" not in name or r.get("format") not in ("CSV", "XLS"):
            continue
        k = "".join(ch for ch in name.split("ה-")[1][:3] if ch.isdigit())
        dest = os.path.join(OUT, f"ballots_k{k}.{r['format'].lower()}")
        if os.path.exists(dest):
            continue
        print("fetching", k, r["url"])
        open(dest, "wb").write(get(r["url"]))

if __name__ == "__main__":
    main()
