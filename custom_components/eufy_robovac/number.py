from homeassistant.components.number import NumberEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_COORDINATOR, CONF_DISCOVERED_DEVICES, DOMAIN, RobovacDPs
from .mixins import CoordinatorTuyaDeviceUniqueIDMixin


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_devices: AddEntitiesCallback,
) -> None:
    discovered_devices = hass.data[DOMAIN][config_entry.entry_id][CONF_DISCOVERED_DEVICES]

    devices = []

    for device_id, props in discovered_devices.items():
        coordinator = props[CONF_COORDINATOR]

        devices.append(VolumeNumberInput(coordinator=coordinator))

    return async_add_devices(devices)


class VolumeNumberInput(CoordinatorTuyaDeviceUniqueIDMixin, CoordinatorEntity, NumberEntity):
    _attr_name = "Volume"
    _attr_entity_category = EntityCategory.CONFIG
    _attr_mode = "slider"
    _attr_native_step = 1
    _attr_native_min_value = 0
    _attr_native_max_value = 10

    @property
    def icon(self) -> str | None:
        if self.value is not None:
            if self.value == 0:
                return "mdi:volume-off"
            elif 1 < self.value < 4:
                return "mdi:volume-low"
            elif 4 < self.value < 7:
                return "mdi:volume-medium"
            else:
                return "mdi:volume-high"

    @property
    def native_value(self) -> float | None:
        if self.coordinator.data:
            return float(self.coordinator.data.get(RobovacDPs.ROBOVAC_LOUDNESS_DPS_ID_111))

    async def async_set_native_value(self, value: float) -> None:
        value = round(value)

        await self.coordinator.tuya_client.async_set({RobovacDPs.ROBOVAC_LOUDNESS_DPS_ID_111: value})
