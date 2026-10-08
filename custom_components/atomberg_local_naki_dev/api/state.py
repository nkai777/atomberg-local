"""Decode fan state and build commands.

State arrives as a comma-separated ``state_string`` whose first field is a
bitfield holding the live state; the same JSON commands drive the fan over
either transport.
"""

from __future__ import annotations

from dataclasses import dataclass

from .const import (
    ATTR_BRIGHTNESS,
    ATTR_LED,
    ATTR_LIGHT_MODE,
    ATTR_POWER,
    ATTR_SLEEP,
    ATTR_SPEED,
    ATTR_TIMER,
    LIGHT_MODE_COOL,
    LIGHT_MODE_DAYLIGHT,
    LIGHT_MODE_WARM,
    MAX_SPEED,
    MAX_TIMER_INDEX,
    MIN_SPEED,
)


@dataclass
class FanState:
    """Decoded fan state."""

    power: bool
    speed: int
    led: bool
    sleep: bool
    brightness: int
    timer_hours: int
    light_mode: str
    series: str | None = None
    raw: int = 0
    voltage: float | None = None
    current: float | None = None
    runtime_hours: float | None = None
    board_temp: float | None = None

    def as_dict(self) -> dict:
        return {
            ATTR_POWER: self.power,
            ATTR_SPEED: self.speed,
            ATTR_LED: self.led,
            ATTR_SLEEP: self.sleep,
            ATTR_BRIGHTNESS: self.brightness,
            "timer_hours": self.timer_hours,
            ATTR_LIGHT_MODE: self.light_mode,
            "voltage": self.voltage,
            "current": self.current,
            "runtime_hours": self.runtime_hours,
            "board_temp": self.board_temp,
        }


def decode_state(state_string: str) -> FanState | None:
    """Decode a fan ``state_string``. Returns None for non-state replies
    (e.g. the fan's ``"No command detected in the message"`` error)."""
    parts = state_string.split(",")
    field0 = parts[0].strip()
    if not field0.lstrip("-").isdigit():
        return None
    v = int(field0)
    cool = bool(v & 0x08)
    warm = bool(v & 0x8000)
    light_mode = (
        LIGHT_MODE_DAYLIGHT if cool and warm
        else LIGHT_MODE_COOL if cool
        else LIGHT_MODE_WARM
    )
    series = parts[7].strip() if len(parts) > 7 else None

    def _safe_float(idx: int) -> float | None:
        try:
            return float(parts[idx].strip())
        except (IndexError, ValueError):
            return None

    def _safe_int(idx: int) -> int | None:
        try:
            return int(parts[idx].strip())
        except (IndexError, ValueError):
            return None

    power_bit = bool(v & 0x10)
    # The fan's firmware does not refresh voltage/current once
    # power is off -- the state_string keeps reporting the last
    # running value indefinitely. Force these to 0.0 when we know
    # power is off, rather than showing stale running-state data.
    voltage = _safe_float(4) if power_bit else 0.0
    current = _safe_float(15) if power_bit else 0.0
    runtime_sec = _safe_int(11)
    runtime_hours = round(runtime_sec / 3600.0, 1) if runtime_sec is not None else None
    board_temp = _safe_float(16)

    return FanState(
        power=bool(v & 0x10),
        speed=v & 0x07,
        led=bool(v & 0x20),
        sleep=bool(v & 0x80),
        brightness=(v & 0x7F00) >> 8,
        timer_hours=(v & 0x0F0000) >> 16,
        light_mode=light_mode,
        series=series,
        raw=v,
        voltage=voltage,
        current=current,
        runtime_hours=runtime_hours,
        board_temp=board_temp,
    )


def build_command(**kwargs) -> dict:
    """Validate and build a command dict from keyword args.

    Accepts: power(bool), speed(1-6), sleep(bool), led(bool),
    brightness(int), timer(0-4), boost(bool), light_mode(cool/warm/daylight).
    """
    cmd: dict = {}
    for key, val in kwargs.items():
        if val is None:
            continue
        if key == ATTR_SPEED:
            val = int(val)
            if not MIN_SPEED <= val <= MAX_SPEED:
                raise ValueError(f"speed must be {MIN_SPEED}-{MAX_SPEED}")
        elif key == ATTR_TIMER:
            val = int(val)
            if not 0 <= val <= MAX_TIMER_INDEX:
                raise ValueError(f"timer index must be 0-{MAX_TIMER_INDEX}")
        elif key in (ATTR_POWER, ATTR_SLEEP, ATTR_LED, "boost"):
            val = bool(val)
        elif key == ATTR_LIGHT_MODE:
            if val not in (LIGHT_MODE_COOL, LIGHT_MODE_WARM, LIGHT_MODE_DAYLIGHT):
                raise ValueError("light_mode must be cool/warm/daylight")
        cmd[key] = val
    return cmd
