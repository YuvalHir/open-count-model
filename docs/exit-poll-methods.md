# How exit polls are done: what is published, what is not

Compiled 29.10.2026 from the pages below (fetched that day). "Published" means the source states it. Anything else is unknown to us.
This is background for the design simulation in `model/exitpoll.py`. Nothing here is a claim about how accurate any broadcaster is.

## Israel
- **Channel 12 (2026).** Per The Briefing Point (a news site, 27.10.2026, relaying the channel): 70 polling stations out of about 13,000, "selected using a mathematical model"; a dummy ballot box with a tablet next to the real box; stratified sampling meant to cover Arab society, ultra-Orthodox and immigrants; consistency checks that remove unreliable answers; a "behavioral model" to correct bias, and the pollster says it "is still not hermetic". Early data are processed before polls close, and the numbers are updated at night as real results from the sampled stations arrive.
  https://thebp.co.il/en/behind-the-scenes-how-the-channel-12-election-exit-poll-works
  Unknown: which stations, how many interviews, the model, the weighting.
- **Channels 1, 2, 10 (2015).** Times of Israel, 18.03.2015: Channels 1 and 2 used about 60 dummy ballot boxes (25,000 and 30,000 voters); stations chosen by socio-economic criteria and by how reliable exit polling had been there in the two previous elections. Channel 10 used a questionnaire, with participation reported at about 80%. After the miss (Likud 28 in the poll, 30 in the result; Zionist Union 27 vs 24), Camil Fuchs and Mina Tzemach pointed to lower participation, said to be greatest where Likud voters were many, including immigrants from the former Soviet Union. That is their explanation as reported, not something we tested.
  https://www.timesofisrael.com/botched-tv-exit-polls-earn-vote-of-non-confidence/

## United Kingdom (BBC, ITV, Sky)
Warwick "Exit polling explained" (Firth; method by Curtice, Kuha, Fisher and others): about 100 polling stations out of about 40,000, 100-200 voters in each. The same stations are revisited each election, because votes are not counted per station in the UK. The poll measures **change since the last election** at each station, a statistical model turns that into change per constituency, and the change is applied to the previous constituency result. Postal voters are not covered. Refusal and lying: they say it is a concern, and that using the previous exit-poll data at the same stations may remove bias that stays the same between elections. Seat forecasts at 10pm: 2024 error of 2 seats for the largest party (their numbers: Lab 410 vs 412).
https://warwick.ac.uk/fac/sci/statistics/staff/academic-research/firth/exit-poll-explainer/
Israel differs: results are published per box, which is an advantage for a model like ours.

## United States (NEP / Edison Research)
2024 methods statement: 279 election-day polling places (stratified probability sample), every nth voter approached, target about 75 questionnaires per place; 27 early in-person locations; a registration-based multi-mode poll (phone, text, email, web) for absentee and early voters, combined in about the right proportion. The statement says nonresponse is likely to add to the total error.
https://s.abcnews.com/assets/dtci/elections/NEPExitPollMethodologyStatement.pdf
Edison/Mitofsky evaluation of the 2004 exit polls: the error was larger than usual because of higher Within-Precinct Error, most likely Kerry voters taking part at a higher rate than Bush voters; they describe an age-race-sex adjustment based on refusals and misses, and changes to interviewer hiring and monitoring.
https://electionintegrity.org/documents/edison-mitofsky-050119.pdf

## Germany (ARD / ZDF)
Tagesschau (22.02.2025): infratest dimap interviews at 560 polling places chosen to represent the country (cities and countryside, high and low turnout, strongholds and diaspora of parties), 80,000-90,000 interviews, results come in hourly from 9:00 and the forecast is made just before 18:00. Postal votes are handled by statistical models from earlier elections plus special surveys. They state the average deviation of the ARD and ZDF forecasts from results was under 0.5 points over past decades.
https://www.tagesschau.de/inland/bundestagswahl/wahlsystem/prognose-entstehung-bundestagswahl-100.html

## What this means for our design
- Everyone selects stations with the help of earlier results, and the UK and Edison systems estimate **change** rather than levels. Our "prior-corrected" designs are of that family.
- Published sample sizes range from about 60-70 (Israel) to 100-130 (UK), 279 (US) and 560 (Germany). Our simulation puts the error at 50 boxes at about 0.6 pp per list with no wrong answers and about 1.0 pp under our assumed non-response, so the German figure is plausible only with several times more boxes.
- Differential non-response is the problem every source names. No box design removes it. Past-vote questions and modelling can reduce it, at a variance cost, and only if the assumption on how it behaves holds.
- Not tested here, and unknown to us: the TV channels' stations, interview counts, weights and models. We therefore make no claim of beating them.
