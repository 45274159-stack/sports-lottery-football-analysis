"""Probability reliability diagnostics, not a fitted calibration transformation."""
import math


def reliability(records, bins=10):
    if type(bins) is not int or bins < 1:
        raise ValueError("Positive integer bins required")
    buckets = [dict(n=0, probability_sum=0., hits=0) for _ in range(bins)]
    for record in records:
        p = record["probability"]
        y = record["outcome"]
        if not math.isfinite(p) or not 0 <= p <= 1 or y not in (0, 1):
            raise ValueError("Invalid calibration observation")
        b = buckets[min(int(p*bins), bins-1)]
        b["n"] += 1
        b["probability_sum"] += p
        b["hits"] += y
    n = sum(b["n"] for b in buckets)
    rows = [dict(lower=i/bins, upper=(i+1)/bins, n=b["n"],
                 mean_probability=b["probability_sum"]/b["n"] if b["n"] else None,
                 observed_frequency=b["hits"]/b["n"] if b["n"] else None)
            for i,b in enumerate(buckets)]
    ece = sum(r["n"]*abs(r["mean_probability"]-r["observed_frequency"])
              for r in rows if r["n"])/n if n else None
    return dict(n=n, bins=rows, expected_calibration_error=ece,
                warning="Use held-out predictions; small bins are uncertain; this diagnostic does not calibrate the model")
