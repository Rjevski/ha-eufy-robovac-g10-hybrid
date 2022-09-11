from homeassistant.components.switch import SwitchEntity
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

        devices.append(AutoReturnCleaningSwitch(coordinator=coordinator))

    return async_add_devices(devices)


class AutoReturnCleaningSwitch(CoordinatorTuyaDeviceUniqueIDMixin, CoordinatorEntity, SwitchEntity):

    _attr_name = "Auto-return cleaning"
    _attr_icon = "mdi:autorenew"
    _attr_entity_category = EntityCategory.CONFIG

    @property
    def is_on(self) -> bool | None:
        if self.coordinator.data:
            value = self.coordinator.data.get(RobovacDPs.ROBOVAC_AUTO_RETURN_CLEAN_DPS_ID_135)

            if isinstance(value, bool):
                return value

    async def async_turn_on(self, **kwargs) -> None:
        await self.coordinator.tuya_client.async_set({RobovacDPs.ROBOVAC_AUTO_RETURN_CLEAN_DPS_ID_135: True})

    async def async_turn_off(self, **kwargs) -> None:
        await self.coordinator.tuya_client.async_set({RobovacDPs.ROBOVAC_AUTO_RETURN_CLEAN_DPS_ID_135: False})
