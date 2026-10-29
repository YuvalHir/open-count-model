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


# ---------- TV exit-poll comparison ----------
_tv = pd.read_csv("results/tv_exit_poll_comparison.csv")
_tvs = _tv[(_tv.scored == "yes") & (_tv.source_tier.isin(["A", "B"]))]
_ek = {21: "אפריל 2019 (כנסת 21)", 22: "ספטמבר 2019 (כנסת 22)", 23: "מרץ 2020 (כנסת 23)", 24: "מרץ 2021 (כנסת 24)", 25: "נובמבר 2022 (כנסת 25)"}
_cn = {"Channel 12": "ערוץ 12", "Channel 13": "ערוץ 13", "Kan 11": "כאן 11"}
TV_ROWS = ""
for _e in [21, 22, 23, 24, 25]:
    _r = _tvs[_tvs.election == _e]
    _cells = "".join(f"<td>{_r[_r.channel == c].out_of_place.iloc[0]:.0f}</td>" if (_r.channel == c).any() else "<td>חסר</td>" for c in _cn)
    _tier = "ב (טבלת ויקיפדיה, לא אומת כראשון)" if _e == 21 else "א (דיווח חדשותי מליל הבחירות)"
    TV_ROWS += f"<tr><td>{_ek[_e]}</td>{_cells}<td>{_tier}</td></tr>"
_ex = pd.read_csv("results/exitpoll.csv")
def _sim(sc, Ts=(22, 23, 24, 25)):
    q = _ex[(_ex.design == "strat_prior") & (_ex.n_places == 60) & (_ex.m == 100) & (_ex.scenario == sc) & (_ex["T"].isin(Ts))]
    return q.seats_misallocated.mean()
_tvA = _tvs[_tvs.election.isin([22, 23, 24, 25])]
TV_N = len(_tvs); TV_MEAN = _tvs.out_of_place.mean(); TV_MIN = _tvs.out_of_place.min(); TV_MAX = _tvs.out_of_place.max()
TV_MEAN_A = _tvA.out_of_place.mean(); TV_MAE = _tvs.mae_list.mean()
SIM_NONE = _sim("none"); SIM_HARD = _sim("hard_both")


# ---------- diagnosis + dashboard data ----------
import json as _json
_gb = pd.read_csv("results/tv_group_errors.csv")
_GN = {"Likud": "הליכוד", "Haredi": "חרדים (ש״ס, יהדות התורה)", "Arab": "מפלגות ערביות", "Rest": "שאר הרשימות"}
GRP_ROWS = ""
for _k in ["Likud", "Haredi", "Arab", "Rest"]:
    _c = ""
    for _e in [21, 22, 23, 24, 25]:
        _v = _gb[(_gb.election == _e) & (_gb.group == _k)].signed_err
        _c += f"<td>{_v.mean():+.1f}</td>"
    _all = _gb[_gb.group == _k].signed_err.mean()
    GRP_ROWS += f"<tr><td>{_GN[_k]}</td>{_c}<td><b>{_all:+.1f}</b></td></tr>"
_mf = pd.read_csv("results/mechanism_fit.csv")
_SCN = {"none": "אין בעיה", "noise10": "10% עונים אקראית", "shy15": "15% ממצביעי הרשימה הגדולה מסתירים", "refuse20": "מצביעי הרשימה הגדולה עונים 20% פחות", "hard_nr": "חרדים וערבים עונים פחות", "place_refuse": "קלפיות חרדיות וערביות מסרבות", "hard_both": "שניהם"}
MECH_ROWS = "".join(f"<tr><td>{_SCN.get(r.scenario, r.scenario)}</td><td>{'ללא תיקון' if r.design=='pps_ratio' else 'מרובד + תיקון'}</td><td>{r.sign_agree}</td><td>{r.mean_abs_diff_seats:.2f}</td></tr>" for r in _mf.sort_values("mean_abs_diff_seats").itertuples())
_k26 = pd.read_csv("results/tv_k26_provisional.csv")
_cn26 = {"Kan 11": "כאן 11", "Channel 12": "ערוץ 12", "Channel 13": "ערוץ 13", "i24NEWS": "i24NEWS", "Channel 16": "ערוץ 16", "Channel 14": "ערוץ 14"}
K26_ROWS = "".join(f"<tr><td>{_cn26[r.channel]}</td><td>{r.out_of_place:.0f}</td><td>{r.likud_err:+d}</td><td>{r.arab_err:+d}</td></tr>" for r in _k26.itertuples())
_bu = pd.read_csv("results/exitpoll_budget.csv")
_bg = _bu[_bu.design == "strat_prior"].groupby(["n_places", "m"])[["seats_out_of_place", "deff_top"]].mean()
BUD_ROWS = ""
for _n in [30, 60, 120, 240]:
    BUD_ROWS += f"<tr><td>{_n}</td>" + "".join(f"<td>{_bg.loc[(_n,_m)].seats_out_of_place:.1f} <span class='small'>(אפקט תכנון {_bg.loc[(_n,_m)].deff_top:.1f})</span></td>" for _m in [50, 100, 200, 400]) + "</tr>"
_nat = pd.read_csv("data/turnout_national.csv")
_nt = _nat.dropna(subset=["turnout_20h_pct"]).copy(); _nt["ratio"] = _nt.final_pct / _nt.turnout_20h_pct
NAT_ROWS = ""
for _i, _r in _nat.iterrows():
    if pd.isna(_r.turnout_20h_pct): NAT_ROWS += f"<tr><td>{int(_r.election)}</td><td>לא נמצא</td><td>{_r.final_pct}%</td><td>-</td><td>-</td></tr>"; continue
    _o = _nt[_nt.election != _r.election].ratio.mean(); _pr = _r.turnout_20h_pct * _o
    NAT_ROWS += f"<tr><td>{int(_r.election)}</td><td>{_r.turnout_20h_pct}%</td><td>{_r.final_pct}%{' (ב-22:00, לא סופי)' if int(_r.election)==26 else ''}</td><td>{_pr:.1f}%</td><td>{_pr-_r.final_pct:+.1f}</td></tr>"
_dd = pd.read_csv("results/exitpoll_dash.csv")
_tw = _dd[(_dd.n == 120) & (_dd.m == 200) & (_dd.pat == "none") & (_dd.nr == "none") & _dd.design.isin(["strat_prior", "strat_prior_tw"])].groupby(["T", "design"]).seats_oop.mean().unstack("design")
TW_ROWS = "".join(f"<tr><td>{int(t)}</td><td>{r.strat_prior:.1f}</td><td>{r.strat_prior_tw:.1f}</td></tr>" for t, r in _tw.iterrows())
_DES = ["pps_ratio", "strat_prior", "strat_prior_bk", "strat_prior_pastvote", "strat_greg_ps_bk", "strat_prior_tw"]
_LIE = [("none", 0), ("shy", 5), ("shy", 10), ("shy", 20), ("rand", 5), ("rand", 10), ("rand", 20)]
_NRL = ["none", "nr", "nr_refuse"]; _TS = [22, 23, 24, 25, 26]; _NN = [30, 60, 120, 240]; _MM = [50, 100, 200, 400]
_ix = _dd.set_index(["T", "design", "pat", "lv", "nr", "n", "m"])
_vals = []
for _t in _TS:
    for _d in _DES:
        for _p, _l in _LIE:
            for _nr in _NRL:
                for _n in _NN:
                    for _m in _MM:
                        _r = _ix.loc[(_t, _d, _p, _l, _nr, _n, _m)]
                        _vals.append([round(float(_r.mae_pp), 2), round(float(_r.seats_oop), 1), round(float(_r.right_err), 1), round(float(_r.arab_err), 1)])
_tvc = pd.read_csv("results/tv_exit_poll_comparison.csv"); _tvc = _tvc[(_tvc.scored == "yes") & _tvc.source_tier.isin(["A", "B"])]
_tvd = {int(e): round(float(g.out_of_place.mean()), 1) for e, g in _tvc.groupby("election")}
_tvd[26] = round(float(_k26.out_of_place.mean()), 1)
DASH_JSON = _json.dumps({"T": _TS, "des": _DES, "lie": _LIE, "nr": _NRL, "n": _NN, "m": _MM, "v": _vals, "tv": _tvd}, separators=(",", ":"))

_LL = {("none",0): "אין שקר", ("shy",5): "הסתרה 5%", ("shy",10): "הסתרה 10%", ("shy",20): "הסתרה 20%", ("rand",5): "אקראי 5%", ("rand",10): "אקראי 10%", ("rand",20): "אקראי 20%"}
_NRN = {"none": "כולם עונים", "nr": "חרדים וערבים עונים פחות", "nr_refuse": "וגם קלפיות מסרבות"}
IDEAL_ROWS = ""
_dev = _dd[_dd["T"].between(22, 25)]
for (_p, _l) in _LIE:
    for _nr in _NRL:
        def _q(des, n, m, df=_dev):
            return df[(df.design == des) & (df.n == n) & (df.m == m) & (df.pat == _p) & (df.lv == _l) & (df.nr == _nr)].seats_oop.mean()
        _a = _q("pps_ratio", 60, 100); _b = _q("strat_prior_pastvote", 120, 200); _c = _q("strat_greg_ps_bk", 120, 200)
        _k = _dd[(_dd["T"] == 26) & (_dd.design == "strat_greg_ps_bk") & (_dd.n == 120) & (_dd.m == 200) & (_dd.pat == _p) & (_dd.lv == _l) & (_dd.nr == _nr)].seats_oop.mean()
        IDEAL_ROWS += f"<tr><td>{_LL[(_p,_l)]}</td><td>{_NRN[_nr]}</td><td>{_a:.1f}</td><td>{_b:.1f}</td><td><b>{_c:.1f}</b></td><td>{_k:.1f}</td></tr>"
DASH_JS = """
const D=__DATA__;
const NM={22:'ספטמבר 2019 (כנסת 22)',23:'מרץ 2020 (כנסת 23)',24:'מרץ 2021 (כנסת 24)',25:'נובמבר 2022 (כנסת 25)',26:'אוקטובר 2026 (כנסת 26) זמני'};
function $(i){return document.getElementById(i)}
function render(){
 const ni=+$('dn').value, mi=+$('dm').value, d=+$('dd').value, li=+$('dl').value, nr=+$('dr').value;
 let h='';
 D.T.forEach((t,ti)=>{
  const k=((((ti*6+d)*7+li)*3+nr)*4+ni)*4+mi, v=D.v[k];
  const w=Math.min(100,v[1]*8);
  const tv=D.tv[t]!==undefined?D.tv[t]:'-';
  h+='<tr><td>'+NM[t]+'</td><td>'+v[0].toFixed(2)+'</td><td><b>'+v[1].toFixed(1)+'</b><div class="bar"><i style="width:'+w+'%"></i></div></td><td>'+v[2].toFixed(1)+'</td><td>'+v[3].toFixed(1)+'</td><td>'+tv+(t==26?' (זמני)':'')+'</td></tr>';
 });
 h+='<tr><td>אפריל 2019 (כנסת 21)</td><td colspan="4">לא ניתן להדמיה (אין בחירות קודמות במאגר)</td><td>'+D.tv[21]+'</td></tr>';
 $('dout').innerHTML=h;
 $('dbud').textContent=(D.n[ni]*D.m[mi]).toLocaleString('he-IL');
}
function preset(n,m,d,l,r){$('dn').value=n;$('dm').value=m;$('dd').value=d;$('dl').value=l;$('dr').value=r;render()}
['dn','dm','dd','dl','dr'].forEach(i=>$(i).addEventListener('change',render));
render();
""".replace("__DATA__", DASH_JSON)

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
EP_REPS = int(EP.reps.iloc[0])
_b = EPD[(EPD.scenario == "shy15") & (EPD.design == "strat_prior")].groupby("n_places").top_bias_pp.mean()
EP_BIAS = f"{-_b.max():.1f} עד {-_b.min():.1f}"
_pv = EPD[(EPD.scenario == "shy15")].pivot_table(index="n_places", columns="design", values="share_mae_pp")
EP_CROSS = next((int(n) for n in _pv.index if _pv.loc[n, "strat_prior_pastvote"] <= _pv.loc[n, "strat_prior"]), None)
EP_M = {m: epv("none", "strat_prior", 50, "share_mae_pp", m) for m in (50, 100, 200)}
EP_26 = EP[(EP["T"] == 26) & (EP.m == 100) & (EP.scenario == "none") & (EP.design == "strat_prior") & (EP.n_places == 50)].iloc[0]
EP_TOP = {T: EP[(EP["T"] == T)].top_list.iloc[0] for T in (22, 25)}

# ---------- exit poll part 2: hard-to-sample groups, improvements, envelopes ----------
EPE = pd.read_csv("results/exitpoll_envelopes.csv")
EPS = pd.read_csv("results/exitpoll_example_sample_k26.csv")
DN2 = {"pps_ratio": "בסיס: הגרלה לפי גודל, בלי נתוני עבר", "strat_prior": "מרובד + תיקון (שיטה 4)", "strat_prior_ps": "שיטה 4 + שקלול לפי קבוצות", "strat_prior_bk": "שיטה 4 + קלפי גיבוי", "strat_ridge": "מודל על הקלפיות שנדגמו", "strat_greg": "מודל + תיקון שאריות", "strat_greg_ps_bk": "מודל + שאריות + קבוצות + גיבוי", "strat_prior_pastvote": "שיטה 5 (שאלת הצבעה קודמת)"}
SC2 = {"none": "אין בעיה", "hard_nr": "פחות משיבים: חרדים ו-ערבים", "place_refuse": "קלפיות חרדיות וערביות מסרבות", "hard_both": "שני הקודמים יחד"}
EP2_TBL = "".join("<tr><td>" + DN2[d] + "</td>" + "".join(f"<td>{epv(sc, d, 50, 'share_mae_pp'):.2f}</td>" for sc in SC2) + f"<td>{epv('hard_both', d, 50, 'seats_misallocated'):.1f}</td></tr>" for d in DN2)
EP2_C = ep_chart([(DN2[d], [epv("hard_both", d, n, "share_mae_pp") for n in EPN], c, d == "pps_ratio") for d, c in zip(["pps_ratio", "strat_prior", "strat_greg_ps_bk", "strat_prior_pastvote"], ["#6b7694", "#f2b84b", "#2fd3c4", "#ff7a8a"])], "שגיאה ממוצעת לרשימה כשיש גם פחות משיבים וגם קלפיות מסרבות", "נקודות אחוז", 3.0)
def _wins(sc, a, b, n=50):
    d = EPD[(EPD.scenario == sc) & (EPD.n_places == n)].pivot(index="T", columns="design", values="share_mae_pp")
    return int((d[a] < d[b] - 0.005).sum())
EP2_W = {sc: _wins(sc, "strat_greg_ps_bk", "strat_prior") for sc in ("none", "hard_both")}
EP2_G = {k: epv("hard_both", k, 50, "share_mae_pp") for k in ("pps_ratio", "strat_prior", "strat_greg_ps_bk")}
EP2_ENV = "".join(f"<tr><td>{int(r['T'])}</td><td>{r.envelope_share_pct:.1f}%</td><td>{r.boxes_only_mae_pp:.2f}</td><td>{r.boxes_only_seats_off:.0f}</td>" + (f"<td>{r.with_prev_envelopes_mae_pp:.2f}</td><td>{r.with_prev_envelopes_seats_off:.0f}</td></tr>" if r.prev_envelope_share_pct > 0 else "<td>אין נתון</td><td>אין נתון</td></tr>") for _, r in EPE.iterrows())
EP2_S = {"n": len(EPS), "loc": EPS.locality.nunique(), "reg": int(EPS.registered.sum()), "h": int((EPS.group == "haredi-profile").sum()), "a": int((EPS.group == "arab-profile").sum())}

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
<li><b>קובצי אחוז ההצבעה של הוועדה (ב-20:00):</b> לכל קלפי מפורסם מספר המצביעים עד אותה שעה. בכנסת 26, הערכת גודל הקלפי (קולות כשרים) ממנו שגויה בכ-3% בממוצע, לעומת כ-11% מהגודל בבחירות הקודמות. הכנסת הגודל הזה למודל הורידה את שגיאת החלקים בסדר אקראי (ב-20% נספרו: מ-0.15 ל-0.10 נקודות אחוז), ושימוש בהצבעה כמשתנה מסביר נתן תוצאה מעורבת (עזר בסדר ליכוד נמוך קודם ב-5%, הזיק בסדר קטנות קודם). <b>מדד זה נבדק רק על כנסת 26, שאינה אימות עצמאי, ואין קבצי ביניים כאלה (לפי שעה) לבחירות קודמות שמצאנו.</b> אחוז ההצבעה <b>הסופי</b> לכל קלפי קיים לכל הבחירות (21 עד 25) והמודל משתמש בו (הצבעה בבחירות הקודמות ושינוי בהצבעה). לכן הוא עדיין לא בברירת המחדל. מקור: <code>results/turnout_k26.csv</code>, <code>python -m model.turnout</code>.</li>
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
<p class="small">ממוצע על הכנסות 22-25, {EP_REPS} הדמיות לכל תא. הרשימה הגדולה: סטיית התקן הושוותה לנוסחה סטטיסטית פשוטה (הגרלה לפי גודל) וההתאמה טובה, ראו <code>model/exitpoll.py</code>. "מנדטים שהוקצו לא נכון" הוא מספר המנדטים שמחוץ למקומם, סכום ההפרשים לחלק ב-2, אחרי הסכמי העודפים של אותה בחירה. המנדטים האחרונים רגישים מאוד, ולכן המספר גבוה יחסית לשגיאת האחוזים. אין כאן מעטפות: מדגם קלפיות אינו מכסה אותן, והאמת בהדמיה היא הקלפיות הרגילות בלבד.</p>
<h3>כמה קלפיות לפחות</h3>
<p>מתחת ל-50 אפשר, אבל המחיר ברור. עם 20 קלפיות השגיאה הממוצעת לרשימה ב-{epv('none','strat_prior',20,'share_mae_pp'):.2f} נקודות אחוז וטעות של כ-{epv('none','strat_prior',20,'seats_misallocated'):.0f} מנדטים. עם 10 קלפיות: {epv('none','strat_prior',10,'share_mae_pp'):.2f} נקודות אחוז וכ-{epv('none','strat_prior',10,'seats_misallocated'):.0f} מנדטים. מספר הקלפיות הנדרש להגיע ליעד, לפי ההנחות על שקר (שיטה 4):</p>
<table><tr><th>הנחה</th><th>שגיאה ≤1.0</th><th>≤0.75</th><th>≤0.5</th><th>מנדטים ≤4</th></tr>{EP_NEED}</table>
<h3>נבדקים שמשקרים</h3>
{EP_C2}
<p>הממצא המרכזי: <b>שקר הוא הטיה, ולא נעלם עם יותר קלפיות.</b> הוספת קלפיות מורידה את הרעש אבל לא את ההטיה. בהנחה ש-15% מבוחרי הרשימה הגדולה מציינים רשימה אחרת, הרשימה הגדולה נמדדת נמוך בכ-{EP_BIAS} נקודות אחוז בכל גודל מדגם.</p>
<table><tr><th>הנחה (50 קלפיות)</th><th>שיטה 2</th><th>שיטה 4</th><th>שיטה 5</th><th>הטיה ש. 4</th><th>הטיה ש. 5</th></tr>{EP_SC}</table>
<p class="small">שלוש העמודות הראשונות: שגיאה ממוצעת לרשימה בנקודות אחוז. הטיה: הרשימה הגדולה, מדוד פחות אמת, בנקודות אחוז. שיטה 2 היא הגרלה לפי גודל.</p>
<p><b>יתירות:</b> שאלת ההצבעה הקודמת (שיטה 5) מתקנת את ההטיה של הרשימה הגדולה כמעט לגמרי בהנחה שהשקר דומה בשתי השאלות, אבל מוסיפה רעש: בלי שקר היא גרועה מ-4, והיא מועילה רק מכ-{EP_CROSS} קלפיות. ההנחה שהשקר יציב בין שאלה לשאלה היא אופטימית, ושאלת "הצבעה קודמת" כאן מדומה מפרופיל הקלפי בבחירות הקודמות, לא מהצבעה אמיתית של הנבדקים: בעולם האמיתי יש גם שגיאות זיכרון ומעבר בין רשימות. אל תקראו את זה כהוכחה שהשיטה עובדת.</p>
<p><b>אילו קלפיות:</b> מיון לפי הפרופיל בבחירות הקודמות ובחירה שיטתית לפי גודל. דוגמה למדגם של 60 קלפיות לכנסת 26 (אילוסטרציה, נבנתה מתוצאות הספירה הנוכחית, לא המלצה מבצעית): <code>results/exitpoll_example_sample_k26.csv</code>. בתכנון אמיתי הרשימה נבחרת לפני הבחירות מרשימת הקלפיות שהוועדה מפרסמת, לפי הבחירות הקודמות.</p>
<p class="small">מגבלות: מעטפות וקולות חיילים, אסירים וכדומה לא במדגם. לא הודלו חוסר שיתוף פעולה של קלפיות שלמות, מראיינים עם הטיה, הצבעה מוקדמת של בוחרים לפני היציאה, ושינוי בהרכב הבוחרים לפי שעה ביום. הכנסת 26 (נתונים חיים, זמני): 50 קלפיות בשיטה 4, שגיאה ממוצעת {EP_26.share_mae_pp:.2f} נקודות אחוז, {EP_26.seats_misallocated:.1f} מנדטים. הכנסות 22-25 הן נתוני פיתוח של שאר המודל, אבל כאן אין כוונון, ולכן הן מבחן ראוי לשיטות המדגם. התוצאות הן סימולציה של תכנון ולא טענה על סקר אמיתי כלשהו.</p>

<h2>9. סקר יציאה, חלק ב: שיטות בעולם, אוכלוסיות קשות לדגימה ושיפורים</h2>
<h3>איך עושים את זה בעולם (מה מפורסם, ומה לא)</h3>
<table><tr><th>מקום</th><th>מה מפורסם</th><th>מקור</th></tr>
<tr><td>ישראל, ערוץ 12 (2026)</td><td>70 קלפיות מתוך כ-13,000, "נבחרו במודל מתמטי". קלפי דמה עם טאבלט ליד הקלפי האמיתית. דגימה מרובדת (ערבים, חרדים, עולים). בדיקות עקביות ו"מודל התנהגותי" לתיקון הטיות, ובלשון הדובר "זה עדיין לא הרמטי". לא ידוע: אילו קלפיות, כמה ראיונות, המודל והשקלול.</td><td><a href="https://thebp.co.il/en/behind-the-scenes-how-the-channel-12-election-exit-poll-works" dir="ltr">The Briefing Point, 27.10.2026</a> (אתר חדשות, מעביר את דברי הערוץ)</td></tr>
<tr><td>ישראל, 2015</td><td>ערוצים 1 ו-2: כ-60 קלפיות דמה, 25,000 ו-30,000 מצביעים. הקלפיות נבחרו לפי קריטריונים חברתיים-כלכליים ולפי מהימנות הסקר בהן בשתי הבחירות הקודמות. ערוץ 10: שאלון, השתתפות כ-80%. אחרי הפספוס (ליכוד 28 בסקר, 30 בפועל) הסבירו פרופ' פוקס ומינה צמח בירידה בהשתתפות, שלדבריהם הייתה חזקה בקלפיות עם הרבה מצביעי ליכוד. זה ההסבר שלהם, לא נבדק על ידינו.</td><td><a href="https://www.timesofisrael.com/botched-tv-exit-polls-earn-vote-of-non-confidence/" dir="ltr">Times of Israel, 18.03.2015</a></td></tr>
<tr><td>בריטניה (BBC, ITV, Sky)</td><td>כ-100 קלפיות מתוך כ-40,000, 100-200 מצביעים בכל אחת. חוזרים לאותן קלפיות. מודדים שינוי מהבחירות הקודמות, מודל סטטיסטי מתרגם לשינוי בכל אזור, ומוסיפים לתוצאות הקודמות. קולות בדואר לא נכללים. הם מציינים שסירוב ושקר הם חשש, ושההשוואה לסקר הקודם באותן קלפיות עשויה לבטל הטיה יציבה.</td><td><a href="https://warwick.ac.uk/fac/sci/statistics/staff/academic-research/firth/exit-poll-explainer/" dir="ltr">Warwick, Exit polling explained</a></td></tr>
<tr><td>ארה"ב (NEP, Edison), 2024</td><td>279 מקומות הצבעה, מדגם הסתברותי מרובד, כל מצביע n-י, כ-75 שאלונים בכל מקום. 27 מקומות הצבעה מוקדמת. סקר נפרד (טלפון, הודעות, מייל) למצביעים בדואר ובהצבעה מוקדמת. ההצהרה מציינת שאי-מענה צפוי להגדיל את השגיאה. בהערכה של 2004: שגיאה גדולה מהרגיל בתוך הקלפיות, ככל הנראה בגלל נכונות שונה להשתתף בין תומכי המפלגות.</td><td><a href="https://s.abcnews.com/assets/dtci/elections/NEPExitPollMethodologyStatement.pdf" dir="ltr">NEP 2024 methods</a>, <a href="https://electionintegrity.org/documents/edison-mitofsky-050119.pdf" dir="ltr">Edison/Mitofsky 2005</a></td></tr>
<tr><td>גרמניה (ARD)</td><td>560 קלפיות שנבחרו כדי לייצג את המדינה (עיר וכפר, הצבעה גבוהה ונמוכה, מעוזים ודיאספורה), 80,000-90,000 ראיונות. דואר: מודלים סטטיסטיים וסקרים מיוחדים. לפי הערוץ, סטיית התחזיות מהתוצאה בממוצע מתחת ל-0.5 נקודות.</td><td><a href="https://www.tagesschau.de/inland/bundestagswahl/wahlsystem/prognose-entstehung-bundestagswahl-100.html" dir="ltr">tagesschau.de, 22.02.2025</a></td></tr></table>
<p>תקציר מקורות ותיעוד: <code>docs/exit-poll-methods.md</code>. מה ללמוד: כולם בוחרים קלפיות בעזרת בחירות קודמות, ובבריטניה ובארה"ב מעריכים <b>שינוי</b> ולא רמה, כמו שיטה 4 שלנו. לישראל יתרון: תוצאות מפורסמות לכל קלפי. אי-מענה שונה בין קבוצות הוא הבעיה שכל המקורות מזכירים. מה שאינו ידוע לנו: הקלפיות, מספר הראיונות, השקלול והמודלים של הערוצים, ולכן <b>אין לנו בסיס לטעון שאנחנו טובים מהם</b>.</p>
<h3>אוכלוסיות קשות לדגימה (הנחות)</h3>
<p>הוספנו שלוש הנחות, והן <b>ניחושים</b>: (א) מצביעי רשימות חרדיות עונים חצי מהפעמים, ומצביעי רשימות ערביות 40% פחות. (ב) חצי מהקלפיות עם פרופיל חרדי או ערבי (לפי ההצבעה בבחירות הקודמות, לא לפי סיווג דמוגרפי) לא מאפשרות ראיונות. (ג) שניהם יחד. שיטות שהתווספו: שקלול לפי קבוצות פרופיל שגודלן ידוע מראש, קלפי גיבוי מאותו פרופיל, ומודל שמותאם לקלפיות שנדגמו (אותו רידג׳ כמו במודל הספירה) עם תיקון שאריות.</p>
<table><tr><th>שגיאה ממוצעת לרשימה (נק׳), 50 קלפיות</th><th>אין בעיה</th><th>פחות משיבים: חרדים וערבים</th><th>קלפיות חרדיות וערביות מסרבות</th><th>שני הקודמים יחד</th><th>מנדטים לא במקומם, שני הקודמים</th></tr>{EP2_TBL}</table>
{EP2_C}
<p>הממצאים: בהנחות הקשות השגיאה של הבסיס עולה מ-{epv('none','pps_ratio',50,'share_mae_pp'):.2f} ל-{EP2_G['pps_ratio']:.2f}. שיטה 4 מגיעה ל-{EP2_G['strat_prior']:.2f}, והשילוב המלא (מודל, שאריות, קבוצות, גיבוי) ל-{EP2_G['strat_greg_ps_bk']:.2f}. כלומר <b>התכנון משחזר חלק גדול מהאובדן אבל לא את כולו</b>. הוא מתקן חסר בקלפיות, אבל אינו מתקן מצביעים של רשימה שמשיבים פחות בתוך אותה קלפי. השיפור על שיטה 4 קטן (כ-0.1 נקודה) ולא מובהק: הוא טוב יותר ב-{EP2_W['none']} מתוך 4 בחירות בלי בעיה וב-{EP2_W['hard_both']} מתוך 4 בהנחות הקשות. המודל גרוע משיטה 4 בעשר קלפיות ועולה עליה מכ-30. השיטות החדשות הוספו אחרי שראינו תוצאות פיתוח של הכנסות 22-25, ולכן הכנסות 22-25 הן כאן <b>נתוני פיתוח</b>, לא מבחן שמור. אין מבחן שמור עד בחירות שבהן הסקר נעשה לפי כלל שקבענו מראש.</p>
<h3>מעטפות וחיילים: מחוץ לכל מדגם קלפיות</h3>
<table><tr><th>כנסת</th><th>חלק המעטפות</th><th>טעות בלי מעטפות (נק׳)</th><th>מנדטים</th><th>טעות עם פרופיל קודם (נק׳)</th><th>מנדטים</th></tr>{EP2_ENV}</table>
<p class="small">העמודה "מנדטים" היא מספר המנדטים שמחוץ למקומם. ההתעלמות ממעטפות עולה מעט, לרוב 1-2 מנדטים. <b>תוצאה שלילית:</b> הוספת פרופיל המעטפות מהבחירות הקודמות לא עזרה: טובה בכנסת 23, גרועה יותר בכנסות 24 ו-25 (רשימות משתנות בין בחירות). לכן אין לנו תיקון מומלץ למעטפות מלבד הרחבת הסקר, וכל מי שישתמש בפרופיל קודם צריך לבדוק אותו.</p>
<h3>רשימת קלפיות מומלצת (איור תכנון, לא המלצה מבצעית)</h3>
<p>הכלל: ממיינים את כל מקומות ההצבעה לפי הפרופיל שלהם בבחירות הקודמות (הרכיב הראשי הראשון), ובוחרים שיטתית, לפי הגודל הצפוי (בעלי זכות בחירה כפול ההצבעה הקודמת), עם נקודת פתיחה אקראית קבועה. לכל קלפי נבחרים שני גיבויים מאותה קבוצת פרופיל הקרובים לה במיון. אם קלפי מסרבת, עוברים לגיבוי הראשון. המדגם: {EP2_S['n']} מקומות הצבעה ב-{EP2_S['loc']} יישובים, {EP2_S['reg']:,} בעלי זכות בחירה, מהם {EP2_S['h']} בפרופיל חרדי ו-{EP2_S['a']} בפרופיל ערבי. הרשימה נבנתה מנתוני הכנסת 26 הזמניים והבחירות הקודמות, כדי להדגים את הכלל, לא לפעול לפיה. בתכנון אמיתי בוחרים לפני הבחירות מרשימת הקלפיות הרשמית. הכתובות במאגר הן טיוטה מקובץ הוועדה ועם שגיאות. הקובץ: <code>results/exitpoll_example_sample_k26.csv</code>.</p>
<h3>מה נדרש כדי לטעון שמדגם כזה טוב מסקרי הטלוויזיה</h3>
<ul><li>תחזיות ה-22:00 שפורסמו לכל בחירות מול התוצאות הסופיות (פומבי, צריך לאסוף) ולבדוק אם השגיאה שלנו בסימולציה קרובה לשלהם.</li>
<li>ניסוי אמיתי: ראיונות בקלפיות מרשימה שנקבעה מראש, ומדד הצלחה שנקבע לפני התוצאות (למשל שגיאת מנדטים), בבחירות שבהן השיטה כבר סומנה בגרסה ולא ישונתה.</li>
<li>נתוני נבדקים לפי קלפי מסקרים קודמים (אינם ציבוריים).</li>
<li>עד אז, כל המספרים כאן הם סימולציות של תכנון תחת הנחות.</li></ul>

<h2>10. סקרי היציאה בטלוויזיה מול התוצאות הסופיות (מבחן ראשון, נקבע מראש)</h2>
<p>המדד נקבע <b>לפני החישוב</b> ונשמר במאגר: <code>docs/prereg/tv_exit_poll_comparison.md</code> (קומיט a80b1a7). מדד ראשי: מנדטים שמחוץ למקומם, כלומר סכום ההפרשים המוחלטים בין המנדטים החזויים לסופיים, חלקי 2, על פני כל הרשימות. תוצאות סופיות: ועדת הבחירות המרכזית (votes21 עד votes25.bechirot.gov.il). התחזיות: מהדיווח הראשון שמצאנו בעיתונות, עם קישור לכל ערך ב-<code>data/tv_exit_polls/tv_exit_polls.csv</code>.</p>
<table><tr><th>בחירות</th><th>ערוץ 12</th><th>ערוץ 13</th><th>כאן 11</th><th>סוג מקור</th></tr>{TV_ROWS}</table>
<p class="small">מספרים: מנדטים שמחוץ למקומם. {CALC}. בכנסת 25 רק ערוץ 12 מלא; לערוצים 13 וכאן 11 מצאנו רק שתי הרשימות הגדולות ולכן הם לא נספרו (חסר, לא הוערך).</p>
<p>סיכום ({TV_N} תאים, ערוץ בחירות): ממוצע {TV_MEAN:.1f} מנדטים שמחוץ למקומם, טווח {TV_MIN:.0f} עד {TV_MAX:.0f}. שגיאה ממוצעת לרשימה: {TV_MAE:.2f} מנדטים. בכנסות 22 עד 25 בלבד: ממוצע {TV_MEAN_A:.1f}. אין מבחן מובהקות, המדגם קטן.</p>
<p>הסימולציה שלנו (תכנון עם 60 קלפיות, 100 ראיונות בכל אחת, בחירה מרובדת לפי הבחירות הקודמות), באותה הגדרה, כנסות 22 עד 25: {SIM_NONE:.1f} בלי בעיות דגימה, {SIM_HARD:.1f} בהנחות הקשות. זה <b>נתוני פיתוח</b> והנחות שלנו, לא תוצאה אמיתית.</p>
<h3>מגבלות והשוואה הוגנת</h3>
<ul><li><b>אין כאן טענה שניצחנו את הטלוויזיה.</b> הסימולציה מניחה שהמראיינים רושמים נכון ושהקלפיות נבחרות לפי הבחירות הקודמות. אנחנו לא יודעים את גודל המדגם בפועל של כל ערוץ בכל בחירות, ולכן אין השוואה שווה בין התנאים.</li>
<li>תחזית ה-22:00 היא לעיתים אחרי עדכון: ויקיפדיה מציגה לרוב את העדכון האחרון, ולכן השתמשנו בעיתונות. כנסת 21 מבוססת על טבלת ויקיפדיה (שני המנדטים הגדולים אומתו מול Ynet). כנסת 24 מ-Globes ב-22:48, ייתכן שאחרי הפרסום הראשון.</li>
<li>הערכים הם מספרים שלמים, ועיגול משפיע: טעות של מנדט אחד ברשימה אחת נספרת כחצי.</li>
<li>5 בחירות, 13 תאים. כנסת 26: התחזיות נשמרו ולא נספרו, עד שיהיו תוצאות סופיות רשמיות.</li>
<li>המדד "מנדטים שמחוץ למקומם" אינו מדד גושים. הוא נקבע מראש כך.</li></ul>

<h2>11. למה ערוצי הטלוויזיה פספסו? (אבחון, נקבע מראש)</h2>
<p>הניתוח נקבע לפני החישוב: <code>docs/prereg/tv_miss_diagnosis.md</code> (תג diagnosis-v1). שגיאה מסומנת לקבוצה = מנדטים חזויים פחות סופיים (חיובי = הערוץ נתן יותר מדי). ממוצע על פני הערוצים, כנסות 21 עד 25. {CALC}</p>
<div class="tw"><table><tr><th>קבוצה</th><th>21</th><th>22</th><th>23</th><th>24</th><th>25</th><th>הכול</th></tr>{GRP_ROWS}</table></div>
<p><b>מה רואים:</b> הרשימות הערביות נחזו נמוך מדי בכל חמש הבחירות. הליכוד והחרדים: אין הטיה קבועה. הפספוסים הגדולים (כנסת 21 וכנסת 25) באים מ"שאר הרשימות", כלומר רשימות סמוך לאחוז החסימה שלא עברו (ניו רייט, זהות, מרצ). <b>כנסת 26 (זמני):</b> כל ששת הערוצים נתנו לרשימות הערביות פחות מהספירה שלנו.</p>
<div class="tw"><table><tr><th>ערוץ (כנסת 26)</th><th>מנדטים שמחוץ למקומם (זמני)</th><th>שגיאת ליכוד</th><th>שגיאת ערביות (ש׳+רע״ם)</th></tr>{K26_ROWS}</table></div>
<p class="small">ההשוואה לכנסת 26 היא מול <b>הספירה החיה שלנו</b> (מעטפות בהנחה), לא תוצאה רשמית, ואינה חלק מהמבחן שנקבע מראש. i24NEWS פגע בליכוד (27 מול 27), אבל טעה ברשימות אחרות, ולכן הסך אינו קרוב יותר. סקרי ערוצים 14, 16 ו-i24NEWS פורסמו בליל הבחירות; בבחירות 2022 ערוץ i24 לא ערך סקר משלו. ערוץ 14: מקורות שונים נותנים רשימות שונות במעט (ליכוד 30 או 31), ייתכן עדכון.</p>
<h3>איזו הנחה בסימולציה משחזרת את הדפוס? (בדיקה שלנו)</h3>
<div class="tw"><table><tr><th>הנחת התנהגות</th><th>שיטה</th><th>כיוון נכון (מתוך תאים)</th><th>הפרש ממוצע במנדטים</th></tr>{MECH_ROWS}</table></div>
<p class="small">כיוון נכון = הסימן של הטיית הקבוצה בסימולציה שווה לזו של סקרי הטלוויזיה. זו התאמה, לא הוכחה. <b>ממצא:</b> ההנחות החזקות שלנו (חרדים וערבים עונים חצי, 15% מסתירים ליכוד) נותנות הטיות של 4 עד 5 מנדטים על החרדים או על הליכוד, וזה <b>לא</b> מה שרואים בסקרי הטלוויזיה בפועל. כלומר ערוצי הטלוויזיה כנראה מתקנים טוב מזה (שקלול לפי הצבעה קודמת, קלפיות דמה מרובדות), ושגיאתם נשארת בעיקר בערבים ובסף החסימה.</p>
<h3>מה שהמפרסמים אמרו (לא בדיקה שלנו)</h3>
<ul><li>שמואל רוזנר (ערוץ 13): "העוצמה של הליכוד היא משהו שלא ראינו בסקרים, אך הופיע די מוקדם במדגמים והמשיך לגדול" (ynet, <a href="https://www.ynetnews.com/article/rk5mt8g6zg" dir="ltr">ynetnews.com/article/rk5mt8g6zg</a>).</li>
<li>צוריאל שרון (Direct Polls, i24NEWS): הצבעה גבוהה של ערבים "משפיעה על המשקל שנותנים לקבוצות אוכלוסייה, וצריך לדעת לטפל בזה בזמן אמת"; הוא מעריך שהמספרים האלה לא יחזרו (אותו מקור).</li></ul>
<p>בכל ערוצי כנסת 26 העדכונים בלילה התקרבו לספירה (ליכוד: ערוץ 12 מ-24 ל-27, כאן 11 מ-25 ל-27, ערוץ 13 מ-25 ל-27), כלומר רשימות הפתיחה החמיצו את הליכוד ב-2 עד 3 מנדטים.</p>

<h2>12. כמה קלפיות מול כמה ראיונות בכל קלפי</h2>
<p>שגיאת מנדטים שמחוץ למקומם, שיטה מרובדת, בלי בעיות התנהגות, ממוצע כנסות 22 עד 25 (חישוב שלנו, סימולציה). בסוגריים "אפקט תכנון": כמה גדולה השונות לעומת מדגם אקראי של אותו מספר אנשים. ככל שמוסיפים ראיונות באותה קלפי, האפקט גדל והתועלת קטנה.</p>
<div class="tw"><table><tr><th>קלפיות \ ראיונות לקלפי</th><th>50</th><th>100</th><th>200</th><th>400</th></tr>{BUD_ROWS}</table></div>
<p><b>ממצא:</b> הכפלת הראיונות בכל קלפי (100 ל-200) משפרת רק ב-0.1 עד 0.3 מנדטים, והכפלת מספר הקלפיות (60 ל-120) משפרת ב-0.8 עד 1.1. 100 ראיונות אינם מעט, ו-200 לא יהפכו את המדגם. עם יותר קלפיות מגיעים לכ-3.3 מנדטים (240 קלפיות). כאן אין הנחות על שקר: זו שגיאת דגימה בלבד.</p>

<h2>13. דשבורד אינטראקטיבי: מה היה קורה בכל בחירות</h2>
<div class="box"><b>איך זה עובד:</b> הדשבורד קורא <b>טבלה שחושבה מראש</b> (לא מריץ סימולציה בדפדפן): לכל שילוב של הפרמטרים שבחרנו, ממוצע 60 הרצות של הדמיית מדגם על תוצאות הקלפיות האמיתיות של כל בחירות. ההתנהגות של הנשאלים (שקר, אי מענה, סירוב קלפיות) היא <b>הנחה שלנו</b>, לא מדידה. כנסות 22 עד 25 הן נתוני פיתוח; כנסת 26 זמנית ואינה אימות עצמאי. עמודת הטלוויזיה היא טעות הסקרים בפועל (ממוצע ערוצים, מנדטים שמחוץ למקומם).</div>
<div class="ctl">
<label>קלפיות <select id="dn"><option value="0">30</option><option value="1">60</option><option value="2" selected>120</option><option value="3">240</option></select></label>
<label>ראיונות לקלפי <select id="dm"><option value="0">50</option><option value="1">100</option><option value="2" selected>200</option><option value="3">400</option></select></label>
<label>שיטה <select id="dd"><option value="0">דגימה רגילה לפי גודל, בלי תיקון</option><option value="1">מרובדת + תיקון לפי הבחירות הקודמות</option><option value="2">+ קלפיות גיבוי כשקלפי מסרבת</option><option value="3">+ שאלת "למי הצבעת בפעם הקודמת" ושקלול (מקטין משקל של תשובות לא עקביות)</option><option value="4" selected>המודל האידיאלי: מרובד, גיבוי, שקלול לקבוצות, תיקון מודל</option><option value="5">מרובד + משקל לפי אחוז הצבעה ביום הבחירות (אם קובץ 20:00 זמין בזמן)</option></select></label>
<label>שקר / טעות בתשובה <select id="dl"><option value="0" selected>אין</option><option value="1">הסתרה 5% (מצביעי הרשימה הגדולה אומרים אחרת)</option><option value="2">הסתרה 10%</option><option value="3">הסתרה 20%</option><option value="4">תשובה אקראית 5%</option><option value="5">תשובה אקראית 10%</option><option value="6">תשובה אקראית 20%</option></select></label>
<label>אי מענה וסירוב <select id="dr"><option value="0" selected>כולם עונים</option><option value="1">חרדים עונים חצי, ערבים 40% פחות</option><option value="2">כנ״ל, וגם חצי מהקלפיות החרדיות והערביות מסרבות</option></select></label>
</div>
<p><button onclick="preset(1,1,0,0,0)">פשוט: 60x100, רגיל</button> <button onclick="preset(2,2,4,0,0)">אידיאלי 120x200, בלי בעיות</button> <button onclick="preset(2,2,4,2,2)">אידיאלי, בהנחות קשות</button> <button onclick="preset(2,2,0,2,2)">רגיל, בהנחות קשות</button> סך ראיונות: <b id="dbud"></b></p>
<div class="tw"><table><tr><th>בחירות</th><th>שגיאת חלקים (נק׳)</th><th>מנדטים שמחוץ למקומם</th><th>שגיאת גוש הימין (מנדטים)</th><th>שגיאת ערביות (מנדטים)</th><th>טלוויזיה בפועל</th></tr><tbody id="dout"></tbody></table></div>
<p class="small">הדשבורד אינו מראה תחזית מוצלחת: הוא מראה מה השיטה המתוכננת הייתה משיגה <b>בהדמיה</b>. אין בו טענה שנכה את הטלוויזיה.</p>

<h2>14. המודל האידיאלי, ההנחות שלו ומה הוא לא מתקן</h2>
<ul><li><b>המודל (נקבע מראש, dashboard-ideal-v1):</b> דגימת קלפיות מרובדת לפי פרופיל הבחירות הקודמות, כל קלפי מייצגת גודל צפוי; קלפיות גיבוי כשקלפי מסרבת; שאלת "למי הצבעת בפעם הקודמת" לשקלול; הערכה מותאמת-מודל ומשוקללת לקבוצות (חרדים, ערבים, אחרים); 120 קלפיות, 200 ראיונות בכל אחת.</li>
<li><b>הנחות במפורש:</b> מצביע בקלפי שנדגמה עונה לראיון; הקלפיות נבחרות לפני הבחירות; התשובה על ההצבעה הקודמת עקבית עם התשובה הנוכחית; גודל הקלפי ידוע (נרשמים כפול הצבעה בבחירות הקודמות); סיכון מעטפות וחיילים מחוץ לדגימה.</li>
<li><b>מה לא ניתן לתקן:</b> שקר שאין לו סימן בנתונים; סירוב שיטתי של קבוצה שלמה; רשימות ממש על אחוז החסימה (מדגם סביר לא יכריע אם רשימה מקבלת 0 או 4 מנדטים); שינוי חד בהצבעה של קבוצה (למשל ערבים ב-2026) לפני שיש נתון.</li></ul>
<div class="tw"><table><tr><th>שקר</th><th>אי מענה</th><th>רגיל 60x100 (מנדטים שמחוץ למקומם, 22 עד 25)</th><th>שאלת הצבעה קודמת 120x200</th><th>המודל האידיאלי 120x200</th><th>המודל האידיאלי, כנסת 26 (זמני)</th></tr>{IDEAL_ROWS}</table></div>
<p class="small">ממוצע על כנסות 22 עד 25, 60 הרצות לכל תא. בהנחות קשות המודל האידיאלי עדיין טועה ב-6 עד 10 מנדטים: ההנחות הקשות שלנו חזקות יותר ממה שנראה בסקרי הטלוויזיה בפועל (סעיף 11), ולכן ייתכן שהן מגזימות.</p>
<h3>מה זמין בשעה 22:00, ומה לא</h3>
<ul><li><b>זמין לפני 22:00:</b> תוצאות כל קלפי בבחירות הקודמות ואחוז ההצבעה הסופי שלה (לכל הבחירות 21 עד 25); אחוז ההצבעה הארצי שהוועדה מפרסמת במהלך היום (כולל 20:00); המדגם עצמו.</li>
<li><b>לא זמין ב-22:00:</b> תוצאות קלפיות מהספירה (מתחילות כשעה אחר כך); קובץ ההצבעה לפי קלפי של 22:00 (לפי הוועדה מתפרסם כשעה אחרי שעת הדיווח). קובץ 20:00 לפי קלפי מתפרסם לפי הוועדה כשעה אחרי 20:00, כלומר בערך ב-21:00, ולכן בגבול: צריך לאמת כמה זמן לפני 22:00 הוא יוצא (לא תיעדנו את זמן הפרסום הראשון).</li></ul>
<h3>הערכה לאחור של אחוז ההצבעה הסופי מאחוז ההצבעה ב-20:00 (ארצי)</h3>
<div class="tw"><table><tr><th>בחירות</th><th>ארצי ב-20:00</th><th>סופי</th><th>הערכה (יחס מהבחירות האחרות, בלי הבחירות הזו)</th><th>שגיאה (נק׳)</th></tr>{NAT_ROWS}</table></div>
<p><b>ממצא:</b> אפשר להעריך את ההצבעה הארצית הסופית ב-1 עד 3.5 נקודות אחוז (כנסת 26: הערכת יתר, כי חלק ההצבעה המאוחרת קטן). אבל <b>מספר ארצי בלבד לא משפר את המדגם</b>: אם מכפילים את ההצבעה בכל הקלפיות באותו מקדם, המשקלים היחסיים לא משתנים. התועלת הייתה רק מהפרש בין קבוצות (ערבים מול אחרים), וזה דורש נתוני אזור או קלפי של אותו יום, שיש לנו רק לכנסת 26.</p>
<div class="tw"><table><tr><th>בחירות</th><th>מרובד, גודל לפי הבחירות הקודמות</th><th>מרובד, גודל לפי ההצבעה בפועל (עם רעש 3%)</th></tr>{TW_ROWS}</table></div>
<p class="small">מנדטים שמחוץ למקומם, 120x200, בלי בעיות התנהגות. העמודה האחרונה היא <b>חסם עליון</b> (כאילו קובץ הקלפי ביום הבחירות זמין בזמן); רק לכנסת 26 יש קובץ כזה בפועל. התוצאה מעורבת: משפרת בחלק מהבחירות (22, 26) ומחמירה באחרות (25, 24), ולכן לא נאמץ אותה כברירת מחדל.</p>

<h2>15. שחזור</h2>
<p>הקוד, הנתונים שנאספו והמבחנים: <a href="{REPO}" dir="ltr">{REPO}</a>. להרצה:</p>
<pre class="f">python3 scripts/fetch_history.py
python3 -m model.backtest
python3 -m model.coverage
python3 -m model.simulate
python3 -m model.live_forecast
python3 -m model.exitpoll
python3 scripts/build_tv_data.py
python3 model/tv_compare.py
python3 docs/site/build.py</pre>
<p>דף זה נבנה מתוצאות המאגר על ידי הסקריפט האחרון. תיעוד נוסף במאגר: <code>docs/method.md</code>, <code>docs/backtest.md</code>, <code>docs/how-it-works.md</code>.</p>
<footer>הנתונים הגולמיים הם של ועדת הבחירות המרכזית (https://votes26.bechirot.gov.il, https://data.gov.il). פרויקט עצמאי, אינו מזוהה עם הוועדה ואינו מאושר על ידה. המודל אינו סקר ואינו תוצאה רשמית.</footer>
<script>{DASH_JS}</script></main></div></body></html>"""
import sys; sys.path.insert(0, "docs/site")
import ux
_tvA = _tvc[_tvc.scored == "yes"]
PAGE = ux.transform(PAGE, f"{OFF} {CALC}").replace("@@TVCHART@@", ux.tv_chart(_tvA, SIM_NONE, SIM_HARD))
open("docs/site/style.css", "a").write("") if False else None
_css = open("docs/site/style.css", encoding="utf8").read()
if "/*UX*/" not in _css: open("docs/site/style.css", "a", encoding="utf8").write("/*UX*/" + ux.CSS)
open("docs/site/index.html", "w", encoding="utf8").write(PAGE)
print("ok", len(PAGE))
