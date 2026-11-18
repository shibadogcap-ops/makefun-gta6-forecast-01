import json
import math
import os
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP

Z = [-1.645, -0.674, 0.0, 0.674, 1.645]
SPREAD_FLOOR = 0.22
SPREAD_SCALE = 1.0
MIN_CURVES = 5


def parse_ts(s):
    if not isinstance(s, str):
        return None
    try:
        t = s.replace("Z", "+00:00")
        dt = datetime.fromisoformat(t)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def percentile(xs, q):
    # linear interpolation method (numpy default)
    if not xs:
        return 0.0
    xs = sorted(xs)
    n = len(xs)
    if n == 1:
        return xs[0]
    pos = q * (n - 1)
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return xs[lo]
    frac = pos - lo
    return xs[lo] + (xs[hi] - xs[lo]) * frac


def median(xs):
    return percentile(xs, 0.5)


def round_half_up_2(x):
    d = Decimal(repr(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    return float(d)


def is_primary(comp, viewers):
    # classification of launch-day curve: True -> primary pool
    u = comp.get("unlock")
    unlock = u.lower() if isinstance(u, str) else ""
    if unlock.strip().startswith("not a launch"):
        return False
    if "early-access-contaminated" in unlock:
        return False
    if "tier: weak" in unlock:
        return False
    daymax = max(viewers.values()) if viewers else 0.0
    v1 = viewers.get(0)
    if v1 is None or v1 < 0.08 * daymax:
        return False
    return True


def collect_ratios(comparables):
    # returns dict hour h (2..24) -> list of log ratios L
    by_hour = {h: [] for h in range(2, 25)}
    if not isinstance(comparables, list):
        return by_hour
    usable = []
    for comp in comparables:
        if not isinstance(comp, dict):
            continue
        day_start = parse_ts(comp.get("day_start"))
        hourly = comp.get("hourly")
        if day_start is None or not isinstance(hourly, list):
            continue
        viewers = {}
        for pt in hourly:
            if not isinstance(pt, dict):
                continue
            t = parse_ts(pt.get("from"))
            if t is None:
                continue
            idx = int(round((t - day_start).total_seconds() / 3600))
            if 0 <= idx <= 23:
                try:
                    v = float(pt.get("viewers") or 0)
                except Exception:
                    v = 0.0
                if v > 0:
                    viewers[idx] = v
        v1 = viewers.get(0)
        if not v1 or v1 <= 0:
            continue
        usable.append((comp, viewers))
    for h in range(2, 25):
        idx = h - 1
        kept = []
        all_l = []
        for comp, viewers in usable:
            vh = viewers.get(idx)
            if not vh or vh <= 0:
                continue
            l = math.log(vh / viewers[0])
            all_l.append(l)
            if is_primary(comp, viewers):
                kept.append(l)
        if len(kept) >= MIN_CURVES:
            by_hour[h] = kept
        else:
            by_hour[h] = all_l
    return by_hour


def forecast_hour(h, ratios):
    L = ratios.get(h, [])
    if len(L) >= MIN_CURVES:
        m = median(L)
        s_emp = (percentile(L, 0.75) - percentile(L, 0.25)) / 1.349
        s = max(SPREAD_FLOOR, SPREAD_SCALE * s_emp)
    else:
        m = 0.0
        s = max(SPREAD_FLOOR, 0.15 * math.sqrt(h - 1))
    return m, s


def process(path):
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        data = {}

    known = data.get("known")
    p = 1.0
    if isinstance(known, list) and known:
        row = known[0]
        if isinstance(row, dict):
            try:
                p = max(1.0, float(row.get("viewers") or 0))
            except Exception:
                p = 1.0

    ratios = collect_ratios(data.get("comparables"))

    forecast = data.get("forecast")
    hours = []
    if isinstance(forecast, list):
        for row in forecast[:23]:
            if not isinstance(row, dict):
                continue
            try:
                h = int(row.get("hour"))
            except Exception:
                continue
            m, s = forecast_hour(h, ratios)
            qs = [p * math.exp(m + z * s) for z in Z]
            qs = [min(1e9, max(1.0, round_half_up_2(q))) for q in qs]
            for i in range(1, len(qs)):
                if qs[i] < qs[i - 1]:
                    qs[i] = qs[i - 1]
            hours.append({"hour": h, "q": qs})
    return {"hours": hours}


def main():
    in_dir = os.environ.get("MAKEFUN_INPUT_DIR") or "/input"
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR") or "/output"
    names = sorted(fn for fn in os.listdir(in_dir) if fn.endswith(".in"))
    os.makedirs(out_dir, exist_ok=True)
    for name in names:
        stem = name[:-3]
        result = process(os.path.join(in_dir, name))
        out_path = os.path.join(out_dir, stem + ".out")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(json.dumps(result, separators=(",", ":")) + "\n")


if __name__ == "__main__":
    main()
