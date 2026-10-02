# DAC output filter change (next respin / rework of built units)

**Date:** 2026-10-02
**Status:** Decided, not yet applied to the schematic. BOM change only, no layout change.

## Symptom

Harsh, fatiguing top end from the DAC outputs. Present on headphones, much worse through a
power amplifier and speakers. The module is wired straight to the amplifier; the backplanes
(`t-dsp_XLR_2x2`, `t-dsp_RCA_8x8`) only add a coupling capacitor before the jack, so nothing
between the codec and the amplifier filters the DAC's out-of-band noise.

## Cause

The output network on every DAC leg is 10 R in series and 4.7 nF to AGND. Its corner is about
3.4 MHz, so the delta-sigma noise from a few hundred kHz upward reaches the cable and the
amplifier input unattenuated. Some amplifier input stages fold that back into the audio band.

## Current network (identical on all four legs)

| Position | OUT1P / OUT1M / OUT2P / OUT2M | Value | Fitted |
|---|---|---|---|
| Series | R108 / R111 / R132 / R135 | 10 R, 0603 | yes |
| Parallel to series R | R127 / R128 / R129 / R130 | 0603, "DNP" | no |
| Shunt to AGND | C113 / C114 / C120 / C122 | 4.7 nF, 0603 | yes |
| Coupling link | R161 / R162 / R163 / R134 | 0 R, 0603 | yes |
| Coupling cap (alternative to the link) | C110 / C117 / C121 / C123 | 47 uF, EIA-3528 | no |
| ESD at the connector | D108 / D109 / D110 / D111 | TPD1E10B06, 0402 | yes |

Connector: board_outline108 pins 21 (OUT1P+), 23 (OUT1M+), 25 (OUT2P+), 27 (OUT2M+), AGND on
22 / 24 / 26 / 28. "Earth" is the analog ground net.

## The change

| References | Now | Change to | Part | LCSC |
|---|---|---|---|---|
| R108, R111, R132, R135 | 10 R | **220 R** 1 %, 0603 | Uniroyal 0603WAF2200T5E | C22962 (Basic) |
| C113, C114, C120, C122 | 4.7 nF | **10 nF C0G 50 V**, 0603 | Murata GRM1885C1H103JA01D | C85973 |

Everything else stays as it is: 0 R links fitted, 47 uF caps not fitted, R127-R130 not fitted,
ESD diodes unchanged.

Result: first-order corner at 72 kHz. -0.3 dB at 20 kHz, -9 dB at 200 kHz, -23 dB at 1 MHz,
-32 dB at 3 MHz. 220 R into a 47 k amplifier input loses 0.04 dB; into 10 k, 0.19 dB.

Why 220 R / 10 nF rather than 100 R / 22 nF: same corner, and the 10 nF C0G is a stocked
Murata part with a verified LCSC listing. Use C0G/NP0 (not X7R) and matched parts: X7R adds
voltage-dependent distortion, and a P/M mismatch converts common-mode noise to signal on a
balanced input.

## Before ordering: bench test on a current unit

1. Solder a 100 nF film cap across an RCA jack (tip to sleeve) on the RCA backplane, or 47 nF
   across XLR pins 2 and 3 on the XLR backplane. With the module's 10 R this makes a corner near
   160 kHz.
2. If the harshness disappears, the BOM change above is the production fix.
3. Remove the test cap once the module is changed. A large cap at the jack together with the
   220 R would start eating the top octave (100 nF with 220 R is a 7 kHz corner).

## Backplane notes (no change required for this fix)

- XLR 2x2: 470 uF electrolytic per leg to XLR pins 2 and 3. Polar: positive end toward the
  module (the codec pin sits at about 1.5 V DC). Not phantom-safe: 48 V phantom on a mixer input
  charges those caps the wrong way and reaches the module. Add 100 R per leg and a clamp before
  that board goes to anyone else.
- RCA 8x8: Nichicon UEP 10 uF bipolar on the P leg, M leg open. Fine as is.
- Optional second pole at the jack on a future backplane spin: 100 R in series and 2.2 nF to
  AGND right at the jack (XLR: 2.2 nF across pins 2 and 3 plus 1 nF from each leg to pin 1).
  Only needed if a trace of edge remains after the module change.

## Single-ended and balanced use

The same build serves both. Balanced: take P and M. Single-ended: take P and AGND, leave M
open. If a build is to be DC-blocked on the module instead of on the backplane, fit the 47 uF
on the EIA-3528 pads (B-case polymer tantalum, 47 uF 6.3 V, positive end toward the codec) and
remove the corresponding 0 R link.
