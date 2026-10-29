# Polling-place addresses (used only to tell which places are the same building)

Columns kept: locality code, box number, address text, place name (K26 also: registered voters listed, point geometry as text).
Nothing is geocoded. No third-party geocoding service is used.

| File | Content | Source of the bytes |
|---|---|---|
| k21..k25.csv.gz | CEC polling-place lists (Hebrew: "רשימת מקומות הקלפי" / ballot report), K21 to K25 | The CEC xls/xlsx lists, retrieved from the mirror at github.com/JacobWeinbren/Israel-Revised (data/21..25). That repo's README says the CEC removed these files from its site. The data is the CEC's; the repo's GNU licence covers his code, not the CEC's data. |
| k26.csv.gz | K26 polling-place layer "קלפיות טופס א' כנסת 26" (govmap), 12,525 rows | govmap layer https://www.govmap.gov.il/?lay=235036, as archived by https://www.over.org.il (version page 1655625d-b2c9-4d22-adca-f21bc16d2eb5). It is a pre-election draft: about 12% of its box numbers differ from the final live numbering, so the model trusts an address only when its listed voters are within 10% of the live file. |

Not used: the 2016 "polling.xls" on data.gov.il (a 2015-era list: only 44% of boxes had the same building as in K26), bechirot.fyi and other derived third-party point sets (licence unclear).
These are Central Elections Committee data. Terms of the CEC apply. No endorsement by the CEC.
