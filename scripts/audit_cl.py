"""Print an apply_patch correction, retaining CSV layout and raw source evidence."""
import csv
import json
import io
import re
import sys
from pathlib import Path
from sports_lottery.history_quality import regulation_score, outcome

root, dataset = map(Path, sys.argv[1:3])
lines = dataset.read_text().splitlines()
rows = list(csv.DictReader(lines))
changes = []
for source in sorted(root.glob("*/cl.txt")):
    if not "2016-17" <= source.parent.name <= "2025-26":
        continue
    for raw in source.read_text().splitlines():
        if "a.e.t." not in raw:
            continue
        m = re.match(r"\s*(?:\d{1,2}:\d{2}\s+)?(.+?)\s+v\s+(.+?)\s+(\d+-\d+.*)", raw)
        if not m:
            raise ValueError(raw)
        clean = lambda s: re.sub(r"\s+\([A-Z]{3}\)\s*$", "", s).strip()
        matches = [(i, r) for i, r in enumerate(rows) if r["season"] == source.parent.name
                   and r["home_team"] == clean(m[1]) and r["away_team"] == clean(m[2])]
        if len(matches) != 1:
            raise ValueError((raw, len(matches)))
        i, row = matches[0]
        h, a = regulation_score(m[3])
        half = re.search(r",\s*(\d+)-(\d+)\)", m[3])
        fields = next(csv.reader([lines[i + 1]]))
        fields[6:11] = [str(h), str(a), half[1], half[2], outcome(h, a)]
        buffer = io.StringIO()
        csv.writer(buffer, lineterminator="").writerow(fields)
        new = buffer.getvalue()
        changes.append(dict(season=row["season"], date=row["date"], home=row["home_team"],
                            away=row["away_team"], before=lines[i+1], after=new, source=raw.strip()))
print(json.dumps(changes, ensure_ascii=False))
