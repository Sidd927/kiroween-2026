# Windows 11 ARM VM print-capture runbook (NOT yet executed)

**Status:** not run. This Mac has no UTM and no Windows image. Downloading Windows and accepting
Microsoft's licence terms is the team's decision, so nothing here was done automatically.
What *was* verified on this Mac is in `../../TEST_RESULTS.md` §5: a Python RAW client (E1–E9) and the
real macOS CUPS spooler (C1–C2).

The Windows test answers the questions CUPS cannot:
- What does the **Generic / Text Only** driver do to the bytes (line endings, page breaks, Notepad headers and footers)?
- Do our bindings still accept the result?
- How does the Windows spooler retry when the listener is offline?

## 0. Prerequisites (team)
- UTM for macOS, plus a Windows 11 ARM image (evaluation or Insider). Licence terms are accepted by you.
- UTM network mode **Shared Network**. On the Mac, find the host address the VM can reach: `ifconfig bridge100`
  (often `192.168.64.1` [unverified]). Find the VM's own IP with `ipconfig` inside Windows.

## 1. Start the receiver side on the Mac
Run each command in its own terminal, from `poc/`:

```bash
.venv/bin/python experiments/print_capture/fake_printer.py --port 9101 --out runtime/win/fake_printer
```

```bash
.venv/bin/python -m spoolgeist.capture --host 192.168.64.1 --port 9100 --forward 127.0.0.1:9101 --spool runtime/win/spool --allow <VM-IP>
```

The listener binds only to the VM-facing interface and accepts only the VM's IP. Never bind to `0.0.0.0` on a public network.

## 2. Create the capture printer in Windows (admin PowerShell)
```powershell
Add-PrinterPort -Name "SPOOLGEIST_9100" -PrinterHostAddress "192.168.64.1" -PortNumber 9100
Add-PrinterDriver -Name "Generic / Text Only"
Add-Printer -Name "Spoolgeist Capture" -DriverName "Generic / Text Only" -PortName "SPOOLGEIST_9100"
Get-PrinterPort -Name "SPOOLGEIST_9100" | Format-List *     # expect Protocol = RAW (1), PortNumber 9100
```
If `Add-PrinterDriver` fails, record the error. Microsoft is phasing out third-party drivers (Windows Protected Print), and you should check that this inbox driver is still available on your build [unverified].

## 3. Experiments (record every result in TEST_RESULTS.md §5)
Copy `data/corpus/test/A/A-11001-clean.json` → extract `text` into `A.txt` (synthetic) and copy it into the VM.

| # | Action in Windows | What to record | Pass if |
|---|---|---|---|
| W1 | `Get-Content A.txt -Raw \| Out-Printer -Name "Spoolgeist Capture"` | captured bytes vs source (`shasum`, `diff`), detected format, ACCEPT/REJECT | job captured; differences understood; binding ACCEPTs or REJECTs with a clear reason (never a wrong value) |
| W2 | Notepad → File → Print → "Spoolgeist Capture" | the same, plus Notepad's header/footer text | as W1. If headers or footers break the rule, that's a real finding |
| W3 | Share the printer as `SpoolCap`, then `NET USE LPT1: \\localhost\SpoolCap` and `copy /b A.txt LPT1:` (the DOS-era path) | bytes identical to the source? | byte-identical capture (raw pass-through) |
| W4 | Stop the listener → print → wait 60 s → start the listener | queue status text, retry interval, number of captured jobs | job delivered **once** after restart |
| W5 | Pause the printer mid-job / power-cycle the listener during a large job | incomplete + complete jobs in `runtime/win/spool` | partial job quarantined; one complete job processed |
| W6 (optional) | Point `--forward` at a real network printer `IP:9100` | paper output identical to printing directly | identical printout |
| W7 (optional) | On the Mac: `ippeveprinter -D file:///tmp/ipp -f application/pdf,image/pwg-raster "SG IPP"`; add it in Windows as an IPP printer | the format Windows' IPP class driver sends | recorded (expected PDF or PWG Raster; the PoC refuses both) |

## 4. Clean up
```powershell
Remove-Printer -Name "Spoolgeist Capture"; Remove-PrinterPort -Name "SPOOLGEIST_9100"
```
