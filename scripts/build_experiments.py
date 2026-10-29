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
_w = pd.read_csv(R + "swing.csv")
def _wg(o, m, f): return _w[(_w.order == o) & (_w["mode"] == m) & np.isclose(_w.frac, f)].share_mae_pp.mean()
add("swing", "תנודה לאומית במקום רגרסיה, 20% נספרו, סדר אקראי", "טעות בנתח הקולות", _wg("random", "base", .2), _wg("random", "swing_full", .2), "פיתוח: כנסות 22-26 (נקבע מראש, swing-v1)", "גרוע יותר בכל חמש הבחירות: נדחה")
add("swing", "תנודה לאומית, 5% נספרו, סדר ליכוד נמוך קודם", "טעות בנתח הקולות", _wg("low_likud_first", "base", .05), _wg("low_likud_first", "swing_full", .05), "פיתוח: כנסות 22-26 (נקבע מראש, swing-v1)", "עוזר בהתחלה בסדר מוטה, מזיק כשנספר יותר: לא מאומץ")
_m = pd.read_csv(R + "matchsens.csv"); _m = _m[(_m.order == "random") & np.isclose(_m.frac, .2) & (_m.kind != "large_first")]
_m["t"] = (_m.target * 100).round()
add("matching", "הורדת אחוז הקולות בקלפיות מותאמות מ-90% ל-65% (דיאגנוסטי), 20% נספרו", "טעות בנתח הקולות", _m[_m.t == 90].share_mae_pp.mean(), _m[_m.t == 65].share_mae_pp.mean(), "פיתוח: כנסות 22-26 (נקבע מראש, matchsens-v1)", "ההשפעה מתונה: עד 76% כמעט אין פגיעה")
_e = pd.read_csv(R + "envelope_models.csv"); _eg = _e.groupby(["scheme", "model"]).mae_pp.mean()
add("envelopes", "מודל יחס במקום מודל הפרש למעטפות, רק עבר (כנסות 23-26)", "טעות בנתח הקולות במעטפות", _eg[("past_only", "additive")], _eg[("past_only", "ratio")], "פיתוח: כנסות 23-26 (נקבע מראש, ideas569-v1)", "עומד בכלל שנקבע, אבל בלי הבדל במנדטים")
add("envelopes", "מודל יחס במקום מודל הפרש, כל הכנסות האחרות כהיסטוריה", "טעות בנתח הקולות במעטפות", _eg[("loo", "additive")], _eg[("loo", "ratio")], "פיתוח: כנסות 22-26 (נקבע מראש, ideas569-v1)", "לא יציב: רשימות קטנות בהיסטוריה מנפחות את היחס")
_r = pd.read_csv(R + "rake_exit.csv"); _r = _r[_r.n == 60]
def _rg(sc, d): return _r[(_r.scenario.isin(sc)) & (_r.design == d)].seats_oop.mean()
add("exitpoll", "שקלול (rake) לפי הצבעה קודמת בתוך קבוצות פרופיל, חוסר מענה, 60 קלפיות", "מנדטים שגויים", _rg(["shy15", "hard_nr"], "strat_prior"), _rg(["shy15", "hard_nr"], "rake_pg"), "פיתוח: סימולציה, כנסות 22-26 (נקבע מראש, ideas569-v1)", "משתפר כשיש חוסר מענה")
add("exitpoll", "אותו שקלול, בלי בעיות במענה", "מנדטים שגויים", _rg(["none"], "strat_prior"), _rg(["none"], "rake_pg"), "פיתוח: סימולציה, כנסות 22-26 (נקבע מראש, ideas569-v1)", "מחמיר בלי בעיות ובשקר מעורב: נדחה")
_q = pd.read_csv(R + "round2.csv"); _q = _q[_q["T"] >= 23]
def _qg(o, m, f): return _q[(_q.order == o) & (_q["mode"] == m) & np.isclose(_q.frac, f)].share_mae_pp.mean()
add("weights", "משקולות לפי הבדל בין קלפיות שנספרו ללא נספרו, 5% נספרו, סדר ליכוד נמוך קודם", "טעות בנתח הקולות", _qg("low_likud_first", "base", .05), _qg("low_likud_first", "iw", .05), "פיתוח: כנסות 23-26 (נקבע מראש, round2-v1)", "לא עוזר, נדחה")
add("transfer", "מודל מעבר קולות עם התחלה מהבחירות הקודמות, 5% נספרו, ליכוד נמוך קודם", "טעות בנתח הקולות", _qg("low_likud_first", "base", .05), _qg("low_likud_first", "transfer_k002", .05), "פיתוח: כנסות 23-26 (נקבע מראש, round2-v1)", "משתפר בכל ארבע הבחירות, אבל המודל נדחה: ראו שתי השורות הבאות")
add("transfer", "אותו מודל מעבר, 20% נספרו, סדר אקראי", "טעות בנתח הקולות", _qg("random", "base", .2), _qg("random", "transfer_k002", .2), "פיתוח: כנסות 23-26 (נקבע מראש, round2-v1)", "פי 4.5 יותר גרוע בסדר אקראי: נדחה לפי הכלל")
add("transfer", "אותו מודל מעבר, 20% נספרו, סדר הצבעה נמוכה קודם", "טעות בנתח הקולות", _qg("low_turnout_first", "base", .2), _qg("low_turnout_first", "transfer_k002", .2), "פיתוח: כנסות 23-26 (נקבע מראש, round2-v1)", "גרוע יותר")
_h = pd.read_csv(R + "holdout.csv")
def _hg(o, m, f, col, ts=(19, 20, 21)): return _h[(_h.order == o) & (_h.method == m) & np.isclose(_h.frac, f) & _h["T"].isin(ts)][col].mean()
_HD = "מוחזק בחוץ: כנסות 19-21, נקבע מראש (holdout-v1)"
add("holdout", "המודל מול סיכום גולמי, 5% נספרו, סדר אקראי (כנסות 19-21)", "מנדטים שגויים", _hg("random", "raw_counted", .05, "seats"), _hg("random", "ridge", .05, "seats"), _HD, "מנדטים שלנו, בלי הסכמי עודפים")
add("holdout", "המודל מול סיכום גולמי, 20% נספרו, סדר ליכוד נמוך קודם (כנסות 19-21)", "מנדטים שגויים", _hg("low_likud_first", "raw_counted", .2, "seats"), _hg("low_likud_first", "ridge", .2, "seats"), _HD, "")
add("holdout", "המודל מול סיכום גולמי, 20% נספרו, סדר אקראי, טעות בנתחים (כנסות 19-21)", "טעות בנתח הקולות", _hg("random", "raw_counted", .2, "share_mae_pp"), _hg("random", "ridge", .2, "share_mae_pp"), _HD, "כישלון: בכנסת 21 המודל גרוע מהסיכום הגולמי (0.37 מול 0.18)")
add("holdout", "מודל מעבר קולות מול המודל, 5% נספרו, ליכוד נמוך קודם (כנסות 20-21)", "טעות בנתח הקולות", _hg("low_likud_first", "ridge", .05, "share_mae_pp", (20, 21)), _hg("low_likud_first", "transfer_k002", .05, "share_mae_pp", (20, 21)), _HD, "חזרה על ההובלה המוקדמת; המודל נשאר נדחה")
add("holdout", "מודל מעבר קולות מול המודל, 20% נספרו, סדר אקראי (כנסות 20-21)", "טעות בנתח הקולות", _hg("random", "ridge", .2, "share_mae_pp", (20, 21)), _hg("random", "transfer_k002", .2, "share_mae_pp", (20, 21)), _HD, "חזרה על ההפסד בסדר אקראי")
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

try:
    S = pd.read_csv(R + "switch.csv"); S["set"] = S["T"].apply(lambda t: "dev" if t >= 23 else "hold")
    sv = lambda st, o, f, m: S[(S.set == st) & (S.order == o) & (S.frac == f) & (S.method == m)].seats.mean()
    for st, lab in (("dev", "פיתוח: כנסות 23-26"), ("hold", "מדגם מוחזק: כנסות 20-21")):
        add("switch", "מעבר אוטומטי למודל ההעברה לפי סטיית g: סדר מוטה (5% נספרו)", "מנדטים שגויים", sv(st, "low_likud_first", 0.05, "base"), sv(st, "low_likud_first", 0.05, "switch"), lab, "")
        add("switch", "מעבר אוטומטי למודל ההעברה לפי סטיית g: סדר אקראי (5% נספרו)", "מנדטים שגויים", sv(st, "random", 0.05, "base"), sv(st, "random", 0.05, "switch"), lab, "לא אומץ: פוגע בסדר אקראי בפיתוח")
except FileNotFoundError: pass
try:
    C = pd.read_csv(R + "cbs_feat.csv"); C = C[C["T"] >= 22]
    for o, lab in (("low_likud_first", "סדר מוטה"), ("random", "סדר אקראי")):
        q = C[(C.order == o) & (C.frac == 0.2)].groupby("mode").share_mae_pp.mean()
        add("data", "מדד חברתי-כלכלי של הלמ\"ס כמשתנה נוסף: " + lab + " (20% נספרו)", "שגיאת נתח (נק' אחוז)", q["base"], q["cbs"], "פיתוח: כנסות 22-26", "אין שיפור לפי הכלל שנקבע מראש")
except FileNotFoundError: pass

try:
    R3 = pd.read_csv(R + "round3.csv"); R3 = R3[R3["T"] >= 23]
    q3 = lambda o, f, m: R3[(R3.order == o) & (R3.frac == f) & (R3.method == m)].seats.mean()
    for o, lab in (("pl8", "סדר מוטה מאוד"), ("pl0", "סדר אקראי")):
        add("stack", "שילוב מודלים בזמן אמת (ערימה רציפה של בסיס, העברה וקיזוז): " + lab + " (5% נספרו)", "מנדטים שגויים", q3(o, 0.05, "base"), q3(o, 0.05, "stack"), "פיתוח: כנסות 23-26", "לא אומץ: נכשל בכלל שנקבע מראש")
        add("stack", "מודל ההעברה עם קנס קבוע (לא גדל עם הספירה): " + lab + " (5% נספרו)", "מנדטים שגויים", q3(o, 0.05, "base"), q3(o, 0.05, "transfer_const"), "פיתוח: כנסות 23-26", "לא אומץ")
except FileNotFoundError: pass
pd.DataFrame(rows).to_csv(R + "experiments.csv", index=False)
print(pd.DataFrame(rows)[["tried", "baseline", "variant", "change_pct", "verdict"]].to_string())
