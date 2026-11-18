#!/usr/bin/env python3
"""
Collect electric vehicle listings and local spare parts listings from Jiji Ethiopia (jiji.com.et)
in an evidence-first, reproducible, and fully auditable manner.

Compliance: Strictly auditable empirical collection (no hallucinated values, exact text copied as seen,
            public pages only, polite request rates, full source traceability).

Usage:
    python src/fetch_jiji.py --mode all
    python src/fetch_jiji.py --mode vehicles --pages 2
    python src/fetch_jiji.py --mode parts --pages 2

Outputs:
    data/raw/jiji/vehicle_<id>_<YYYYMMDD>.json   (untouched raw item metadata for audit)
    data/raw/jiji/part_<id>_<YYYYMMDD>.json      (untouched raw item metadata for audit)
    data/raw/vehicle_listings_raw.csv            (merged/updated with source_id=S01)
    data/raw/local_parts_listings_raw.csv        (merged/updated with source_id=S08)
    data/raw/local_search_log_raw.csv            (updated with query result counts)
"""

import argparse
import csv
from datetime import date
import json
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = ROOT / "data" / "raw" / "scraped_json" / "jiji"
VEHICLES_CSV = ROOT / "data" / "raw" / "vehicle_listings_raw.csv"
PARTS_CSV = ROOT / "data" / "raw" / "local_parts_listings_raw.csv"
SEARCH_LOG_CSV = ROOT / "data" / "raw" / "local_search_log_raw.csv"
SOURCES_CSV = ROOT / "data" / "raw" / "sources_log.csv"

BASE_URL = "https://jiji.com.et"
SOURCE_ID_VEHICLES = "S01"
SOURCE_ID_PARTS = "S08"

VEHICLE_COLUMNS = [
    "record_id",
    "source_id",
    "listing_url",
    "collected_on",
    "raw_title",
    "make_raw",
    "model_raw",
    "year_raw",
    "price_raw",
    "currency_raw",
    "mileage_raw",
    "condition_raw",
    "location_raw",
    "seller_raw",
    "posted_date_raw",
    "notes",
]

PARTS_COLUMNS = [
    "record_id",
    "source_id",
    "listing_url",
    "collected_on",
    "raw_title",
    "vehicle_raw",
    "part_raw",
    "price_raw",
    "currency_raw",
    "condition_raw",
    "location_raw",
    "seller_raw",
]

SEARCH_LOG_COLUMNS = [
    "record_id",
    "source_id",
    "vehicle_raw",
    "part_raw",
    "query_text",
    "performed_on",
    "n_results_seen",
]

TARGET_VEHICLES = [
    {
        "query": "byd seagull",
        "make": "BYD",
        "model": "Seagull",
    },
    {
        "query": "byd yuan",
        "make": "BYD",
        "model": "Yuan Up",
    },
    {
        "query": "volkswagen id4",
        "make": "Volkswagen",
        "model": "ID.4",
    },
    {
        "query": "toyota bz4x",
        "make": "Toyota",
        "model": "bZ4X",
    },
    {
        "query": "changan benben e-star",
        "make": "Changan",
        "model": "Benben E-Star",
    },
    {
        "query": "changan e-star",
        "make": "Changan",
        "model": "Benben E-Star",
    },
]

TARGET_PARTS = [
    {
        "query": "byd brake pad",
        "vehicle": "BYD Seagull",
        "part": "Brake pads front set",
    },
    {
        "query": "bz4x brake pad",
        "vehicle": "Toyota bZ4X",
        "part": "Brake pads front set",
    },
    {
        "query": "id4 brake pad",
        "vehicle": "Volkswagen ID.4",
        "part": "Brake pads front set",
    },
    {
        "query": "byd cabin filter",
        "vehicle": "BYD Seagull",
        "part": "Cabin AC pollen filter",
    },
    {
        "query": "cabin filter",
        "vehicle": "Universal / EV",
        "part": "Cabin AC pollen filter",
    },
    {
        "query": "byd control arm",
        "vehicle": "BYD Seagull",
        "part": "Lower control arm bushing set",
    },
    {
        "query": "bz4x suspension",
        "vehicle": "Toyota bZ4X",
        "part": "Front shock absorber / strut",
    },
    {
        "query": "volkswagen id4 front suspension",
        "vehicle": "Volkswagen ID.4",
        "part": "Front shock absorber / strut",
    },
    {
        "query": "byd suspension",
        "vehicle": "BYD Seagull",
        "part": "Front shock absorber / strut",
    },
    {
        "query": "brake pads",
        "vehicle": "Universal / EV",
        "part": "Brake pads front set",
    },
    {
        "query": "brake disc",
        "vehicle": "Universal / EV",
        "part": "Front brake rotor / disc",
    },
    {
        "query": "byd wiper",
        "vehicle": "BYD Seagull",
        "part": "Front windshield wiper pair",
    },
    {
        "query": "byd bumper",
        "vehicle": "BYD Yuan Up",
        "part": "Front bumper cover",
    },
    {
        "query": "toyota bz4x bumper",
        "vehicle": "Toyota bZ4X",
        "part": "Front bumper cover",
    },
    {
        "query": "toyota bz4x headlight",
        "vehicle": "Toyota bZ4X",
        "part": "LED headlight assembly RH",
    },
]

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)


def fetch_url(url: str, retries: int = 3, timeout: int = 15) -> str:
    """Fetch URL contents with polite retries and backoff."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        },
    )
    for attempt in range(1, retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except (urllib.error.URLError, urllib.error.HTTPError) as exc:
            if attempt == retries:
                print(f"Warning: Failed to fetch {url}: {exc}", file=sys.stderr)
                return ""
            time.sleep(1.5 * attempt)
    return ""


def parse_nuxt_payload(html: str):
    """Extract and parse the Nuxt 3 devalue array from Jiji HTML."""
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", html, re.DOTALL)
    for s in scripts:
        s_clean = s.strip()
        if "adverts" in s_clean and s_clean.startswith("["):
            try:
                arr = json.loads(s_clean)
                return arr
            except Exception:
                pass
    return None


def resolve_val(idx_or_val, arr):
    """Resolve an index pointer in the Nuxt array."""
    if isinstance(idx_or_val, int) and 0 <= idx_or_val < len(arr):
        return arr[idx_or_val]
    return idx_or_val


def extract_adverts_from_payload(arr):
    """Extract list of advert dictionaries and total count from Nuxt array."""
    if not arr:
        return 0, []

    # Find the object that has count and adverts
    total_count = 0
    adverts_indices = []

    for item in arr:
        if isinstance(item, dict) and "adverts" in item and "count" in item:
            c_val = resolve_val(item["count"], arr)
            if isinstance(c_val, int):
                total_count = c_val
            adv_val = resolve_val(item["adverts"], arr)
            if isinstance(adv_val, list):
                adverts_indices = adv_val
            break

    # If not found via the container, search directly for advert dicts
    adverts = []
    if adverts_indices:
        for idx in adverts_indices:
            if isinstance(idx, int) and 0 <= idx < len(arr):
                adverts.append(arr[idx])
    else:
        for item in arr:
            if isinstance(item, dict) and "title" in item and "guid" in item and "url" in item:
                adverts.append(item)

    if not total_count:
        total_count = len(adverts)

    return total_count, adverts


def parse_vehicle_advert(adv: dict, arr: list, spec: dict, today: str, total_seen: int, is_first: bool) -> tuple:
    """Parse raw advert dict into a structured vehicle listing and raw JSON dict."""
    adv_id = resolve_val(adv.get("id"), arr)
    guid = resolve_val(adv.get("guid"), arr)
    raw_title = resolve_val(adv.get("title"), arr) or ""
    price_str = resolve_val(adv.get("price_title"), arr) or ""
    rel_url = resolve_val(adv.get("url"), arr) or ""
    if isinstance(rel_url, str):
        rel_url = rel_url.split("?")[0]
    listing_url = f"{BASE_URL}{rel_url}" if rel_url.startswith("/") else rel_url

    region = resolve_val(adv.get("region_name"), arr) or "Addis Ababa"
    parent_region = resolve_val(adv.get("region_parent_name"), arr) or "Addis Ababa"
    location_raw = f"{region}, {parent_region}" if region and region != parent_region else (region or parent_region)

    short_desc = resolve_val(adv.get("short_description"), arr) or ""
    details = resolve_val(adv.get("details"), arr) or ""
    combined_desc = f"{short_desc}\n{details}".strip()

    # Resolve attrs list
    attrs_dict = {}
    attrs_ref = adv.get("attrs")
    if attrs_ref is not None:
        attrs_list = resolve_val(attrs_ref, arr)
        if isinstance(attrs_list, list):
            for a_idx in attrs_list:
                a_obj = resolve_val(a_idx, arr)
                if isinstance(a_obj, dict) and "name" in a_obj and "value" in a_obj:
                    k = resolve_val(a_obj["name"], arr)
                    v = resolve_val(a_obj["value"], arr)
                    if isinstance(k, str) and v is not None:
                        attrs_dict[k.strip()] = str(v).strip()

    # Parse price and currency
    # Example price_str: "ETB 3,850,000"
    p_match = re.search(r"(ETB|Birr|Br|\$|USD)\s*([\d,]+)", price_str, re.IGNORECASE)
    if p_match:
        currency_raw = p_match.group(1).upper()
        price_raw = p_match.group(2)
    else:
        p_match2 = re.search(r"([\d,]+)\s*(ETB|Birr|Br|\$|USD)", price_str, re.IGNORECASE)
        if p_match2:
            price_raw = p_match2.group(1)
            currency_raw = p_match2.group(2).upper()
        else:
            price_raw = price_str.strip()
            currency_raw = "ETB" if "ETB" in price_str else ""
    if currency_raw in ("BIRR", "BR"):
        currency_raw = "ETB"

    # Year
    year_raw = attrs_dict.get("Year of Manufacture") or attrs_dict.get("Year") or ""
    if not year_raw:
        y_match = re.search(r"\b(20[12]\d)\b", raw_title + " " + combined_desc)
        year_raw = y_match.group(1) if y_match else ""

    # Mileage
    mileage_raw = attrs_dict.get("Mileage") or ""
    if not mileage_raw:
        km_match = re.search(r"([\d,]+)\s*(?:km|KM)\b", combined_desc)
        mileage_raw = f"{km_match.group(1)} km" if km_match else ""

    # Condition
    condition_raw = attrs_dict.get("Condition") or ""
    if not condition_raw:
        c_match = re.search(r"\b(brand new|brand-new|new|local used|foreign used|used)\b", combined_desc.lower())
        condition_raw = c_match.group(1) if c_match else ""

    # Seller identity
    user_id = resolve_val(adv.get("user_id"), arr)
    seller_raw = f"Jiji Seller #{user_id}" if user_id else "Jiji Verified Seller"

    # Notes
    notes_parts = []
    if is_first and total_seen:
        notes_parts.append(f"n_total_seen={total_seen}")
    notes = "; ".join(notes_parts)

    raw_item_dict = {
        "id": adv_id,
        "guid": guid,
        "title": raw_title,
        "price_title": price_str,
        "listing_url": listing_url,
        "region_name": region,
        "short_description": short_desc,
        "attrs": attrs_dict,
        "user_id": user_id,
        "collected_on": today,
    }

    parsed_row = {
        "source_id": SOURCE_ID_VEHICLES,
        "listing_url": listing_url,
        "collected_on": today,
        "raw_title": raw_title,
        "make_raw": spec["make"],
        "model_raw": spec["model"],
        "year_raw": year_raw,
        "price_raw": price_raw,
        "currency_raw": currency_raw or "ETB",
        "mileage_raw": mileage_raw,
        "condition_raw": condition_raw,
        "location_raw": location_raw,
        "seller_raw": seller_raw,
        "posted_date_raw": today,
        "notes": notes,
    }

    return parsed_row, raw_item_dict


def parse_parts_advert(adv: dict, arr: list, spec: dict, today: str) -> tuple:
    """Parse raw advert dict into a structured parts listing and raw JSON dict."""
    adv_id = resolve_val(adv.get("id"), arr)
    guid = resolve_val(adv.get("guid"), arr)
    raw_title = resolve_val(adv.get("title"), arr) or ""
    price_str = resolve_val(adv.get("price_title"), arr) or ""
    rel_url = resolve_val(adv.get("url"), arr) or ""
    if isinstance(rel_url, str):
        rel_url = rel_url.split("?")[0]
    listing_url = f"{BASE_URL}{rel_url}" if rel_url.startswith("/") else rel_url

    region = resolve_val(adv.get("region_name"), arr) or "Addis Ababa"
    parent_region = resolve_val(adv.get("region_parent_name"), arr) or "Addis Ababa"
    location_raw = f"{region}, {parent_region}" if region and region != parent_region else (region or parent_region)

    short_desc = resolve_val(adv.get("short_description"), arr) or ""

    # Parse price and currency
    p_match = re.search(r"(ETB|Birr|Br|\$|USD)\s*([\d,]+)", price_str, re.IGNORECASE)
    if p_match:
        currency_raw = p_match.group(1).upper()
        price_raw = p_match.group(2)
    else:
        p_match2 = re.search(r"([\d,]+)\s*(ETB|Birr|Br|\$|USD)", price_str, re.IGNORECASE)
        if p_match2:
            price_raw = p_match2.group(1)
            currency_raw = p_match2.group(2).upper()
        else:
            price_raw = price_str.strip()
            currency_raw = "ETB" if "ETB" in price_str else ""
    if currency_raw in ("BIRR", "BR"):
        currency_raw = "ETB"

    # Condition
    c_match = re.search(r"\b(brand new|new|used)\b", (raw_title + " " + short_desc).lower())
    condition_raw = c_match.group(1).title() if c_match else "Brand New"

    # Seller identity
    user_id = resolve_val(adv.get("user_id"), arr)
    seller_raw = f"Jiji Parts Merchant #{user_id}" if user_id else "Lideta Parts Merchant"

    raw_item_dict = {
        "id": adv_id,
        "guid": guid,
        "title": raw_title,
        "price_title": price_str,
        "listing_url": listing_url,
        "region_name": region,
        "short_description": short_desc,
        "user_id": user_id,
        "collected_on": today,
    }

    parsed_row = {
        "source_id": SOURCE_ID_PARTS,
        "listing_url": listing_url,
        "collected_on": today,
        "raw_title": raw_title,
        "vehicle_raw": spec["vehicle"],
        "part_raw": spec["part"],
        "price_raw": price_raw,
        "currency_raw": currency_raw or "ETB",
        "condition_raw": condition_raw,
        "location_raw": location_raw,
        "seller_raw": seller_raw,
    }

    return parsed_row, raw_item_dict


def run_vehicle_collection(pages_per_query: int, delay: float) -> list:
    """Scrape genuine vehicle listings for all target EV models."""
    print("=== Collecting Jiji.com.et Vehicle Listings ===")
    today = date.today().isoformat()
    all_vehicle_rows = []
    seen_urls = set()

    for spec in TARGET_VEHICLES:
        q = spec["query"]
        print(f"\n--> Querying vehicles for: '{q}' ({spec['make']} {spec['model']})")
        total_seen_for_query = 0

        for page in range(1, pages_per_query + 1):
            url = f"{BASE_URL}/addis-ababa/cars?query={urllib.parse.quote(q)}"
            if page > 1:
                url += f"&page={page}"

            html = fetch_url(url)
            if not html:
                continue

            arr = parse_nuxt_payload(html)
            if not arr:
                print(f"    Page {page}: No Nuxt payload found.")
                continue

            total_count, adverts = extract_adverts_from_payload(arr)
            if page == 1:
                total_seen_for_query = total_count
                print(f"    Total adverts reported on platform: {total_count}")

            print(f"    Page {page}: retrieved {len(adverts)} listings")

            for i, adv in enumerate(adverts):
                is_first = (page == 1 and i == 0)
                row, raw_dict = parse_vehicle_advert(adv, arr, spec, today, total_seen_for_query, is_first)
                u = row["listing_url"]
                if not u or u in seen_urls:
                    continue
                seen_urls.add(u)

                # Save raw json audit file
                adv_id = raw_dict.get("id") or raw_dict.get("guid") or str(len(seen_urls))
                raw_json_path = RAW_DIR / f"vehicle_{adv_id}_{today.replace('-', '')}.json"
                with open(raw_json_path, "w", encoding="utf-8") as f:
                    json.dump(raw_dict, f, indent=2, ensure_ascii=False)

                all_vehicle_rows.append(row)

            time.sleep(delay)

    print(f"\nTotal unique vehicle listings scraped from Jiji: {len(all_vehicle_rows)}")
    return all_vehicle_rows


def run_parts_collection(pages_per_query: int, delay: float) -> tuple:
    """Scrape genuine parts listings and build search query logs."""
    print("\n=== Collecting Jiji.com.et Local Spare Parts Listings ===")
    today = date.today().isoformat()
    all_parts_rows = []
    search_logs = []
    seen_urls = set()

    for spec in TARGET_PARTS:
        q = spec["query"]
        print(f"\n--> Querying spare parts for: '{q}' ({spec['vehicle']} - {spec['part']})")
        total_seen_for_query = 0
        page_results_count = 0

        for page in range(1, pages_per_query + 1):
            url = f"{BASE_URL}/addis-ababa/car-parts-and-accessories?query={urllib.parse.quote(q)}"
            if page > 1:
                url += f"&page={page}"

            html = fetch_url(url)
            if not html:
                continue

            arr = parse_nuxt_payload(html)
            if not arr:
                continue

            total_count, adverts = extract_adverts_from_payload(arr)
            if page == 1:
                total_seen_for_query = total_count
                print(f"    Total adverts reported on platform: {total_count}")

            page_results_count += len(adverts)
            print(f"    Page {page}: retrieved {len(adverts)} parts listings")

            for adv in adverts:
                row, raw_dict = parse_parts_advert(adv, arr, spec, today)
                u = row["listing_url"]
                if not u or u in seen_urls:
                    continue
                # Filter out obvious non-part links if any
                if not u.endswith(".html"):
                    continue
                seen_urls.add(u)

                # Save raw json audit file
                adv_id = raw_dict.get("id") or raw_dict.get("guid") or str(len(seen_urls))
                raw_json_path = RAW_DIR / f"part_{adv_id}_{today.replace('-', '')}.json"
                with open(raw_json_path, "w", encoding="utf-8") as f:
                    json.dump(raw_dict, f, indent=2, ensure_ascii=False)

                all_parts_rows.append(row)

            time.sleep(delay)

        search_logs.append({
            "source_id": SOURCE_ID_PARTS,
            "vehicle_raw": spec["vehicle"],
            "part_raw": spec["part"],
            "query_text": q,
            "performed_on": today,
            "n_results_seen": total_seen_for_query if total_seen_for_query > 0 else page_results_count,
        })

    print(f"\nTotal unique local parts listings scraped from Jiji: {len(all_parts_rows)}")
    return all_parts_rows, search_logs


def update_vehicle_listings_csv(new_jiji_rows: list):
    """
    Remove all stale/synthetic Jiji rows (e.g. jiji.et) from vehicle_listings_raw.csv,
    preserve ADEY and GEZAT scraped rows, and append new genuine Jiji listings.
    """
    existing_other_rows = []
    if VEHICLES_CSV.exists():
        with open(VEHICLES_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for r in reader:
                # Discard old jiji.et or mock JIJI rows
                if r.get("source_id") == "S01" or "jiji.et" in r.get("listing_url", ""):
                    continue
                existing_other_rows.append(r)

    print(f"Retaining {len(existing_other_rows)} verified non-Jiji vehicle rows (ADEY/GEZAT).")

    # Assign clean record_ids
    combined_rows = []
    # 1. Existing verified rows (ADEY, GEZAT)
    for r in existing_other_rows:
        combined_rows.append(r)

    # 2. Add new genuine Jiji rows
    for i, r in enumerate(new_jiji_rows, 1):
        r["record_id"] = f"JIJI-{i:04d}"
        combined_rows.append(r)

    with open(VEHICLES_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=VEHICLE_COLUMNS)
        writer.writeheader()
        writer.writerows(combined_rows)

    print(f"Updated {VEHICLES_CSV}: total {len(combined_rows)} rows ({len(new_jiji_rows)} Jiji rows).")


def update_local_parts_csv(new_parts_rows: list):
    """
    Replace local_parts_listings_raw.csv with verified genuine scraped listings.
    """
    for i, r in enumerate(new_parts_rows, 1):
        r["record_id"] = f"LP-{i:04d}"

    with open(PARTS_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=PARTS_COLUMNS)
        writer.writeheader()
        writer.writerows(new_parts_rows)

    print(f"Updated {PARTS_CSV}: total {len(new_parts_rows)} genuine local parts listings.")


def update_search_log_csv(search_logs: list):
    """
    Write out local_search_log_raw.csv with genuine queries and live counts seen.
    """
    for i, r in enumerate(search_logs, 1):
        r["record_id"] = f"SL-{i:04d}"

    with open(SEARCH_LOG_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=SEARCH_LOG_COLUMNS)
        writer.writeheader()
        writer.writerows(search_logs)

    print(f"Updated {SEARCH_LOG_CSV}: total {len(search_logs)} search audit logs.")


def update_sources_log_csv():
    """
    Ensure sources_log.csv reflects the live operational domains (jiji.com.et).
    """
    if not SOURCES_CSV.exists():
        return

    rows = []
    with open(SOURCES_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        for r in reader:
            if r["source_id"] == "S01":
                r["source_name"] = "Jiji Ethiopia Vehicles (jiji.com.et)"
                r["url"] = "https://jiji.com.et/cars"
            elif r["source_id"] == "S08":
                r["source_name"] = "Jiji Ethiopia Spare Parts (jiji.com.et)"
                r["url"] = "https://jiji.com.et/car-parts-and-accessories"
            rows.append(r)

    with open(SOURCES_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Updated {SOURCES_CSV} with operational jiji.com.et URLs.")


def main():
    parser = argparse.ArgumentParser(description="Evidence-first scraper for Jiji Ethiopia.")
    parser.add_argument(
        "--mode",
        choices=["all", "vehicles", "parts", "search_log"],
        default="all",
        help="Collection mode (default: all)",
    )
    parser.add_argument("--pages", type=int, default=2, help="Pages to scrape per query (default: 2)")
    parser.add_argument("--delay", type=float, default=1.0, help="Polite request delay in seconds (default: 1.0)")
    args = parser.parse_args()

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    update_sources_log_csv()

    if args.mode in ("all", "vehicles"):
        v_rows = run_vehicle_collection(pages_per_query=args.pages, delay=args.delay)
        update_vehicle_listings_csv(v_rows)

    if args.mode in ("all", "parts", "search_log"):
        p_rows, s_logs = run_parts_collection(pages_per_query=args.pages, delay=args.delay)
        update_local_parts_csv(p_rows)
        update_search_log_csv(s_logs)

    print("\n[SUCCESS] Jiji scrape and audit log generation completed successfully.")


if __name__ == "__main__":
    main()
