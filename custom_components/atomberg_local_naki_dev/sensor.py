"""Sensor platform: which transport is active, and BLE signal strength."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory, SIGNAL_STRENGTH_DECIBELS_MILLIWATT
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import AtombergCoordinator
from .entity import AtombergEntity, setup_atomberg_platform


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    def build(coordinator: AtombergCoordinator, device_id: str, _device) -> list:
        return [
            AtombergConnectionSensor(coordinator, device_id),
            AtombergRssiSensor(coordinator, device_id),
            AtombergVoltageSensor(coordinator, device_id),
            AtombergCurrentSensor(coordinator, device_id),
            AtombergRuntimeSensor(coordinator, device_id),
            AtombergBoardTempSensor(coordinator, device_id),
        ]

    setup_atomberg_platform(hass, entry, async_add_entities, build)


class AtombergConnectionSensor(AtombergEntity, SensorEntity):
    """Active control transport: wifi / ble / offline."""

    _attr_translation_key = "connection"
    _attr_icon = "mdi:transit-connection-variant"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["wifi", "ble", "offline"]

    def __init__(self, coordinator: AtombergCoordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_unique_id = self._unique_id("connection")

    @property
    def available(self) -> bool:
        return self._device_id in self.coordinator.manager.devices

    @property
    def native_value(self) -> str:
        return self.device.connection

    @property
    def extra_state_attributes(self) -> dict:
        d = self.device
        return {
            "provisioned": d.is_provisioned,
            "wifi_ip": d.wifi_ip,
            "wifi_available": d.wifi_available,
            "ble_available": d.ble_available,
        }


class AtombergRssiSensor(AtombergEntity, SensorEntity):
    """BLE signal strength."""

    _attr_translation_key = "ble_rssi"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.SIGNAL_STRENGTH
    _attr_native_unit_of_measurement = SIGNAL_STRENGTH_DECIBELS_MILLIWATT
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: AtombergCoordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_unique_id = self._unique_id("ble_rssi")

    @property
    def available(self) -> bool:
        return self._device_id in self.coordinator.manager.devices

    @property
    def native_value(self) -> int | None:
        return self.device.ble_rssi


class AtombergVoltageSensor(AtombergEntity, SensorEntity):
    """Motor drive voltage (confirmed via testing: scales with fan speed)."""

    _attr_translation_key = "voltage"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = "V"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: AtombergCoordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_unique_id = self._unique_id("voltage")

    @property
    def available(self) -> bool:
        return self._device_id in self.coordinator.manager.devices

    @property
    def native_value(self) -> float | None:
        return self.device.state.voltage if self.device.state else None


class AtombergCurrentSensor(AtombergEntity, SensorEntity):
    """Motor current (confirmed via testing: scales with fan speed)."""

    _attr_translation_key = "current"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = "A"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: AtombergCoordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_unique_id = self._unique_id("current")

    @property
    def available(self) -> bool:
        return self._device_id in self.coordinator.manager.devices

    @property
    def native_value(self) -> float | None:
        return self.device.state.current if self.device.state else None


class AtombergRuntimeSensor(AtombergEntity, SensorEntity):
    """Fan lifetime runtime, in hours. Verified against the Atomberg app's
    own reported 'hours run' figure (matched within rounding)."""

    _attr_translation_key = "runtime_hours"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = "h"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_icon = "mdi:clock-outline"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: AtombergCoordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_unique_id = self._unique_id("runtime_hours")

    @property
    def available(self) -> bool:
        return self._device_id in self.coordinator.manager.devices

    @property
    def native_value(self) -> float | None:
        return self.device.state.runtime_hours if self.device.state else None


class AtombergBoardTempSensor(AtombergEntity, SensorEntity):
    """Board/ambient temperature. NOTE: confidence is 'likely, not fully
    confirmed' -- this field consistently sits in a plausible ambient-temp
    range (24-25C) across many samples, but has not been isolated/verified
    against a known reference the way voltage/current/runtime_hours were."""

    _attr_translation_key = "board_temp"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = "\u00b0C"
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_registry_enabled_default = False

    def __init__(self, coordinator: AtombergCoordinator, device_id: str) -> None:
        super().__init__(coordinator, device_id)
        self._attr_unique_id = self._unique_id("board_temp")

    @property
    def available(self) -> bool:
        return self._device_id in self.coordinator.manager.devices

    @property
    def native_value(self) -> float | None:
        return self.device.state.board_temp if self.device.state else None
