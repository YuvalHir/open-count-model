import os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from model.load import load_history, party_cols
from model.seats import allocate

# Knesset 25 (1 Nov 2022) official seats and surplus agreements.
OFFICIAL_25 = {"מחל": 32, "פה": 24, "ט": 14, "כן": 12, "שס": 11, "ג": 7, "ל": 6, "עם": 5, "ום": 5, "אמת": 4}
AGREEMENTS_25 = [("אמת", "מרצ"), ("ג", "שס"), ("מחל", "ט"), ("פה", "כן")]

def test_knesset25_matches_official():
    d = load_history(25)
    votes = {c: int(d[c].sum()) for c in party_cols(d)}
    assert allocate(votes, AGREEMENTS_25) == OFFICIAL_25

if __name__ == "__main__":
    test_knesset25_matches_official(); print("ok")
