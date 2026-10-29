"""Load CEC station-level results (history from data.gov.il, 2026 live snapshots).

Output frame columns: knesset, loc_code, loc_name, station (float, e.g. 3.1), registered,
voters, invalid, valid, plus one integer column per list letter (votes).
Rows of "external envelope" boxes (loc_code 9999) are kept but flagged in `is_envelope`.
"""
import glob, gzip, io, os
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
META_RENAME = {
    "שם ישוב": "loc_name", "סמל ישוב": "loc_code", "קלפי": "station", "מספר קלפי": "station",
    "ברזל": "ballot_id", "בזב": "registered", "מצביעים": "voters", "פסולים": "invalid", "כשרים": "valid",
}
NOT_PARTY = {"סמל ועדה", "ריכוז", "שופט", "חיצוניות", "קלפי אחרת", "", "Unnamed: 0"}

def _read_text(raw: bytes) -> str:
    for enc in ("utf-8-sig", "cp1255"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("cp1255", errors="replace")

def parse_station_csv(raw: bytes, knesset: int) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(_read_text(raw)), dtype=str)
    df.columns = [c.strip() for c in df.columns]
    df = df.loc[:, [c for c in df.columns if c and not c.startswith("Unnamed")]]
    df = df.rename(columns=META_RENAME)
    party_cols = [c for c in df.columns if c not in META_RENAME.values() and c not in NOT_PARTY]
    for c in ["loc_code", "station"] + (["ballot_id"] if "ballot_id" in df.columns else []) + ["registered", "voters", "invalid", "valid"] + party_cols:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df[party_cols] = df[party_cols].fillna(0)
    if "ballot_id" not in df.columns:
        df["ballot_id"] = float("nan")
    df = df.dropna(subset=["loc_code", "station"]).copy()
    df["loc_code"] = df["loc_code"].astype(int)
    df["loc_name"] = df["loc_name"].astype(str).str.strip()
    df["knesset"] = knesset
    df["is_envelope"] = df["loc_code"] == 9999
    df.attrs["party_cols"] = party_cols
    keep = ["knesset", "loc_code", "loc_name", "station", "ballot_id", "registered", "voters", "invalid", "valid", "is_envelope"]
    out = df[keep + party_cols].reset_index(drop=True)
    out.attrs["party_cols"] = party_cols
    return out

def load_history(knesset: int) -> pd.DataFrame:
    path = os.path.join(ROOT, "data-raw", "cec_history", f"ballots_k{knesset}.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} missing - run scripts/fetch_history.py")
    return parse_station_csv(open(path, "rb").read(), knesset)

def live_snapshots():
    """Sorted list of (utc_stamp, dir) for saved live snapshots."""
    d = sorted(glob.glob(os.path.join(ROOT, "data-raw", "live", "2*Z")))
    return [(os.path.basename(x), x) for x in d]

def load_live(snapshot_dir: str, name: str = "expb") -> pd.DataFrame:
    raw = gzip.open(os.path.join(snapshot_dir, name + ".csv.gz"), "rb").read()
    return parse_station_csv(raw, 26)

def party_cols(df):
    return df.attrs["party_cols"]

def to_places(df: pd.DataFrame) -> pd.DataFrame:
    """Merge sub-boxes (station numbers like 5.1, 5.2, 5.3) into one voting place (locality, 5).
    Box numbers change between elections, so the place is the most stable unit we have
    without addresses. Envelope boxes are kept as separate rows (loc_code 9999)."""
    pc = party_cols(df)
    d = df.copy()
    d["place"] = d.station.astype(float).apply(lambda x: int(x))
    num = ["registered", "voters", "invalid", "valid"] + pc
    g = d.groupby(["knesset", "loc_code", "place", "is_envelope"], as_index=False)
    out = g[num].sum()
    names = d.groupby(["loc_code"]).loc_name.first()
    out["loc_name"] = out.loc_code.map(names)
    out = out.rename(columns={"place": "station"})
    out["station"] = out.station.astype(float)
    out["ballot_id"] = float("nan")
    out.attrs["party_cols"] = pc
    return out
