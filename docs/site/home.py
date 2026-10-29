"""Landing page + one-question-per-screen layout for /model/. Every number comes from results/*.csv (passed in)."""
import json
COL = {"raw": "#6b7694", "model": "#2fd3c4", "tv": "#ffd166", "bad": "#ff7a90"}

def bars(groups, ymax, unit="", w=400, h=250, note_y=None):
    """groups: [(label, [(value, color)])]; first group drawn at the right (RTL)."""
    L, B, T = 8, 34, 22; ph = h - B - T; n = len(groups); gw = (w - L * 2) / n; inner = ""
    for v in range(0, int(ymax) + 1, max(1, int(ymax) // 5)):
        y = h - B - v * ph / ymax
        inner += f'<line x1="{L}" y1="{y:.1f}" x2="{w-L}" y2="{y:.1f}" stroke="#1f2a48"/>'
    for gi, (lab, items) in enumerate(groups):
        gx = w - L - (gi + 1) * gw; k = len(items); bw = min(46, (gw - 14) / k - 6)
        tot = k * bw + (k - 1) * 6; x0 = gx + (gw - tot) / 2 + tot - bw
        for ii, (v, c) in enumerate(items):
            bh = max(1.5, v * ph / ymax); x = x0 - ii * (bw + 6)
            inner += f'<rect x="{x:.1f}" y="{h-B-bh:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="5" fill="{c}"/>'
            inner += f'<text x="{x+bw/2:.1f}" y="{h-B-bh-6:.1f}" fill="#eef2ff" font-size="17" font-weight="800" text-anchor="middle">{v:.1f}{unit}</text>'
        inner += f'<text x="{gx+gw/2:.1f}" y="{h-10}" fill="#c4cde6" font-size="15" text-anchor="middle">{lab}</text>'
    return f'<svg viewBox="0 0 {w} {h}" dir="rtl" role="img" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto">{inner}</svg>'

def legend(items):
    return '<div class="hm-leg">' + "".join(f'<span><i style="background:{c}"></i>{t}</span>' for t, c in items) + "</div>"

def screen(sid, title, answer, chart_html, cap, more, tag, deep):
    return f'''<section class="screen" id="{sid}"><a class="hm-back" href="#home">→ חזרה לשאלות</a>
<h2 class="hm-q">{title}</h2><p class="hm-a">{answer}</p>
<div class="hm-chart">{chart_html}</div><p class="hm-tags">{tag}</p><p class="hm-cap">עמודה נמוכה יותר = פחות טעויות. {cap}</p>
<details class="hm-more"><summary>הרחבה</summary><div>{more}<p class="hm-deep">{tag} <a href="#{deep}">לפרטים המלאים, למי שרוצה (לחוקרים) ←</a></p></div></details>
<div class="hm-next"><a href="#home">← לשאלה אחרת</a></div></section>'''

def build(ctx):
    bt, g, tv_a, tv_mean_a, bu, dd, OFF, CALC = (ctx[k] for k in ("g", "g", "tv_a", "tv_mean_a", "bu", "dd", "OFF", "CALC")) if False else (None,) * 8
    g, tvA, TVM, bu, dd, OFF, CALC = ctx["g"], ctx["tvA"], ctx["tv_mean_a"], ctx["bu"], ctx["dd"], ctx["OFF"], ctx["CALC"]
    # Q1
    q1 = bars([(f"{int(f*100)}%", [(g('random', 'raw_counted', f), COL['raw']), (g('random', 'ridge', f), COL['model'])]) for f in (0.05, 0.20, 0.40)], 6, "")
    r5, m5 = g('random', 'raw_counted', .05), g('random', 'ridge', .05)
    s1 = screen("q1", "איך מנבאים את התוצאה מהספירה החלקית?",
        f"בזמן הספירה הקלפיות מגיעות בסדר לא אקראי, ולכן הסיכום החלקי מטעה. המודל משווה כל קלפי לעצמה בבחירות הקודמות ומשלים את מה שנשאר. כשנספרו רק 5% מהקלפיות הוא טעה בכ-{m5:.1f} מנדטים מתוך 120, והסיכום הגולמי ב-{r5:.1f}.",
        legend([("סיכום גולמי", COL['raw']), ("המודל שלנו", COL['model'])]) + q1,
        f"כמה מנדטים (מתוך 120) הוצבו אצל מפלגה אחרת ממה שקיבלה בסוף. הציר התחתון: איזה חלק מהקלפיות נספר. ממוצע על כנסות 22 עד 26, בסדר הגעה אקראי מדומה.",
        f"<p>חשוב: סדרי ההגעה בעבר לא פורסמו, ולכן הבדיקה נעשתה על סדר מדומה. ההשוואה הפוכה כשהסדר מוטה, ראו 'מה לא הוכח'.</p>",
        CALC, "s4")
    # Q2
    bu4 = bu[(bu.design == "strat_prior") & (bu["T"].isin([22, 23, 24, 25]))]
    v = lambda n, m: float(bu4[(bu4.n_places == n) & (bu4.m == m)].seats_out_of_place.mean())
    a = bars([(f"{n}", [(v(n, 100), COL['model'])]) for n in (30, 60, 120, 240)], 8)
    b = bars([(f"{m}", [(v(60, m), COL['raw'])]) for m in (50, 100, 200, 400)], 8)
    s2 = screen("q2", "כמה קלפיות צריך למדגם יציאה?",
        f"יותר קלפיות עוזר הרבה יותר מיותר ראיונות באותה קלפי. מ-60 ל-120 קלפיות הטעות יורדת מ-{v(60,100):.1f} ל-{v(120,100):.1f} מנדטים. מ-100 ל-200 ראיונות בכל קלפי היא יורדת רק מ-{v(60,100):.1f} ל-{v(60,200):.1f}.",
        '<h4 class="hm-sub">מוסיפים קלפיות (100 ראיונות בכל אחת)</h4>' + a + '<h4 class="hm-sub">מוסיפים ראיונות (60 קלפיות)</h4>' + b,
        f"מספרים: כמה מנדטים שגויים, בממוצע על כנסות 22 עד 25. הציר התחתון: מספר הקלפיות בתרשים הראשון, וראיונות בכל קלפי בשני. זו סימולציה בהנחה שכולם עונים בכנות.",
        "<p>הסיבה: אנשים באותה קלפי דומים זה לזה, ולכן הראיון ה-200 בקלפי כמעט לא מוסיף מידע חדש. קלפי נוספת מוסיפה מידע חדש.</p>",
        CALC, "s12")
    # Q3
    d4 = dd[dd["T"].isin([22, 23, 24, 25]) & (dd.n == 120) & (dd.m == 200)]
    def sd(design, pat, lv, nr): return float(d4[(d4.design == design) & (d4.pat == pat) & (d4.lv == lv) & (d4.nr == nr)].seats_oop.mean())
    ideal0, idealH, plain0 = sd("strat_greg_ps_bk", "none", 0, "none"), sd("strat_greg_ps_bk", "shy", 10, "nr_refuse"), sd("pps_ratio", "none", 0, "none")
    q3 = bars([("טלוויזיה", [(TVM, COL['tv'])]), ("בלי בעיות", [(ideal0, COL['model'])]), ("הנחות קשות", [(idealH, COL['bad'])])], 10)
    s3 = screen("q3", "האם אפשר לנצח את הטלוויזיה?",
        f"עדיין לא הוכח. בסימולציה, בלי שקר ובלי סירוב, מודל עם 120 קלפיות ו-200 ראיונות טועה בכ-{ideal0:.1f} מנדטים, והטלוויזיה טעתה בכ-{TVM:.1f} בכנסות 22 עד 25. אבל כשמניחים שחלק מהאנשים מסתירים ושקבוצות לא עונות, המודל טועה בכ-{idealH:.1f}.",
        legend([("הטלוויזיה (בפועל)", COL['tv']), ("סימולציה שלנו", COL['model']), ("סימולציה, הנחות קשות", COL['bad'])]) + q3,
        f"כמה מנדטים שגויים, בממוצע על כנסות 22 עד 25. הטלוויזיה: סקרי היציאה בפועל מול התוצאות הסופיות של הוועדה. המודל: סימולציה על נתוני פיתוח. ההנחות הקשות הן הנחה שלנו, לא מדידה.",
        "<p>דבר אחד כן ברור מהנתונים: הטלוויזיה נתנה למפלגות הערביות פחות מדי מנדטים בכל חמש הבחירות (בממוצע כ-1.2 מנדטים), והטעויות הגדולות באו מרשימות קרובות לאחוז החסימה. אין בכך טענה שנהיה מדויקים יותר.</p>",
        OFF + " " + CALC, "s10")
    # Q4: mini dashboard (precomputed, 120 boxes x 200 interviews, mean K22-25)
    tab = {}
    for des in ("pps_ratio", "strat_greg_ps_bk"):
        for li, (pat, lv) in enumerate([("none", 0), ("shy", 5), ("shy", 10), ("shy", 20)]):
            for ni, nr in enumerate(("none", "nr", "nr_refuse")):
                tab[f"{des[0]}{li}{ni}"] = round(sd(des, pat, lv, nr), 1)
    dash = f'''<div class="hm-ctl"><label>כמה מצביעי הרשימה הגדולה מסתירים?<select id="mq_l"><option value="0">אף אחד</option><option value="1">5%</option><option value="2" selected>10%</option><option value="3">20%</option></select></label>
<label>מי לא עונה?<select id="mq_n"><option value="0">כולם עונים</option><option value="1">חרדים וערבים עונים פחות</option><option value="2" selected>גם קלפיות חרדיות וערביות מסרבות</option></select></label></div>
<div id="mq_out"></div>{legend([("הטלוויזיה (בפועל)", COL['tv']), ("שיטה רגילה", COL['raw']), ("המודל שלנו", COL['model'])])}'''
    js = "const MQ=" + json.dumps(tab) + ";const MQTV=" + f"{TVM:.1f}" + ";" + '''
function bar(v,c,t){const w=Math.min(100,v*100/16);return '<div class="mq-row"><span class="mq-t">'+t+'</span><div class="mq-b"><i style="width:'+w+'%;background:'+c+'"></i></div><b>'+v.toFixed(1)+'</b></div>'}
function mqr(){const l=document.getElementById('mq_l').value,n=document.getElementById('mq_n').value;
document.getElementById('mq_out').innerHTML=bar(MQTV,'#ffd166','הטלוויזיה')+bar(MQ['p'+l+n],'#6b7694','שיטה רגילה')+bar(MQ['s'+l+n],'#2fd3c4','המודל שלנו')}
['mq_l','mq_n'].forEach(i=>document.getElementById(i).addEventListener('change',mqr));mqr();'''
    s4 = screen("q4", "מה קורה אם אנשים משקרים?",
        f"בחרו כמה אנשים מסתירים למי הצביעו ומי לא עונה, וראו כמה מנדטים טועים. בלי בעיות המודל שלנו טועה בכ-{ideal0:.1f} מנדטים (שיטה רגילה: {plain0:.1f}). ככל שיש יותר הסתרה וסירוב, הטעות גדלה, והשיטה הרגילה נפגעת יותר.",
        dash, f"כמה מנדטים שגויים, 120 קלפיות ו-200 ראיונות, ממוצע על כנסות 22 עד 25 (סימולציה). שקר ואי מענה הם הנחות שלנו, לא מדידה. שיטה רגילה: הגרלת קלפיות לפי גודל, בלי שימוש בנתוני העבר. הטלוויזיה: סקרי היציאה בפועל.",
        "<p>הטבלה המלאה לפי בחירה, ועוד אפשרויות (גודל מדגם, שיטות נוספות), נמצאת בדשבורד לחוקרים.</p>", OFF + " " + CALC, "s13")
    # Q5
    wc20, wr20 = g('low_likud_first', 'ridge', .20), g('low_likud_first', 'raw_counted', .20)
    q5 = bars([("סדר אקראי", [(g('random', 'raw_counted', .20), COL['raw']), (g('random', 'ridge', .20), COL['model'])]),
               ("סדר מוטה (מקרה גרוע)", [(wr20, COL['raw']), (wc20, COL['model'])])], 80)
    s5 = screen("q5", "מה לא הוכח?",
        f"לא הוכחנו שהמודל מדויק כמו Votes26 או כל מודל אחר. לא הוכחנו שהוא מנצח את הטלוויזיה. לא ידוע לנו סדר ההגעה האמיתי של קלפיות בעבר, ולכן כל הבדיקות הן על סדר מדומה. ואם הסדר מוטה מאוד, גם המודל טועה: במקרה הגרוע שבדקנו {wc20:.0f} מנדטים אחרי ספירת 20%.",
        legend([("סיכום גולמי", COL['raw']), ("המודל שלנו", COL['model'])]) + q5,
        f"כמה מנדטים שגויים כשנספרו 20% מהקלפיות. סדר הגעה מדומה. בשני המקרים המודל טוב יותר מהסיכום הגולמי, אבל במקרה הגרוע הוא עדיין רחוק מאוד.",
        "<ul><li>כנסות 22 עד 25 הן נתוני פיתוח. כנסת 26 עדיין לא תוצאה סופית ואינה בדיקה עצמאית.</li><li>התוצאות של המודל אינן תוצאה רשמית. רק ועדת הבחירות המרכזית מפרסמת תוצאות רשמיות.</li><li>הנחות על שקר ואי מענה הן שלנו, לא מדידה.</li></ul>",
        CALC, "s7")
    tiles = [("q1", "1", "איך מנבאים את התוצאה מהספירה החלקית?"), ("q2", "2", "כמה קלפיות צריך למדגם יציאה?"), ("q3", "3", "האם אפשר לנצח את הטלוויזיה?"), ("q4", "4", "מה קורה אם אנשים משקרים?"), ("q5", "5", "מה לא הוכח?")]
    home = '<section class="screen" id="home"><h1 class="hm-h">הספירה החלקית מטעה. אנחנו בונים מודל פתוח שמתקן אותה.</h1><p class="hm-sub0">בחרו שאלה:</p><div class="hm-tiles">' + "".join(f'<a class="hm-tile" href="#{i}"><b>{n}</b><span>{t}</span></a>' for i, n, t in tiles) + '</div><a class="hm-res" href="#research">לחוקרים: שיטות, נתונים, שחזור ←</a>@@BANNER@@</section>'
    return home + s1 + s2 + s3 + s4 + s5, js

CSS = """
.screen{display:none}.screen.on{display:block}
.hm-h{font-size:30px;line-height:1.3;margin:18px 0 8px}.hm-sub0{color:var(--muted,#a8b3d1);font-size:18px;margin:6px 0 12px}
.hm-tiles{display:grid;gap:12px;margin:8px 0 18px}
.hm-tile{display:flex;align-items:center;gap:14px;background:#16203a;border:1px solid #3b4a77;border-radius:16px;padding:18px 16px;text-decoration:none;color:#eef2ff;font-size:21px;font-weight:700;line-height:1.3}
.hm-tile b{flex:0 0 auto;width:38px;height:38px;border-radius:50%;background:#ffd166;color:#101426;display:flex;align-items:center;justify-content:center;font-size:20px}
.hm-tile:active,.hm-tile:hover{border-color:#ffd166}
.hm-res{display:block;text-align:center;color:#a8b3d1;padding:12px;margin-bottom:14px}
.hm-back{display:inline-block;margin:10px 0 4px;padding:10px 14px;border:1px solid #3b4a77;border-radius:12px;color:#ffd166;text-decoration:none;font-size:17px;font-weight:700}
.hm-q{font-size:27px;line-height:1.3;margin:12px 0 10px}.hm-a{font-size:20px;line-height:1.6;margin:0 0 14px}
.hm-chart{background:#10172b;border:1px solid #26335a;border-radius:16px;padding:14px 10px}.hm-sub{font-size:16px;color:#c4cde6;margin:8px 6px 0}
.hm-cap{font-size:15px;line-height:1.55;color:#a8b3d1;margin:10px 2px 14px}
.hm-leg{display:flex;flex-wrap:wrap;gap:6px 16px;margin:0 6px 10px;font-size:16px}.hm-leg i{display:inline-block;width:14px;height:14px;border-radius:4px;margin-inline-end:6px;vertical-align:-2px}
.hm-more{background:#0f1526;border:1px solid #2b3860;border-radius:14px;padding:4px 14px;margin:8px 0}.hm-more summary{cursor:pointer;font-size:19px;font-weight:700;color:#ffd166;padding:12px 0}.hm-more div{font-size:17px;line-height:1.6}
.hm-tags{margin:12px 2px 0;font-size:14px}.hm-deep{font-size:15px}.hm-next{margin:18px 0 28px}.hm-next a{font-size:18px;color:#ffd166}
.hm-ctl{display:grid;gap:10px;margin:0 4px 14px}.hm-ctl label{display:grid;gap:6px;font-size:17px}.hm-ctl select{font-size:17px;padding:12px;border-radius:10px;background:#16203a;color:#eef2ff;border:1px solid #3b4a77}
.mq-row{display:grid;grid-template-columns:96px 1fr 44px;align-items:center;gap:10px;margin:12px 4px;font-size:17px}.mq-b{background:#1a2442;border-radius:8px;height:26px;overflow:hidden}.mq-b i{display:block;height:100%;border-radius:8px}.mq-row b{font-size:20px}
.hm-chart{max-width:560px}.hm-chart svg{max-height:340px}.hm-h{max-width:640px}
.hm-back2{display:inline-block;margin:6px 0;padding:10px 14px;border:1px solid #3b4a77;border-radius:12px;color:#ffd166;text-decoration:none;font-weight:700}
"""
ROUTER = """(function(){function r(){var h=location.hash.slice(1)||'home',id=h;if(/^s\\d+$/.test(h)||h==='top')id='research';var s=document.getElementById(id);if(!s||!s.classList.contains('screen')){id='home';s=document.getElementById('home')}
document.querySelectorAll('.screen').forEach(function(e){e.classList.toggle('on',e===s)});
if(id==='research'&&/^s\\d+$/.test(h)){var t=document.getElementById(h);if(t)t.scrollIntoView()}else window.scrollTo(0,0)}
window.addEventListener('hashchange',r);r()})()"""

def wrap(page, ctx):
    scr, js = build(ctx)
    i = page.index('<div id="top"></div>'); j = page.index('<main>')
    banner = page[i + len('<div id="top"></div>'):j]
    k = page.rindex('</main>')
    scr = scr.replace('@@BANNER@@', banner)
    res = '<section class="screen" id="research"><a class="hm-back" href="#home">→ חזרה לשאלות</a>' + page[j:k] + '</main></section>'
    tail = page[k + len('</main>'):]
    out = page[:i] + '<div id="top"></div>' + scr + res + tail
    out = out.replace('</body>', '<script>' + js + '</script><script>' + ROUTER + '</script><noscript><style>.screen{display:block}</style></noscript></body>')
    return out
