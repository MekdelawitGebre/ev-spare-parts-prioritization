#!/usr/bin/env python3
"""
Collect NHTSA complaints and recalls for the selected vehicles (US-market FAILURE evidence).

Why a script and not a prompt: the NHTSA API is public, structured and free, so a script gives
a reproducible, timestamped raw file (better evidence than copy-pasting from a chat answer).

Usage (run on your own machine - it needs internet access):
    python src/fetch_nhtsa.py --make TOYOTA --model bZ4X --years 2023 2024 2025
    python src/fetch_nhtsa.py --make VOLKSWAGEN --model ID.4 --years 2021 2022 2023 2024

Output (appended, never overwritten):
    data/raw/nhtsa/<make>_<model>_<year>_<type>_<YYYYMMDD>.json   (untouched API response)
    data/raw/nhtsa_records_raw.csv                                 (flattened, one row per record)

Notes
  * Vehicles that were never sold in the US (e.g. BYD Seagull) will return count = 0.
    That is a valid finding - record it, do not fill it with another vehicle's data.
  * Endpoint field names are read defensively; if NHTSA changes them, check the raw JSON.
"""
import argparse, csv, json, time, urllib.parse, urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "scraped_json" / "nhtsa"
OUT_CSV = ROOT / "data" / "raw" / "nhtsa_records_raw.csv"
BASE = "https://api.nhtsa.gov"
COLUMNS = ["record_type", "external_record_id", "make", "model", "model_year",
           "component_raw", "summary_text", "collected_on", "request_url"]


def get_json(url: str, retries: int = 3, pause: float = 2.0) -> dict:
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(url, timeout=30) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except Exception as exc:  # network errors are expected; retry politely
            print(f"  attempt {attempt}/{retries} failed: {exc}")
            time.sleep(pause * attempt)
    return {"count": None, "results": [], "error": f"failed after {retries} attempts"}


def flatten(kind: str, payload: dict, make: str, model: str, year: int, url: str, today: str):
    for rec in payload.get("results", []) or []:
        if kind == "complaint":
            rid = rec.get("odiNumber")
            comp = rec.get("components")
            summ = rec.get("summary")
        else:
            rid = rec.get("NHTSACampaignNumber")
            comp = rec.get("Component")
            summ = rec.get("Summary")
        yield [kind, rid, make, model, year, comp, (summ or "")[:500].replace("\n", " "), today, url]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--make", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--years", type=int, nargs="+", required=True)
    args = ap.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    new_file = not OUT_CSV.exists()
    with open(OUT_CSV, "a", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        if new_file:
            writer.writerow(COLUMNS)
        for year in args.years:
            for kind, path in (("complaint", "complaints/complaintsByVehicle"),
                               ("recall", "recalls/recallsByVehicle")):
                qs = urllib.parse.urlencode({"make": args.make, "model": args.model, "modelYear": year})
                url = f"{BASE}/{path}?{qs}"
                print(f"GET {url}")
                payload = get_json(url)
                stamp = today.replace("-", "")
                fname = f"{args.make}_{args.model}_{year}_{kind}_{stamp}.json".replace("/", "-").replace(" ", "")
                (RAW_DIR / fname).write_text(json.dumps(payload, indent=2), encoding="utf-8")
                n = 0
                for row in flatten(kind, payload, args.make, args.model, year, url, today):
                    writer.writerow(row)
                    n += 1
                print(f"  {kind}: {n} records saved  (API count = {payload.get('count')})")
                time.sleep(1.0)  # be polite to the public API


if __name__ == "__main__":
    main()
