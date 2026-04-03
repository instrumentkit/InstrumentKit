# DOS1104 Command Matrix

## Header

- Hardware / firmware: `HANMATEK,DOS1104,24050102,V1.2.0`
- Transport: raw USB via PyUSB, `VID:PID 5345:1234`, bulk endpoints `0x01` / `0x81`
- Audit dates:
  - March 7, 2026: initial HANMATEK DOS1104 / vendor-app audit
  - March 8, 2026: OWON SDS1000 PDF + OWON app comparison
  - March 8, 2026: live probe passes for trigger, measurement, binary-data, AG/FFT, and `FILE` candidates
  - March 8, 2026: repeated isolated soak of `:DATA:WAVE:DEPMem:All?`
  - March 30, 2026: repeated fresh-session trigger-source / sweep follow-up probes during driver completion
- Probing method summary:
  - candidate commands came from the SDS-series PDF, the newer OWON SDS1000 PDF, community reports, and OWON / HANMATEK app JAR inspection
  - live validation uses [probe_dos1104.py](./probe_dos1104.py) with fresh USB sessions and post-command health checks
  - the driver is the source of truth for the public API
  - this matrix is the source of truth for verification status and evidence

## Driver-Facing Summary

### Promoted Into Driver

| Capability | Canonical command family | Public API surface | Notes |
| --- | --- | --- | --- |
| Identity / SCPI entry | `*IDN?`, `:SDSLSCPI#` | `identity`, `ensure_scpi_mode()` | `:SDSLSCPI#` is a transport handshake, not a normal user command family. |
| Run / stop acquisition | `:RUN`, `:STOP` | `run()`, `stop()` | Canonical public control path. |
| Conservative trigger control | `:TRIGger:STATUS?`, `:TRIGger:TYPE?`, `:TRIGger:SINGle:MODE`, `:TRIGger:SINGle:EDGE:*`, `:TRIGger:SINGle:VIDeo:SOURce`, `:TRIGger:SINGle:VIDeo:MODU?`, `:TRIGger:SINGle:VIDeo:SYNC?`, `:TRIGger:SINGle:VIDeo:LNUM?`, `:TRIGger:SINGle:HOLDoff`, `:TRIGger:SINGle:System`, `:TRIGger:SINGle:Sync`, `:TRIGger:SINGle:LineNum` | `trigger_status`, `trigger_type`, `single_trigger_mode` / `trigger_mode`, EDGE trigger properties and aliases, `trigger_holdoff`, VIDEO trigger queries plus verified setters, `read_trigger_configuration()`, `wait_for_trigger_status()` | `:TRIGger:TYPE` remains query-only. EDGE source writes are currently promoted only for `CH1`-`CH4` and `ACLine`; `EXT` / `EXT/5` stay query-only. `:TRIGger:SINGle:VIDeo:SOURce` write support is currently promoted only for `CH1` / `CH2`. `:TRIGger:SINGle:SWEEp` remains unpromoted because fresh-session `NORMal` readback was not reproducible. |
| Channel control | `:CH<n>:DISP`, `:CH<n>:COUP`, `:CH<n>:PROB`, `:CH<n>:SCAL`, `:CH<n>:OFFS`, `:CH<n>:POS`, `:CH<n>:INVErse` | `channel[n].display_enabled`, `coupling`, `probe_attenuation`, `scale`, `offset`, `position`, `inverted` | Long `:CHANnel...` forms are not the public path. |
| Acquisition / timebase | `:ACQUire:Mode`, `:ACQUire:average:num`, `:ACQUIRE:DEPMEM`, `:HORIzontal:Scale`, `:HORIzontal:OFFSET` | `acquisition_mode`, `acquisition_average_count`, `memory_depth`, `timebase_scale` | Canonical commands are the verified OWON-family spellings. |
| Scalar measurements | `:MEASUrement:CH<n>:<item>?` | `measure_*` methods | Old generic `:MEASure:<item>?` queries are not used. |
| Measurement blobs | `:MEAS?`, `:MEAS:CH<n>?` | `read_all_measurement_data()`, `read_measurement_data()`, snapshot helpers | Wrapper-style JSON-like payloads remain part of the stable driver because they are reproducible. |
| Measurement display | `:MEASUrement:DISPlay` | `measurement_display_enabled` | Stable public toggle. |
| Screen waveform capture | `:DATA:WAVE:SCREen:HEAD?`, `:DATA:WAVE:SCREEN:CH<n>?` | `read_waveform()`, `channel[n].read_waveform()` | Stable screen-data path. |
| Screen BMP capture | `:DATA:WAVE:SCREen:BMP?` | `read_screen_bmp()` | Stable binary tooling / driver path. |
| Structured deep-memory capture | `:DATA:WAVE:DEPMEM:HEAD?`, `:DATA:WAVE:DEPMEM:CH<n>?` | `read_deep_memory_metadata()`, `read_deep_memory_channel()`, `channel[n].read_deep_memory()` | Experimental / undocumented path. Not listed in the official SDS1000 SCPI PDF. |
| Bundled deep-memory capture | `:DATA:WAVE:DEPMem:All?` | `read_deep_memory_all()` | Official documented deep-memory path. Preferred public capture API. |
| Saved waveforms | `:SAVE:READ:HEAD?`, `:SAVE:READ:DATA <index>` | `list_saved_waveforms()`, `read_saved_waveform_data()`, `read_saved_waveform()` | Vendor-specific but reproducible and useful. |

### Verified On Hardware But Not Promoted

| Command family | Status | Why it is not public driver API |
| --- | --- | --- |
| `:TRIGger:SINGle:SWEEp` | Partial probe evidence only | `AUTO` query/write is benign, but a fresh-session `NORMal` probe read back as `AUTO`, so the family remains probe-only. |

## 2026-03-31 Bench Note

- In the `owon_esp32_trigger_jig_runner.py` comparison workflow, forcing
  `:TRIGger:SINGle:SWEEp NORMal` correlated with deep-memory calls timing out
  later in the same session.
- A later focused probe on the same bench showed the stronger failure mode:
  `:TRIGger:SINGle:SWEEp NORMal` combined with `single(stop_first=True)` could
  push the scope into USB timeout / pipe-error states even before the later
  waveform-read phase.
- A still narrower sweep-only probe then showed `:TRIGger:SINGle:SWEEp SINGle`
  is also unsafe on this bench: setting sweep to `SINGle` alone was enough to
  make the next `read_deep_memory_metadata()` call time out and contaminate the
  session.
- The same full comparison flow with sweep left unchanged restored
  `read_deep_memory_metadata()`, `read_deep_memory_channel()`, and
  `read_deep_memory_all()` on the bench, even though the corresponding screen
  waveform capture was still not aligned to the desired trigger event.
- Treat `SWEEp NORMal` as a real DOS1104 runner-path bug until reproduced away
  from this bench setup.

## 2026-04-01 Nuance

- A later one-command-per-session traced probe from the current confirmed safe
  state did **not** reproduce the earlier failure for:
  - `:TRIGger:SINGle:SWEEp SINGle`
  - `:TRIGger:SINGle:SWEEp NORMal`
- That successful probe started from:
  - `500 us/div`
  - `20K` memory depth
  - edge level `1.64 V`
  - status `AUTO` / `STOP`
- Artifact:
  - `doc/examples/artifacts/20260401/20260401_141727_unsafe_command_probe/`

Current wording should therefore be:

- non-`AUTO` sweep **can** poison deep-memory in some persisted scope states
- non-`AUTO` sweep is **not** proven universally toxic on this model

## 2026-04-01 Transition-Probe Nuance

- In the dedicated fresh-session transition probe, the first failing traced
  command on the latest non-strict run was not a sweep-set command.
- It was:
  - `:TRIGger:SINGle:SWEEp?`
- This happened even in the control case with no state-changing transition.
- Artifact:
  - `doc/examples/artifacts/20260401/20260401_154439_trigger_transition_probe/`

Current implication:

- the transition-probe flow is currently failing at baseline sweep observation
  before the candidate transition command is reached
- so that flow does not yet isolate the toxic state change itself

## 2026-04-01 Raw-SCPI Reconstructor Nuance

- A later raw-SCPI-only reconstructor was used to recreate the visible March 31
  good state without the high-level driver property setters.
- Artifact:
  - `doc/examples/artifacts/20260401/20260401_165321_good_state_reconstructor/`
- Result:
  - the reconstructed visible state reached:
    - `TRIG`
    - `500us`
    - `10K`
    - `1.64V`
  - but the next `:DATA:WAVE:DEPMEM:HEAD?` still timed out

This means:

- the problem is not solely in the driver property-wrapper layer
- pure raw SCPI can still poison deep-memory after reconstructing the visible
  "good" state

## 2026-04-01 Official `DEPMem:All?` Nuance

- A later probe used only the official documented deep-memory command:
  - `:DATA:WAVE:DEPMem:All?`
- Artifact:
  - `doc/examples/artifacts/20260401/20260401_195728_depmem_all_probe/`
- Result:
  - `DEPMem:All?` works from the safe AUTO baseline
  - but that successful bundle does not match the March 31 good captures
  - after raw visible-state reconstruction, `DEPMem:All?` still times out

So the current corrected position is:

- `DEPMem:All?` is the official command and should remain the preferred public
  API
- but the official command alone does not solve the March 31 reproduction issue

## 2026-04-02 Working Sequence

- A later raw sequence finally produced a clean end-to-end path for:
  - `:DATA:WAVE:SCREen:HEAD?`
  - `:DATA:WAVE:SCREen:CH1?`
  - `:DATA:WAVE:SCREen:CH2?`
  - `:DATA:WAVE:SCREen:BMP?`
  - `:DATA:WAVE:DEPMem:All?`
- Artifact:
  - `doc/examples/artifacts/20260402/20260402_155041_raw_sequence_probe/`

Working conditions from that run:

- configure scope first with raw SCPI
- include:
  - `:TRIGger:SINGle:SWEEp SINGle`
- do **not** send:
  - `:MEASUrement:ALL?`
  - `:STOP`
- start / reconfigure the ESP32 jig only **after** scope setup is complete
- wait for the signal to occur
- then read:
  - `:TRIGger:STATUS?` -> `STOP`
  - `:DATA:WAVE:SCREen:*`
  - `:DATA:WAVE:DEPMem:All?`

What this implies:

- `:MEASUrement:ALL?` is a poison command in the earlier failing path
- `:STOP` was also hurting deep-memory availability in that workflow
- `DEPMem:All?` appears to be available after a genuine triggered / frozen
  state, not just after scope setup alone
| `:TRIGger:SINGle:EDGE:SOURce EXT`, `:TRIGger:SINGle:EDGE:SOURce EXT/5` | Query replies, write/readback not reproducible on current DOS1104 bench | Keep parser support, but do not promote these write targets in the public driver. |
| `:AUTOscale?` | Replies | Observation only. |
| `:AUTOscale ON` | Accepted at write level, session healthy | Action-like command; no strong stateful readback model yet. |
| `:MEASUrement:ALL?` | Replies | Useful evidence path, but the driver already exposes reproducible measurement reads via better-scoped APIs. |
| `:MEASUrement:CH<n>?` | Replies | Blob-style query exists, but the driver already exposes item queries and wrapper-style blobs. |

Alias note:

- Where both long and short forms reply, this matrix keeps the long form as the canonical entry.
- Verified short aliases that are intentionally not given separate rows here include:
  - `:TRIG:TYPE?` for `:TRIGger:TYPE?`
  - `:ACQ:MODE?` for `:ACQUire:Mode?`
  - `:HOR:OFFS?` for `:HORIzontal:OFFSET?`
  - `:HOR:SCAL?` for `:HORIzontal:Scale?`
  - `:CH<n>:INV?` for `:CH<n>:INVErse?`

### Unsupported / Unsafe / Not Reproducible

| Family | Status | Practical rule |
| --- | --- | --- |
| `:RUNning RUN` / `:RUNning STOP` | Write accepted, behavior not trustworthy | Keep out of the public API. |
| Old generic measurement queries like `:MEASure:PERiod?` | Time out | Use `:MEASUrement:CH<n>:<item>?` or the wrapper-style blobs instead. |
| Extended measurement items `FRR`, `FRF`, `FFR`, `FFF`, `LRR`, `LRF`, `LFR`, `LFF`, `RPHAse` | Timed out while leaving the session healthy | Keep probe-only. |
| Delay measurements `:MEASUrement:CH<n>:RDELay?`, `:FDELay?` | Not reproducible | Exposed as unsupported in the driver. |
| Long `:CHANnel<n>:...` forms | Time out | Use the short `:CH<n>:...` family. |
| AG / `:FUNCtion` / `:CHANnel` generator control | No verified side effects or replies | Keep out of the driver. |
| `:FUNCtion:ARB:FILE?` | Times out, session remains healthy | Keep probe-only. |
| `:FILE:DOWNload USERn` | Times out, session remains healthy | Do not promote. |
| `:FILE:UPLoad <USERn>,<binary>` | Destructive, not sent to hardware | Keep out of the driver. |
| `:FILE:DELete <USERn>` | Destructive, not sent to hardware | Keep out of the driver. |
| FFT / `:FFT:*` | Not reproducible | Treat as unsupported remote-control feature. |
| `CALCulate` / `MATH` families | Not reproducible | Treat as unsupported remote-control feature. |
| Several SDS-family setters such as `:ACQ:TYPE`, `:ACQ:AVER`, `:ACQ:MDEP`, `:TIM:SCAL`, `:CH1:SCA`, `:TRIG:TYPE ALT`, `:TRIG VIDEO` | Read back unchanged or behaved inconsistently | Keep out of the public API. |

## Appendix / Evidence Log

### Workflow Rules

- New candidate command -> probe with [probe_dos1104.py](./probe_dos1104.py)
- If reproducible and useful -> record it here as verified
- If stable and worth exposing -> promote it into [dos1104.py](../../instruments/hanmatek/dos1104.py)
- Otherwise keep it in the appendix as experimental, unsupported, or unsafe

### Canonical Command Selection Rules

- Prefer one command spelling per feature in the public summary.
- If a long form times out but a short or vendor-specific form works, only the working canonical form appears in the promoted section.
- Aliases, wrapper quirks, and reverse-engineering discoveries belong in the appendix unless they are the best stable command family.

### Measurement Evidence

- The newer OWON SDS1000 PDF matched the DOS1104 measurement behavior better than the older SDS-series PDF.
- Stable scalar queries are the official per-channel forms such as:
  - `:MEASUrement:CH1:PERiod?`
  - `:MEASUrement:CH1:FREQuency?`
  - `:MEASUrement:CH1:AVERage?`
  - `:MEASUrement:CH1:MAX?`
  - `:MEASUrement:CH1:MIN?`
  - `:MEASUrement:CH1:VTOP?`
  - `:MEASUrement:CH1:VBASe?`
  - `:MEASUrement:CH1:VAMP?`
  - `:MEASUrement:CH1:PKPK?`
  - `:MEASUrement:CH1:CYCRms?`
  - `:MEASUrement:CH1:RTime?`
  - `:MEASUrement:CH1:FTime?`
  - `:MEASUrement:CH1:PDUTy?`
  - `:MEASUrement:CH1:NDUTy?`
  - `:MEASUrement:CH1:PWIDth?`
  - `:MEASUrement:CH1:NWIDth?`
  - `:MEASUrement:CH1:OVERshoot?`
  - `:MEASUrement:CH1:PREShoot?`
- Verified extra items:
  - `:MEASUrement:CH1:RISEedgenum?` -> `+E : 0->`
  - `:MEASUrement:CH1:FALLedgenum?` -> `-E : 0->`
  - `:MEASUrement:CH1:HARDfrequency?` -> `<2Hz->`
  - short-form aliases for the same three also reply
- Timed out while keeping the session healthy:
  - `FRR`, `FRF`, `FFR`, `FFF`, `LRR`, `LRF`, `LFR`, `LFF`, `RPHAse`
- The wrapper-style blob families remain important evidence and stay public because they are stable:
  - `:MEAS?`
  - `:MEAS:CH<n>?`
  - `:MEASUrement:ALL?`
  - `:MEASUrement:CH<n>?`

### Trigger / Autoscale Evidence

- Verified trigger queries include:
  - `:TRIGger:STATUS?`
  - `:TRIG:TYPE?`
  - `:TRIGger:SINGle:EDGE?`
  - `:TRIGger:SINGle:EDGE:SOURce?`
  - `:TRIGger:SINGle:EDGE:COUPling?`
  - `:TRIGger:SINGle:EDGE:SLOPe?`
  - `:TRIGger:SINGle:EDGE:LEVel?`
  - `:TRIGger:SINGle:VIDeo:SOURce?`
  - `:TRIGger:SINGle:VIDeo:MODU?`
  - `:TRIGger:SINGle:VIDeo:SYNC?`
  - `:TRIGger:SINGle:VIDeo:LNUM?`
- Verified read/write cases include:
  - `:TRIGger:SINGle:MODE VIDEO`
  - `:TRIGger:SINGle:HoldOff 200ns`
  - `:TRIGger:SINGle:System PAL`
  - `:TRIGger:SINGle:Sync FIELD`
  - `:TRIGger:SINGle:LineNum 2`
  - March 30 follow-up: repeated fresh-session `:TRIGger:SINGle:VIDeo:SOURce CH1` / `CH2` write-readback passed
- March 30 follow-up probe:
  - `:TRIGger:SINGle:EDGE:SOURce ACLine` wrote and read back cleanly
  - `:TRIGger:SINGle:EDGE:SOURce EXT` read back as `CH1`
  - `:TRIGger:SINGle:EDGE:SOURce EXT/5` read back as `CH1`
  - EDGE source writes therefore stay promoted only for `CH1`-`CH4` and `ACLine`
  - `:TRIGger:SINGle:SWEEp AUTO` read back cleanly
  - `:TRIGger:SINGle:SWEEp NORMal` read back as `AUTO`
  - `:TRIGger:SINGle:SWEEp` therefore remains unpromoted
- `:AUTOscale?` replied `ON->` during the probe run.
- `:AUTOscale ON` was accepted at the USB write level and left the session healthy, but it still lacks a strong promotion-ready verification model.

### Acquisition / Timebase Evidence

- The driver-facing canonical spellings come from the verified OWON-family dialect:
  - `:ACQUire:Mode`
  - `:ACQUire:average:num`
  - `:ACQUIRE:DEPMEM`
  - `:HORIzontal:Scale`
  - `:HORIzontal:OFFSET`
- Short aliases `:ACQ:MODE?`, `:HOR:OFFS?`, and `:HOR:SCAL?` also reply.
- Several older SDS-style setters were rejected by readback:
  - `:ACQ:TYPE <mode>`
  - `:ACQ:AVER <count>`
  - `:ACQ:MDEP <depth>`
  - `:TIM:SCAL <scale>`
  - `:ACQUIRE:DEPMEM 10K`

### Channel Command Evidence

- Stable canonical public family:
  - `:CH<n>:DISP`
  - `:CH<n>:COUP`
  - `:CH<n>:PROB`
  - `:CH<n>:SCAL`
  - `:CH<n>:OFFS`
  - `:CH<n>:POS`
  - `:CH<n>:INVErse`
- `:CH<n>:INV` also replies and works as an alias.
- `:CH<n>:SCA` did not verify cleanly and is not canonical.
- Long `:CHANnel<n>:...` spellings timed out and are not used by the driver.

### Screen, Deep-Memory, and Save-Read Evidence

- `:DATA:WAVE:SCREen:BMP?` is real.
  - The scope returns a 4-byte DOS1104 prefix followed by a normal BMP file starting with `BM`.
- Structured deep-memory path was promoted from reverse engineering, not from
  the official PDF:
  - `:DATA:WAVE:DEPMEM:HEAD?`
  - `:DATA:WAVE:DEPMEM:CH<n>?`
  - current status: experimental / undocumented
- Bundled deep-memory path is also real:
  - `:DATA:WAVE:DEPMem:All?`
  - observed structure:
    - outer 4-byte little-endian body length
    - inner 4-byte little-endian metadata JSON length
    - metadata JSON
    - one length-prefixed raw channel block per bundled channel
  - repeated isolated soak on March 8, 2026: `8/8` successful fresh-session runs
  - observed stable payload:
    - total reply length `41162`
    - metadata JSON length `1138`
    - `DATATYPE = WAVEDEPMEM`
    - `SAMPLE.DATALEN = 5000`
    - channel block lengths `10000, 10000, 10000, 10000`
- Later live hardware also showed a smaller valid bundle with only the displayed channels present, so the parser maps blocks to displayed channels first when that count matches.
- `SAVE:READ` family is real:
  - `:SAVE:READ:HEAD?`
  - `:SAVE:READ:DATA <index>`
  - the `HEAD?` payload needs small syntax cleanup before JSON parsing

### `.bin` / `SPBXDS` Evidence

- The OWON app’s normal “Get Data” flow on this install does not use `:DATA:WAVE:DEPMem:All?`.
- With `USBRequestCMDidx=0`, the app uses:
  - `:DATA:WAVE:SCREEN:HEAD?`
  - `:DATA:WAVE:SCREEN:CH<n>?`
- The app packages that into an `SPBXDS` container.
- `SAVE:READ:*` is a separate saved-waveform packaging path.
- The official PDF documents:
  - `:DATA:WAVE:SCREen:HEAD?`
  - `:DATA:WAVE:SCREen:CH<x>?`
  - `:DATA:WAVE:SCREen:BMP?`
  - `:DATA:WAVE:DEPMem:All?`
  and does **not** document `:DATA:WAVE:DEPMEM:HEAD?`.

### AG / `:FUNCtion` / `:FILE` Evidence

- The OWON PDF documents a generator subsystem built around the current generator channel:
  - `:CHANnel CH1|CH2`
  - `:FUNCtion`
  - `:FUNCtion:FREQuency`
  - `:FUNCtion:AMPLitude`
  - `:FUNCtion:ARB:*`
  - `:FILE:*`
- Live DOS1104 results:
  - `:CHANnel?`, `:CHANnel:CH1?`, `:CHANnel:CH2?`, `:FUNCtion?`, `:FUNCtion:FREQuency?`, and `:FUNCtion:AMPLitude?` timed out
  - sending `:CHANnel CH1` / `CH2` first did not make those queries work
  - ad hoc channel-qualified guesses such as `:FUNCtion:CH1:FREQuency?` also timed out
  - `:FUNCtion:ARB:FILE?` timed out but left the session healthy
- `:FILE` subsystem:
  - documented by the OWON PDF as arbitrary-waveform internal-memory control
  - `:FILE:DOWNload USER1`, `USER4`, and `USER10` all timed out while leaving the session healthy
  - `:FILE:UPLoad` and `:FILE:DELete` were not sent to hardware because they are destructive internal-memory write/delete operations
- App JAR finding:
  - the installed OWON app contains `:FILE:UPLoad` and `:FILE:Download` strings in `UploadAgSavedWFFrame`
  - no matching `:FILE:DELete` string was found in the installed OWON app during this pass

### FFT / CALC / MATH Evidence

- The older SDS-series PDF documents an `:FFT:*` subsystem.
- The newer OWON SDS1000 PDF does not document FFT, CALC, or MATH remote-control families.
- Live DOS1104 probes timed out for:
  - `:FFT:display?`
  - `:FFT:ch?`
  - `:FFT:SOURce?`
  - `:FFT:WINDow?`
  - `:FFT:FORMat?`
  - `:FFT:HCENter?`
  - `:FFT:ZONE?`
  - `:CALCulate:MATH?`
  - `:CALCulate:TRANsform?`
  - `:CALCulate:TRANsform:FREQuency?`
  - `:MATH?`
  - `:MATH:FFT?`
- Setter-only guesses such as `:FFT:display ON` and `:FFT:ch CH1` were accepted at the USB write level but produced no verified readback path or visible promoted behavior.
