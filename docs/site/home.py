"""Landing page + one-question-per-screen layout for /model/. Every number comes from results/*.csv (passed in)."""
import json
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
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
    # Q4: Monte Carlo lying (pre-registered lies-mc-v1)
    import pandas as pd
    L = pd.read_csv("results/lies_mc.csv"); LM = pd.read_csv("results/lies_mc_mild_posthoc.csv")
    tab = {}
    for key, df, reg in (("A", L, "all"), ("R1", L, "R1"), ("R2", L, "R2"), ("R3", L, "R3"), ("M", LM, "all")):
        for (n, m) in ((60, 100), (120, 200)):
            for des, dk in (("pps_ratio", "p"), ("strat_greg_ps_bk", "s")):
                r = df[(df.n == n) & (df.regime == reg) & (df.design == des)].iloc[0]
                tab[f"{key}{n}{dk}"] = [float(r["median"]), float(r["p5"]), float(r["p95"]), float(r["p_above_tv"])]
    dash = f'''<div class="hm-ctl"><label>איך משקרים?<select id="mq_r"><option value="A">לא יודעים: כל האפשרויות מעורבבות</option><option value="R1">מתואמים: כל השקרנים אומרים אותו דבר</option><option value="R2">מפוזרים: כל אחד אומר משהו אחר</option><option value="R3">לא עקביים: משקרים בהווה ולא בעבר</option><option value="M">פחות שקרנים (בדיקת רגישות, לא נקבעה מראש)</option></select></label>
<label>גודל המדגם<select id="mq_s"><option value="120">120 קלפיות, 200 ראיונות בכל אחת</option><option value="60">60 קלפיות, 100 ראיונות בכל אחת</option></select></label></div>
<div id="mq_out"></div>{legend([("הטלוויזיה (ממוצע בפועל)", COL['tv']), ("שיטה רגילה", COL['raw']), ("המודל שלנו", COL['model'])])}'''
    js = "const MQ=" + json.dumps(tab) + ";const MQTV=" + f"{TVM:.1f}" + ";" + '''
function band(v,c,t,tv){const S=18,lo=v[1]/S*100,wd=Math.max(1.5,(v[2]-v[1])/S*100),md=v[0]/S*100;
return '<div class="mq-row2"><div class="mq-t2">'+t+'</div><div class="mq-b"><i style="right:'+lo+'%;width:'+wd+'%;background:'+c+';opacity:.45"></i><i style="right:'+md+'%;width:4px;background:'+c+'"></i>'+(tv?'':'<u style="right:'+(MQTV/S*100)+'%"></u>')+'</div><div class="mq-n">'+(tv?'<b>'+v[0].toFixed(1)+'</b> ממוצע בפועל, כנסות 22 עד 25':'<b>'+v[0].toFixed(0)+'</b> חציון, טווח '+v[1].toFixed(0)+' עד '+v[2].toFixed(0)+'. מעל ממוצע הטלוויזיה ב-'+Math.round(v[3]*100)+'% מהריצות')+'</div></div>'}
function mqr(){const r=document.getElementById('mq_r').value,n=document.getElementById('mq_s').value;
document.getElementById('mq_out').innerHTML=band([MQTV,MQTV,MQTV],'#ffd166','הטלוויזיה',1)+band(MQ[r+n+'p'],'#6b7694','שיטה רגילה',0)+band(MQ[r+n+'s'],'#2fd3c4','המודל שלנו',0)}
['mq_r','mq_s'].forEach(i=>document.getElementById(i).addEventListener('change',mqr));mqr();'''
    A = lambda n, k: tab[f"A{n}{k}"]
    s4 = screen("q4", "מה קורה אם אנשים משקרים?",
        f"אף אחד לא יודע איך משקרים ולמי, ולכן לא בחרנו תרחיש אחד. בכל אחת מ-300 ריצות לכל בחירות הגרלנו מי משקר, כמה, ולמי הם אומרים שהצביעו. עם 120 קלפיות ו-200 ראיונות, המודל שלנו טעה בחציון ב-{A(120,'s')[0]:.0f} מנדטים (טווח 90% מ-{A(120,'s')[1]:.0f} עד {A(120,'s')[2]:.0f}). השיטה הרגילה: {A(120,'p')[0]:.0f} (מ-{A(120,'p')[1]:.0f} עד {A(120,'p')[2]:.0f}).",
        dash, f"הפס הבהיר הוא הטווח שבו נפלו 90% מהריצות, והקו הכהה הוא החציון. הקו האפור הוא ממוצע הטלוויזיה ({TVM:.1f}). אלה הנחות שלנו על שקר, לא מדידה, וההנחה הראשית קשה: בממוצע כ-3.7 רשימות משקרות והן מסתירות כ-12% ממצביעיהן. שיטה רגילה: הגרלת קלפיות לפי גודל, בלי נתוני עבר.",
        "<p>מה כבר היה מונטה קרלו קודם: בחירת הקלפיות, הנשאלים ומי מסרב. מה היה קבוע: דפוס השקר (הרשימה הגדולה מסתירה 5, 10 או 20%) ושיעורי אי המענה. עכשיו גם דפוס השקר מוגרל.</p><p>ממצא שלילי: כששקרנים עקביים (גם בהווה וגם בעבר), שקלול לפי 'למי הצבעת בפעם הקודמת' מחמיר את המצב. כששקרנים לא עקביים, המודל לא מרוויח הרבה מכך.</p>", OFF + " " + CALC, "s16")
    # Q5
    wc20, wr20 = g('low_likud_first', 'ridge', .20), g('low_likud_first', 'raw_counted', .20)
    q5 = bars([("סדר אקראי", [(g('random', 'raw_counted', .20), COL['raw']), (g('random', 'ridge', .20), COL['model'])]),
               ("סדר מוטה (מקרה גרוע)", [(wr20, COL['raw']), (wc20, COL['model'])])], 80)
    s5 = screen("q5", "מה לא הוכח?",
        f"לא הוכחנו שהמודל מדויק כמו Votes26 או כל מודל אחר. לא הוכחנו שהוא מנצח את הטלוויזיה. לא ידוע לנו סדר ההגעה האמיתי של קלפיות בעבר, ולכן כל הבדיקות הן על סדר מדומה. ואם הסדר מוטה מאוד, גם המודל טועה: במקרה הגרוע שבדקנו {wc20:.0f} מנדטים אחרי ספירת 20%.",
        legend([("סיכום גולמי", COL['raw']), ("המודל שלנו", COL['model'])]) + q5,
        f"כמה מנדטים שגויים כשנספרו 20% מהקלפיות. סדר הגעה מדומה. בשני המקרים המודל טוב יותר מהסיכום הגולמי, אבל במקרה הגרוע הוא עדיין רחוק מאוד.",
        "<ul><li>כנסות 22 עד 25 הן נתוני פיתוח. כנסת 26 היא תוצאה מלאה (פרסום רשמי צפוי ב-4.11) ואינה בדיקה עצמאית.</li><li>התוצאות של המודל אינן תוצאה רשמית. רק ועדת הבחירות המרכזית מפרסמת תוצאות רשמיות.</li><li>הנחות על שקר ואי מענה הן שלנו, לא מדידה.</li></ul>",
        CALC, "s7")
    EX = pd.read_csv("results/experiments.csv")
    ccol = {"better": "#2fd3c4", "none": "#6b7694", "worse": "#ff7a90"}; ctxt = {"better": "שיפור", "none": "אין השפעה", "worse": "החמרה"}
    rows6 = ""
    for _, r in EX.sort_values("change_pct").iterrows():
        w = min(100, abs(r.change_pct) * 1.4); smaller = 'קטנה' if r.change_pct < 0 else 'גדלה'
        rows6 += f'<div class="ex-row"><div class="ex-t">{r.tried}</div><div class="ex-bar"><i style="width:{max(w,2):.0f}%;background:{ccol[r.verdict]}"></i></div><div class="ex-n" style="color:{ccol[r.verdict]}"><b>{ctxt[r.verdict]}</b>: הטעות {smaller} ב-{abs(r.change_pct):.0f}%</div></div>'
    nb, nn, nw = (EX.verdict == "better").sum(), (EX.verdict == "none").sum(), (EX.verdict == "worse").sum()
    s6 = screen("q6", "מה ניסינו, מה שיפר ומה החמיר?",
        f"ניסינו {len(EX)} דברים. {nb} שיפרו, {nn} לא שינו, ו-{nw} החמירו. הדוגמה הבולטת: שיפור ההתאמה בין קלפיות (מ-83% ל-92% מהקולות) לא שיפר כמעט את התחזית.",
        '<div class="ex-list">' + rows6 + '</div>' + legend([("שיפור", ccol['better']), ("אין השפעה", ccol['none']), ("החמרה", ccol['worse'])]),
        "השינוי באחוזים בטעות, לעומת הגרסה הבסיסית של אותו ניסוי. סימון: שיפור או החמרה של 5% ויותר; פחות מזה נחשב 'אין השפעה'. הכלל נקבע אחרי שהניסויים הרצו, והמספרים מהמאגר (results/experiments.csv). בכל שורה בהרחבה מסומן אם זה נתוני פיתוח או מוחזק בחוץ.",
        "<table class='ex-tab'><tr><th>ניסוי</th><th>לפני</th><th>אחרי</th><th>נתונים</th></tr>" + "".join(f"<tr><td>{r.tried}<br><small>{r.metric}{(' · ' + r.note) if isinstance(r.note, str) else ''}</small></td><td>{r.baseline:g}</td><td>{r.variant:g}</td><td>{r.data}</td></tr>" for _, r in EX.iterrows()) + "</table><p>ניסויים שנכשלו נשארים בטבלה. כנסות 22 עד 25 הן נתוני פיתוח. כנסת 26 אינה בדיקה עצמאית.</p>",
        CALC, "s17")
    tiles = [("q1", "1", "איך מנבאים את התוצאה מהספירה החלקית?"), ("q2", "2", "כמה קלפיות צריך למדגם יציאה?"), ("q3", "3", "האם אפשר לנצח את הטלוויזיה?"), ("q4", "4", "מה קורה אם אנשים משקרים?"), ("q5", "5", "מה לא הוכח?"), ("q6", "6", "מה ניסינו, מה שיפר ומה החמיר?")]
    home = '<section class="screen" id="home"><h1 class="hm-h">הספירה החלקית מטעה. אנחנו בונים מודל פתוח שמתקן אותה.</h1><p class="hm-sub0">בחרו שאלה:</p><div class="hm-tiles">' + "".join(f'<a class="hm-tile" href="#{i}"><b>{n}</b><span>{t}</span></a>' for i, n, t in tiles) + '</div><a class="hm-res" href="#research">לחוקרים: שיטות, נתונים, שחזור ←</a>@@BANNER@@</section>'
    return home + s1 + s2 + s3 + s4 + s5 + s6, js

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
.mq-b{overflow:visible;height:22px}.mq-row2{margin:14px 4px}.mq-t2{font-size:17px;margin-bottom:4px}.mq-b{position:relative}.mq-b i{position:absolute;top:0;height:100%;border-radius:6px}.mq-b u{position:absolute;top:-3px;bottom:-3px;width:2px;background:#ffd166}.mq-n{font-size:15px;color:#c4cde6;margin-top:4px}
.ex-row{margin:12px 2px;padding-bottom:10px;border-bottom:1px solid #1f2a48}.ex-t{font-size:17px;line-height:1.4}.ex-bar{background:#1a2442;border-radius:6px;height:12px;margin:6px 0}.ex-bar i{display:block;height:100%;border-radius:6px;margin-inline-start:0}.ex-n{font-size:16px}
.ex-tab{width:100%;border-collapse:collapse;font-size:14px}.ex-tab th,.ex-tab td{padding:6px;border-bottom:1px solid #1f2a48;text-align:right}
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

def research_sections(ctx):
    import pandas as pd
    CALC = ctx["CALC"]; L = pd.read_csv("results/lies_mc.csv"); LM = pd.read_csv("results/lies_mc_mild_posthoc.csv"); EX = pd.read_csv("results/experiments.csv")
    DN = {"pps_ratio": "הגרלה לפי גודל (רגיל)", "strat_prior": "מרובד + תיקון לפי עבר", "strat_greg_ps_bk": "המודל האידיאלי", "strat_prior_pastvote": "שקלול לפי הצבעה קודמת"}
    RN = {"R1": "מתואמים", "R2": "מפוזרים", "R3": "לא עקביים", "all": "הכול יחד"}
    def tab(df, size, regs):
        t = "<table><tr><th>שקרנים</th><th>שיטה</th><th>חציון</th><th>טווח 90%</th><th>ממוצע</th><th>מעל ממוצע הטלוויזיה</th></tr>"
        for rg in regs:
            for d in DN:
                r = df[(df.n == size[0]) & (df.m == size[1]) & (df.regime == rg) & (df.design == d)].iloc[0]
                t += f"<tr><td>{RN[rg]}</td><td>{DN[d]}</td><td>{r['median']:.0f}</td><td>{r.p5:.0f} עד {r.p95:.0f}</td><td>{r['mean']:.1f}</td><td>{100*r.p_above_tv:.0f}%</td></tr>"
        return t + "</table>"
    h16 = f"""<h2>16. מונטה קרלו על שקרנים (נקבע מראש, lies-mc-v1)</h2>
<p>עד עכשיו דפוס השקר היה קבוע (הרשימה הגדולה מסתירה 5, 10 או 20%). רק הדגימה הייתה מונטה קרלו. כאן גם השקר מוגרל בכל ריצה: אילו רשימות משקרות (כל רשימה מעל 3%, בהסתברות 0.35), כמה מהמצביעים שלהן מסתירים (אחיד בין 0 ל-25%), ולמי הם אומרים שהצביעו. הכול הנחות שלנו. {CALC}</p>
<p>שלושה סוגי שקרנים: מתואמים (כולם בוחרים אותה רשימה אחרת, ומשקרים באותו אופן גם על העבר), מפוזרים (כל אחד אומר משהו אחר, גם כאן עקביים בעבר), ולא עקביים (משקרים בהווה, אומרים אמת על העבר). 300 ריצות לכל בחירות, כנסות 22 עד 25 (נתוני פיתוח), בלי אי מענה.</p>
<p>120 קלפיות, 200 ראיונות בכל קלפי (מנדטים שגויים):</p>{tab(L, (120, 200), ["R1", "R2", "R3", "all"])}
<p>60 קלפיות, 100 ראיונות:</p>{tab(L, (60, 100), ["all"])}
<p><b>בדיקת רגישות, לא נקבעה מראש:</b> אם ההסתברות לשקר 0.15 והשיעור עד 10% (בממוצע 1.6 רשימות משקרות), 120 קלפיות ו-200 ראיונות:</p>{tab(LM, (120, 200), ["all"])}
<p>קריאה: ההנחה המקורית קשה (בממוצע 3.7 רשימות משקרות, כ-12% מהמצביעים של כל אחת). אין לנו נתון על שקר אמיתי. בהנחה הקשה גם המודל האידיאלי חורג מממוצע הטלוויזיה (4.2) ברוב הריצות. בהנחה המתונה זה קורה בכשליש מהן. הממצא שנשאר בשתיהן: המודל טוב מההגרלה הרגילה, והשקלול לפי הצבעה קודמת לבדו לא יציב כששקרנים עקביים.</p>
<p>קבצים: <span class="f">model/lies_mc.py</span> <span class="f">results/lies_mc.csv</span> <span class="f">results/lies_mc_draws.csv.gz</span> <span class="f">docs/prereg/lies_montecarlo.md</span></p>"""
    cc = {"better": "שיפור", "none": "אין השפעה", "worse": "החמרה"}
    t17 = "<table><tr><th>ניסוי</th><th>מדד</th><th>לפני</th><th>אחרי</th><th>שינוי</th><th>תוצאה</th><th>נתונים</th></tr>" + "".join(f"<tr><td>{r.tried}</td><td>{r.metric}</td><td>{r.baseline:g}</td><td>{r.variant:g}</td><td dir='ltr'>{r.change_pct:+.0f}%</td><td>{cc[r.verdict]}</td><td>{r.data}</td></tr>" for _, r in EX.iterrows()) + "</table>"
    h17 = f"""<h2>17. כל הניסויים בטבלה אחת</h2><p>כל שורה לקוחה מקובצי התוצאות במאגר (results/experiments.csv, נבנה ב-scripts/build_experiments.py). שיפור או החמרה: שינוי של 5% ויותר בטעות. הכלל נקבע אחרי שהניסויים הורצו. ניסויים שנכשלו נשארים.</p>{t17}{__import__("fan").mc_block()}<h3>ניסויים אבחוניים (בלי "שיפר או החמיר")</h3><ul><li><b>מאיפה בא הטעות (decomp-v1):</b> בסדר מוטה כמעט כל הטעות בחלקי הרשימות; בסדר אקראי רוב הטעות בגודל הקלפיות.</li><li><b>כמה התאמה צריך (matchsens-v1):</b> ירידה מ-90% ל-76% של קולות מותאמים כמעט לא משנה (0.198 ל-0.204 נקודות אחוז בסדר אקראי, 20% נספרו); רק ב-65% יש עלייה של 17%.</li><li><b>מה קובע את הטעות (round2-v1):</b> הטעות קשורה חזק גם להבדל הנראה בין הקלפיות שנספרו לכלל (מתאם דרגות 0.83) וגם להבדל הנסתר בשינוי (0.85); אי אפשר להפריד ביניהם. <b>הבדל נראה הוא מדד שאפשר לחשב בזמן אמת</b>.</li><li><b>מעבר אוטומטי לפי ההבדל הנראה (switch-v1):</b> כשההבדל חורג מהצפוי בהגרלה אקראית, עוברים למודל ההעברה. בסדר מוטה (5% נספרו) מנדטים שגויים: 62 ל-28 בפיתוח (כנסות 23-26) ו-62 ל-36 באימות בשימוש חוזר (כנסות 20-21). בסדר אקראי פוגע בפיתוח (2.3 ל-3.4) ובספירה מאוחרת הוא מזיק. <b>לא אומץ</b> לפי הכלל שנקבע מראש.</li><li><b>מדד חברתי-כלכלי של הלמ"ס (cbs-v1):</b> מקור: הלמ"ס, אפיון יחידות גאוגרפיות לפי הרמה החברתית-כלכלית 2021, בשימוש לפי רישיון השימוש של הלמ"ס. אין שיפור לפי הכלל (בסדר מוטה 2.34 ל-2.22, בסדר אקראי 0.179 ל-0.184).</li><li><b>סיבת ההפסד של מודל ההעברה בסדר אקראי (round3-v1):</b> הקנס של המודל גדל עם מספר הקלפיות שנספרו ולכן לא נעלם. כשהקנס קבוע, הטעות בסדר אקראי (20% נספרו) יורדת מ-0.76 ל-0.30 נקודות אחוז (בסיס: 0.18), אבל נשארת רצפה: גם מטריצה שנאמדה על כל הקלפיות (בדיקה בלבד, לא ניתן לחשב בזמן אמת) נותנת 0.25. הרידג' הבסיסי כמעט לא מוענש (קנס 5 מול משקלות של אלפים), אבל הגדלת הקנס שלו לא עוזרת. <b>אף שיטה חדשה לא עברה את הכלל</b>: ערימה רציפה של שלושה מודלים מורידה את הטעות בכ-30% בסדר מוטה מאוד בספירה מוקדמת (1% נספרו), ומחמירה ב-21% בסדר אקראי באותה ספירה (פיתוח, כנסות 23-26).</li><li><b>מדד הטיה בזמן אמת (round4-v1, בדיקה בלבד, לא משנה את התחזית):</b> ההבדל הנראה g (בין קלפיות שנספרו לכלל, לפי הבחירות הקודמות) מזהה סדר מוטה: בסדר מוטה כלשהו הוא מעל סף ההגרלה ב-100% מהמקרים (חוץ מ"קטנות קודם" ב-1% נספרו: 50%); בסדר אקראי אזעקת שווא ב-0% עד 25% מהמקרים. מתאם דרגות בין g לטעות של המודל הבסיסי: 0.88 בפיתוח, 0.87 באימות בשימוש חוזר. g מזהה שהסדר מוטה, לא כמה הטעות גדולה בכל מקרה.</li><li><b>הפעלת המעבר רק עד אחוז ספירה מסוים (switch-cutoff-v1):</b> סף 5%: בסדר מוטה (ליכוד נמוך קודם, 5% נספרו) מנדטים שגויים 62 ל-28 בפיתוח ו-62 ל-36 באימות בשימוש חוזר; בסדר אקראי אין עלות באימות בשימוש חוזר, ובפיתוח עלות של כמנדט אחד באזעקת שווא אחת. סף 20%: עלות גדולה בסדר אקראי (עד 101% בטעות). נבדקו שני ספים שנקבעו מראש (5%, 20%), הראשון עובר את הכלל באימות בשימוש חוזר בלבד, ולכן לא אומץ.</li><li><b>תוצאות נוספות (round4-v1):</b> שילוב לפי אימות צולב לפי בלוקים (רעיון 4), תהליך גאוסי על השאריות (רעיון 6) וטווחים לפי טעות קודמת (רעיון 5): <b>אף אחד לא עבר את הכלל</b>. התהליך הגאוסי הכי קרוב: אותו יתרון מוקדם בסדר מוטה כמו מודל ההעברה (בערך 44% פחות שגיאה ב-5%) ובלי הפסד כמעט בסדר אקראי, אבל נכשל בבדיקות מסוימות (עד 17% יותר בסדר "הצבעה נמוכה קודם" ב-40% נספרו). טווחים: ברוב המקרים בסדר אקראי רחבים מדי (כיסוי 99%) ובסדר מוטה צרים מדי (כיסוי 26%).</li><li><b>תהליך גאוסי עם שער והפסקה ב-20% (gp-gate-v1, נרשם מראש):</b> שלושה ערכי רעש (0.1, 0.5, 2.0), עם שער ובלעדיו. הגרסה עם רעש 2.0 ושער עוברת את הכלל בפיתוח (שום תא לא גרוע ביותר מ-0%, ובסדר מוטה 43% עד 56% פחות שגיאה), אבל <b>לא עוברת באימות בשימוש חוזר</b>: שם היתרון ב-5% נספרו הוא רק 16% עד 17% (הכלל דורש 20%) ויש תא אחד עם 11% החמרה. אף וריאנט לא עבר בשתי הקבוצות; לא אומץ.</li><li><b>אימות בשימוש חוזר, כנסות 19-21 (holdout-v1):</b> היתרון על הסכום הגולמי בסדר מוטה אושר; היתרון בסדר אקראי לא אושר. מנדטים לפי חישוב שלנו.</li><li><b>טווחי מנדטים (ideas569-v1, results/seat_draws.csv):</b> בסדר אקראי טווח 80% מכסה בערך 67% עד 100% מהרשימות; בסדר מוטה (ליכוד נמוך קודם) רק 36% עד 80%. כלומר הטווחים צרים מדי כשהסדר מוטה, גם אחרי הרחבה שנבחרה מכנסות אחרות. הכיול לא טוב מספיק.</li></ul>"""
    return h16 + h17
