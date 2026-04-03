# ESP32 Trigger Test Jig For OWON SDS1104 / DOS1104

This note describes a very small bench jig for validating the SDS1104 / DOS1104
trigger families that now look real on hardware but are not fully exercised in
the front-panel UI:

- `PULSe`
- `SLOPe`
- `EDGE:COUPling HF`
- `EDGE:SOURce ACLine`

The goal is not RF-grade timing accuracy. The goal is to generate clean,
repeatable, low-voltage bench signals that are good enough to validate trigger
behavior at easy time scales such as `10 us`, `50 us`, `100 us`, and `1 ms`.

## Hardware

Use any ordinary 3.3 V ESP32 dev board with exposed GPIOs.

Preferred firmware path:

- PlatformIO project: [owon_esp32_trigger_jig_pio/platformio.ini](./owon_esp32_trigger_jig_pio/platformio.ini)
- PlatformIO source: [owon_esp32_trigger_jig_pio/src/main.cpp](./owon_esp32_trigger_jig_pio/src/main.cpp)
- Command-line scope runner: [owon_esp32_trigger_jig_runner.py](./owon_esp32_trigger_jig_runner.py)

Recommended parts:

- 1 x ESP32 dev board
- 2 x `330 ohm` series resistors
- 1 x `1 kohm` series resistor
- 1 x `100 kohm` resistor, optional
- 4 x capacitors for the slope node
  - `4.7 nF`
  - `22 nF`
  - `47 nF`
  - `470 nF`
- jumper wires
- optional small breadboard

Use `10x` probes if possible. They load the signal less and make the RC slope
node behave more predictably.

## Exact Wiring

Common ground:

- ESP32 `GND` -> scope ground clips for all channels used

CH1 direct pulse output:

- ESP32 `GPIO18` -> `330 ohm` -> scope `CH1` probe tip

CH2 slope output node:

- ESP32 `GPIO19` -> `1 kohm` -> node `SLOPE_OUT`
- `SLOPE_OUT` -> scope `CH2` probe tip
- `SLOPE_OUT` -> selected capacitor -> `GND`
- optional: `SLOPE_OUT` -> `100 kohm` -> `GND`

CH3 frame marker, optional:

- ESP32 `GPIO21` -> `330 ohm` -> scope `CH3` probe tip

Do not connect the scope probe tips directly to `3V3`.

### RC Values For Approximate Slope Times

The CH2 node is a first-order RC edge shaper. The approximate `10%` to `90%`
rise or fall time is about `2.2 * R * C`.

With `R = 1 kohm`:

- `4.7 nF` -> about `10 us`
- `22 nF` -> about `48 us`
- `47 nF` -> about `103 us`
- `470 nF` -> about `1.03 ms`

This is good enough for conservative trigger validation.

## What Each Channel Is For

`CH1`

- direct digital pulse train
- use this for `PULSe` trigger tests

`CH2`

- RC-shaped version of a square wave
- use this for `SLOPe` trigger tests

`CH3`

- optional burst marker
- useful when checking where one pulse frame starts

## Scope Setup Suggestions

For pulse tests on `CH1`:

- source: `CH1`
- trigger mode: `PULSe`
- coupling: start with `DC`
- slope or direction: match the pulse edge you care about

For slope tests on `CH2`:

- source: `CH2`
- trigger mode: `SLOPe`
- set upper and lower levels around the middle of the RC swing, for example
  `0.8 V` and `2.4 V`
- set `TIME` near the expected slope time from the RC table

For `HF` coupling tests:

- start from ordinary `EDGE` mode on `CH1`
- compare trigger behavior with `DC`, `AC`, and `HF`
- `HF` is easiest to see later with a signal that has slow baseline movement
  plus a fast edge component

For `ACLine`:

- the ESP32 jig does not generate line-synchronous AC
- use a separate isolated low-voltage AC source later, for example a small
  transformer secondary
- never connect mains directly to the scope or to the ESP32

## Minimal Test Procedure

### Pulse Trigger

The firmware emits a repeating burst on `CH1` with pulse widths:

- `10 us`
- `50 us`
- `100 us`
- `1000 us`

Suggested checks:

- set `PULSe:TIME 50us`
- try `PULSe:SIGN >`, `<`, and `=`
- verify the scope prefers the matching pulse width or class

### Slope Trigger

Pick one capacitor on `CH2`, for example:

- `22 nF` for about `50 us`

Suggested checks:

- set `SLOPe:TIME 50us`
- try `SLOPe:SIGN >`, `<`, and `=`
- try `SLOPe:SLOPe POS` and `NEG`
- verify that triggering changes when you swap the capacitor to another
  timescale

### HF Coupling

Start with the CH1 pulse source.

Suggested checks:

- compare `EDGE:COUPling DC`, `AC`, and `HF`
- later, if needed, add a slow baseline modulation source and confirm `HF`
  ignores it better than `DC`

## Limitations

- `delayMicroseconds()` on ESP32 is good enough for bench trigger validation,
  not for calibrated timing metrology
- the RC slope node is only approximately linear
- for sub-microsecond work, use RP2040 PIO or a function generator instead

## Firmware

The maintained firmware path is the PlatformIO project:

- [owon_esp32_trigger_jig_pio/platformio.ini](./owon_esp32_trigger_jig_pio/platformio.ini)
- [owon_esp32_trigger_jig_pio/src/main.cpp](./owon_esp32_trigger_jig_pio/src/main.cpp)

## PlatformIO Build And Upload

From the repo root:

```powershell
cd doc/examples/owon_esp32_trigger_jig_pio
pio run
pio run -t upload
pio device monitor
```

## Command-Line Runner

The Python runner configures the ESP32 over serial, configures the scope,
captures a BMP screenshot, saves waveform CSV files, and writes a Markdown and
JSON report into a timestamped artifact directory.

Basic pulse example:

```powershell
python doc/examples/owon_esp32_trigger_jig_runner.py `
  --esp-port COM7 `
  --profile pulse `
  --pulse-mode burst `
  --pulse-trigger-time-us 50 `
  --capture-channels 1 `
  --timebase-s-div 0.00005
```

Basic slope example:

```powershell
python doc/examples/owon_esp32_trigger_jig_runner.py `
  --esp-port COM7 `
  --profile slope `
  --slope-trigger-time-us 50 `
  --slope-upper-v 2.4 `
  --slope-lower-v 0.8 `
  --capture-channels 2 `
  --timebase-s-div 0.001
```

Pretty stable edge capture:

```powershell
python doc/examples/owon_esp32_trigger_jig_runner.py `
  --esp-port COM7 `
  --capture-edge-pretty
```

Waveform truth validation capture:

```powershell
python doc/examples/owon_esp32_trigger_jig_runner.py `
  --esp-port COM7 `
  --capture-edge-pretty `
  --validate-waveforms
```

The runner saves artifacts under:

```text
doc/examples/artifacts/YYYYMMDD_HHMMSS_<label>/
```

Each run currently records:

- `edge_single_scope_screen.bmp` or `pulse_run_scope_screen.bmp`, depending on profile
- `ch1_waveform.csv`
- `ch2_waveform.csv`
- `ch3_waveform.csv`, only if you explicitly request `CH3`
- `waveform_truth.json`, when `--validate-waveforms` is used
- `report.md`
- `report.json`

The report includes:

- the exact ESP32 command settings used
- scope trigger state and timebase
- simple waveform statistics such as sample count and `Vpp`
- the artifact file names for traceability

The waveform-truth / debug capture can record these APIs side by side:

- `read_screen_bmp()`
- `read_waveform_metadata()`
- `read_waveform(channel)`
- `channel[n].read_waveform()`
- `read_deep_memory_all()`

Experimental / undocumented deep-memory APIs still exist in the driver for
bench work, but they are not the promoted deep-memory path:

- `read_deep_memory_metadata()`
- `read_deep_memory_channel(channel)`

Treat the native BMP as the visual source of truth until the voltage conversion
for the waveform APIs is fully validated on the DOS1104 bench.

## DOS1104 Sweep Interaction

Bench findings on March 31, 2026 with the connected DOS1104:

- `SWEEp AUTO` plus `single(stop_first=True)` kept deep-memory reads working,
  but the screen capture often stayed in an `AUTO`-style flat acquisition.
- `SWEEp NORMal` plus `single(stop_first=True)` produced the desired `CH1`
  trigger event on screen, but deep-memory calls later in the same session
  frequently timed out.
- A more focused probe then showed the stronger failure mode: `SWEEp NORMal`
  combined with `single(stop_first=True)` could drive the scope into USB
  timeout / pipe-error states even before the later waveform-read phase.
- A later sweep-only probe showed `SWEEp SINGle` is also unsafe on this bench:
  simply setting sweep to `SINGle` was enough to make the next
  `read_deep_memory_metadata()` call time out and contaminate the session.
- The current `--capture-edge-pretty` preset therefore does not force
  any non-`AUTO` sweep mode.

This is a real bench bug or bench-specific interaction, not just a WebGUI
presentation problem.
