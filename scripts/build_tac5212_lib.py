"""Build the T-DSP TAC5212 module's module footprints and symbol pin list (KiCad 10 bundled python).

Usage:
  "C:/Program Files/KiCad/10.0/bin/python.exe" scripts/build_tac5212_lib.py

Backplane side of the core method (t-dsp_core/scripts/build_core_module_fp.py). The module itself keeps its own
footprint (project_fp:audio_module_board_outline_50x34.5_e1, board_outline108, pads 1-52); this only writes what a
backplane needs, with the module's top-left corner as origin:

  lib_fp/t-dsp_tac5212_pro_audio_module.pretty/T-DSP_TAC5212_Socket   backplane footprint, outline on F.SilkS
  lib_sch/symbol_pins.json                                            pin list for the T-DSP_TAC5212 symbol

Pad numbers are "<header>-<pin>", at the module's pad positions snapped to one 2.54 mm grid (moves of 0.01 mm or
less). Module pad n -> J1-n (n 1-20), J2-(n-20) (21-36), J2-17 (48), J3-(n-36) (37-44), H1-H4 (49-52).
H1-H4 are the module's four plated 2.2 mm holes (M2 standoffs); on the module they tie to AGND / DGND through
E108 / E109 / G117 / G118.
"""
import os, sys, json
import pcbnew

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LIB = os.path.join(ROOT, 'lib_fp', 't-dsp_tac5212_pro_audio_module.pretty')
LIBNAME = 't-dsp_tac5212_pro_audio_module'
NAMES = ('T-DSP_TAC5212_Socket',)
TITLE = 'T-DSP TAC5212'
KEYWORDS = 'T-DSP TAC5212 codec module backplane'

# Module outline (module coordinates): 41.34 x 26.46 mm, origin top-left.
W, H = 41.34, 26.46
# Grid origin: every header pin sits on a 2.54 mm grid starting at (1.965, 1.795) from the board's top-left corner.
GX, GY = 1.965, 1.795
P = 2.54


def g(i, j):
    """Grid point i columns right, j rows down from the grid origin."""
    return round(GX + i * P, 4), round(GY + j * P, 4)


# Header definitions: name, pins, grid (i, j) of pin 1, grid step to the next odd pin, grid offset of each even pin
# from the odd pin before it (None = single row).
HEADERS = [
    ('J1', 20, (1, 9), (0, -1), (-1, 0)),   # DSP IO 2x10, left edge: odd pins right column, rows run up (-Y)
    ('J2', 17, (6, 1), (1, 0), (0, -1)),    # analog 2x9 along the top: odd = signal row, even = AGND row; 17 = MICBIAS
    ('J3', 8, (6, 9), (1, 0), None),        # codec I2C / GPIO 1x8 along the bottom
]
PIN_NAMES = {
    'J1': ['EN', 'NC', '5V', '3V3_IO', 'NC', 'GNDD', 'DIN', 'GNDD', 'DOUT', 'GNDD', 'BCLK', 'GNDD', 'LRCK', 'GNDD',
           'DSP_SDA', 'GNDD', 'DSP_SCL', 'GNDD', 'MCLK', 'GNDD'],
    'J2': ['OUT1P', 'AGND', 'OUT1M', 'AGND', 'OUT2P', 'AGND', 'OUT2M', 'AGND', 'IN1P', 'AGND', 'IN1M', 'AGND',
           'IN2P', 'AGND', 'IN2M', 'AGND', 'MICBIAS'],
    'J3': ['SCL', 'SDA', 'GNDD', 'GPIO1', 'GPIO2', 'GPO1', 'GPI1', 'GNDD'],
}
PAD_SIZE, PAD_DRILL = 1.7, 1.0
SILK_OFF = 1.33
CRT_OFF = 1.80
# M2 mounting holes, module coordinates: plated, 3.2 mm pad, 2.2 mm drill (unchanged from the old footprint).
HOLES = [('H1', 12.12, 1.80, 'AGND'), ('H2', 40.06, 1.80, 'AGND'), ('H3', 12.12, 24.66, 'DGND'),
         ('H4', 40.06, 24.66, 'DGND')]
HOLE_PAD, HOLE_DRILL = 3.2, 2.2
HOLE_CRT_R = 2.15

# 3D model: the module board exported to STEP with the module's top-left corner as origin (export_step(), run with
# --step or when the file is missing), saved next to the footprints. Only the socket footprint carries it: on the
# module itself it would draw the board a second time. It sits STACK_Z above the backplane (8.5 mm female socket +
# 2.5 mm male-header spacer); option parts (DNP) are left out.
STEP = 'T-DSP_TAC5212.step'
STEP_PCB = os.path.join(ROOT, 't-dsp_tac5212_pro_audio_module.kicad_pcb')
STEP_ORIGIN = (84.8325, 97.9450)  # module top-left on the module board
STACK_Z = 11.0
# leave DNP parts out of the model (option parts)
STEP_NO_DNP = True


def export_step():
    import subprocess, sys
    cli = os.path.join(os.path.dirname(sys.executable), 'kicad-cli.exe')
    out = os.path.join(LIB, STEP)
    # older footprints name their models with KiCad 6-9 path variables: point them at KiCad 10's 3D library
    lib3d = os.path.join(os.path.dirname(os.path.dirname(sys.executable)), 'share', 'kicad', '3dmodels')
    old = sum((['-D', 'KICAD%d_3DMODEL_DIR=%s' % (v, lib3d)] for v in (6, 7, 8, 9)), [])
    r = subprocess.run([cli, 'pcb', 'export', 'step', '--force', '--subst-models'] + (['--no-dnp'] if STEP_NO_DNP else []) + old +
                       ['--user-origin', '%.4fx%.4fmm' % STEP_ORIGIN, '-o', out, STEP_PCB], capture_output=True, text=True)
    print('STEP', out, '%.1f MB' % (os.path.getsize(out) / 1e6) if os.path.exists(out) else (r.stdout + r.stderr)[-800:])


def add_model(fp):
    m = pcbnew.FP_3DMODEL()
    m.m_Filename = '${KIPRJMOD}/lib_fp/t-dsp_tac5212_pro_audio_module.pretty/' + STEP
    m.m_Offset = pcbnew.VECTOR3D(0, 0, STACK_Z)
    fp.Models().push_back(m)

mm, MM = pcbnew.ToMM, pcbnew.FromMM


def vec(x, y):
    return pcbnew.VECTOR2I(MM(x), MM(y))


def header_pads(name, n, start, step, even):
    i0, j0 = start
    out = []
    for k in range(1, n + 1):
        if even is None:
            i, j = i0 + step[0] * (k - 1), j0 + step[1] * (k - 1)
        else:
            r = (k - 1) // 2
            i, j = i0 + step[0] * r, j0 + step[1] * r
            if k % 2 == 0:
                i, j = i + even[0], j + even[1]
        x, y = g(i, j)
        out.append(dict(ref=name, num=str(k), x=x, y=y))
    return out


def all_pads():
    pads = []
    for h in HEADERS:
        pads += header_pads(*h)
    seen = {}
    for p in pads:
        key = (p['x'], p['y'])
        if key in seen:
            raise SystemExit('pad collision: %s-%s and %s' % (p['ref'], p['num'], seen[key]))
        seen[key] = '%s-%s' % (p['ref'], p['num'])
        if not (0 < p['x'] < W and 0 < p['y'] < H):
            raise SystemExit('pad off the module: %s-%s' % (p['ref'], p['num']))
    return pads


def rect(fp, layer, x0, y0, x1, y1, width):
    s = pcbnew.PCB_SHAPE(fp, pcbnew.SHAPE_T_RECT)
    s.SetStart(vec(x0, y0)); s.SetEnd(vec(x1, y1))
    s.SetLayer(layer); s.SetWidth(MM(width))
    fp.Add(s)


def line(fp, layer, x0, y0, x1, y1, width):
    s = pcbnew.PCB_SHAPE(fp, pcbnew.SHAPE_T_SEGMENT)
    s.SetStart(vec(x0, y0)); s.SetEnd(vec(x1, y1))
    s.SetLayer(layer); s.SetWidth(MM(width))
    fp.Add(s)


def text(fp, layer, s, x, y, size=1.0):
    t = pcbnew.PCB_TEXT(fp)
    t.SetText(s); t.SetPosition(vec(x, y)); t.SetLayer(layer)
    t.SetTextSize(vec(size, size)); t.SetTextThickness(MM(size * 0.15))
    fp.Add(t)


def build(name, pads, socket):
    fp = pcbnew.FOOTPRINT(None)
    fp.SetFPID(pcbnew.LIB_ID(LIBNAME, name))
    fp.SetAttributes(pcbnew.FP_THROUGH_HOLE)
    desc = ('T-DSP TAC5212 codec module, %.2f x %.2f mm, %d header pins (%s) on one 2.54 mm grid, %d plated M2 holes '
            '(H1-H4). Origin = module top-left corner. ' % (W, H, len(pads), ', '.join(h[0] for h in HEADERS), len(HOLES)))
    desc += ('Backplane side: fit female 2.54 mm sockets matching each header.' if socket else
             'Module side: fit male 2.54 mm headers; board edge comes from the module board.')
    fp.SetLibDescription(desc)
    fp.SetKeywords(KEYWORDS)
    if socket:
        add_model(fp)
    fp.Reference().SetText('A**'); fp.Reference().SetPosition(vec(W / 2, -1.5)); fp.Reference().SetLayer(pcbnew.F_SilkS)
    fp.Value().SetText(name); fp.Value().SetPosition(vec(W / 2, H + 1.5)); fp.Value().SetLayer(pcbnew.F_Fab)

    groups = {}
    for p in pads:
        pad = pcbnew.PAD(fp)
        pad.SetNumber('%s-%s' % (p['ref'], p['num']))
        pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        pad.SetShape(pcbnew.F_Cu, pcbnew.PAD_SHAPE_RECT if p['num'] == '1' else pcbnew.PAD_SHAPE_CIRCLE)
        pad.SetSize(pcbnew.F_Cu, vec(PAD_SIZE, PAD_SIZE))
        pad.SetDrillSize(vec(PAD_DRILL, PAD_DRILL))
        pad.SetLayerSet(pcbnew.PAD.PTHMask())
        pad.SetFPRelativePosition(vec(p['x'], p['y']))
        fp.Add(pad)
        gr = groups.setdefault(p['ref'], [1e9, 1e9, -1e9, -1e9, None])
        gr[0], gr[1], gr[2], gr[3] = min(gr[0], p['x']), min(gr[1], p['y']), max(gr[2], p['x']), max(gr[3], p['y'])
        if p['num'] == '1':
            gr[4] = (p['x'], p['y'])

    # M2 mounting holes, plated: the module bonds its grounds to the standoffs through them
    for num, hx, hy, _ in HOLES:
        h = pcbnew.PAD(fp)
        h.SetNumber(num)
        h.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        h.SetShape(pcbnew.F_Cu, pcbnew.PAD_SHAPE_CIRCLE)
        h.SetSize(pcbnew.F_Cu, vec(HOLE_PAD, HOLE_PAD))
        h.SetDrillSize(vec(HOLE_DRILL, HOLE_DRILL))
        h.SetLayerSet(pcbnew.PAD.PTHMask())
        h.SetFPRelativePosition(vec(hx, hy))
        fp.Add(h)
        c = pcbnew.PCB_SHAPE(fp, pcbnew.SHAPE_T_CIRCLE)
        c.SetCenter(vec(hx, hy)); c.SetEnd(vec(hx + HOLE_CRT_R, hy))
        c.SetLayer(pcbnew.F_CrtYd); c.SetWidth(MM(0.05))
        fp.Add(c)

    # outline: F.Fab on both, F.SilkS on the socket (mainboard) version
    rect(fp, pcbnew.F_Fab, 0, 0, W, H, 0.1)
    if socket:
        rect(fp, pcbnew.F_SilkS, 0, 0, W, H, 0.15)
        text(fp, pcbnew.F_SilkS, TITLE, W / 2 + 4, H / 2, 1.5)
    # per-header silk, courtyard and pin-1 mark
    for ref, (x0, y0, x1, y1, p1) in groups.items():
        rect(fp, pcbnew.F_SilkS, x0 - SILK_OFF, y0 - SILK_OFF, x1 + SILK_OFF, y1 + SILK_OFF, 0.12)
        rect(fp, pcbnew.F_CrtYd, x0 - CRT_OFF, y0 - CRT_OFF, x1 + CRT_OFF, y1 + CRT_OFF, 0.05)
        rect(fp, pcbnew.F_Fab, x0 - 1.27, y0 - 1.27, x1 + 1.27, y1 + 1.27, 0.1)
        px, py = p1
        # pin-1 mark: short silk tick outside the header outline, on the side nearest pin 1
        if px == x1 and x1 != x0:
            line(fp, pcbnew.F_SilkS, x1 + SILK_OFF + 0.5, py, x1 + SILK_OFF + 0.5, py + 0.01, 0.4)
        elif px == x0 and x1 != x0:
            line(fp, pcbnew.F_SilkS, x0 - SILK_OFF - 0.5, py, x0 - SILK_OFF - 0.5, py + 0.01, 0.4)
        else:
            line(fp, pcbnew.F_SilkS, x0 - SILK_OFF - 0.5, py, x0 - SILK_OFF - 0.5, py + 0.01, 0.4)
        text(fp, pcbnew.F_Fab, ref, (x0 + x1) / 2, (y0 + y1) / 2, 0.8)
    return fp


def symbol_pins():
    """pin list per header for the module symbol: 2-row headers put odd pins left / even pins right, single rows go
    down the left side (same as T-DSP_Core); the holes are one more unit, H"""
    units = []
    for name, n, start, step, even in HEADERS:
        pins = []
        for k in range(1, n + 1):
            nm = PIN_NAMES[name][k - 1]
            if even is not None:
                row = (k - 1) // 2
                x, ang = (-20.32, 0) if k % 2 else (20.32, 180)
            else:
                row, x, ang = k - 1, -15.24, 0
            pins.append(dict(number='%s-%d' % (name, k), name=nm, type='no_connect' if nm == 'NC' else 'passive',
                             x=x, y=round(17.78 - row * 2.54, 2), angle=ang, length=2.54))
        units.append(dict(header=name, pins=pins))
    units.append(dict(header='H', pins=[dict(number=num, name=nm, type='passive', x=-15.24,
                                             y=round(17.78 - k * 2.54, 2), angle=0, length=2.54)
                                        for k, (num, _, _, nm) in enumerate(HOLES)]))
    return units


def main():
    pads = all_pads()
    if not os.path.isdir(LIB):
        os.makedirs(LIB)
    if '--step' in sys.argv or not os.path.exists(os.path.join(LIB, STEP)):
        export_step()
    io = pcbnew.PCB_IO_MGR.FindPlugin(pcbnew.PCB_IO_MGR.KICAD_SEXP)
    for name in NAMES:
        io.FootprintSave(LIB, build(name, pads, True))
        print('wrote', name, len(pads), 'pads,', len(HOLES), 'holes')
    for h in HEADERS:
        hp = header_pads(*h)
        print('  %-3s %2d  pin1 (%.3f, %.3f)' % (h[0], h[1], hp[0]['x'], hp[0]['y']))

    out = os.path.join(ROOT, 'lib_sch', 'symbol_pins.json')
    json.dump(symbol_pins(), open(out, 'w'), indent=1)
    print('wrote', out)


if __name__ == '__main__':
    main()
