# OWON Runner Refactor Plan 2026-04-02

## Goal

Split `owon_esp32_trigger_jig_runner.py` into:

- a stable example path
- debug / validation helpers

The stable path should be the only place that end users need to look for the
recommended capture workflow.

## Stable Path

The stable supported flows are:

- `--capture-edge-pretty`
- `--capture-edge-pretty-burst`

These use:

- the proven April 2 raw setup ordering
- the documented deep-memory path `:DATA:WAVE:DEPMem:All?`
- screen `SCREen:*` capture
- BMP capture
- SCPI trace logging

## Debug Path

The remaining debug-oriented functionality should be clearly isolated:

- `--verify-pulse`
- `--verify-slope`
- `--verify-edge-arming`
- `--validate-waveforms`
- state trace snapshots
- experimental deep-memory HEAD / CH comparisons

## Proposed File Split

### Keep as main entry point

- `doc/examples/owon_esp32_trigger_jig_runner.py`

Responsibilities:

- CLI parsing
- dispatch between stable and debug modes
- top-level artifact directory creation

### New stable helper module

- `doc/examples/_owon_capture_stable.py`

Move here:

- promoted stable presets
- ESP32 configure-after-setup helper
- raw screen capture helpers for:
  - `SCREen:HEAD?`
  - `SCREen:CH1?`
  - `SCREen:CH2?`
  - `SCREen:BMP?`
- documented deep-memory helper for:
  - `DEPMem:All?`
- report / JSON composition for:
  - `--capture-edge-pretty`
  - `--capture-edge-pretty-burst`

### New debug helper module

- `doc/examples/_owon_capture_debug.py`

Move here:

- state trace helpers
- verification-case builders
- waveform-truth capture
- legacy comparison helpers
- experimental trigger-arming matrix support

### New shared helper module

- `doc/examples/_owon_capture_common.py`

Move here:

- trace context dataclass
- JSONL writer
- HTML rendering helpers
- waveform CSV writer
- comparison HTML renderer
- sample-rate formatting

## Deep-Memory Policy

### Supported

- `read_deep_memory_all()`
- `read_deep_memory_all_raw()`

### Experimental

- `read_deep_memory_metadata()`
- `read_deep_memory_channel()`

Rules:

- supported path appears in examples and stable runner output
- experimental path may remain in driver/tests for bench work
- experimental path should not be used in stable example docs

## Cleanup Tasks

1. Remove `.ino` references from `owon_esp32_trigger_jig.md`
2. Keep only PlatformIO as the maintained firmware path
3. Mark experimental deep-memory helpers explicitly in code and example docs
4. Keep `owon_safe_scope_smoke.py` and `owon_scope_state_dump.py`, but avoid
   making undocumented deep-memory commands part of their default path

## Suggested Order

1. Extract common render / CSV / comparison helpers
2. Extract stable capture path
3. Update runner to delegate stable modes to the new module
4. Extract debug helpers
5. Reduce the main runner to CLI + dispatch

## Acceptance Criteria

- stable users only need the main runner plus the jig note
- stable captures still produce:
  - BMP
  - screen plots
  - `depmem_all_summary.json`
  - `depmem_all_raw.bin`
  - `waveform_comparison.html`
  - `scpi_trace.jsonl`
- debug logic remains available but is clearly separated
- no stable doc recommends undocumented deep-memory HEAD / CH commands
