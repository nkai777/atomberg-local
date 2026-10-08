# Atomberg Local
 
Local control for **Atomberg smart BLDC fans** in Home Assistant — over **Wi-Fi and Bluetooth**, with **no cloud, no account, and no internet required**.
 
[![hacs][hacs-badge]][hacs] [![Validate](https://github.com/allusv/atomberg-local/actions/workflows/validate.yml/badge.svg)](https://github.com/allusv/atomberg-local/actions/workflows/validate.yml)
 
> **This is a fork** of [allusv/atomberg-local](https://github.com/allusv/atomberg-local), maintained here with a few additions while the upstream repository awaits maintainer review. All credit for the original design, the Wi-Fi/BLE discovery and fallback architecture, and the bulk of this integration goes to **[@allusv](https://github.com/allusv)**.
 
## Changes in this fork
 
**Merged from [upstream PR #1](https://github.com/allusv/atomberg-local/pull/1) by [@FlashWreck](https://github.com/FlashWreck)** (open, unmerged at the time of writing) — thank you for this fix:
- Fixed a bug where setting fan speed also forced `power: true` in the same command, which the fan's firmware silently ignored (it only acts on the first key in a command) — speed changes were failing as a result.
- More robust `:5625`/`:5600` datagram parsing: tries plain JSON first, falls back to hex-encoded JSON, and validates presence-beacon device IDs properly.
- `send_command` now reads the fan's direct UDP response on `:5600`, confirming state in well under a second instead of waiting up to 1.5s for a separate `:5625` broadcast.
**Added in this fork** (telemetry fields decoded through hands-on BLE reverse-engineering, confirmed against real logged data and the official Atomberg app):
- **Motor voltage** and **motor current** sensors — confirmed via several days of logged real-world data; both track fan speed with correlation r ≈ 0.91, and both are forced to `0` when the fan reports `power: off`, since the fan's own firmware otherwise keeps reporting the last-running value indefinitely rather than refreshing them.
- **Runtime hours** sensor — the fan's own lifetime run-hour counter, read directly off the device (not derived or estimated); cross-checked against the Atomberg app's own "hours run" figure and found to match.
- **Board/ambient temperature** sensor — included as a lower-confidence diagnostic entity (disabled by default). It consistently reports a plausible ambient-range value, essentially uncorrelated with motor current, which is more consistent with ambient temperature than motor heat — but this hasn't been independently verified against a reference thermometer.
## Features
 
- 🔍 **Discovers every fan** on your network **and** over Bluetooth — and tells you which are **provisioned** (on Wi-Fi) vs **un-provisioned** (Bluetooth-only, not yet set up).
- 📶 **Wi-Fi + Bluetooth, automatically.** Provisioned fans are controlled over Wi-Fi (fast, push state). Fans not on Wi-Fi are controlled over **Bluetooth** — no setup required.
- 🔁 **Automatic fallback.** If a fan's Wi-Fi is weak, disconnected, or a command isn't confirmed, it **falls back to Bluetooth** transparently.
- 🧩 **Self-reconciling.** A fan first seen over Bluetooth and later provisioned onto Wi-Fi is recognised as the **same device** (keyed by its `device_id`) — no duplicates, it just gains Wi-Fi.
- 🏷️ **Model recognition** from the fan's series code (e.g. `S2 → Renesa Elite`).
- 🎛️ **Full control:** power, speed (1–6), sleep mode, off-timer (Off / 1 / 2 / 3 / 6 h), and the LED underlight (on/off, brightness, and warm/cool/daylight — where the model supports them).
- 🔌 **Diagnostic telemetry:** motor voltage, motor current, lifetime runtime hours, and (optional) board temperature.
- ☁️ **100% local** — verified with all cloud/proxy tooling switched off.
## Requirements
 
- Home Assistant **2024.8** or newer.
- A **Bluetooth adapter** configured in Home Assistant (for BLE discovery, fallback, and Bluetooth-only fans). Wi-Fi-only use works without one.
- Home Assistant on the **same subnet** as your fans, with **UDP ports 5600 and 5625** not blocked (used for local control and state).
## Installation
 
### HACS (recommended)
 
1. HACS → **⋮** → **Custom repositories** → add this fork's URL as an **Integration**.
2. Open the **Atomberg Local** card, click **Download**, then **restart Home Assistant**.
3. **⚠️ This last step is required — downloading in HACS does *not* add the integration.**
   Go to **Settings → Devices & Services → ➕ Add Integration**, search **Atomberg Local**, and add it.
4. Your fans are discovered automatically. No IP addresses or configuration needed.
> **If you skip step 3 you'll see no devices and no entities** — HACS only copies the files; Home Assistant still needs you to *add* the integration so it starts the discovery listener.
 
### Manual
 
1. Copy `custom_components/atomberg_local` into your Home Assistant `config/custom_components/` folder and **restart**.
2. Then do step 3 above: **Settings → Devices & Services → ➕ Add Integration → Atomberg Local**.
## How it works
 
| | Wi-Fi (UDP) | Bluetooth (GATT) |
|---|---|---|
| **Commands** | JSON datagram → fan `:5600` | same JSON → command characteristic |
| **State** | fan broadcasts on `:5625` (push), plus a direct `:5600` reply on command | read from the state characteristic |
| **Works when** | fan is provisioned & on your LAN | always in BLE range (even un-provisioned) |
 
Each fan is identified by its stable `device_id` (its Wi-Fi MAC), which both transports expose — so Home Assistant always sees one device per fan regardless of how it's reached. Set the per-fan **"Prefer Bluetooth"** switch to force BLE-only control.
 
## Entities per fan
 
- **Fan** — power + speed (1–6)
- **Light** — LED underlight: on/off on all lit models, **brightness** on dimmable models, and **warm / cool / daylight** as selectable *effects* on the decorative Aris models
- **Switch** — Sleep mode, Prefer Bluetooth
- **Select** — Timer (Off / 1 / 2 / 3 / 6 hours)
- **Sensor** — Connection (Wi-Fi / Bluetooth / Offline), BLE signal, motor voltage, motor current, runtime hours, board temperature (all diagnostic)
Which light controls appear depends on the fan model (below).
 
## Supported models
 
Works with any Atomberg smart fan that announces itself on your network or over Bluetooth. The **series code** (part of the fan's local name, e.g. `atomberg_S2_…`) maps to a friendly name and a **capability profile** that decides which controls appear — so a fan only shows brightness/colour if that model actually has them. Names are best-effort; capabilities are cross-checked against Atomberg's cloud integration and extended across each product family — see [`models.py`](custom_components/atomberg_local/api/models.py).
 
| Series | Model (approx.) | Speed | LED on/off | Brightness | Colour modes |
|:---:|---|:---:|:---:|:---:|:---:|
| `R1` | Renesa | ✅ | ✅ | – | – |
| `R2` | Renesa+ | ✅ | ✅ | – | – |
| `R3` | Renesa Smart+ | ✅ | ✅ | – | – |
| `S1` | Studio+ | ✅ | ✅ | ✅ | – |
| `S2` | Renesa Elite | ✅ | ✅ | ✅ | – |
| `I1`–`I5` | Aris / Aris Starlight | ✅ | ✅ | ✅ | ✅ |
| `M1` | Efficio | ✅ | ✅ | ✅ | – |
| `M2` | Efficio+ | ✅ | ✅ | – | – |
| `K1` | Gorilla | ✅ | – | – | – |
 
Unknown series still work (power/speed/sleep/timer, plus an on/off light), and an unrecognised `I…` code is assumed to be an Aris with brightness + colour. **`S2` (Renesa Elite)** and **`R1` (Renesa)** are hardware-verified; `R3` (Renesa Halo Smart) is hardware-verified via [PR #1](https://github.com/allusv/atomberg-local/pull/1). If your fan is mis-detected or a control is missing or non-functional, please open an issue with your series code; refining the table is a one-line change.
 
## Limitations
 
- **Onboarding a brand-new fan to Wi-Fi** still uses the Atomberg app (the credential exchange is encrypted). Once provisioned, everything here is local. Bluetooth-only control works without provisioning.
- Model detection is series-based and approximate.
- Board temperature is a best-effort diagnostic field — see "Changes in this fork" above for its confidence level.
## Troubleshooting
 
**"No devices detected" / no entities after installing.**
The usual cause: the integration was **downloaded in HACS but never added**. Go to **Settings → Devices & Services → ➕ Add Integration → Atomberg Local** (see step 3 above). Then give it a few seconds — Wi-Fi fans announce themselves on your LAN and appear automatically.
 
Still nothing? Check:
- Home Assistant is on the **same subnet** as the fan, and **UDP 5600/5625** aren't blocked (VLANs/guest networks often block broadcast).
- A **Bluetooth adapter** is set up in HA if you're relying on Bluetooth-only (un-provisioned) fans.
- Enable debug logging to see discovery activity: add to `configuration.yaml` →
```yaml
  logger:
    logs:
      custom_components.atomberg_local: debug
```
 
**The icon shows as "image not available" in the HACS store panel.**
This is a [known HACS limitation](https://github.com/hacs/integration/issues/5223), not a problem with this integration. Since HA 2026.3, custom integrations ship their brand icons inside the integration (this one does, under `custom_components/atomberg_local/brand/`), and the HACS store panel hasn't yet been updated to read them — it still queries the public brands CDN, which doesn't host custom-integration icons. **The icon displays correctly once installed**, on the Integrations page and on each device. Nothing to fix here.
 
## Disclaimer
 
Not affiliated with or endorsed by Atomberg. Trademarks belong to their owners. Use at your own risk.
 
[hacs]: https://github.com/hacs/integration
[hacs-badge]: https://img.shields.io/badge/HACS-Custom-41BDF5.svg