# T-DSP TAC5212 Pro Audio Module

**Part of the [T-DSP](https://t-dsp.com) open modular audio platform.**

A compact (50mm x 34.5mm) stereo audio codec module built around the **Texas Instruments TAC5212** high-performance audio ADC.

## About T-DSP

T-DSP is an open modular audio platform designed for musicians, engineers, and developers who want powerful digital signal processing in a flexible, hackable format. Built around a high-performance Teensy microcontroller and a high-quality codec, T-DSP combines studio-quality audio with a growing library of open-source modules for mixing, synthesis, effects, and more.

Whether you're building a custom digital mixer, crafting a unique instrument, or prototyping audio products, T-DSP gives you the tools to bring your ideas to life -- no proprietary systems, no licensing walls, just clean, creative freedom.

Join the community, contribute to the library, or grab a module and start patching. Learn more at [t-dsp.com](https://t-dsp.com).

## Overview

This codec module provides stereo ADC and DAC conversion and is one of the core building blocks of the T-DSP platform. It is designed as a **chip-on-board module** -- a complete, self-contained audio codec that solders directly onto a user-designed backplane PCB, just like any other component. A KiCad footprint is provided so you can drop the module into your own backplane design, add whatever jacks and connectors your application needs, and build a custom audio device without dealing with codec layout or analog design.

## Audio Capabilities

### Inputs (2 stereo channels)
- Line-level (consumer -10dBV or professional +4dBu)
- Instrument-level (guitar/bass)
- Microphone (dynamic with up to 60dB internal gain)
- 100k ohm input impedance, DC-coupled
- Input voltage range: +/-5V max

### Outputs (2 stereo channels)
- Headphone drive (16-300 ohm, ~50mW @ 32 ohm)
- Consumer line out (-10dBV)
- Professional balanced output (+4dBu)
- 10 ohm output impedance, +/-3.3V output swing

## Digital Interface

- **I2S/PCM** audio data (DIN, DOUT, BCLK, LRCK, MCLK)
- **I2C** control bus for codec register configuration
- **GPIO** pins for additional control and sensing

## Modular Architecture

The module connects to your backplane via **2.54mm (0.1") header pins** (52 pins total), organized into functional groups. Headers can be male/female for a removable connection, or soldered permanently with straight pins:

- **DSP IO** (20 pins) -- digital audio (I2S), I2C control, MCLK, and power. Also available as a 20-pin ribbon header for off-board connection via standard ribbon cable.
- **Analog IO** (16 pins) -- stereo input and output pairs with analog ground references.
- **GPIO** (8 pins) -- additional I2C, general-purpose IO, and digital ground.
- **Power** (8 pins) -- 5V, 3.3V, MIC_BIAS, and ground lines.

![T-DSP TAC5212 Pro Audio Module Pinout](documentation/T-DSP-TAC5212-PRO-AUDIO-MODULE-PINOUT.jpg)

### Backplane Integration

A KiCad footprint for the module is included in `/lib_fp/`, allowing you to import it directly into your own backplane PCB design. You handle the jacks, connectors, and mechanical layout on your backplane -- the module takes care of codec, filtering, and power regulation.

### Multi-Module Chaining

Because the digital outputs are buffered on each module, multiple modules can run together on the same digital bus. You can daisy-chain modules in two ways:

- **On the backplane** -- route the digital bus as board traces between multiple module footprints.
- **Via ribbon cable** -- use a ribbon cable with multiple taps to connect up to 4 modules per chain.

System designers only need to focus on analog signal routing. The buffered digital bus works reliably over longer distances and across many modules.

## On-Board Circuitry

- LDO regulator for clean 3.3V analog power
- Buffered digital outputs for reliable backplane distribution
- TVS protection on audio outputs
- Ferrite bead RF filtering on audio inputs
- Solder jumpers for I2C address configuration
- Power indicator LED

## Project Files

| Directory | Contents |
|-----------|----------|
| `/3d_models/` | 3D models for PCB components and enclosure |
| `/documentation/` | TAC5212 datasheets and evaluation module docs |
| `/gerber/` | Manufacturing-ready Gerber output files |
| `/lib_fp/` | Custom KiCad footprint libraries |
| `/lib_sch/` | Custom KiCad schematic symbol libraries |
| `/panel/` | Panelized board layouts for production |

## License

This project is licensed under the [Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International (CC BY-NC-SA 4.0)](https://creativecommons.org/licenses/by-nc-sa/4.0/).

You are free to share and adapt this work for non-commercial purposes, as long as you give appropriate credit and distribute any derivatives under the same license.
