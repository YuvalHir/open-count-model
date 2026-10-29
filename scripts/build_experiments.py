"""Build results/experiments.csv: one row per experiment, all numbers from results/*.csv and data files.
Rule (fixed when this table was written, applied to experiments run earlier): change in error >= 5% lower = better; >= 5% higher = worse; otherwise no effect."""
import numpy as np, pandas as pd
R = "results/"
rows = []
def add(area, tried, metric, base, var, data, note=""):
    ch = 100 * (var - base) / base
    verdict = "better" if ch <= -5 else ("worse" if ch >= 5 else "none")
    rows.append(dict(area=area, tried=tried, metric=metric, baseline=round(base, 3), variant=round(var, 3), change_pct=round(ch, 1), verdict=verdict, data=data, note=note))
bt = pd.read_csv(R + "backtest.csv")
def g(o, m, f): return bt[(bt.order == o) & (bt.method == m) & np.isclose(bt.frac, f)].seats_misallocated.mean()
for f in (0.05, 0.20):
    add("projection", f"המודל מול סיכום גולמי, נספרו {int(f*100)}% (סדר אקראי)", "מנדטים שגויים", g("random", "raw_counted", f), g("random", "ridge", f), "פיתוח: כנסות 22-26, סדר מדומה")
add("projection", "המודל מול סיכום גולמי, נספרו 20% (סדר מוטה, המקרה הגרוע)", "מנדטים שגויים", g("low_likud_first", "raw_counted", .2), g("low_likud_first", "ridge", .2), "פיתוח: כנסות 22-26, סדר מדומה")
m = pd.read_csv(R + "matching.csv").groupby("strategy").mean(numeric_only=True)
add("matching", "השלמת קלפיות שלא הותאמו לפי גודל (התאמה 83% ל-92%)", "טעות בנתח הקולות, 20% נספרו", m.loc["exact", "random_20_shareMAE"], m.loc["fill", "random_20_shareMAE"], "פיתוח: כנסות 22-26", "ההתאמה עלתה, הטעות כמעט לא השתנתה")
add("matching", "התאמה לפי כתובת הקלפי", "טעות בנתח הקולות, 20% נספרו", m.loc["fill", "random_20_shareMAE"], m.loc["site", "random_20_shareMAE"], "פיתוח: כנסות 22-26", "אין שיפור בכנסת 26")
add("matching", "התאמה לפי כתובת, גרסת שימוש חוזר בכתובת", "טעות בנתח הקולות, 20% נספרו", m.loc["fill", "random_20_shareMAE"], m.loc["site2", "random_20_shareMAE"], "פיתוח: כנסות 22-26", "התאמה גבוהה יותר, תוצאה גרועה יותר")
for nm, tx, nt in (("split", "התאמה עם פיצול קלפיות (מקום אחד לכמה)", "התאמה כמעט לא עלתה"), ("fillcum", "יישור לפי סכום בוחרים מצטבר בתוך יישוב (התאמה 76% ל-89% בכנסת 26)", "התאמות שגויות: גרוע מהחזרה לפרופיל היישוב")):
    q = pd.read_csv(R + ("matching_split.csv" if nm == "split" else "matching_cum.csv")); q = q.groupby("strategy").mean(numeric_only=True)
    add("matching", tx, "טעות בנתח הקולות, 20% נספרו", q.loc["fill", "random_20_shareMAE"], q.loc[nm, "random_20_shareMAE"], "פיתוח: כנסות 22-26 (נקבע מראש, matching-split-v1)", nt)
l = pd.read_csv(R + "loo.csv")
add("matching", "בחירת פרמטרים לפי כנסות אחרות (עזיבת בחירות אחת)", "מנדטים שגויים", l.default_held_seats.mean(), l.held_seats.mean(), "מוחזק בחוץ: כל כנסת בתורה", "אין יתרון על ברירת המחדל")
add("envelopes", "קולות מעטפות חיצוניות: נטייה היסטורית מול 'כמו הקלפיות הרגילות'", "טעות בנתח הקולות", 0.565, 0.531, "מוחזק בחוץ: כנסת 25", "מפספס שינויים חדשים; מקור: results/envelope_backtest.txt")
_s = pd.read_csv(R + "sizemodel.csv")
def _sg(o, m, f): return _s[(_s.order == o) & (_s["mode"] == m) & np.isclose(_s.frac, f)].share_mae_pp.mean()
add("size", "מודל גודל קלפי (רגרסיה על שינוי בגודל), 20% נספרו, סדר אקראי", "טעות בנתח הקולות", _sg("random", "base", .2), _sg("random", "size_ridge", .2), "פיתוח: כנסות 22-26 (נקבע מראש, sizemodel-v1)", "משתפר בסדר אקראי אבל מחמיר בסדר של הצבעה נמוכה קודם (47% יותר): נדחה לפי הכלל שנקבע מראש")
add("size", "מודל גודל קלפי, אותו מודל, סדר 'הצבעה נמוכה קודם', 20% נספרו", "טעות בנתח הקולות", _sg("low_turnout_first", "base", .2), _sg("low_turnout_first", "size_ridge", .2), "פיתוח: כנסות 22-26 (נקבע מראש, sizemodel-v1)", "הסיבה לדחייה")
t = pd.read_csv(R + "turnout_k26.csv"); t = t[t.order == "random"].groupby(["size_from_turnout", "turnout_feature"]).share_mae_pp.mean()
add("turnout", "גודל קלפי מקובץ ההצבעה ב-20:00", "טעות בנתח הקולות", t[(0, 0)], t[(1, 0)], "פיתוח: כנסת 26")
add("turnout", "אחוז הצבעה כמשתנה במודל", "טעות בנתח הקולות", t[(0, 0)], t[(0, 1)], "פיתוח: כנסת 26")
d = pd.read_csv(R + "exitpoll_dash.csv"); d = d[d["T"].isin([22, 23, 24, 25]) & (d.n == 120) & (d.m == 200)]
def v(des, hard): 
    q = d[(d.design == des)]; q = q[(q.pat == "shy") & (q.lv == 10) & (q.nr == "nr_refuse")] if hard else q[(q.pat == "none") & (q.nr == "none")]
    return q.seats_oop.mean()
add("exitpoll", "מדגם יציאה: המודל האידיאלי מול הגרלה רגילה, בלי בעיות", "מנדטים שגויים", v("pps_ratio", 0), v("strat_greg_ps_bk", 0), "פיתוח: סימולציה, כנסות 22-25")
add("exitpoll", "מדגם יציאה: המודל האידיאלי מול הגרלה רגילה, בהנחות קשות", "מנדטים שגויים", v("pps_ratio", 1), v("strat_greg_ps_bk", 1), "פיתוח: סימולציה, כנסות 22-25", "הנחות על שקר ואי מענה הן שלנו")
add("exitpoll", "גודל הקלפי מאחוז ההצבעה ביום הבחירות (רעש 3%, הנחה)", "מנדטים שגויים", v("strat_prior", 0), v("strat_prior_tw", 0), "פיתוח: סימולציה, כנסות 22-25", "אחוז הצבעה ארצי לבדו לא מוסיף")
add("exitpoll", "שקלול לפי 'למי הצבעת בפעם הקודמת' (לבדו)", "מנדטים שגויים", v("strat_prior", 0), v("strat_prior_pastvote", 0), "פיתוח: סימולציה, כנסות 22-25")
bu = pd.read_csv(R + "exitpoll_budget.csv"); bu = bu[(bu.design == "strat_prior") & bu["T"].isin([22, 23, 24, 25])]
b = lambda n, mm: bu[(bu.n_places == n) & (bu.m == mm)].seats_out_of_place.mean()
add("exitpoll", "להכפיל את מספר הקלפיות (60 ל-120)", "מנדטים שגויים", b(60, 100), b(120, 100), "פיתוח: סימולציה, כנסות 22-25")
add("exitpoll", "להכפיל את מספר הראיונות בכל קלפי (100 ל-200)", "מנדטים שגויים", b(60, 100), b(60, 200), "פיתוח: סימולציה, כנסות 22-25")
try:
    L = pd.read_csv(R + "lies_mc.csv"); L = L[(L.n == 120) & (L.regime == "all")].set_index("design")["mean"]
    add("lying", "מונטה קרלו על שקרנים: המודל האידיאלי מול הגרלה רגילה", "מנדטים שגויים (ממוצע)", L["pps_ratio"], L["strat_greg_ps_bk"], "פיתוח: סימולציה, התפלגות הנחה", "")
    add("lying", "מונטה קרלו על שקרנים: שקלול לפי הצבעה קודמת מול מודל מרובד", "מנדטים שגויים (ממוצע)", L["strat_prior"], L["strat_prior_pastvote"], "פיתוח: סימולציה, התפלגות הנחה", "שקרנים עקביים שוברים את השקלול")
except FileNotFoundError: pass
pd.DataFrame(rows).to_csv(R + "experiments.csv", index=False)
print(pd.DataFrame(rows)[["tried", "baseline", "variant", "change_pct", "verdict"]].to_string())
