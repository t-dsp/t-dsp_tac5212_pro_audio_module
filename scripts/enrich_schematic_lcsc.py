#!/usr/bin/env python3
"""
Enrich KiCad schematic with LCSC manufacturer data.

For each component that has an LCSC field, fetches the manufacturer name and
part number from the LCSC API and writes LCSC_Manufacturer and LCSC_MPN
properties directly into the schematic file.

These fields then flow into any BOM output automatically via KiBot.

Usage:
    python scripts/enrich_schematic_lcsc.py t-dsp_tac5212_pro_audio_module.kicad_sch

A backup is created at <filename>.bak before modifying.
"""

import argparse
import json
import re
import shutil
import sys
import time
import urllib.request
import urllib.error


LCSC_API_URL = "https://wmsc.lcsc.com/ftps/wm/product/detail?productCode={}"
REQUEST_DELAY = 0.3


def fetch_lcsc_part(lcsc_code):
    """Fetch part details from LCSC API."""
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
                }
    except (urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
        print(f"  WARNING: Failed to fetch {lcsc_code}: {e}", file=sys.stderr)
    return None


def find_lcsc_codes(content):
    """Find all unique LCSC codes referenced in symbol instances."""
    # Match LCSC property values in symbol instances (not in lib_symbols)
    codes = set()
    for match in re.finditer(r'\(property\s+"LCSC"\s+"(C\d+)"', content):
        codes.add(match.group(1))
    return codes


def enrich_schematic(content, lcsc_data):
    """Insert LCSC_Manufacturer and LCSC_MPN properties after each LCSC property."""
    updated = 0
    skipped = 0

    def replace_lcsc_block(match):
        nonlocal updated, skipped
        full_match = match.group(0)
        lcsc_code = match.group(1)
        indent = match.group(2)

        # Skip if already enriched (check if LCSC_MPN follows soon after)
        after_pos = match.end()
        next_chunk = content[after_pos:after_pos + 300]
        if '"LCSC_MPN"' in next_chunk and '"LCSC_Manufacturer"' in next_chunk:
            skipped += 1
            return full_match

        part = lcsc_data.get(lcsc_code)
        if not part:
            return full_match

        # Build new properties matching the LCSC property's format
        new_props = (
            f'\n{indent}(property "LCSC_Manufacturer" "{part["manufacturer"]}"\n'
            f'{indent}\t(at 0 0 0)\n'
            f'{indent}\t(effects\n'
            f'{indent}\t\t(font\n'
            f'{indent}\t\t\t(size 1.27 1.27)\n'
            f'{indent}\t\t)\n'
            f'{indent}\t\t(hide yes)\n'
            f'{indent}\t)\n'
            f'{indent})\n'
            f'{indent}(property "LCSC_MPN" "{part["mpn"]}"\n'
            f'{indent}\t(at 0 0 0)\n'
            f'{indent}\t(effects\n'
            f'{indent}\t\t(font\n'
            f'{indent}\t\t\t(size 1.27 1.27)\n'
            f'{indent}\t\t)\n'
            f'{indent}\t\t(hide yes)\n'
            f'{indent}\t)\n'
            f'{indent})'
        )

        updated += 1
        return full_match + new_props

    # Match LCSC property blocks: captures the full property including its closing paren,
    # and the indentation level
    pattern = re.compile(
        r'(\(property\s+"LCSC"\s+"(C\d+)"\s*\n'   # opening + LCSC code
        r'(\s*)\(at\s[^)]+\)\s*\n'                  # (at ...) — captures indent
        r'\s*\(effects\s*\n'                         # (effects
        r'(?:\s*\([^)]*\)\s*\n)*'                    # nested items
        r'\s*\)\s*\n'                                # close effects
        r'\s*\))',                                    # close property
        re.MULTILINE
    )

    # Simpler approach: find each LCSC property and insert after it
    result = []
    pos = 0
    for match in re.finditer(r'(property "LCSC" "(C\d+)")', content):
        lcsc_code = match.group(2)

        # Find the end of this property block (matching parens)
        prop_start = content.rfind('(', 0, match.start())
        depth = 0
        i = prop_start
        while i < len(content):
            if content[i] == '(':
                depth += 1
            elif content[i] == ')':
                depth -= 1
                if depth == 0:
                    break
            i += 1
        prop_end = i + 1

        # Check if already enriched — look for LCSC_Manufacturer as the very next property
        next_chunk = content[prop_end:prop_end + 300]
        if '(property "LCSC_Manufacturer"' in next_chunk:
            skipped += 1
            result.append(content[pos:prop_end])
            pos = prop_end
            continue

        part = lcsc_data.get(lcsc_code)
        if not part:
            result.append(content[pos:prop_end])
            pos = prop_end
            continue

        # Detect indent from the LCSC property line
        line_start = content.rfind('\n', 0, prop_start) + 1
        indent = ''
        for ch in content[line_start:prop_start]:
            if ch in (' ', '\t'):
                indent += ch
            else:
                break

        new_props = (
            f'\n{indent}(property "LCSC_Manufacturer" "{part["manufacturer"]}"\n'
            f'{indent}\t(at 0 0 0)\n'
            f'{indent}\t(effects\n'
            f'{indent}\t\t(font\n'
            f'{indent}\t\t\t(size 1.27 1.27)\n'
            f'{indent}\t\t)\n'
            f'{indent}\t\t(hide yes)\n'
            f'{indent}\t)\n'
            f'{indent})\n'
            f'{indent}(property "LCSC_MPN" "{part["mpn"]}"\n'
            f'{indent}\t(at 0 0 0)\n'
            f'{indent}\t(effects\n'
            f'{indent}\t\t(font\n'
            f'{indent}\t\t\t(size 1.27 1.27)\n'
            f'{indent}\t\t)\n'
            f'{indent}\t\t(hide yes)\n'
            f'{indent}\t)\n'
            f'{indent})'
        )

        result.append(content[pos:prop_end])
        result.append(new_props)
        updated += 1
        pos = prop_end

    result.append(content[pos:])
    return ''.join(result), updated, skipped


def main():
    parser = argparse.ArgumentParser(
        description="Enrich KiCad schematic with LCSC manufacturer data"
    )
    parser.add_argument("schematic", help="Path to .kicad_sch file")
    parser.add_argument("--dry-run", action="store_true",
                        help="Show what would be done without modifying the file")
    args = parser.parse_args()

    with open(args.schematic, "r", encoding="utf-8") as f:
        content = f.read()

    # Find all LCSC codes
    lcsc_codes = find_lcsc_codes(content)
    print(f"Found {len(lcsc_codes)} unique LCSC codes in schematic\n")

    if not lcsc_codes:
        print("Nothing to do.")
        return

    # Fetch all parts from LCSC
    lcsc_data = {}
    for i, code in enumerate(sorted(lcsc_codes), 1):
        print(f"[{i}/{len(lcsc_codes)}] Fetching {code}...", end=" ")
        part = fetch_lcsc_part(code)
        if part:
            lcsc_data[code] = part
            print(f"{part['manufacturer']} / {part['mpn']}")
        else:
            print("FAILED")
        if i < len(lcsc_codes):
            time.sleep(REQUEST_DELAY)

    print(f"\nFetched {len(lcsc_data)}/{len(lcsc_codes)} parts successfully")

    # Enrich the schematic
    new_content, updated, skipped = enrich_schematic(content, lcsc_data)

    print(f"\nResults: {updated} properties added, {skipped} already enriched")

    if args.dry_run:
        print("\n(Dry run — no changes written)")
        return

    if updated == 0:
        print("No changes needed.")
        return

    # Backup and write
    backup = args.schematic + ".bak"
    shutil.copy2(args.schematic, backup)
    print(f"Backup saved to: {backup}")

    with open(args.schematic, "w", encoding="utf-8") as f:
        f.write(new_content)

    print(f"Schematic updated: {args.schematic}")
    print(f"\nOpen in KiCad to verify, then commit the changes.")


if __name__ == "__main__":
    main()
