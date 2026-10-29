"""UX post-processing for the /model/ page: plain summary, sticky nav, collapsible sections, schematic SVGs."""
import re
SHORT = {1: "הבעיה", 2: "הנתונים", 3: "השיטה", 4: "מבחן בדיעבד", 5: "מגזרים ומעטפות", 6: "תחזית נוכחית", 7: "מגבלות", 8: "סקר יציאה", 9: "סקר יציאה ב", 10: "טלוויזיה מול תוצאות", 11: "למה פספסו", 12: "קלפיות מול ראיונות", 13: "דשבורד", 14: "מודל אידיאלי", 15: "שחזור", 16: "מונטה קרלו: שקרנים", 17: "כל הניסויים"}
OPEN = {13}
def svg_wrap(w, h, inner, cap):
    return f'<figure class="fig"><svg viewBox="0 0 {w} {h}" role="img" dir="rtl" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto;max-width:520px">{inner}</svg><figcaption>{cap}</figcaption></figure>'
def flow(steps, cap):
    inner = ""
    for i, (a, b) in enumerate(steps):
        col, row = i % 2, i // 2
        x = 400 - 10 - 185 - col * 195; y = 10 + row * 100
        inner += f'<rect x="{x}" y="{y}" width="185" height="86" rx="12" fill="#16203a" stroke="#3b4a77"/>'
        inner += f'<circle cx="{x+185-22}" cy="{y+24}" r="13" fill="#ffd166"/><text x="{x+185-22}" y="{y+30}" fill="#101426" font-size="16" font-weight="800" text-anchor="middle">{i+1}</text>'
        inner += f'<text x="{x+82}" y="{y+30}" fill="#eef2ff" font-size="18" font-weight="700" text-anchor="middle">{a}</text>'
        inner += f'<text x="{x+92}" y="{y+62}" fill="#a8b3d1" font-size="14" text-anchor="middle">{b}</text>'
    return svg_wrap(400, 206, inner, cap)
def arrival_fig():
    inner = '<text x="200" y="22" fill="#a8b3d1" font-size="14" text-anchor="middle">סדר פרסום הקלפיות (מימין לשמאל)</text>'
    cols = ["#6ea2ff"] * 6 + ["#2fd3c4", "#6ea2ff", "#2fd3c4", "#2fd3c4", "#2fd3c4", "#2fd3c4", "#2fd3c4", "#2fd3c4", "#2fd3c4", "#2fd3c4"]
    for i, c in enumerate(cols[:16]):
        inner += f'<rect x="{370-i*22.5}" y="36" width="19" height="36" rx="4" fill="{c}"/>'
    inner += '<text x="200" y="100" fill="#ffd166" font-size="14" text-anchor="middle">בתחילה רוב הקלפיות כחולות, ואחר כך הצבע מתהפך,</text><text x="200" y="120" fill="#ffd166" font-size="14" text-anchor="middle">ולכן סיכום חלקי מטעה</text>'
    return svg_wrap(400, 132, inner, "איור סכמתי להמחשה בלבד (אין בו נתונים אמיתיים): אם קלפיות של צד אחד מגיעות קודם, הסיכום החלקי מוטה.")
def tv_chart(tvc, sim_ideal, sim_hard):
    W, H, L, B = 420, 300, 30, 44; inner = ""; mx = 10; ph = H - B - 40
    for v in (0, 2, 4, 6, 8, 10):
        y = H - B - v * ph / mx
        inner += f'<line x1="{L}" y1="{y}" x2="{W-6}" y2="{y}" stroke="#1f2a48"/><text x="{L-12}" y="{y+4}" fill="#7380a3" font-size="11" text-anchor="middle">{v}</text>'
    cols = {"Channel 12": "#6ea2ff", "Channel 13": "#2fd3c4", "Kan 11": "#ffd166"}
    gw = (W - L - 6) / 5
    for gi, e in enumerate([21, 22, 23, 24, 25]):
        gx = W - 6 - (gi + 1) * gw
        for ci, (ch, col) in enumerate(cols.items()):
            r = tvc[(tvc.election == e) & (tvc.channel == ch)]
            bx = gx + gw - 8 - (ci + 1) * 20
            if len(r):
                v = float(r.out_of_place.iloc[0]); h = v * ph / mx
                inner += f'<rect x="{bx}" y="{H-B-h}" width="17" height="{h}" rx="3" fill="{col}"/><text x="{bx+8.5}" y="{H-B-h-4}" fill="#eef2ff" font-size="11" text-anchor="middle">{v:.0f}</text>'
            else:
                inner += f'<text x="{bx+8.5}" y="{H-B-6}" fill="#7380a3" font-size="10" text-anchor="middle" transform="rotate(-90 {bx+8.5} {H-B-6})">חסר</text>'
        inner += f'<text x="{gx+gw/2}" y="{H-B+18}" fill="#a8b3d1" font-size="13" text-anchor="middle">כנסת {e}</text>'
    for v, col, t in ((sim_ideal, "#4fdc9c", "הדמיה שלנו, בלי בעיות"), (sim_hard, "#ff9fb0", "הדמיה שלנו, הנחות קשות")):
        y = H - B - v * ph / mx
        inner += f'<line x1="{L}" y1="{y}" x2="{W-6}" y2="{y}" stroke="{col}" stroke-dasharray="6 4" stroke-width="2"/><text x="{W/2}" y="{y-5}" fill="{col}" font-size="12" text-anchor="middle">{t} ({v:.1f}, הנחה)</text>'
    for i, (ch, col) in enumerate({"ערוץ 12": "#6ea2ff", "ערוץ 13": "#2fd3c4", "כאן 11": "#ffd166"}.items()):
        inner += f'<rect x="{230-i*80}" y="6" width="12" height="12" rx="3" fill="{col}"/><text x="{200-i*80}" y="17" fill="#a8b3d1" font-size="12" text-anchor="middle">{ch}</text>'
    return svg_wrap(W, H, inner, "מנדטים שמחוץ למקומם בכל סקר יציאה בטלוויזיה (נתונים אמיתיים, חישוב שלנו מול תוצאות הוועדה). הקווים המקווקווים הם סימולציה על נתוני פיתוח ובהנחות שלנו, לא תוצאה אמיתית.")
FIGS = {1: arrival_fig(),
 3: flow([("השוואה", "כל קלפי מול הקודמת"), ("למידה", "מה השתנה עד כה"), ("השלמה", "הקלפיות שטרם נספרו"), ("תוצאה", "מנדטים וטווח")], "איור סכמתי של השיטה. אין בו נתונים."),
 8: flow([("בחירה", "קלפיות לפי פרופיל"), ("ראיונות", "בכל קלפי שנבחרה"), ("תיקון", "לפי בחירות קודמות"), ("הערכה", "חלקים ומנדטים")], "איור סכמתי של תכנון סקר היציאה שנבדק בהדמיה. אין בו נתונים.")}
PLAIN = """<div class="plain"><div class="pc"><b>הבעיה</b><span>בזמן הספירה הקלפיות מתפרסמות בסדר לא אקראי, ולכן הסיכום החלקי מטעה.</span></div>
<div class="pc"><b>מה בנינו</b><span>מודל פתוח שמשווה כל קלפי לעצמה בבחירות הקודמות, לומד את השינוי ומשלים את מה שנשאר. ועוד: בדיקה מול סקרי היציאה של הטלוויזיה ודשבורד אינטראקטיבי.</span></div>
<div class="pc"><b>מה לא הוכח</b><span>אין לנו סדרי הגעה אמיתיים מהעבר, ולכן הבדיקות הן הדמיות. אין טענה שאנחנו מדויקים כמו מודל אחר או טובים מהטלוויזיה.</span></div></div>
<p class="hint">איך לקרוא: בכל סעיף מופיע קודם הסבר קצר. לחצו על "הרחבה" כדי לראות טבלאות ופרטים. {TAGS}</p>"""
def transform(page, tags):
    i = page.index("<main>") + 6; j = page.index("<footer>")
    head, body, tail = page[:i], page[i:j], page[j:]
    parts = re.split(r"(?=<h2>)", body); intro, secs = parts[0], parts[1:]
    nav = ""; out = ""
    for s in secs:
        m = re.match(r"<h2>(\d+)\.\s*(.*?)</h2>", s, re.S); n = int(m.group(1)); title = m.group(2)
        rest = s[m.end():]
        # lead = everything up to and including the first </p>
        k = rest.find("</p>"); lead, more = (rest[:k + 4], rest[k + 4:]) if k >= 0 else (rest, "")
        fig = FIGS.get(n, "")
        if n == 10: fig = "@@TVCHART@@"
        body_more = f'<details class="more"{" open" if n in OPEN else ""}><summary>הרחבה: פרטים, טבלאות ושיטה</summary>{more}</details>' if more.strip() else ""
        out += f'<section id="s{n}"><h2><span class="num">{n}</span>{title}</h2>{lead}{fig}{body_more}<a class="top" href="#top">↑ לראש הדף</a></section>'
        nav += f'<a href="#s{n}" data-s="s{n}"><i>{n}</i> {SHORT.get(n, title)}</a>'
    head = head.replace('<div class="banner">', '<div id="top"></div><div class="banner">', 1)
    navhtml = f'<nav class="nav" id="nav">{nav}</nav><div class="tools"><button onclick="document.querySelectorAll(\'details.more\').forEach(d=>d.open=true)">פתח הכול</button><button onclick="document.querySelectorAll(\'details.more\').forEach(d=>d.open=false)">סגור הכול</button></div>'
    h1 = re.search(r"<h1>.*?</h1>", intro, re.S)
    intro2 = intro.replace(h1.group(0), h1.group(0) + PLAIN.replace("{TAGS}", tags), 1)
    # existing "בקצרה" box becomes expandable
    intro2 = intro2.replace('<div class="box sum"><h3>בקצרה</h3>', '<details class="box sum more" open><summary>תוצאות המבחן בדיעבד, בקצרה</summary>', 1)
    ix = intro2.find("</ol></div>"); 
    if ix > 0: intro2 = intro2[:ix] + "</ol></details>" + intro2[ix + 11:]
    js = """<script>(function(){var l=[].slice.call(document.querySelectorAll('#nav a')),s=l.map(function(a){return document.getElementById(a.dataset.s)});function f(){var y=window.scrollY+120,c=0;s.forEach(function(e,i){if(e.offsetTop<=y)c=i});l.forEach(function(a,i){a.classList.toggle('on',i==c)});var o=l[c];if(o){var n=document.getElementById('nav');n.scrollLeft=o.offsetLeft-n.clientWidth/2}}window.addEventListener('scroll',f,{passive:true});f()})()</script>"""
    return head + navhtml + intro2 + out + tail.replace("</main>", js + "</main>", 1)
CSS = """
.nav{position:sticky;top:0;z-index:20;background:rgba(7,11,22,.94);backdrop-filter:blur(8px);margin:0 -18px;padding:8px 18px}
.nav a i{font-style:normal;color:var(--gold);margin-left:4px;font-weight:700}
.tools{display:flex;gap:8px;margin:10px 0}.tools button{font-size:13px;padding:5px 12px}
.plain{display:grid;grid-template-columns:1fr;gap:10px;margin:16px 0}@media(min-width:760px){.plain{grid-template-columns:repeat(3,1fr)}}
.pc{border:1px solid var(--line);background:var(--card);border-radius:14px;padding:14px;display:flex;flex-direction:column;gap:6px;line-height:1.55}.pc b{font-size:18px}.pc span{color:var(--dim);font-size:15px}
.hint{font-size:14px;color:var(--dim)}
section{scroll-margin-top:60px;margin-top:8px;border-top:1px solid var(--line);padding-top:6px}
h2 .num{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:50%;background:var(--gold);color:#101426;font-size:16px;margin-left:10px}
details.more{margin:12px 0;border:1px solid var(--line);border-radius:12px;background:rgba(255,255,255,.025)}details.more>summary{cursor:pointer;padding:12px 16px;font-weight:700;color:var(--gold);list-style:none}details.more>summary::-webkit-details-marker{display:none}details.more>summary::before{content:"＋ ";}details.more[open]>summary::before{content:"－ ";}details.more[open]>summary{border-bottom:1px solid var(--line)}details.more>*:not(summary){margin-right:16px;margin-left:16px}details.box.more{padding:0}
.fig{margin:14px 0;text-align:center}.fig figcaption{font-size:13px;color:var(--dim);margin-top:4px}
a.top{display:block;text-align:left;font-size:13px;color:var(--faint);text-decoration:none;margin:8px 0 4px}
"""
