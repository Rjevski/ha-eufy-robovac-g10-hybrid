import logging

from homeassistant.components.vacuum import (
    STATE_CLEANING,
    STATE_DOCKED,
    STATE_ERROR,
    STATE_RETURNING,
    StateVacuumEntity,
    VacuumEntityFeature,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_COORDINATOR, CONF_DISCOVERED_DEVICES, DOMAIN, CleaningMode, RobovacDPs

logger = logging.getLogger(__name__)


HA_TO_EUFY_FAN_SPEED_MAP = {"Standard": "Standard", "Maximum": "Max"}

EUFY_TO_HA_FAN_SPEED_MAP = {value: key for key, value in HA_TO_EUFY_FAN_SPEED_MAP.items()}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_devices: AddEntitiesCallback,
) -> None:
    discovered_devices = hass.data[DOMAIN][config_entry.entry_id][CONF_DISCOVERED_DEVICES]

    logger.debug("Got discovered devices: %s", discovered_devices)

    return async_add_devices(
        [RobovacVacuum(coordinator=props[CONF_COORDINATOR]) for device_id, props in discovered_devices.items()]
    )


class RobovacVacuum(CoordinatorEntity, StateVacuumEntity):

    _attr_name = "Eufy Robovac"

    @property
    def icon(self) -> str:
        if self.state == STATE_ERROR:
            return "mdi:robot-vacuum-alert"

        return "mdi:robot-vacuum"

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={(DOMAIN, self.unique_id)},
            manufacturer="Eufy",
            name=self.name,
            model="T2150",
        )

    @property
    def unique_id(self) -> str:
        return self.coordinator.tuya_client.device_id

    @property
    def supported_features(self) -> int:
        base_features = VacuumEntityFeature.BATTERY | VacuumEntityFeature.STATE

        status = (self.coordinator.data or {}).get(RobovacDPs.ROBOVAC_MODE_STATUS_DPS_ID_15)

        # locate has no effect when docked
        if status in [
            "auto",
            "Collecting",
            "Edge",
            "Goto",
            "Locating",
            "Pause",
            "Paused",
            "reached",
            "Recharge",
            "remote",
            "Room",
            "Running",
            "Sleeping",
            "SmallRoom",
            "Spot",
            "standby",
            "sterilize",
        ]:
            base_features |= VacuumEntityFeature.LOCATE

        # fan speed can only be set when running
        if status in [
            "auto",
            "Collecting",
            "Edge",
            "Goto",
            "Locating",
            "reached",
            "remote",
            "Room",
            "Running",
            "SmallRoom",
            "Spot",
            "sterilize",
        ]:
            base_features |= VacuumEntityFeature.FAN_SPEED

        # can only pause if running
        if status in [
            "auto",
            "Collecting",
            "Edge",
            "Goto",
            "Locating",
            "reached",
            "Recharge",
            "remote",
            "Room",
            "Running",
            "SmallRoom",
            "Spot",
            "sterilize",
        ]:
            base_features |= VacuumEntityFeature.PAUSE

        # can only start if stopped
        if status in [
            "Pause",
            "Paused",
            "Recharge",
            "Sleeping",
            "standby",
            "sterilize",
            "completed",
            "Charging",
        ]:
            base_features |= VacuumEntityFeature.START

        # spot cleaning can only start if stopped and not docked
        if status in [
            "Pause",
            "Paused",
            "Sleeping",
            "standby",
            "sterilize",
        ]:
            base_features |= VacuumEntityFeature.CLEAN_SPOT

        # can only return home if not already home
        if status in [
            "auto",
            "Collecting",
            "Edge",
            "Goto",
            "Locating",
            "reached",
            "remote",
            "Room",
            "Running",
            "SmallRoom",
            "Spot",
            "sterilize",
            "standby",
        ]:
            base_features |= VacuumEntityFeature.RETURN_HOME

        return base_features

    # states

    @property
    def state(self) -> str | None:
        if self.coordinator.data:
            if self.error_code is not None:
                return STATE_ERROR

            status = self.coordinator.data.get(RobovacDPs.ROBOVAC_MODE_STATUS_DPS_ID_15)

            if status in [
                "auto",
                "Collecting",
                "Edge",
                "Goto",
                "reached",
                "remote",
                "Room",
                "Running",
                "SmallRoom",
                "Spot",
                "sterilize",
            ]:
                return STATE_CLEANING

            if status in ["Charging", "completed"]:
                return STATE_DOCKED

            if status in ["Recharge"]:
                return STATE_RETURNING

            if status is not None:
                # unknown, return raw value
                return status.title()

    @property
    def battery_level(self) -> int | None:
        """
        Returns the battery level as a percentage
        """
        if self.coordinator.data:
            return self.coordinator.data.get(RobovacDPs.ROBOVAC_ELECTRIC_DPS_ID_104.value)

    @property
    def state_attributes(self) -> dict[str, int | str | None]:
        data = super().state_attributes

        data.update(
            {
                "error_code": self.error_code,
            }
        )

        data.update(self.coordinator.data or {})

        return data

    @property
    def error_code(self) -> str | None:
        if self.coordinator.data:
            if error_code := self.coordinator.data.get(RobovacDPs.ROBOVAC_ERROR_ALARM_DPS_ID_106.value):
                if error_code != 0:
                    return error_code

    # commands

    async def async_return_to_base(self, **kwargs) -> None:
        await self.coordinator.tuya_client.async_set({RobovacDPs.ROBOVAC_GO_HOME_DPS_ID_101: True})

    async def async_pause(self) -> None:
        await self.coordinator.tuya_client.async_set(
            {
                # RobovacDPs.ROBOVAC_PLAY_OR_PAUSE_DPS_ID_2: False
                RobovacDPs.ROBOVAC_PAUSE_STAR_DPS_ID_122: "Pause"
            }
        )

    async def async_start(self) -> None:
        await self.coordinator.tuya_client.async_set(
            {
                # RobovacDPs.ROBOVAC_CLEAN_MODE_DPS_ID_5: CleaningMode.AUTO
                RobovacDPs.ROBOVAC_PAUSE_STAR_DPS_ID_122: "Continue"
            }
        )

    async def async_start_pause(self):
        currently_paused = (self.coordinator.data or {}).get(RobovacDPs.ROBOVAC_PAUSE_STAR_DPS_ID_122) == "Pause"

        if currently_paused:
            await self.async_start()
        else:
            await self.async_pause()

    async def async_clean_spot(self, **kwargs) -> None:
        await self.coordinator.tuya_client.async_set({RobovacDPs.ROBOVAC_CLEAN_MODE_DPS_ID_5: CleaningMode.SPOT_CLEAN})

    # locate

    async def async_locate(self, **kwargs) -> None:
        currently_locating = (self.coordinator.data or {}).get(RobovacDPs.ROBOVAC_FIND_ROBOVAC_DPS_ID_103)

        # this makes it a toggle

        await self.coordinator.tuya_client.async_set(
            {RobovacDPs.ROBOVAC_FIND_ROBOVAC_DPS_ID_103: not currently_locating}
        )

    # fan speed

    _attr_fan_speed_list = list(HA_TO_EUFY_FAN_SPEED_MAP.keys())

    @property
    def fan_speed(self) -> str | None:
        if self.coordinator.data:
            raw_speed_value = self.coordinator.data.get(RobovacDPs.ROBOVAC_ROBOVAC_SPEED_DPS_ID_102)

            return EUFY_TO_HA_FAN_SPEED_MAP[raw_speed_value]

    async def async_set_fan_speed(self, fan_speed: str, **kwargs) -> None:
        raw_speed_value = HA_TO_EUFY_FAN_SPEED_MAP[fan_speed]

        await self.coordinator.tuya_client.async_set({RobovacDPs.ROBOVAC_ROBOVAC_SPEED_DPS_ID_102: raw_speed_value})
