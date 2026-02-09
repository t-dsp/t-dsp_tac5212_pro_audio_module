#!/usr/bin/env python3
"""
Verify and enrich BOM with LCSC part data.

Reads the generated generic BOM CSV, looks up each LCSC code via the LCSC API,
and produces a report showing manufacturer + MPN for each part. Optionally
outputs an enriched CSV with LCSC_Manufacturer and LCSC_MPN columns.

Usage:
    python scripts/verify_lcsc_bom.py manufacturing/BOM/t-dsp_tac5212_pro_audio_module_bom.csv
    python scripts/verify_lcsc_bom.py manufacturing/BOM/t-dsp_tac5212_pro_audio_module_bom.csv --output enriched_bom.csv
"""

import argparse
import csv
import json
import sys
import time
import urllib.request
import urllib.error


LCSC_API_URL = "https://wmsc.lcsc.com/ftps/wm/product/detail?productCode={}"
REQUEST_DELAY = 0.3  # seconds between API calls to be polite


def fetch_lcsc_part(lcsc_code):
    """Fetch part details from LCSC API. Returns dict or None on failure."""
    url = LCSC_API_URL.format(lcsc_code)
    req = urllib.request.Request(url, headers={"User-Agent": "KiCad-BOM-Verify/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("code") == 200 and data.get("result"):
                result = data["result"]
                return {
                    "manufacturer": result.get("brandNameEn", ""),
                    "mpn": result.get("productModel", ""),
                    "package": result.get("encapStandard", ""),
                    "description": result.get("productIntroEn", ""),
                    "stock": result.get("stockNumber", 0),
                    "lcsc_url": f"https://lcsc.com/product-detail/{lcsc_code}.html",
                }
    except (urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
        print(f"  WARNING: Failed to fetch {lcsc_code}: {e}", file=sys.stderr)
    return None


def main():
    parser = argparse.ArgumentParser(description="Verify BOM against LCSC catalog")
    parser.add_argument("bom_csv", help="Path to generic BOM CSV file")
    parser.add_argument("--output", "-o", help="Write enriched CSV with LCSC_Manufacturer and LCSC_MPN columns")
    args = parser.parse_args()

    with open(args.bom_csv, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames

    # Find the LCSC column
    lcsc_col = None
    for col in fieldnames:
        if col.strip().upper() in ("LCSC", "LCSC PART #", "LCSC PART#"):
            lcsc_col = col
            break

    if not lcsc_col:
        print("ERROR: No LCSC column found in BOM CSV", file=sys.stderr)
        sys.exit(1)

    # Find existing MPN column for comparison
    mpn_col = None
    mfr_col = None
    for col in fieldnames:
        if col.strip().upper() in ("MPN", "MANUFACTURER_PART_NUMBER"):
            mpn_col = col
        if col.strip().upper() in ("MANUFACTURER",):
            mfr_col = col

    # Collect unique LCSC codes
    lcsc_codes = set()
    for row in rows:
        code = row.get(lcsc_col, "").strip().strip('"')
        if code and code.startswith("C") and code[1:].isdigit():
            lcsc_codes.add(code)

    print(f"Found {len(lcsc_codes)} unique LCSC parts to verify\n")

    # Fetch all parts
    lcsc_data = {}
    for i, code in enumerate(sorted(lcsc_codes), 1):
        print(f"[{i}/{len(lcsc_codes)}] Fetching {code}...", end=" ")
        part = fetch_lcsc_part(code)
        if part:
            lcsc_data[code] = part
            print(f"{part['manufacturer']} / {part['mpn']} ({part['package']})")
        else:
            print("FAILED")
        if i < len(lcsc_codes):
            time.sleep(REQUEST_DELAY)

    # Report
    print(f"\n{'=' * 80}")
    print(f"BOM VERIFICATION REPORT")
    print(f"{'=' * 80}\n")

    missing_lcsc = 0
    mismatched = 0
    missing_mpn_in_sch = 0
    ok = 0

    for row in rows:
        code = row.get(lcsc_col, "").strip().strip('"')
        designator = row.get("Designator", "").strip().strip('"')
        value = row.get("Value", "").strip().strip('"')
        sch_mpn = row.get(mpn_col, "").strip().strip('"') if mpn_col else ""
        sch_mfr = row.get(mfr_col, "").strip().strip('"') if mfr_col else ""

        if not code or not code.startswith("C") or not code[1:].isdigit():
            missing_lcsc += 1
            print(f"  MISSING LCSC  {designator:12s}  {value}")
            continue

        part = lcsc_data.get(code)
        if not part:
            print(f"  FETCH FAILED  {designator:12s}  {value}  [{code}]")
            continue

        # Check for mismatches
        status = "OK"
        notes = []

        if sch_mpn and part["mpn"] and sch_mpn.upper() != part["mpn"].upper():
            status = "MISMATCH"
            notes.append(f"MPN: schematic={sch_mpn} vs LCSC={part['mpn']}")
            mismatched += 1
        elif not sch_mpn and part["mpn"]:
            status = "NO MPN"
            notes.append(f"LCSC has: {part['manufacturer']} / {part['mpn']}")
            missing_mpn_in_sch += 1
        else:
            ok += 1

        icon = {"OK": "+", "MISMATCH": "!", "NO MPN": "?"}[status]
        line = f"  {icon} {status:10s}  {designator:12s}  {code:10s}  {part['manufacturer']:20s}  {part['mpn']}"
        if notes:
            line += f"  -- {'; '.join(notes)}"
        print(line)

    print(f"\n{'=' * 80}")
    print(f"SUMMARY: {ok} OK, {missing_mpn_in_sch} missing MPN in schematic, "
          f"{mismatched} mismatched, {missing_lcsc} missing LCSC code")
    print(f"{'=' * 80}")

    # Optionally write enriched CSV
    if args.output:
        out_fields = list(fieldnames) + ["LCSC_Manufacturer", "LCSC_MPN"]
        with open(args.output, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=out_fields, quoting=csv.QUOTE_ALL)
            writer.writeheader()
            for row in rows:
                code = row.get(lcsc_col, "").strip().strip('"')
                part = lcsc_data.get(code, {})
                row["LCSC_Manufacturer"] = part.get("manufacturer", "")
                row["LCSC_MPN"] = part.get("mpn", "")
                writer.writerow(row)
        print(f"\nEnriched BOM written to: {args.output}")


if __name__ == "__main__":
    main()
