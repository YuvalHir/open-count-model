"""Build docs/site/index.html (static, no external dependencies) from repo results.
Every number comes from results/*.csv, data-raw/live or a model run at build time.
    python3 docs/site/build.py
"""
import json, os, sys, warnings, html
warnings.filterwarnings("ignore")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT); os.chdir(ROOT)
import numpy as np, pandas as pd
from model.load import load_history, load_live, live_snapshots
from model.project import build_frame
from model.simulate import simulate
from model.backtest import seats_of, AGREEMENTS

REPO = "https://github.com/YuvalHir/open-count-model"
bt = pd.read_csv("results/backtest.csv"); cov = pd.read_csv("results/coverage.csv")
FR = [0.01, 0.02, 0.05, 0.10, 0.20, 0.40, 0.60, 0.80]

def g(order, method, frac, col="seats_misallocated", T=None):
    d = bt[(bt.order == order) & (bt.method == method) & (np.isclose(bt.frac, frac))]
    if T is not None: d = d[d["T"] == T]
    return float(d[col].mean())

# ---------- SVG helpers (text is real text, direction handled by the browser) ----------
def esc(s): return html.escape(str(s))
def line_chart(series, title, ylab, ymax, w=720, h=330):
    L, R, Tp, B = 56, 16, 14, 52
    pw, ph = w - L - R, h - Tp - B
    x = lambda i: L + pw * i / (len(FR) - 1)
    y = lambda v: Tp + ph * (1 - min(v, ymax) / ymax)
    o = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}" style="width:100%;height:auto;direction:ltr">']
    for t in np.linspace(0, ymax, 6):
        o.append(f'<line x1="{L}" x2="{w-R}" y1="{y(t):.1f}" y2="{y(t):.1f}" stroke="#ffffff22"/><text x="{L-8}" y="{y(t)+4:.1f}" text-anchor="end" font-size="12" fill="#a8b3d1">{t:.0f}</text>')
    for i, f in enumerate(FR):
        o.append(f'<text x="{x(i):.1f}" y="{h-B+18}" text-anchor="middle" font-size="12" fill="#a8b3d1">{f*100:.0f}%</text>')
    o.append(f'<text x="{L+pw/2}" y="{h-8}" text-anchor="middle" font-size="12.5" fill="#a8b3d1" direction="rtl">אחוז הקלפיות שנספרו</text>')
    o.append(f'<text transform="translate(14,{Tp+ph/2}) rotate(-90)" text-anchor="middle" font-size="12.5" fill="#a8b3d1" direction="rtl">{esc(ylab)}</text>')
    for name, vals, col, dash in series:
        pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(vals))
        da = 'stroke-dasharray="6 4"' if dash else ""
        o.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2.5" {da}/>')
        for i, v in enumerate(vals): o.append(f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="3" fill="{col}"/>')
    o.append("</svg>")
    leg = "".join(f'<span style="margin-left:14px;white-space:nowrap"><i class="k" style="background:{c}"></i>{esc(n)}</span>' for n, v, c, d in series)
    return f'<figure class="chart"><figcaption>{esc(title)}</figcaption><div class="legend">{leg}</div>{"".join(o)}</figure>'

def hbars(rows, title, unit="", vmax=None, colors=("#6b7694", "#2fd3c4"), names=()):
    vmax = vmax or max(max(r[1:]) for r in rows) * 1.1
    o = [f'<figure class="chart"><figcaption>{esc(title)}</figcaption>']
    if names: o.append('<div class="legend">' + "".join(f'<span style="margin-left:14px"><i class="k" style="background:{c}"></i>{esc(n)}</span>' for n, c in zip(names, colors)) + "</div>")
    for r in rows:
        o.append(f'<div class="row"><span class="lab">{esc(r[0])}</span><span class="bars">')
        for v, c in zip(r[1:], colors):
            o.append(f'<span class="bar" style="width:{100*v/vmax:.1f}%;background:{c}"><em>{v:.1f}{unit}</em></span>')
        o.append("</span></div>")
    o.append("</figure>"); return "".join(o)

def range_chart(items, title, w=720):
    # items: (label, lo, med, hi, truth); one row per list, x axis seats
    rowh = 26; h = 40 + rowh * len(items); L = 150; R = 20; xmax = max(i[3] for i in items) + 3
    x = lambda v: L + (w - L - R) * v / xmax
    o = [f'<svg viewBox="0 0 {w} {h}" style="width:100%;height:auto;direction:ltr" role="img" aria-label="{esc(title)}">']
    for t in range(0, int(xmax) + 1, 5):
        o.append(f'<line x1="{x(t):.1f}" x2="{x(t):.1f}" y1="10" y2="{h-24}" stroke="#ffffff22"/><text x="{x(t):.1f}" y="{h-8}" text-anchor="middle" font-size="12" fill="#a8b3d1">{t}</text>')
    for k, (lab, lo, med, hi, tr) in enumerate(items):
        yy = 20 + k * rowh
        o.append(f'<text x="{L-10}" y="{yy+5}" text-anchor="start" font-size="13" fill="#eef2ff" direction="rtl">{esc(lab)}</text>')
        o.append(f'<rect x="{x(lo):.1f}" y="{yy-6}" width="{max(x(hi)-x(lo),3):.1f}" height="12" rx="3" fill="#2fd3c4" opacity=".55"/>')
        o.append(f'<circle cx="{x(med):.1f}" cy="{yy}" r="3.5" fill="#fff"/>')
        o.append(f'<path d="M{x(tr):.1f} {yy-9} l5 9 l-5 9 l-5 -9z" fill="#ffd166"/>')
    o.append("</svg>")
    leg = '<span style="margin-left:14px"><i class="k" style="background:#2fd3c4"></i>טווח 80%</span><span style="margin-left:14px"><i class="k" style="background:#fff"></i>חציון</span><span><i class="k" style="background:#ffd166"></i>התוצאה הסופית הרשמית</span>'
    return f'<figure class="chart"><figcaption>{esc(title)}</figcaption><div class="legend">{leg}</div>{"".join(o)}</figure>'

# ---------- numbers ----------
match = {}
for T in (22, 23, 24, 25, 26):
    fr, yc, xc = build_frame(load_history(T) if T < 26 else load_live(live_snapshots()[-1][1]), load_history(T - 1))
    match[T] = (len(fr), float(fr.valid[fr.matched].sum() / fr.valid.sum()))
snaps = live_snapshots(); live_rows = []
prev = None
for st, d in snaps:
    m = json.load(open(os.path.join(d, "meta.json"))); df = load_live(d)
    reg = df[~df.is_envelope]
    live_rows.append((st, m["expb"]["last_modified"], len(df), int((~df.is_envelope).sum()), int(df.is_envelope.sum()), int(df.valid.sum())))
# Monte Carlo example: K25, 5% of places, random order
frame25, yc25, xc25 = build_frame(load_history(25), load_history(24))
rng = np.random.default_rng(0); mask = np.zeros(len(frame25), bool); mask[rng.permutation(len(frame25))[:int(0.05 * len(frame25))]] = True
mc, tm = simulate(frame25, yc25, xc25, mask, AGREEMENTS[25])
truth = seats_of(dict(zip(yc25, frame25[["v_" + y[2:] for y in yc25]].sum().values)), yc25, AGREEMENTS[25])
NAMES25 = {"מחל": "ליכוד", "פה": "יש עתיד", "ט": "הציונות הדתית", "כן": "המחנה הממלכתי", "שס": "ש״ס", "ג": "יהדות התורה", "ל": "ישראל ביתנו", "ום": "חד״ש-תע״ל", "עם": "רע״ם", "אמת": "העבודה", "ד": "בל״ד", "מרצ": "מרצ"}
items = [(f"{NAMES25.get(k,k)} ({k})", v["lo"], v["median"], v["hi"], truth.get(k, 0)) for k, v in sorted(mc.items(), key=lambda kv: -kv[1]["median"])]
cov_g = cov.groupby("frac")[["hit", "width"]].mean()
LF = json.load(open("results/live_forecast.json"))
_d = load_live(snaps[-1][1]); LFREG = int((~_d.is_envelope).sum()); K25REG = int((~load_history(25).is_envelope).sum())
N26 = {"מחל": "הליכוד", "דרך": "ישר!", "רק": "ביחד (בנט)", "ודם": "הרשימה המשותפת", "אמת": "הדמוקרטים", "עם": "רע״ם", "ב": "עוצמה יהודית", "ג": "יהדות התורה", "ל": "ישראל ביתנו", "ט": "הציונות הדתית", "שס": "ש״ס", "די": "המילואימניקים", "ך": "עמך ישראל"}
LFTBL = "".join(f"<tr><td>{N26.get(k,k)} ({k})</td><td>{v['share_counted_pct']:.2f}%</td><td>{v['seats_median']:.0f}</td><td>{v['seats_lo']:.0f} עד {v['seats_hi']:.0f}</td></tr>" for k, v in sorted(LF['lists'].items(), key=lambda kv: -kv[1]['seats_median']))

# ---------- page ----------
def tag(k, t): return f'<span class="t {k}">{t}</span>'
OFF, CALC = tag("off", "נתוני ועדת הבחירות"), tag("calc", "חישוב שלנו")
bb = pd.read_csv("results/bloc_backtest.csv")
def bg(order, method, frac, col="mae_bloc"):
    d = bb[(bb.order == order) & (bb.method == method) & np.isclose(bb.frac, frac)]
    return float(d[col].mean())
bc1 = line_chart([
    ("ספירה גולמית, סדר אקראי", [bg("random", "raw_counted", f) for f in FR], "#6b7694", False),
    ("המודל, סדר אקראי", [bg("random", "ridge", f) for f in FR], "#2fd3c4", False),
    ("ספירה גולמית, סדר מוטה (ליכוד נמוך קודם)", [bg("low_likud_first", "raw_counted", f) for f in FR], "#ff7a8e", True),
    ("המודל, אותו סדר מוטה", [bg("low_likud_first", "ridge", f) for f in FR], "#ffd166", True)],
    "שגיאה ממוצעת במנדטים של שלושת הגושים (ימין, ערבים, יתר), לפי חלק הקלפיות שנספרו", "מנדטים שגויים לגוש (ממוצע)", 60)
bbl = "".join(f"<tr><td>{int(f*100)}%</td><td>{bg('random','raw_counted',f):.1f}</td><td>{bg('random','ridge',f):.1f}</td><td>{bg('random','ridge',f,'err_right'):.1f}</td><td>{bg('random','raw_counted',f,'side61')*100:.0f}%</td><td>{bg('random','ridge',f,'side61')*100:.0f}%</td><td>{bg('low_likud_first','raw_counted',f):.1f}</td><td>{bg('low_likud_first','ridge',f):.1f}</td></tr>" for f in FR)
BO = {"random": "אקראי", "large_first": "גדולות קודם", "small_first": "קטנות קודם", "low_turnout_first": "הצבעה נמוכה קודם", "high_likud_first": "ליכוד גבוה קודם", "low_likud_first": "ליכוד נמוך קודם"}
bbo = "".join(f"<tr><td>{BO[o]}</td>" + "".join(f"<td>{bg(o,'raw_counted',f):.1f} / {bg(o,'ridge',f):.1f}</td>" for f in (0.05, 0.20, 0.40)) + "</tr>" for o in BO)
BLOC = f"""<h3>רמת הגושים</h3>
<p>המדד הרלוונטי לשאלה "מי מגיע ל-61" הוא סך המנדטים של הגושים, לא כל רשימה לחוד. חילקנו את הרשימות לשלושה גושים לפי האות, בהגדרה פשוטה ומוצהרת: <b>ימין</b> = ליכוד, ש״ס, יהדות התורה והרשימות מימין לליכוד (ימינה, הציונות הדתית, עוצמה); <b>ערבים</b> = המשותפת, רע״ם, חד״ש-תע״ל; <b>יתר</b> = כל היתר (מרכז ושמאל, כולל ישראל ביתנו ותקווה חדשה). ההגדרה שנויה במחלוקת פוליטית והיא כלי מדידה בלבד. הבדיקה על כנסות 22 עד 25 עם התוצאה הסופית כאמת. מדובר בארבע בחירות בלבד, ולכן אחוזי ההצלחה בקביעת הצד של 61 מבוססים על מעט מאוד מקרים. <b>הסדרים מדומים.</b></p>
{bc1}
<table><tr><th>נספרו</th><th>שגיאת גושים, גולמי, אקראי</th><th>שגיאת גושים, מודל, אקראי</th><th>שגיאת גוש הימין, מודל, אקראי</th><th>צד ה-61 נכון, גולמי</th><th>צד ה-61 נכון, מודל</th><th>גולמי, ליכוד נמוך קודם</th><th>מודל, ליכוד נמוך קודם</th></tr>{bbl}</table>
<p class="small">מנדטים, ממוצע על כנסות 22 עד 25. מקור: <code>results/bloc_backtest.csv</code> (<code>python -m model.bloc_backtest</code>). {CALC}</p>
<table><tr><th>סדר הגעה (גולמי / מודל)</th><th>5% נספרו</th><th>20% נספרו</th><th>40% נספרו</th></tr>{bbo}</table>
<p><b>מתי מדויקים?</b> בסדר אקראי המודל מגיע לשגיאת גושים של כ-2 מנדטים כבר ב-1% עד 2% מהקלפיות, ולכ-1 מ-5% ואילך (בין 0.3 ל-1.2). הסיכום הגולמי מגיע לכ-2 ב-10% ולכ-1 רק ב-40% עד 60%. בסדר מוטה במיוחד (ליכוד נמוך קודם) המודל מגיע ל-2 מנדטים ב-40% ול-1 ב-60%, והסיכום הגולמי לא מגיע ל-2 אפילו ב-80%. בשאר הסדרים המוטים שבדקנו המודל נמצא בטווח של כ-1 עד 3 מנדטים מ-20% ואילך. אלה תרחישים מדומים, לא חיזוי של הסדר האמיתי. <b>צד ה-61:</b> בסדר אקראי המודל קבע נכון את הצד של 61 כמעט בכל השלבים, אבל עם ארבע בחירות בלבד זו אינה הוכחה סטטיסטית, ובסדרים מוטים הוא טעה לפעמים.</p>
"""
c1 = line_chart([
    ("ספירה גולמית, סדר אקראי", [g("random", "raw_counted", f) for f in FR], "#6b7694", False),
    ("המודל, סדר אקראי", [g("random", "ridge", f) for f in FR], "#2fd3c4", False),
    ("ספירה גולמית, סדר מוטה (ליכוד נמוך קודם)", [g("low_likud_first", "raw_counted", f) for f in FR], "#ff7a8e", True),
    ("המודל, אותו סדר מוטה", [g("low_likud_first", "ridge", f) for f in FR], "#ffd166", True)],
    "מנדטים שהוקצו לרשימה הלא נכונה (מתוך 120), לפי חלק הקלפיות שנספרו", "מנדטים שגויים", 100)
c2 = hbars([(o, g(o, "raw_counted", 0.20), g(o, "ridge", 0.20)) for o in ["random", "large_first", "small_first", "low_turnout_first", "high_likud_first", "low_likud_first"]],
           "מנדטים שגויים כשנספרו 20% מהקלפיות, לפי סדר ההגעה", names=("ספירה גולמית", "המודל"), vmax=80)
ORD = {"random": "אקראי", "large_first": "גדולות קודם", "small_first": "קטנות קודם", "low_turnout_first": "הצבעה נמוכה קודם", "high_likud_first": "ליכוד גבוה קודם", "low_likud_first": "ליכוד נמוך קודם"}
c2 = c2
for k, v in ORD.items(): c2 = c2.replace(f">{k}<", f">{v}<")
c3 = hbars([(f"כנסת {T}", *[bt[(bt["T"] == T) & (bt.order == "random") & (bt.method == m) & np.isclose(bt.frac, 0.05)].seats_misallocated.mean() for m in ("raw_counted", "ridge")]) for T in (22, 23, 24, 25, 26)],
           "סדר אקראי, 5% נספרו: מנדטים שגויים לפי כנסת (ממוצע של כמה ניסויים)", names=("ספירה גולמית", "המודל"), vmax=12)
c4 = range_chart(items, "הדגמה: חזרה על כנסת 25 כשנספרו רק 5% מהקלפיות (סדר אקראי), 200 הרצות מונטה קרלו")

tbl = "".join(f"<tr><td>{int(f*100)}%</td><td>{g('random','raw_counted',f):.1f}</td><td>{g('random','ridge',f):.1f}</td><td>{g('low_likud_first','raw_counted',f):.1f}</td><td>{g('low_likud_first','ridge',f):.1f}</td><td>{g('high_likud_first','ridge',f):.1f}</td><td>{g('low_turnout_first','ridge',f):.1f}</td></tr>" for f in FR)
covtbl = "".join(f"<tr><td>{int(f*100)}%</td><td>{r.hit*100:.0f}%</td><td>{r.width:.2f}</td></tr>" for f, r in cov_g.iterrows())
mtbl = "".join(f"<tr><td>כנסת {T-1} ← {T}</td><td>{n:,}</td><td>{s*100:.0f}%</td></tr>" for T, (n, s) in match.items())
ltbl = "".join(f"<tr><td dir='ltr'>{st}</td><td dir='ltr'>{lm}</td><td>{nb:,}</td><td>{nr:,}</td><td>{ne:,}</td><td>{v:,}</td></tr>" for st, lm, nb, nr, ne, v in live_rows)
env = open("results/envelopes.txt", encoding="utf8").read().splitlines()
K25env = [l for l in env if l.startswith("K25")][0]
envtbl = "".join(f"<tr><td>{k}</td><td>{a}</td><td>{b}</td></tr>" for k, a, b in [("ליכוד", "23.5%", "23.4%"), ("הציונות הדתית", "15.5%", "10.3%"), ("יש עתיד", "16.9%", "17.9%"), ("ש״ס", "6.8%", "8.4%")])

# ---------- exit-poll sampling section (results/exitpoll.csv; model/exitpoll.py) ----------
EP = pd.read_csv("results/exitpoll.csv"); EPD = EP[EP["T"].isin([22, 23, 24, 25]) & (EP.m == 100)]
EPN = sorted(EPD.n_places.unique())
def epv(sc, des, n, col, m=100):
    d = EP[EP["T"].isin([22, 23, 24, 25]) & (EP.m == m) & (EP.scenario == sc) & (EP.design == des) & (EP.n_places == n)]
    return float(d[col].mean())
def ep_chart(series, title, ylab, ymax, w=720, h=330):
    L, R, Tp, B = 56, 16, 14, 52
    pw, ph = w - L - R, h - Tp - B
    x = lambda i: L + pw * i / (len(EPN) - 1)
    y = lambda v: Tp + ph * (1 - min(v, ymax) / ymax)
    o = [f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="{esc(title)}" style="width:100%;height:auto;direction:ltr">']
    for t in np.linspace(0, ymax, 6):
        o.append(f'<line x1="{L}" x2="{w-R}" y1="{y(t):.1f}" y2="{y(t):.1f}" stroke="#ffffff22"/><text x="{L-8}" y="{y(t)+4:.1f}" text-anchor="end" font-size="12" fill="#a8b3d1">{t:.1f}</text>')
    for i, n in enumerate(EPN):
        o.append(f'<text x="{x(i):.1f}" y="{h-B+18}" text-anchor="middle" font-size="12" fill="#a8b3d1">{n}</text>')
    o.append(f'<text x="{L+pw/2}" y="{h-8}" text-anchor="middle" font-size="12.5" fill="#a8b3d1" direction="rtl">מספר קלפיות במדגם</text>')
    o.append(f'<text transform="translate(14,{Tp+ph/2}) rotate(-90)" text-anchor="middle" font-size="12.5" fill="#a8b3d1" direction="rtl">{esc(ylab)}</text>')
    for name, vals, col, dash in series:
        pts = " ".join(f"{x(i):.1f},{y(v):.1f}" for i, v in enumerate(vals))
        da = 'stroke-dasharray="6 4"' if dash else ""
        o.append(f'<polyline points="{pts}" fill="none" stroke="{col}" stroke-width="2.5" {da}/>')
        for i, v in enumerate(vals): o.append(f'<circle cx="{x(i):.1f}" cy="{y(v):.1f}" r="3" fill="{col}"/>')
    o.append("</svg>")
    leg = "".join(f'<span style="margin-left:14px;white-space:nowrap"><i class="k" style="background:{c}"></i>{esc(n)}</span>' for n, v, c, d in series)
    return f'<figure class="chart"><figcaption>{esc(title)}</figcaption><div class="legend">{leg}</div>{"".join(o)}</figure>'
DN = {"srs_ratio": "הגרלה פשוטה", "pps_ratio": "הגרלה לפי גודל", "strat_ratio": "מדגם מרובד לפי פרופיל קודם", "strat_prior": "מרובד + תיקון לפי הבחירות הקודמות", "strat_prior_pastvote": "מרובד + תיקון + שאלת הצבעה קודמת"}
DC = {"srs_ratio": "#6b7694", "pps_ratio": "#a77bff", "strat_ratio": "#f2b84b", "strat_prior": "#2fd3c4", "strat_prior_pastvote": "#ff7a8a"}
EP_C1 = ep_chart([(DN[d], [epv("none", d, n, "share_mae_pp") for n in EPN], DC[d], d == "srs_ratio") for d in DN], "שגיאת אחוזים ממוצעת לרשימה (נקודות אחוז), בלי נבדקים משקרים, 100 ראיונות לקלפי", "נקודות אחוז", 3.0)
SCN = {"none": "אין שקר", "noise10": "10% עונים באקראי", "shy15": "15% מבוחרי הרשימה הגדולה מציינים אחרת", "refuse20": "מצביעי הרשימה הגדולה עונים 20% פחות", "noise10_shy15": "שני הקודמים יחד"}
EP_C2 = ep_chart([(SCN[s], [epv(s, "strat_prior", n, "share_mae_pp") for n in EPN], c, s == "none") for s, c in zip(SCN, ["#2fd3c4", "#f2b84b", "#ff7a8a", "#a77bff", "#6b7694"])], "אותו מדגם הטוב ביותר, תחת הנחות שקר שונות", "נקודות אחוז", 3.0)
def need(des, sc, col, thr):
    g_ = EPD[(EPD.design == des) & (EPD.scenario == sc)].groupby("n_places")[col].mean()
    ns, v = g_.index.values, g_.values
    for i in range(len(ns)):
        if v[i] <= thr:
            return str(int(ns[0])) if i == 0 else str(int(round(ns[i-1] + (v[i-1] - thr) / (v[i-1] - v[i]) * (ns[i] - ns[i-1]))))
    return "יותר מ-150"
EP_NEED = "".join(f"<tr><td>{SCN[sc]}</td><td>{need('strat_prior', sc, 'share_mae_pp', 1.0)}</td><td>{need('strat_prior', sc, 'share_mae_pp', 0.75)}</td><td>{need('strat_prior', sc, 'share_mae_pp', 0.5)}</td><td>{need('strat_prior', sc, 'seats_misallocated', 4)}</td></tr>" for sc in SCN)
EP_ROWS = "".join(f"<tr><td>{n}</td><td>{epv('none','strat_prior',n,'share_mae_pp'):.2f}</td><td>{epv('none','strat_prior',n,'top_sd_pp'):.2f}</td><td>±{1.645*epv('none','strat_prior',n,'top_sd_pp'):.1f}</td><td>{epv('none','strat_prior',n,'seats_misallocated'):.1f}</td></tr>" for n in (10, 20, 30, 40, 50, 60, 80, 100, 150))
EP_SC = "".join(f"<tr><td>{SCN[sc]}</td>" + "".join(f"<td>{epv(sc, d, 50, 'share_mae_pp'):.2f}</td>" for d in ("pps_ratio", "strat_prior", "strat_prior_pastvote")) + f"<td><bdi dir='ltr'>{epv(sc,'strat_prior',50,'top_bias_pp'):+.1f}</bdi></td><td><bdi dir='ltr'>{epv(sc,'strat_prior_pastvote',50,'top_bias_pp'):+.1f}</bdi></td></tr>" for sc in SCN)
EP_M = {m: epv("none", "strat_prior", 50, "share_mae_pp", m) for m in (50, 100, 200)}
EP_26 = EP[(EP["T"] == 26) & (EP.m == 100) & (EP.scenario == "none") & (EP.design == "strat_prior") & (EP.n_places == 50)].iloc[0]
EP_TOP = {T: EP[(EP["T"] == T)].top_list.iloc[0] for T in (22, 25)}

PAGE = f"""<!DOCTYPE html>
<html lang="he" dir="rtl"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>המודל: איך מנבאים תוצאות סופיות מסדר פרסום הקלפיות | התחזית</title>
<link rel="stylesheet" href="style.css"><style>.f{{direction:ltr;text-align:left;background:rgba(255,255,255,.05);border:1px solid var(--line);border-radius:10px;padding:10px 14px;margin:10px 0;font-family:ui-monospace,Menlo,monospace;font-size:14.5px;overflow-x:auto}}td.n,th.n{{text-align:left}}th{{white-space:nowrap}}code{{direction:ltr;unicode-bidi:isolate;font-size:.92em}}pre.f{{white-space:pre-wrap;word-break:break-all}}</style></head>
<body><div class="wrap">
<header class="top"><a class="logo" href="/"><b>התחזית</b> · כנסת 26</a><span class="stamp">גרסה 1 · קוד פתוח · {REPO.split('//')[1]}</span></header>
<div class="banner">זהו מודל סטטיסטי ניסיוני, לא תוצאה רשמית ולא סקר. כל מספר של המודל מסומן {CALC}; כל נתון גולמי מסומן {OFF}. רק ועדת הבחירות המרכזית מפרסמת תוצאות רשמיות.</div>
<main>
<h1>המודל: איך מנבאים את התוצאה הסופית מסדר פרסום הקלפיות</h1>
<p class="lead">בזמן הספירה ועדת הבחירות מפרסמת קלפי אחרי קלפי. הקלפיות לא מגיעות בסדר אקראי, ולכן סיכום של מה שהגיע עד כה מוטה. הפרויקט הוא מודל פתוח (קוד MIT) שמשווה כל קלפי שנספרה לעצמה בבחירות הקודמות, לומד את השינוי ומשלים את הקלפיות שטרם נספרו. הדף מסביר את השיטה, מציג מבחנים בדיעבד עם שגיאות כנות, ואומר במפורש מה לא הוכח.</p>

<div class="box sum"><h3>בקצרה</h3><ol>
<li>במבחן בדיעבד על כנסות 22 עד 26 עם סדר הגעה אקראי, כשנספרו 5% מהקלפיות המודל טעה ב-{g('random','ridge',0.05):.1f} מנדטים (מתוך 120), לעומת {g('random','raw_counted',0.05):.1f} בסיכום הגולמי. {CALC}</li>
<li>כשנספרו 20%: {g('random','ridge',0.20):.1f} לעומת {g('random','raw_counted',0.20):.1f}. כשנספרו 40%: {g('random','ridge',0.40):.1f} לעומת {g('random','raw_counted',0.40):.1f}. {CALC}</li>
<li>אם הקלפיות מגיעות בסדר מוטה פוליטית, השגיאה גדולה בהרבה, במיוחד בשלבים המוקדמים: במקרה הגרוע שבדקנו, {g('low_likud_first','ridge',0.20):.0f} מנדטים שגויים ב-20% (הסיכום הגולמי: {g('low_likud_first','raw_counted',0.20):.0f}). {CALC}</li>
<li>סדרי ההגעה בעבר אינם פומביים, לכן כל המבחנים הם על סדרים מדומים. <b>לא הוכחנו דיוק כמו של מודל אחר כלשהו</b>, כולל Votes26, שהטענות שלו נשארות טענות שלו.</li></ol></div>

<h2>1. הבעיה: סדר ההגעה אינו אקראי</h2>
<p>קלפיות שונות מסתיימות בזמנים שונים (גודל הקלפי, המקום, מהירות הספירה), והמעטפות החיצוניות נספרות בנפרד ונוטות להצביע אחרת מהקלפיות הרגילות (ראו סעיף 5). אם הקלפיות שמגיעות קודם מוטות לטובת מפלגה אחת, הסיכום החלקי נראה כאילו היא מובילה יותר או פחות מכפי שתהיה בסוף. סדרי ההגעה בעבר לא פורסמו, ולכן אנחנו לא יודעים עד כמה הם מוטים בפועל, והמבחן למטה בודק מגוון תרחישים. הניסוי למטה מראה כמה זה משנה.</p>

<h2>2. הנתונים</h2>
<ul><li><b>היסטוריה:</b> תוצאות לפי קלפי של כנסות 18 עד 25 מפורטל data.gov.il, שפרסמה ועדת הבחירות. {OFF} הקוד מוריד אותם (<code>scripts/fetch_history.py</code>) ואינו מפיץ אותם.</li>
<li><b>הספירה הנוכחית:</b> הקבצים הרשמיים <code>expb.csv</code> (לפי קלפי) ו-<code>expc.csv</code> (לפי יישוב) באתר ועדת הבחירות. {OFF} אוסף מקליט כל גרסה שלהם פעם בדקה, עם חותמת זמן UTC (<code>data-raw/live/</code>).</li>
<li><b>מה אין:</b> בקובץ אין שעה לכל קלפי. סדר ההגעה נגזר מהשוואה בין גרסאות עוקבות, ולכן הרזולוציה היא בין גרסאות שהוועדה פרסמה, ובנוסף ה-CDN מאחר את הגרסה עד כ-9 דקות שראינו.</li></ul>
<div class="box"><b>הבהרה:</b> כל נתוני הבחירות במאגר הם של ועדת הבחירות המרכזית ולא שלנו. אנחנו שומרים עותקים ללא שינוי, עם חותמת זמן. תנאי הוועדה חלים עליהם. אין אישור או חסות של הוועדה. רישיון MIT חל על הקוד והניתוח שלנו בלבד.</div>
<table><tr><th>גרסת קובץ (UTC, זמן איסוף)</th><th>Last-Modified של הוועדה</th><th>שורות</th><th>קלפיות רגילות</th><th>קלפיות מעטפות</th><th>קולות כשרים</th></tr>{ltbl}</table>
<p class="small">מקור: <code>data-raw/live/*/meta.json</code>. {OFF} אוסף שלנו.</p>

<h2>3. השיטה צעד אחר צעד</h2>
<h3>יחידת הניתוח</h3>
<p>מקום הצבעה = (סמל יישוב, החלק השלם של מספר הקלפי). קלפיות 5.1, 5.2, 5.3 מאוחדות. מספרי הקלפיות משתנים בין בחירות, ולכן אפשר להתאים רק חלק מהקולות לבחירות הקודמות. השאר מקבלים את הפרופיל של היישוב שלהם, או הארצי.</p>
<table><tr><th>זוג בחירות</th><th>מקומות הצבעה</th><th>חלק הקולות שהותאם</th></tr>{mtbl}</table>
<p class="small">{CALC} מתוך <code>build_frame</code>. ההתאמה היא החולשה הידועה הגדולה של המודל.</p>
<h3>למה ההתאמה חלקית, ומה ניסינו</h3>
<p>בקבצי הוועדה אין כתובת או מיקום לקלפי, רק סמל יישוב, מספר קלפי ומספר בעלי זכות בחירה. מספרי הקלפיות מתחלפים בין בחירות (קלפיות מתאחדות, מתפצלות ומוסדרות מחדש), ולכן ההתאמה לפי מספר בלבד מפספסת קולות: כנסת 24 לכנסת 25 הותאמו רק 67% מהקולות. ניסינו כמה שיטות והשווינו (<code>python -m model.match_eval</code>, <code>results/matching.csv</code>):</p>
<ul><li><b>לפי מספר בלבד (שיטת המוצא):</b> 88% מהקולות הותאמו בממוצע.</li>
<li><b>מספר, ופסילת התאמה אם גודל הקלפי שונה מאוד:</b> גרוע יותר. בכנסת 24 גודל הקלפיות השתנה בגלל הקורונה והפסילה זרקה 55% מהקולות.</li>
<li><b>שיוך לפי גודל בלבד בתוך היישוב:</b> מתאים 97%, אבל פרופיל ההצבעה המשויך גרוע יותר מההתאמה לפי מספר.</li>
<li><b>מספר קודם, ורק מה שנשאר משויך לפי גודל:</b> 96% התאמה בממוצע. כנסת 25: מ-67% ל-92%. כנסת 26 הנוכחית: מ-62% ל-76%.</li></ul>
<li><b>כתובת הקלפי (בשימוש עכשיו, ואחריה מספר וגודל):</b> רשימות מקומות הקלפי הרשמיות של הוועדה לכנסות 21 עד 25, ושכבת הקלפיות של govmap לכנסת 26 (טיוטה לפני הבחירות), מאפשרות לדעת איזה קלפי נמצא באותו בניין. בכנסת 25 שגיאת הפרופיל הקודם ירדה, בנקודות אחוז: ליכוד 3.2 ל-2.8, יהדות התורה 1.6 ל-1.0, ש״ס 2.2 ל-1.8. בכנסת 26 אין שיפור: מספרי הקלפיות בשכבה שונים מהמספרים הסופיים בכ-12% מהמקרים, ולכן סומכים על כתובת רק כשמספר הבוחרים הרשום תואם (במרחק 10%), ורוב הכתובות נפסלו.</li>
<li><b>ניסיון שנכשל:</b> כשבניין קיבל קלפיות נוספות, שיוך כל הקלפיות החדשות לפרופיל של אותו בניין (גם בלי התאמה 1 לאחד) הוריד את שגיאת הפרופיל, אבל החמיר את שגיאת התחזית (ב-20% נספרו: 1.8 עד 2.5 מנדטים שגויים במקום 1.8). לא אימצנו.</li>
</ul>
<p><b>האפקט מדוד אך קטן (מספר ואז גודל, מול מספר בלבד):</b> שגיאת הפרופיל הקודם (ליכוד, ש״ס, יהדות התורה) ירדה בכ-1% עד 7% יחסית, ושגיאת המנדטים בסדר אקראי ב-20% מהקלפיות ירדה מ-2.2 ל-1.7. בסדרים מוטים התוצאה מעורבת, ללא שיפור ברור. מה שלא ניסינו: קואורדינטות וגיאוקוד, והמשכיות שכנות בין קלפיות. מקורות הכתובות: <code>data-raw/addresses/README.md</code>.</p>
<div class="box"><b>אימות:</b> שיטות ההתאמה נבחרו לפי אותן בחירות 22 עד 25, ולכן אלה בחירות פיתוח ולא אימות עצמאי. בחירה של כנסת 26 אינה אימות עצמאי: הספירה שלה כבר השפיעה על החלטות. בדקנו השארת-בחירות-אחת-בחוץ (<code>python -m model.loo</code>, <code>results/loo.csv</code>): בכל סבב בוחרים שיטה ופרמטר לפי שלוש הבחירות האחרות ובודקים על הרביעית. בממוצע על ארבעת הסבבים, שגיאת החלקים בבחירה חיצונית היא 0.48 נקודות אחוז לשיטה הנבחרת, 0.48 לברירת המחדל (התאמה לפי בניין) ו-0.48 להתאמה לפי מספר בלבד, ושגיאת המנדטים 4.4 בכולן. <b>כלומר, בהקרנה עצמה, שיפור ההתאמה לא הוכח.</b> השיפור שנמדד הוא באיכות הפרופיל הקודם בלבד. הכללים הוקפאו בתג <code>matching-rules-v1</code> לפני ההערכה הבאה.</div>
<h3>שלב א: לומדים את השינוי</h3>
<p>לכל רשימה בבחירות הנוכחיות, חלקה בכל מקום הצבעה (<i>y</i>) מוסבר ברגרסיית רכס (ridge) מהחלקים של רשימות הבחירות הקודמות באותו מקום, ההצבעה הקודמת ולוגריתם גודל הבוחרים:</p>
<div class="f">y_j(p) = b_j0 + Σ_k B_jk · x_k(p) + c_j · turnout_prev(p) + d_j · log(registered(p)) + ε_j(p)<br>
B = argmin Σ_p w_p ‖y(p) − B·x(p)‖² + λ‖B‖²,  w_p = √(valid_p),  λ = 5</div>
<p>המטריצה B לומדת מעברים כמו "מצביעי רשימה X בבחירות הקודמות הצביעו עכשיו לרשימה Y", בלי מיפוי ידני בין מפלגות. היא נלמדת רק מהקלפיות שכבר נספרו.</p>
<h3>שלב ב: משלימים את מה שלא נספר</h3>
<p>לכל מקום שטרם נספר: חזוי חלק כל רשימה לפי B והתוצאות שלו בבחירות הקודמות, וגודלו הוא מספר הקולות הכשרים הקודם שלו כפול יחס הצמיחה שנמדד בקלפיות שנספרו. אין ניחוש מי "הגיע"; הקובץ אומר מה נספר, והשאר מוערך מההיסטוריה של אותו מקום, לא מהקלפיות שהגיעו ראשונות.</p>
<h3>שלב ג: סכום ומנדטים</h3>
<div class="f">V_j = Σ_{{counted}} v_j(p) + Σ_{{uncounted}} ŷ_j(p) · N̂(p)</div>
<p>רשימות מתחת לאחוז החסימה (3.25%) נופלות, והמנדטים מחולקים בשיטת בדר-עופר עם הסכמי עודפים. הקוד משחזר במדויק את ההקצאה הרשמית של כנסת 25 (<code>tests/test_seats.py</code>). הסכמי העודפים ל-2026 נלקחו מדיווחים ועדיין לא אומתו מול נתוני הוועדה, ולכן מספרי מנדטים ל-2026 אינם מוכנים להסתמכות.</p>
<h3>שלב ד: מונטה קרלו ואי-ודאות</h3>
<p>200 פעמים: דוגמים מחדש יישובים מהקלפיות שנספרו (bootstrap לפי יישוב), מתאימים את B מחדש, ומוסיפים רעש ברמת יישוב שנלקח מהשאריות האמיתיות של המודל, בקנה מידה של 1 חלקי שורש הגודל. כל הרצה מייצרת טבלת מנדטים, וכך מתקבלים טווח לכל רשימה והסיכוי שתעבור את החסימה (<code>python -m model.simulate</code>). זמן ריצה שנמדד: {tm['draws_s']:.1f} שניות ל-{tm['n_draws']} הרצות על שני ליבות, כנסת 25, 5% נספרו. הקצאת המנדטים לכל ההרצות: {tm['seats_s']:.3f} שניות.</p>
{c4}
<p class="small">הנתונים: <code>python -m model.simulate 25 0.05</code>. הסרגל הירוק הוא טווח 80% מההרצות; היהלום הצהוב הוא התוצאה הסופית.</p>

<h2>4. מבחן בדיעבד</h2>
<div class="box"><b>מה נבדק:</b> לכל אחת מכנסות 22 עד 26 חוזרים על הספירה בסדרי הגעה מדומים (אקראי, גדולות קודם, קטנות קודם, הצבעה נמוכה קודם, ליכוד גבוה או נמוך קודם), עוצרים כשנספר חלק נתון מהקלפיות, ומודדים כמה מנדטים (מתוך 120) הוקצו לרשימה הלא נכונה לעומת התוצאה הסופית. <b>סדרי הגעה אמיתיים מהעבר אינם פומביים</b>, ולכן הסדרים המוטים הם תרחישי קיצון מכוונים, לא חיזוי של מה שיקרה. עבור כנסת 26 האמת היא הקובץ הנוכחי ללא מעטפות, שאינו סופי.</div>
{c1}
<table><tr><th>נספרו</th><th>גולמי, אקראי</th><th>מודל, אקראי</th><th>גולמי, ליכוד נמוך קודם</th><th>מודל, ליכוד נמוך קודם</th><th>מודל, ליכוד גבוה קודם</th><th>מודל, הצבעה נמוכה קודם</th></tr>{tbl}</table>
<p class="small">מנדטים שגויים מתוך 120, ממוצע על כנסות 22 עד 26. מקור: <code>results/backtest.csv</code>. {CALC}</p>
{c2}{c3}
<p><b>איך לקרוא:</b> עם סדר אקראי המודל מוריד את הטעות עד פי 3 בשלבים המוקדמים (ב-1%: 4.5 לעומת 13.0) ופחות בהמשך. עם סדר מוטה הוא עדיין טוב בהרבה מהסיכום הגולמי, אבל רחוק מלהיות מדויק עד שנספרים כ-20 עד 40% מהקלפיות. ב-1% הנספרים התוצאה עדיין חלשה. המודל לא "מנחש מי הגיע", הוא מסיר את ההטיה של קלפיות שכבר הגיעו, ככל שההיסטוריה של המקום מסבירה אותה.</p>
{BLOC}
<h3>כיול הטווחים</h3>
<table><tr><th>נספרו</th><th>כיסוי בפועל של טווח 80%</th><th>רוחב הטווח הממוצע (מנדטים)</th></tr>{covtbl}</table>
<p>בסדר אקראי הטווח הנומינלי של 80% כיסה את התוצאה האמיתית ב-{cov_g.hit.min()*100:.0f}% עד {cov_g.hit.max()*100:.0f}% מהמקרים: קרוב למוצהר. <b>בסדרים מוטים לא מדדנו כיסוי, והטווחים כנראה צרים מדי שם.</b> מקור: <code>results/coverage.csv</code>.</p>

<h2>5. מגזרים ומעטפות</h2>
<ul><li><b>מגזרים:</b> אין תווית מגזר. כל מקום מנובא מהתוצאות הקודמות שלו, כך שעיר ערבית מנובאת מחלקי רע״ם וחד״ש-תע״ל הקודמים שלה, ועיר חרדית מש״ס ויהדות התורה. זה מטפל בהטיית מגזר ככל שהעבר מסביר אותה. <b>לא נבנו:</b> אפקטים מגזריים מפורשים וקורלציה בין יישובים שכנים.</li>
<li><b>מעטפות חיצוניות (סמל 9999):</b> 6.3% עד 9.6% מהקולות הכשרים בכנסות 22 עד 25, ונוטות אחרת מהקלפיות הרגילות. אומדן ראשון קיים (<code>model/envelopes.py</code>) ושיפר את שגיאת כנסת 25 מ-0.565 ל-0.531 נקודות אחוז בממוצע, אבל הוא עדיין <b>לא משולב בהקצאת המנדטים</b>.</li></ul>
<table><tr><th>כנסת 25, חלק מהקולות</th><th>מעטפות</th><th>קלפיות רגילות</th></tr>{envtbl}</table>
<p class="small">מקור: <code>results/envelopes.txt</code>. {CALC} על נתוני הוועדה.</p>

<h2>6. תחזית המודל לספירה הנוכחית</h2>
<div class="box"><b>פלט מודל, לא תוצאה רשמית.</b> הקובץ הרשמי האחרון שאספנו ({LF['snapshot']} UTC) כבר מכיל {LFREG:,} קלפיות רגילות (בכנסת 25 היו בקובץ הסופי {K25REG:,}). לכן אנחנו מניחים שהספירה הרגילה כמעט שלמה, והדבר העיקרי שעוד מגיע הוא המעטפות החיצוניות. <b>ההנחה הזו לא אומתה</b>, ואם חסרות קלפיות רגילות התחזית שגויה.</div>
<p>החישוב: הקולות הרגילים והמעטפות שכבר נספרו, ועוד הערכה של המעטפות שנותרו. סך המעטפות נאמד כיחס למספר הקולות הרגילים: ביחס שנע בין {min(LF['env_ratio_hist'].values())*100:.1f}% ל-{max(LF['env_ratio_hist'].values())*100:.1f}% בכנסות 22 עד 25 ({OFF}), כלומר בין כ-{LF['env_remaining_votes_range'][0]/1000:,.0f} אלף לכ-{LF['env_remaining_votes_range'][1]/1000:,.0f} אלף קולות שעדיין לא נספרו (כשנספרו עד כה {LF['envelope_valid_so_far']/1000:,.0f} אלף). חלקי הרשימות במעטפות שנותרו הם תערובת אקראית בין חלקם במעטפות שכבר נספרו לבין חלקם בקלפיות הרגילות בתוספת ההטיה ההיסטורית של המעטפות (לרשימות חדשות, בלי הטיה). 2,000 הרצות. {CALC}, <b>היוריסטיקה שלא כויילה על נתוני עבר.</b></p>
<table><tr><th>רשימה</th><th>אחוז מהקולות שנספרו</th><th>מנדטים (חציון)</th><th>טווח 80% בין ההרצות</th></tr>{LFTBL}</table>
<p class="small">מקור: <code>results/live_forecast.json</code> (<code>python -m model.live_forecast</code>). הסכמי עודפים בשימוש: הליכוד-הציונות הדתית, ש״ס-יהדות התורה, ישר!-הדמוקרטים, ביחד-ישראל ביתנו, רע״ם-הרשימה המשותפת (חמישה, לפי דיווחי גלובס וynet לאחר סגירת החלון ב-16.10; האותיות לפי רשימת הוועדה ב-gov.il; לא נבדקו מול הודעת הוועדה עצמה).</p>
<p><b>שימו לב:</b> הטווח צר כי בהרצות רק המעטפות משתנות. המנדטים האחרונים רגישים הרבה יותר לפרט אחר: אילו הסכמי עודפים בתוקף. בבדיקה שלנו, בלי הסכם רע״ם-המשותפת רע״ם מקבלת 7 ולא 8 וש״ס 7 ולא 6. לכן מנדטים בודדים של רע״ם, ש״ס והמשותפת אינם מוכחים עד שנאמת מול הודעת הוועדה. חלוקת המנדטים הרשמית תיקבע רק על ידי ועדת הבחירות.</p>

<h2>7. מגבלות ומה לא הוכח</h2>
<ul><li>סדרי ההגעה במבחנים מדומים. סדר אמיתי נרשם רק מאז 29.10.2026, אחרי שרוב הקלפיות הרגילות כבר היו בקובץ.</li>
<li>לא הוכחנו דיוק שווה או טוב יותר מ-Votes26 או ממודל אחר. הקוד והנתונים שלו סגורים, והטענות שלו נשארות שלו.</li>
<li>הטווחים נבדקו בסדר אקראי בלבד.</li>
<li>התאמת מקומות הצבעה בין בחירות חלקית (ראו הטבלה).</li>
<li><b>קובצי אחוז ההצבעה של הוועדה (ב-20:00):</b> לכל קלפי מפורסם מספר המצביעים עד אותה שעה. בכנסת 26, הערכת גודל הקלפי (קולות כשרים) ממנו שגויה בכ-3% בממוצע, לעומת כ-11% מהגודל בבחירות הקודמות. הכנסת הגודל הזה למודל הורידה את שגיאת החלקים בסדר אקראי (ב-20% נספרו: מ-0.15 ל-0.10 נקודות אחוז), ושימוש בהצבעה כמשתנה מסביר נתן תוצאה מעורבת (עזר בסדר ליכוד נמוך קודם ב-5%, הזיק בסדר קטנות קודם). <b>מדד זה נבדק רק על כנסת 26, שאינה אימות עצמאי, ואין קבצים כאלה לבחירות קודמות שמצאנו.</b> לכן הוא עדיין לא בברירת המחדל. מקור: <code>results/turnout_k26.csv</code>, <code>python -m model.turnout</code>.</li>
<li>מעטפות, קורלציה בין יישובים ואפקטים מגזריים לא בפנים.</li>
<li>הסכמי העודפים של 2026 נלקחו מדיווחי תקשורת ולא אומתו מול הודעת הוועדה.</li><li>תחזית 2026 מניחה שהקלפיות הרגילות בקובץ שלמות, וההנחה לא אומתה; חלקי המעטפות שנותרו הם היוריסטיקה שלא כויילה.</li>
<li>הדיוק בשלב מוקדם מאוד (1% נספרו) חלש.</li></ul>

<h2>8. סקר יציאה: כמה קלפיות ואיזה</h2>
<p><b>זו הדמיית תכנון מדגם, לא סקר ולא תחזית.</b> בחנו מה היה קורה אילו ראיינו מצביעים ביציאה מ-n קלפיות (מקומות הצבעה), 100 מצביעים בכל אחת. <span class="t ours">חישוב שלנו</span> על <span class="t off">נתוני ועדת הבחירות</span> של הכנסות 22-25: התוצאה האמיתית של כל קלפי היא האמת. מה שמדומה בלבד: מי משקר ובאיזה כיוון. אלה <b>הנחות</b>, לא מדידות.</p>
<p>אין פרמטר שכוונן על התוצאות, ולכן הכנסות 22-25 משמשות מבחן לשיטות המדגם. אוסף השיטות נקבע לפני שראינו תוצאות. הכנסת 26 נבדקה בנפרד על הספירה החיה ועדיין לא סופית. גודל הקלפי בבחירה וההגרלה נעשים רק לפי מה שידוע לפני יום הבחירות: בעלי זכות בחירה כפול ההצבעה בבחירות הקודמות.</p>
<p>חמש שיטות: (1) הגרלה פשוטה; (2) הגרלה לפי גודל הקלפי; (3) מיון הקלפיות לפי הפרופיל שלהן בבחירות הקודמות ובחירה שיטתית לפי גודל לאורך המיון, כך שהמדגם מכסה את כל סוגי הקלפיות; (4) כמו 3, ועוד תיקון: מוסיפים לתוצאה הכללית של הבחירות הקודמות את השינוי שנמדד בקלפיות המדגם; (5) כמו 4, ועוד שאלה לנבדק "במה הצבעת בפעם הקודמת" כדי להעריך כמה הנבדקים מדווחים בשגיאה.</p>
{EP_C1}
<p>מה רואים: שיטה 4 עדיפה בבירור. ב-50 קלפיות, בלי נבדקים משקרים, שגיאת האחוזים הממוצעת לרשימה היא <b>{epv('none','strat_prior',50,'share_mae_pp'):.2f}</b> נקודות אחוז, לעומת <b>{epv('none','srs_ratio',50,'share_mae_pp'):.2f}</b> בהגרלה פשוטה. מספר הראיונות בכל קלפי כמעט לא משנה: 50 ראיונות {EP_M[50]:.2f}, 100 ראיונות {EP_M[100]:.2f}, 200 ראיונות {EP_M[200]:.2f}. הקלפיות שונות זו מזו הרבה יותר משונים הנבדקים בתוך קלפי, ולכן באותו מספר ראיונות כולל (5,000) עדיף להרחיב את מספר הקלפיות: 50 קלפיות × 100 ראיונות = {epv('none','strat_prior',50,'share_mae_pp',100):.2f}, 100 קלפיות × 50 ראיונות = {epv('none','strat_prior',100,'share_mae_pp',50):.2f}.</p>
<table><tr><th>קלפיות</th><th>שגיאה ממוצעת (נק׳)</th><th>סטיית תקן, רשימה גדולה</th><th>טווח 90% (נק׳)</th><th>מנדטים לא במקומם</th></tr>{EP_ROWS}</table>
<p class="small">ממוצע על הכנסות 22-25, 300 הדמיות לכל תא. הרשימה הגדולה: סטיית התקן הושוותה לנוסחה סטטיסטית פשוטה (הגרלה לפי גודל) וההתאמה טובה, ראו <code>model/exitpoll.py</code>. "מנדטים שהוקצו לא נכון" הוא מספר המנדטים שמחוץ למקומם, סכום ההפרשים לחלק ב-2, אחרי הסכמי העודפים של אותה בחירה. המנדטים האחרונים רגישים מאוד, ולכן המספר גבוה יחסית לשגיאת האחוזים. אין כאן מעטפות: מדגם קלפיות אינו מכסה אותן, והאמת בהדמיה היא הקלפיות הרגילות בלבד.</p>
<h3>כמה קלפיות לפחות</h3>
<p>מתחת ל-50 אפשר, אבל המחיר ברור. עם 20 קלפיות השגיאה הממוצעת לרשימה ב-{epv('none','strat_prior',20,'share_mae_pp'):.2f} נקודות אחוז וטעות של כ-{epv('none','strat_prior',20,'seats_misallocated'):.0f} מנדטים. עם 10 קלפיות: {epv('none','strat_prior',10,'share_mae_pp'):.2f} נקודות אחוז וכ-{epv('none','strat_prior',10,'seats_misallocated'):.0f} מנדטים. מספר הקלפיות הנדרש להגיע ליעד, לפי ההנחות על שקר (שיטה 4):</p>
<table><tr><th>הנחה</th><th>שגיאה ≤1.0</th><th>≤0.75</th><th>≤0.5</th><th>מנדטים ≤4</th></tr>{EP_NEED}</table>
<h3>נבדקים שמשקרים</h3>
{EP_C2}
<p>הממצא המרכזי: <b>שקר הוא הטיה, ולא נעלם עם יותר קלפיות.</b> הוספת קלפיות מורידה את הרעש אבל לא את ההטיה. בהנחה ש-15% מבוחרי הרשימה הגדולה מציינים רשימה אחרת, הרשימה הגדולה נמדדת נמוך בכ-3.8 עד 3.9 נקודות אחוז בכל גודל מדגם.</p>
<table><tr><th>הנחה (50 קלפיות)</th><th>שיטה 2</th><th>שיטה 4</th><th>שיטה 5</th><th>הטיה ש. 4</th><th>הטיה ש. 5</th></tr>{EP_SC}</table>
<p class="small">שלוש העמודות הראשונות: שגיאה ממוצעת לרשימה בנקודות אחוז. הטיה: הרשימה הגדולה, מדוד פחות אמת, בנקודות אחוז. שיטה 2 היא הגרלה לפי גודל.</p>
<p><b>יתירות:</b> שאלת ההצבעה הקודמת (שיטה 5) מתקנת את ההטיה של הרשימה הגדולה כמעט לגמרי בהנחה שהשקר דומה בשתי השאלות, אבל מוסיפה רעש: בלי שקר היא גרועה מ-4, והיא מועילה רק מכ-60 קלפיות. ההנחה שהשקר יציב בין שאלה לשאלה היא אופטימית, ושאלת "הצבעה קודמת" כאן מדומה מפרופיל הקלפי בבחירות הקודמות, לא מהצבעה אמיתית של הנבדקים: בעולם האמיתי יש גם שגיאות זיכרון ומעבר בין רשימות. אל תקראו את זה כהוכחה שהשיטה עובדת.</p>
<p><b>אילו קלפיות:</b> מיון לפי הפרופיל בבחירות הקודמות ובחירה שיטתית לפי גודל. דוגמה למדגם של 60 קלפיות לכנסת 26 (אילוסטרציה, נבנתה מתוצאות הספירה הנוכחית, לא המלצה מבצעית): <code>results/exitpoll_example_sample_k26.csv</code>. בתכנון אמיתי הרשימה נבחרת לפני הבחירות מרשימת הקלפיות שהוועדה מפרסמת, לפי הבחירות הקודמות.</p>
<p class="small">מגבלות: מעטפות וקולות חיילים, אסירים וכדומה לא במדגם. לא הודלו חוסר שיתוף פעולה של קלפיות שלמות, מראיינים עם הטיה, הצבעה מוקדמת של בוחרים לפני היציאה, ושינוי בהרכב הבוחרים לפי שעה ביום. הכנסת 26 (נתונים חיים, זמני): 50 קלפיות בשיטה 4, שגיאה ממוצעת {EP_26.share_mae_pp:.2f} נקודות אחוז, {EP_26.seats_misallocated:.1f} מנדטים. הכנסות 22-25 הן נתוני פיתוח של שאר המודל, אבל כאן אין כוונון, ולכן הן מבחן ראוי לשיטות המדגם. התוצאות הן סימולציה של תכנון ולא טענה על סקר אמיתי כלשהו.</p>

<h2>9. שחזור</h2>
<p>הקוד, הנתונים שנאספו והמבחנים: <a href="{REPO}" dir="ltr">{REPO}</a>. להרצה:</p>
<pre class="f">python3 scripts/fetch_history.py
python3 -m model.backtest
python3 -m model.coverage
python3 -m model.simulate
python3 -m model.live_forecast
python3 -m model.exitpoll
python3 docs/site/build.py</pre>
<p>דף זה נבנה מתוצאות המאגר על ידי הסקריפט האחרון. תיעוד נוסף במאגר: <code>docs/method.md</code>, <code>docs/backtest.md</code>, <code>docs/how-it-works.md</code>.</p>
<footer>הנתונים הגולמיים הם של ועדת הבחירות המרכזית (https://votes26.bechirot.gov.il, https://data.gov.il). פרויקט עצמאי, אינו מזוהה עם הוועדה ואינו מאושר על ידה. המודל אינו סקר ואינו תוצאה רשמית.</footer>
</main></div></body></html>"""
open("docs/site/index.html", "w", encoding="utf8").write(PAGE)
print("ok", len(PAGE))
