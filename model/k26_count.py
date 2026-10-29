"""Knesset 26 completed count, computed by us from the CEC live files (latest snapshot): votes, shares, seats, totals.
OUR CALCULATION from the CEC file. The CEC says the count is complete (29.10.2026) and official results are due 4.11.2026; this is not the official publication."""
import json, warnings; warnings.filterwarnings("ignore")
from .load import load_live, live_snapshots
from .project import party_cols
from .backtest import seats_of, AGREEMENTS
# Seat numbers as announced in the press on 29.10 (citing the CEC count), for cross-check only.
ANNOUNCED = {"מחל": 27, "דרך": 21, "רק": 12, "ודם": 11, "עם": 8, "אמת": 8, "ל": 7, "ג": 7, "ב": 7, "שס": 6, "ט": 6}
ANNOUNCED_SRC = ["https://en.globes.co.il/en/article-count-complete-likud-has-27-knesset-seats-shas-drops-to-6-1001561412", "https://www.calcalistech.com/ctechnews/article/bkkzoebtgl", "https://www.i24news.tv/he/news/israel-elections-2026/artc-81364d4f"]
def main():
    stamp, path = live_snapshots()[-1]; d = load_live(path); pc = party_cols(d); tot = d[pc].sum(); r = d[~d.is_envelope]; e = d[d.is_envelope]
    yc = ["y_" + l for l in pc]; s = seats_of(dict(zip(yc, tot.values.astype(float))), yc, AGREEMENTS.get(26, []))
    seats = {k[2:] if k.startswith("y_") else k: v for k, v in s.items() if v}
    out = dict(snapshot=stamp, regular_boxes=int(len(r)), envelope_rows=int(len(e)), registered_regular=int(r.registered.sum()),
               voters_regular=int(r.voters.sum()), voters_envelopes=int(e.voters.sum()), voters_total=int(d.voters.sum()),
               valid_total=int(d.valid.sum()), invalid_total=int(d.invalid.sum()),
               turnout_pct_incl_envelopes=round(100 * d.voters.sum() / r.registered.sum(), 2),
               lists={l: dict(votes=int(tot[l]), share_pct=round(100 * tot[l] / tot.sum(), 3), seats=int(seats.get(l, 0)), announced=ANNOUNCED.get(l)) for l in tot.sort_values(ascending=False).index if tot[l] / tot.sum() > 0.005},
               matches_announced=all(seats.get(k, 0) == v for k, v in ANNOUNCED.items()) and sum(seats.values()) == 120, announced_sources=ANNOUNCED_SRC)
    json.dump(out, open("results/k26_count.json", "w"), ensure_ascii=False, indent=1); print({k: v for k, v in out.items() if k != "lists"})
if __name__ == "__main__": main()
