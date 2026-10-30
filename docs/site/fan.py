"""Fan charts of the Monte Carlo replication (mc-v1): mean line and 5th-95th percentile band over the 200 order draws."""
import pandas as pd, os
R = os.path.join(os.path.dirname(__file__), "..", "..", "results")
COLM = {"base": "#6b7694", "transfer": "#ff7a90", "gp": "#2fd3c4", "switch5": "#ffd166"}
NAMEM = {"base": "המודל הנוכחי", "transfer": "מודל ההעברה", "gp": "מודל ההעברה + תהליך גאוסי", "switch5": "מעבר עד 5%"}
def fan(dm, st, beta, metric="seats", methods=("base", "transfer", "gp", "switch5"), w=390, h=250, ymax=None):
    d = dm[(dm.set == st) & (dm.beta == beta) & (dm.metric == metric) & dm.method.isin(methods)]
    fr = sorted(d.frac.unique()); L, Rr, T, B = 44, 14, 14, 36; pw, ph = w - L - Rr, h - T - B
    q = d.groupby(["method", "frac"]).val.agg(m="mean", lo=lambda x: x.quantile(.05), hi=lambda x: x.quantile(.95)).reset_index()
    ymax = ymax or float(q.hi.max()) * 1.08; X = lambda f: L + pw * fr.index(f) / (len(fr) - 1); Y = lambda v: T + ph * (1 - min(v, ymax) / ymax)
    s = ""
    for k in range(5):
        v = ymax * k / 4; y = Y(v); s += f'<line x1="{L}" y1="{y:.1f}" x2="{w-Rr}" y2="{y:.1f}" stroke="#1f2a48"/><text x="{L-6}" y="{y+5:.1f}" fill="#c4cde6" font-size="13" text-anchor="end">{v:.0f}</text>'
    for f in fr: s += f'<text x="{X(f):.1f}" y="{h-12}" fill="#c4cde6" font-size="14" text-anchor="middle">{int(round(f*100))}%</text>'
    for m in methods:
        x = q[q.method == m].sort_values("frac"); pts = [(X(r.frac), Y(r.m), Y(r.lo), Y(r.hi)) for r in x.itertuples()]
        band = " ".join(f"{a:.1f},{c:.1f}" for a, b, c, e in pts) + " " + " ".join(f"{a:.1f},{e:.1f}" for a, b, c, e in reversed(pts))
        s += f'<polygon points="{band}" fill="{COLM[m]}" fill-opacity="0.18" stroke="none"/>'
        s += f'<polyline points="{" ".join(f"{a:.1f},{b:.1f}" for a, b, c, e in pts)}" fill="none" stroke="{COLM[m]}" stroke-width="3"/>'
        for a, b, c, e in pts: s += f'<circle cx="{a:.1f}" cy="{b:.1f}" r="4" fill="{COLM[m]}"/>'
    return f'<svg viewBox="0 0 {w} {h}" dir="ltr" role="img" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto">{s}</svg>'
def legend(methods=("base", "transfer", "gp", "switch5")):
    return '<p class="legend">' + " &nbsp; ".join(f'<span style="color:{COLM[m]}">&#9632;</span> {NAMEM[m]}' for m in methods) + "</p>"
def mc_block():
    p = os.path.join(R, "mc_draws_agg.csv")
    if not os.path.exists(p): return ""
    dm = pd.read_csv(p); S = pd.read_csv(os.path.join(R, "mc_summary.csv"))
    def sv(st, m, b, f, k="mean"): return S[(S.set == st) & (S.metric == "seats") & (S.method == m) & (S.beta == b) & (S.frac == f)][k].iloc[0]
    def one(st, beta, title, ymax):
        return f'<figure class="fig"><h4>{title}</h4>{fan(dm, st, beta, ymax=ymax)}</figure>'
    out = ['<h3>הרצה חוזרת עם 200 הגרלות סדר</h3>',
        '<p>(נרשם מראש, תג mc-v1.) כדי לבדוק שהתוצאות לא מקריות הרצנו 200 הגרלות חדשות של סדר פרסום (סימולציה שלנו, לא סדר אמיתי) לכל בחירות, בארבע רמות הטיה. הקו הוא הממוצע, הרצועה היא הטווח בין אחוזון 5 ל-95 של 200 ההגרלות (ממוצע על הבחירות). ציר אנכי: מנדטים שגויים מתוך 120; ציר אופקי: כמה אחוז מהקלפיות נספרו. הקו הצהוב מסתיר את הוורוד כשהמעבר פעיל (אותם ערכים).</p>', legend(),
        '<p><b>מה ההרצה הזאת מראה ומה לא:</b> 200 ההגרלות הן וריאציה של סדר הפרסום בסימולציה בתוך אותן בחירות, לא 200 בחירות בלתי תלויות, ואינן הוכחה לאמינות בעולם האמיתי. הן מראות יציבות (המספרים לא תלויים בהגרלה אחת), לא אימות עצמאי. כנסות 20-21 שימשו כבר פעמים רבות ולכן הן אימות בשימוש חוזר ולא מדגם נקי; לא נותר לנו מערך בחירות חדש לגמרי לבדיקה סופית (כנסת 27 תהיה הבדיקה הראשונה הכזאת). שלוש רמות ראיה נפרדות: התקדמות ניסויית, יציבות מונטה קרלו, אימות עצמאי (עדיין אין).</p>', '<p><b>פיתוח</b> (כנסות 23 עד 26) מול <b>אימות בשימוש חוזר</b> (כנסות 20 ו-21), בנפרד. כל הקווים הם חישוב שלנו, לא תוצאה רשמית.</p>']
    for st, lab in (("dev", "פיתוח, כנסות 23-26"), ("hold", "אימות בשימוש חוזר, כנסות 20-21")):
        out.append(one(st, 0, f"סדר אקראי: {lab}", 16)); out.append(one(st, 8, f"סדר מוטה מאוד (ליכוד נמוך קודם): {lab}", 75))
    g = lambda st, m, b, f: sv(st, m, b, f)
    out.append(f'<p><b>מה רואים:</b> בסדר מוטה מאוד, אחרי 1% נספרו, המודל הנוכחי טועה בכ-{g("dev","base",8,.01):.0f} מנדטים (פיתוח) ו-{g("hold","base",8,.01):.0f} (אימות חוזר); עם התהליך הגאוסי {g("dev","gp",8,.01):.0f} ו-{g("hold","gp",8,.01):.0f}. הרצועות של התהליך הגאוסי והמעבר צרות ולא נוגעות ברצועה של המודל הנוכחי: ההבדל לא נובע ממזל של הגרלה. בסדר אקראי התהליך הגאוסי קרוב למודל הנוכחי (לא גרוע ממנו), ואילו מודל ההעברה לבדו גרוע פי כמה. המעבר עד 5% עולה מעט בסדר אקראי (אזעקות שווא: {g("dev","switch5",0,.05):.1f} מול {g("dev","base",0,.05):.1f} מנדטים בפיתוח ב-5%). <b>אזהרה:</b> זה עדיין סימולציה של סדר, והתהליך הגאוסי עדיין לא עבר את הכלל המלא שנקבע מראש (נכשל בתא אחד, "הצבעה נמוכה קודם" ב-40%).</p>')
    return "".join(out)
