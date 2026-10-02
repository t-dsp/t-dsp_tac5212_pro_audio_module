# ⚠️ REWORK REQUIRED — SD_IN / SD_OUT data lines swapped

**Date found:** 2026-06-18
**Status:** Confirmed on bench. Needs a board respin.

## The bug
On the TDM expansion-header interface between this daughtercard
(`t-dsp_tac5212_pro_audio_module`) and the host `teensy41_digital_audio_board`,
the audio **data lines SD_IN and SD_OUT (codec DIN / DOUT) are swapped.**

The Teensy's TX data (SAI1 OUT1A) lands on the codec's **DOUT** pin (an output)
instead of **DIN**, so the DAC starves → **silent output**. Clocks are fine, so
the codec's PLL still locks and everything *looks* healthy over I²C — which is
what made this sneaky.

## Proof
Bridging the header's SD_IN + SD_OUT pins together makes audio play (TX data now
also reaches DIN). Capture stays dead under the bodge because the codec's DOUT
driver contends with the Teensy TX on the shared node.

## Root cause
- Host header uses **odd/even** pin numbering: `DSP_DATA_IN = 7`, `DSP_DATA_OUT = 9`.
- This module's J1 uses **sequential** numbering: `DOUT = 4`, `DIN = 5`.
- Mixed numbering conventions across the mating connector crossed the pair.

## The fix
- **The host board is believed CORRECT.** Its header follows the **FreeDSP
  expansion-header standard.** → **TODO: confirm against the FreeDSP pinout spec
  before respinning.**
- **Respin THIS module** to swap its SD_IN / SD_OUT header pins so DIN/DOUT match
  the FreeDSP / host pinout.
- Not fixable in Teensy firmware: SAI1 pads are fixed (pin 7 = TX_DATA, pin 8 =
  RX_DATA) and can't swap roles. (Possible-but-unverified stopgap: a TAC5212
  pin-mux / INTF_CFG ASI reroute to receive DAC data on the DOUT pin.)

---

# Output filter: 10 R / 4.7 nF -> 220 R / 10 nF C0G (harsh top end)

**Date:** 2026-10-02
**Status:** Decided. BOM change only, no layout change. Bench-confirm first with a test cap at the jack.

R108 / R111 / R132 / R135 10 R -> 220 R (C22962); C113 / C114 / C120 / C122 4.7 nF -> 10 nF C0G
50 V (C85973). Corner moves from 3.4 MHz to 72 kHz so the DAC's out-of-band noise no longer
reaches the amplifier. Full write-up: `documentation/output-filter-change.md`.
