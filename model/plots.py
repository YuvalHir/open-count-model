import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt, pandas as pd

def main():
    r = pd.read_csv("out/backtest.csv")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharey=True)
    for ax, (title, sel) in zip(axes, (("Random station order", r.order == "random"),
                                       ("Politically biased orders (worst of 5)", r.order != "random"))):
        for method, col in (("raw_counted", "tab:red"), ("ridge", "tab:blue")):
            d = r[sel & (r.method == method)]
            if title.startswith("Random"):
                g = d.groupby("frac").seats_misallocated.mean()
            else:
                g = d.groupby(["order", "frac"]).seats_misallocated.mean().groupby("frac").max()
            ax.plot(100 * g.index, g.values, marker="o", color=col, label={"raw_counted": "counted so far (baseline)", "ridge": "projection (ridge on previous result)"}[method])
        ax.set_xscale("log"); ax.set_xlabel("share of voting places counted (%)"); ax.set_title(title); ax.grid(alpha=.3)
    axes[0].set_ylabel("seats misallocated (of 120)\nmean over Knesset 22-26 replays"); axes[0].legend()
    fig.tight_layout(); fig.savefig("docs/backtest_seats.png", dpi=130)
    c = pd.read_csv("out/coverage.csv"); c = c[c.truth > 0]
    print(c.groupby("frac").hit.mean().round(2).to_dict())

if __name__ == "__main__":
    main()
