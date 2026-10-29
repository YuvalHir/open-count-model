"""K26 exit polls vs OUR calculation of the completed count (results/k26_count.json, from the CEC file; matches the seat numbers announced 29.10). Official CEC publication is due 4.11.2026: NOT official, NOT the preregistered scoring."""
import csv, json, collections
M = {"Likud": "מחל", "Yashar": "דרך", "Together": "רק", "Joint List": "ודם", "Ra'am": "עם", "Democrats": "אמת", "Yisrael Beiteinu": "ל", "Otzma": "ב", "Shas": "שס", "UTJ": "ג", "Religious Zionism": "ט"}
LF = json.load(open("results/k26_count.json"))["lists"]; fin = {k: v["seats"] for k, v in LF.items() if v["seats"]}
P = collections.defaultdict(dict)
for r in csv.DictReader(open("data/tv_exit_polls/tv_exit_polls.csv", encoding="utf-8")):
    if r["election"] == "26" and r["complete"] == "full": P[r["channel"]][M[r["list"]]] = int(r["seats"])
rows = []
for ch, p in P.items():
    ls = set(fin) | {l for l, v in p.items() if v >= 1}
    d = {l: abs(p.get(l, 0) - fin.get(l, 0)) for l in ls}
    rows.append(dict(channel=ch, sum_pred=sum(p.values()), out_of_place=sum(d.values()) / 2, likud_err=p.get("מחל", 0) - fin["מחל"], arab_err=sum(p.get(l, 0) for l in ("ודם", "עם")) - sum(fin[l] for l in ("ודם", "עם"))))
with open("results/tv_k26_provisional.csv", "w", newline="") as f:
    w = csv.DictWriter(f, list(rows[0])); w.writeheader(); w.writerows(rows)
for r in rows: print(r)
print("seats (our calculation of the completed count):", sum(fin.values()), fin)
