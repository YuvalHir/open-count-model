#!/usr/bin/env python3
"""Fetch the CBS socio-economic index 2021 per locality (CBS GIS ArcGIS service). Source: הלמ"ס. Used under the CBS usage license (attribution). Not committed; run this script."""
import json, os, urllib.request, urllib.parse, csv
OUT = os.path.join(os.path.dirname(__file__), "..", "data-raw", "cbs"); os.makedirs(OUT, exist_ok=True)
base = "https://services2.arcgis.com/xMRYm7cNgdR5RN6F/arcgis/rest/services/" + urllib.parse.quote("אשכולחברתיכלכלי2021לפייישוב_ExportFeatures") + "/FeatureServer/26"
u = base + "/query?where=1%3D1&outFields=" + urllib.parse.quote("SETL_CODE,CODE_OF_LOCALITY,HEB_NAME,INDEX_VALUE_2021,CLUSTER_2021,סך_הכל_אוכלוסייה_2021") + "&returnGeometry=false&resultRecordCount=2000&f=json"
r = json.loads(urllib.request.urlopen(urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"}), timeout=90).read())
with open(os.path.join(OUT, "cbs_index_2021.csv"), "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f); w.writerow(["loc_code", "name", "index_2021", "cluster_2021", "pop_2021"])
    for ft in r["features"]:
        a = ft["attributes"]; code = a["SETL_CODE"] if a["SETL_CODE"] is not None else a["CODE_OF_LOCALITY"]
        w.writerow([int(code), a["HEB_NAME"], a["INDEX_VALUE_2021"], a["CLUSTER_2021"], a["סך_הכל_אוכלוסייה_2021"]])
print(len(r["features"]), "rows")
