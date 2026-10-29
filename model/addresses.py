"""Polling-place addresses from the CEC's own station lists (K21-K25) and the K26 govmap layer.
See data-raw/addresses/README.md for sources. Only used to tell which voting places are the same building."""
import os, re
import pandas as pd
from .load import ROOT

def norm(s):
    s = str(s).replace('"', "").replace("״", "").replace("'", "").replace("׳", "")
    s = s.replace("בית ספר", "ביס").replace("בי\u05d4ס", "ביס").replace("ביה ס", "ביס")
    return re.sub(r"[^\w]", "", s)

def load_addr(T):
    p = os.path.join(ROOT, "data-raw", "addresses", f"k{T}.csv.gz")
    if not os.path.exists(p):
        return None
    d = pd.read_csv(p)
    d["place_no"] = d.station.astype(float).astype(int)
    d = d.drop_duplicates(["loc_code", "place_no"])
    d["s_addr"] = d.address.map(norm)
    d["s_name"] = d.place.map(norm)
    cols = ["loc_code", "place_no", "s_addr", "s_name"] + (["registered_listed"] if "registered_listed" in d else [])
    return d[cols]
