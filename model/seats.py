"""Bader-Ofer seat allocation with surplus-vote agreements (הסכמי עודפים)."""
import numpy as np

def allocate(votes: dict, agreements=(), threshold=0.0325, total_seats=120):
    """votes: {list_letter: votes}. agreements: iterable of (a, b), used only if both pass.
    Returns {letter: seats} for lists that pass the threshold."""
    total = sum(votes.values())
    passing = {k: v for k, v in votes.items() if v >= threshold * total}
    if not passing:
        return {}
    quota = sum(passing.values()) / total_seats
    base = {k: int(v // quota) for k, v in passing.items()}
    pairs = [(a, b) for a, b in agreements if a in passing and b in passing]
    in_pair = {x for p in pairs for x in p}
    units = [(a, b) for a, b in pairs] + [(k,) for k in passing if k not in in_pair]
    uvotes = [sum(passing[m] for m in u) for u in units]
    useats = [sum(base[m] for m in u) for u in units]
    remaining = total_seats - sum(base.values())
    extra = [0] * len(units)
    for _ in range(remaining):
        i = int(np.argmax([uvotes[j] / (useats[j] + extra[j] + 1) for j in range(len(units))]))
        extra[i] += 1
    seats = dict(base)
    for u, e in zip(units, extra):
        if len(u) == 2 and e:
            a, b = u
            for _ in range(e):
                ca = passing[a] / (seats[a] + 1)
                cb = passing[b] / (seats[b] + 1)
                seats[a if ca >= cb else b] += 1
        elif e:
            seats[u[0]] += e
    return seats
