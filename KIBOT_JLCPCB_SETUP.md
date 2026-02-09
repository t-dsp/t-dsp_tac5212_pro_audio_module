# KiBot JLCPCB Setup Notes

Reference for generating JLCPCB-ready manufacturing files from KiCad using KiBot + Docker.

## Prerequisites

- **Docker**: Required (kicad-cli and KiBot are NOT installed locally)
- **Docker image**: `ghcr.io/inti-cmnb/kicad9_auto:latest` (bundles KiBot + KiCad 9)
- Pull it first: `docker pull ghcr.io/inti-cmnb/kicad9_auto:latest`

## Project Files

```
t-dsp_tac5212_pro_audio_module.kicad_pro
t-dsp_tac5212_pro_audio_module.kicad_pcb   (4-layer: F.Cu, In1.Cu, In2.Cu, B.Cu)
t-dsp_tac5212_pro_audio_module.kicad_sch   (LCSC field with 237 occurrences)
```

## Run Command

PowerShell:
```powershell
docker run --rm -v "${PWD}:/workspace" -w /workspace ghcr.io/inti-cmnb/kicad9_auto:latest kibot -c .kibot.yaml -b t-dsp_tac5212_pro_audio_module.kicad_pcb -e t-dsp_tac5212_pro_audio_module.kicad_sch
```

cmd.exe:
```cmd
docker run --rm -v "%cd%:/workspace" -w /workspace ghcr.io/inti-cmnb/kicad9_auto:latest kibot -c .kibot.yaml -b t-dsp_tac5212_pro_audio_module.kicad_pcb -e t-dsp_tac5212_pro_audio_module.kicad_sch
```

Git Bash (must disable MSYS path conversion):
```bash
MSYS_NO_PATHCONV=1 docker run --rm -v "${PWD}:/workspace" -w /workspace ghcr.io/inti-cmnb/kicad9_auto:latest kibot -c .kibot.yaml -b t-dsp_tac5212_pro_audio_module.kicad_pcb -e t-dsp_tac5212_pro_audio_module.kicad_sch
```

## Output

All files go to `JLCPCB/` directory:
- Gerber files (.gtl, .gbl, .g1, .g2, .gto, .gbo, .gts, .gbs, .gtp, .gbp, .gm1)
- Drill files (-PTH.drl, -NPTH.drl, drill maps)
- BOM CSV: columns = Comment, Designator, Footprint, LCSC Part #
- CPL CSV: columns = Designator, Val, Package, Mid X, Mid Y, Rotation, Layer
- ZIP containing everything above

## Issues to Fix Before Running

### 1. Malformed Reference Designators (BLOCKING)

KiBot will ERROR and skip BOM/CPL generation if any reference designator starts with a digit.

Two components have this problem:
- **`5V108`** — Device:NetTie_2, value "jumper", footprint project_fp:jumper_slice_1mm, DNP, at (57.15, 226.06) in schematic
- **`3V108`** — Device:NetTie_2, value "jumper", footprint project_fp:jumper_slice_1mm, DNP, at (116.84, 355.6) in schematic

**Fix in KiCad**: Rename these to valid designators (e.g. NT110, NT111 or JP110, JP111). KiCad will automatically update the associated net names. Do this in KiCad's schematic editor (not by text editing) so it handles all the cross-references properly.

Note: NT108 and NT109 already exist in the schematic (different net ties with footprint NetTie-2_SMD_Pad0.2mm), so don't use those numbers.

Gerbers generate fine from the PCB file regardless — only BOM/CPL are blocked.

### 2. Non-Blocking Warnings (cosmetic, won't prevent output)

**Trailing spaces in TAC5212EVM fields (W037):**
- D116: `LTST-C170KRKT ` (trailing space)
- R115, R118, R119: `ERJ-2GE0R00X ` (trailing space)
- Fix: Edit these fields in KiCad symbol properties, remove trailing space

**Missing library components (W043):**
- `proejct_lib:Jumper_NO_Small-Device_1` and `_2`
- Note the typo: "proejct" not "project"
- The whole project uses `proejct_lib` throughout — this is a legacy typo baked into the project

**Malformed component values (W020/W127):**
- C113, C114, C120, C122: `0.0047µF (4.7nF)` — KiBot can't parse this format. Consider `4.7nF`
- C124: `10UF confirm polarity` — extra text. Consider `10uF`
- R120: `2.21k ohm` — redundant "ohm". Consider `2.21k`

**BOM field conflicts (W004):**
These happen when KiBot groups components with same Value but different metadata. Not output-breaking but may indicate real BOM issues:
- C109,C112,C116 (0402) grouped with C128,C129 (0603) — same value "0.1uF" but different packages
- C124-C127: package mismatch C0805 vs C0603
- R120,R121,R126: different LCSC codes (C138019 vs C60491) — R126 may be a different value (100K vs 2.21k)

## .kibot.yaml Configuration

Place this file at the repo root as `.kibot.yaml`:

```yaml
# KiBot configuration for JLCPCB manufacturing outputs
# Project: T-DSP TAC5212 Pro Audio Module
# Board: 4-layer (F.Cu, In1.Cu, In2.Cu, B.Cu)

kibot:
  version: 1

filters:
  - name: only_jlc_parts
    comment: 'Only parts with LCSC code'
    type: generic
    include_only:
      - column: 'LCSC'
        regex: '^C\d+'

variants:
  - name: rotated
    comment: 'JLCPCB rotation correction'
    type: kibom
    variant: rotated
    pre_transform: _rot_footprint_jlcpcb

outputs:
  - name: JLCPCB_gerbers
    comment: Gerbers compatible with JLCPCB
    type: gerber
    dir: JLCPCB
    options:
      exclude_edge_layer: true
      exclude_pads_from_silkscreen: true
      plot_sheet_reference: false
      plot_footprint_refs: true
      plot_footprint_values: false
      force_plot_invisible_refs_vals: false
      tent_vias: true
      use_protel_extensions: true
      create_gerber_job_file: false
      disable_aperture_macros: true
      gerber_precision: 4.6
      use_gerber_x2_attributes: false
      use_gerber_net_attributes: false
      line_width: 0.1
      subtract_mask_from_silk: true
      inner_extension_pattern: '.g%n'
    layers:
      - F.Cu
      - B.Cu
      - In1.Cu
      - In2.Cu
      - F.SilkS
      - B.SilkS
      - F.Mask
      - B.Mask
      - F.Paste
      - B.Paste
      - Edge.Cuts

  - name: JLCPCB_drill
    comment: Drill files compatible with JLCPCB
    type: excellon
    dir: JLCPCB
    options:
      pth_and_npth_single_file: false
      pth_id: '-PTH'
      npth_id: '-NPTH'
      metric_units: true
      map: gerber
      route_mode_for_oval_holes: false
      output: "%f%i.%x"

  - name: JLCPCB_position
    comment: Pick and place file, JLCPCB style
    type: position
    dir: JLCPCB
    options:
      variant: rotated
      output: '%f_cpl_jlc.%x'
      format: CSV
      units: millimeters
      separate_files_for_front_and_back: false
      only_smd: true
      columns:
        - id: Ref
          name: Designator
        - Val
        - Package
        - id: PosX
          name: "Mid X"
        - id: PosY
          name: "Mid Y"
        - id: Rot
          name: Rotation
        - id: Side
          name: Layer

  - name: JLCPCB_bom
    comment: BoM for JLCPCB
    type: bom
    dir: JLCPCB
    options:
      output: '%f_bom_jlc.%x'
      exclude_filter: 'only_jlc_parts'
      ref_separator: ','
      columns:
        - field: Value
          name: Comment
        - field: References
          name: Designator
        - Footprint
        - field: 'LCSC'
          name: 'LCSC Part #'
      csv:
        hide_pcb_info: true
        hide_stats_info: true
        quote_all: true

  - name: JLCPCB
    comment: ZIP file for JLCPCB
    type: compress
    dir: JLCPCB
    options:
      files:
        - from_output: JLCPCB_gerbers
          dest: /
        - from_output: JLCPCB_drill
          dest: /
        - from_output: JLCPCB_position
          dest: /
        - from_output: JLCPCB_bom
          dest: /
```

## Key Config Notes

- **LCSC field name**: This project uses `LCSC` (not `LCSC#` which is the KiBot sample default)
- **Rotation filter**: `_rot_footprint_jlcpcb` is a KiBot built-in that adjusts component rotations to match JLCPCB's coordinate system
- **BOM filter**: `exclude_filter: 'only_jlc_parts'` confusingly acts as an include filter — it includes only parts with valid LCSC codes
- **Existing panel outputs**: `panel/jlcpcb_1x1/gerbers/` has manually-generated JLCPCB files (bom.csv, pos.csv) for reference

## Checklist

1. [ ] Fix `5V108` and `3V108` reference designators in KiCad (rename to NT110/NT111 or similar)
2. [ ] Place `.kibot.yaml` at repo root (copy from this file)
3. [ ] Run Docker command above
4. [ ] Verify JLCPCB/ output: gerbers, drill, BOM CSV, CPL CSV, ZIP
5. [ ] Optionally fix cosmetic warnings (trailing spaces, malformed values)
6. [ ] Commit JLCPCB/ output files to repo
