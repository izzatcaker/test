#!/usr/bin/env python3
"""Merge junction traffic exports and build a self-contained HTML dashboard.

Usage:
    python3 scripts/build_dashboard.py            # reads data/raw, writes dist/traffic-dashboard.html
    python3 scripts/build_dashboard.py --raw other/folder --out other.html

Every .xlsx or .csv file in the raw folder is read. Each file needs the same
columns as the Looker export (Date, Day_Type, Hour, Detector, Detector_Sort,
Stage, Class, Vehicles, Junction). Rows that repeat the same Junction, Date,
Hour, Detector and Class are reported and only the first copy is kept.

Junction names, stage notes and layout images come from data/junctions.json.
Layout images are embedded into the HTML, so the output is a single file.
"""

import argparse
import base64
import csv
import datetime as dt
import json
import mimetypes
import sys
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = ["Date", "Day_Type", "Hour", "Detector", "Detector_Sort", "Stage", "Class", "Vehicles", "Junction"]
STAGE_ORDER = ["Stage 1", "Stage 2", "Stage 3", "Stage 4", "Stage 5", "No stage"]
CLASS_ORDER = ["SML", "Motorcycle", "MID", "BIG", "Unclassified"]


def read_rows(path):
    if path.suffix.lower() == ".csv":
        with path.open(newline="", encoding="utf-8-sig") as f:
            yield from csv.DictReader(f)
        return
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb["Data"] if "Data" in wb.sheetnames else wb.worksheets[0]
    it = ws.iter_rows(values_only=True)
    header = [str(h).strip() if h is not None else "" for h in next(it)]
    for row in it:
        if row is None or all(v is None for v in row):
            continue
        yield dict(zip(header, row))


def to_date(v):
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    s = str(v).strip()
    for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%Y-%m-%d %H:%M:%S", "%d-%m-%Y"):
        try:
            return dt.datetime.strptime(s, fmt).date()
        except ValueError:
            pass
    raise ValueError(f"unrecognised date {v!r}")


def ordered(values, preferred):
    known = [v for v in preferred if v in values]
    return known + sorted(v for v in values if v not in preferred)


def embed_image(rel):
    if not rel:
        return None
    p = ROOT / "data" / rel
    if not p.exists():
        print(f"  note: layout image {p.relative_to(ROOT)} not found, the panel will show stage notes only")
        return None
    mime = mimetypes.guess_type(p.name)[0] or "image/png"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw", default=ROOT / "data" / "raw", type=Path)
    ap.add_argument("--config", default=ROOT / "data" / "junctions.json", type=Path)
    ap.add_argument("--template", default=ROOT / "dashboard" / "template.html", type=Path)
    ap.add_argument("--out", default=ROOT / "dist" / "traffic-dashboard.html", type=Path)
    ap.add_argument("--fragment", action="store_true", help="write the page without the <!doctype html> wrapper (for hosts that add their own)")
    args = ap.parse_args()

    files = sorted(p for p in args.raw.iterdir() if p.suffix.lower() in (".xlsx", ".csv") and not p.name.startswith("~$"))
    if not files:
        sys.exit(f"No .xlsx or .csv files found in {args.raw}")

    seen = {}
    records = []
    problems = 0
    for path in files:
        kept = dupes = 0
        for i, r in enumerate(read_rows(path), start=2):
            missing = [c for c in REQUIRED if c not in r]
            if missing:
                sys.exit(f"{path.name}: missing columns {', '.join(missing)}")
            try:
                rec = {
                    "junction": str(r["Junction"]).strip(),
                    "date": to_date(r["Date"]),
                    "day_type": str(r["Day_Type"]).strip(),
                    "hour": int(float(r["Hour"])),
                    "detector": str(r["Detector"]).strip(),
                    "det_sort": str(r["Detector_Sort"]).strip(),
                    "stage": str(r["Stage"]).strip(),
                    "cls": str(r["Class"]).strip(),
                    "vehicles": float(r["Vehicles"] or 0),
                }
            except (ValueError, TypeError) as e:
                print(f"  {path.name} row {i}: skipped ({e})")
                problems += 1
                continue
            if not 0 <= rec["hour"] <= 23 or rec["vehicles"] < 0:
                print(f"  {path.name} row {i}: skipped (hour {rec['hour']}, vehicles {rec['vehicles']})")
                problems += 1
                continue
            key = (rec["junction"], rec["date"], rec["hour"], rec["detector"], rec["cls"])
            if key in seen:
                dupes += 1
                continue
            seen[key] = path.name
            records.append(rec)
            kept += 1
        msg = f"{path.name}: {kept:,} rows"
        if dupes:
            msg += f", {dupes:,} duplicate rows ignored (already in an earlier file)"
        print(msg)

    config = json.loads(args.config.read_text(encoding="utf-8")) if args.config.exists() else {}

    junctions = sorted({r["junction"] for r in records})
    dates = sorted({r["date"] for r in records})
    det_sort = {}
    for r in records:
        det_sort[r["detector"]] = r["det_sort"]
    detectors = sorted(det_sort, key=lambda d: det_sort[d])
    stages = ordered({r["stage"] for r in records}, STAGE_ORDER)
    classes = ordered({r["cls"] for r in records}, CLASS_ORDER)

    day_type = {}
    for r in records:
        day_type[r["date"]] = r["day_type"]

    ji = {v: i for i, v in enumerate(junctions)}
    di = {v: i for i, v in enumerate(dates)}
    ei = {v: i for i, v in enumerate(detectors)}
    si = {v: i for i, v in enumerate(stages)}
    ci = {v: i for i, v in enumerate(classes)}

    rows = [
        [ji[r["junction"]], di[r["date"]], r["hour"], ei[r["detector"]], si[r["stage"]], ci[r["cls"]], round(r["vehicles"] * 100)]
        for r in records
    ]

    payload = {
        "generated": dt.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "junctions": [
            {
                "code": j,
                "name": config.get(j, {}).get("name", ""),
                "layout": embed_image(config.get(j, {}).get("layout_image")),
                "stageNotes": config.get(j, {}).get("stages", {}),
            }
            for j in junctions
        ],
        "dates": [d.isoformat() for d in dates],
        "dayTypes": [day_type[d] for d in dates],
        "detectors": detectors,
        "stages": stages,
        "classes": classes,
        "cols": ["junction", "date", "hour", "detector", "stage", "class", "vehicles_x100"],
        "rows": rows,
    }

    template = args.template.read_text(encoding="utf-8")
    # Build the chart library into the page so it works offline and behind firewalls
    lib = args.template.parent / "vendor" / "echarts.min.js"
    cdn_tag = '<script src="https://cdnjs.cloudflare.com/ajax/libs/echarts/5.5.1/echarts.min.js"></script>'
    if lib.exists() and cdn_tag in template:
        template = template.replace(cdn_tag, "<script>" + lib.read_text(encoding="utf-8").replace("</script", "<\\/script") + "</script>")
    else:
        print("  note: chart library not embedded, the page will load it from the internet")
    marker = "/*__DATA__*/null"
    if marker not in template:
        sys.exit(f"{args.template} has no {marker} placeholder")
    data_js = json.dumps(payload, separators=(",", ":")).replace("</", "<\\/")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    page = template.replace(marker, data_js)
    if not args.fragment:
        page = '<!doctype html>\n<html lang="en">\n<meta charset="utf-8">\n' + page + "\n</html>\n"
    args.out.write_text(page, encoding="utf-8")

    total = sum(r["vehicles"] for r in records)
    print(
        f"\nBuilt {args.out.relative_to(ROOT) if args.out.is_relative_to(ROOT) else args.out}"
        f"\n  {len(records):,} rows, {len(junctions)} junction(s): {', '.join(junctions)}"
        f"\n  {dates[0]} to {dates[-1]} ({len(dates)} days), {total:,.0f} vehicles"
        f"\n  {args.out.stat().st_size / 1024:,.0f} KB"
    )
    if problems:
        print(f"  {problems} row(s) skipped, see messages above")


if __name__ == "__main__":
    main()
