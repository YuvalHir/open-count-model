"""Builds data/tv_exit_polls/*.csv from values transcribed from the cited public sources (one-off transcription)."""
import csv
W="https://en.wikipedia.org/wiki/Opinion_polling_for_the_"
V="https://votes%d.bechirot.gov.il/"
fin={21:[("Likud",35),("Blue & White",35),("Shas",8),("UTJ",8),("Hadash-Ta'al",6),("Labor",6),("Yisrael Beiteinu",5),("URWP",5),("Meretz",4),("Kulanu",4),("Ra'am-Balad",4)],
22:[("Blue & White",33),("Likud",32),("Joint List",13),("Shas",9),("Yisrael Beiteinu",8),("UTJ",7),("Yamina",7),("Labor-Gesher",6),("Democratic Union",5)],
23:[("Likud",36),("Blue & White",33),("Joint List",15),("Shas",9),("UTJ",7),("Labor-Gesher-Meretz",7),("Yisrael Beiteinu",7),("Yamina",6)],
24:[("Likud",30),("Yesh Atid",17),("Shas",9),("Blue & White",8),("Yamina",7),("Labor",7),("UTJ",7),("Yisrael Beiteinu",7),("Religious Zionism",6),("Joint List",6),("New Hope",6),("Meretz",6),("Ra'am",4)],
25:[("Likud",32),("Yesh Atid",24),("Religious Zionism-Otzma",14),("National Unity",12),("Shas",11),("UTJ",7),("Yisrael Beiteinu",6),("Ra'am",5),("Hadash-Ta'al",5),("Labor",4)]}
with open("data/tv_exit_polls/official_final_seats.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["election","list","seats","source_url"])
    for e,l in fin.items():
        assert sum(s for _,s in l)==120
        for n,s in l: w.writerow([e,n,s,V%e])
rows=[]
def add(e,ch,names,vals,tier,src,note,comp="full",chk=True):
    assert len(names)==len(vals)
    if comp=="full" and chk: assert sum(vals)==120,(e,ch,sum(vals))
    for n,v in zip(names,vals): rows.append([e,ch,n,v,tier,comp,src,note])
L21=["Likud","Labor","Blue & White","Kulanu","Ra'am-Balad","Shas","UTJ","URWP","Yisrael Beiteinu","Meretz","Hadash-Ta'al","New Right","Gesher","Zehut"]
s=W+"April_2019_Israeli_legislative_election ; top-two seats checked vs https://www.ynetnews.com/article/5491929"
nB="Per-list values from Wikipedia table (sum as stated); top-two seats match first-broadcast Ynet report; others not verified as first values"
add(21,"Channel 13",L21,[36,7,36,4,0,7,7,4,4,4,7,4,0,0],"B",s,nB,chk=False)
add(21,"Kan 11",L21,[36,8,37,5,0,7,7,5,4,5,6,0,0,0],"B",s,nB,chk=False)
add(21,"Channel 12",L21,[33,6,37,4,6,6,7,5,5,5,6,0,0,0],"B",s,nB,chk=False)
L22=["Likud","Blue & White","Joint List","Shas","UTJ","Yamina","Labor-Gesher","Yisrael Beiteinu","Democratic Union"]
s="https://www.timesofisrael.com/israels-exit-polls-show-no-clear-election-winner-netanyahu-far-from-majority/"
n="First broadcast as reported by Times of Israel on election night"
add(22,"Channel 12",L22,[33,34,11,8,8,8,5,8,5],"A",s,n)
add(22,"Channel 13",L22,[31,33,13,9,8,6,6,8,6],"A",s,n)
add(22,"Kan 11",L22,[32,32,12,9,8,7,5,10,5],"A",s,n)
L23=["Likud","Blue & White","Joint List","Shas","UTJ","Yamina","Labor-Gesher-Meretz","Yisrael Beiteinu"]
s="https://www.timesofisrael.com/exit-polls-show-netanyahu-poised-to-retain-premiership-with-60-seats-for-right/"
n="As reported by Times of Israel election-night article (no update noted)"
add(23,"Channel 12",L23,[37,33,14,9,7,7,7,6],"A",s,n)
add(23,"Channel 13",L23,[37,32,14,9,8,6,6,8],"A",s,n)
add(23,"Kan 11",L23,[36,33,15,9,8,7,6,6],"A",s,n)
L24=["Likud","Yesh Atid","Yamina","New Hope","Joint List","Shas","Yisrael Beiteinu","UTJ","Labor","Religious Zionism","Blue & White","Meretz"]
s="https://en.globes.co.il/en/article-exit-polls-give-netanyahu-block-majority-1001365137"
n="Globes full lists published 22:48 on election night; first-minute value not verified"
add(24,"Channel 12",L24,[31,18,8,6,9,9,6,6,7,7,7,6],"A",s,n)
add(24,"Channel 13",L24,[33,16,7,5,8,8,8,7,7,6,8,7],"A",s,n)
add(24,"Kan 11",L24,[31,18,7,6,8,9,7,7,7,7,7,6],"A",s,n)
L25=["Likud","Yesh Atid","Religious Zionism-Otzma","National Unity","Shas","UTJ","Yisrael Beiteinu","Labor","Meretz","Ra'am","Hadash-Ta'al"]
add(25,"Channel 12",L25,[30,24,14,11,10,7,4,6,5,5,4],"A","https://en.globes.co.il/en/article-exit-polls-indicate-narrow-victory-for-netanyahu-1001428559","Globes first Channel 12 list; Channel 12 later updated (INN: Likud 31, Yesh Atid 23, Meretz 4)")
for ch,v in (("Kan 11",[30,22]),("Channel 13",[31,24])):
    add(25,ch,["Likud","Yesh Atid"],v,"P","https://www.ynetnews.com/article/h1tyl0a4s","Partial: only two lists found; full first list not found",comp="partial")
add(25,"Channel 12 (later update)",L25,[31,23,14,11,10,7,5,5,4,5,5],"S","https://www.israelnationalnews.com/news/362084","Later updated list (not first broadcast); sensitivity only")
L26=["Likud","Yashar","Together","Joint List","Ra'am","Democrats","Yisrael Beiteinu","Otzma","Shas","UTJ","Religious Zionism"]
s="https://www.israelhayom.com/2026/10/27/israel-election-2026-exit-polls-full-results/"
n="First published ~22:20; K26 official results not final, NOT scored"
add(26,"Kan 11",L26,[25,21,14,10,7,10,8,7,6,6,6],"A",s,n)
add(26,"Channel 12",L26,[24,22,12,11,7,9,9,6,8,6,6],"A",s,n)
add(26,"Channel 13",L26,[25,23,14,10,7,9,7,6,6,7,6],"A",s,n)

# K26 other broadcasters (election night, first lists as reported by Times of Israel / ynet). NOT scored until official finals.
nt="Election-night first list (ToI 27.10.2026 23:58 summary of exit polls); K26 not scored"
add(26,"i24NEWS",L26,[27,20,15,9,7,9,5,7,8,7,6],"A","https://www.timesofisrael.com/liveblog_entry/three-more-exit-polls-by-non-mainstream-networks-diverge-wildly-with-one-projecting-60-seats-for-pms-bloc/ ; https://www.i24news.tv/en/news/israeli-elections/artc-i24news-exit-poll-likud-wins-27-seats-yashar-20-coalition-bloc-reaches-55-seats-opposition-49-and-arab-parties-16",nt+"; poll by Direct Polls (per ynet interview)")
add(26,"Channel 16",L26,[25,22,13,11,5,10,6,7,7,7,7],"A","https://www.ynetnews.com/article/xl2l49txt ; https://www.timesofisrael.com/liveblog_entry/three-more-exit-polls-by-non-mainstream-networks-diverge-wildly-with-one-projecting-60-seats-for-pms-bloc/",nt)
add(26,"Channel 14",L26,[31,20,11,11,7,9,0,7,10,7,7],"A","https://www.timesofisrael.com/liveblog_entry/three-more-exit-polls-by-non-mainstream-networks-diverge-wildly-with-one-projecting-60-seats-for-pms-bloc/",nt+"; differs from Israel Hayom's Channel 14 list (Likud 30, YB 4), which may be an earlier/other version")
with open("data/tv_exit_polls/tv_exit_polls.csv","w",newline="",encoding="utf-8") as f:
    w=csv.writer(f); w.writerow(["election","channel","list","seats","source_tier","complete","source_url","as_stated_note"]); w.writerows(rows)
