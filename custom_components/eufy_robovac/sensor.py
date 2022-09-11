from homeassistant.components.sensor import SensorDeviceClass, SensorEntity, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.icon import icon_for_battery_level
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import CONF_COORDINATOR, CONF_DISCOVERED_DEVICES, DOMAIN, MAINTENANCE_ITEMS, RobovacDPs
from .coordinators import EufyTuyaDataUpdateCoordinator
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

        for maintenance_item in MAINTENANCE_ITEMS:
            devices.append(
                MaintenanceDurationSensor(
                    name=f"{maintenance_item.name} time",
                    icon=maintenance_item.icon,
                    status_dp=maintenance_item.status_dp,
                    coordinator=coordinator,
                ),
            )

        devices.append(
            MaintenanceDurationSensor(
                name="Last clean time",
                icon="mdi:timer-sync",
                status_dp=RobovacDPs.ROBOVAC_CLEAR_TIME_DPS_ID_109,
                coordinator=coordinator,
            )
        )

        devices.append(
            MaintenanceSensor(
                name="Last clean area",
                icon="mdi:map-marker",
                status_dp=RobovacDPs.ROBOVAC_CLEAR_AREA_DPS_ID_110,
                coordinator=coordinator,
            )
        )

        devices.append(BatteryPercentageSensor(coordinator=coordinator))

        devices.append(
            DP140LastCleanID(
                name="Last clean ID? (via DP 140)",
                icon=None,
                status_dp=RobovacDPs.ROBOVAC_SMART_ROOMS_DPS_ID_140,
                coordinator=coordinator,
            )
        )

        devices.append(
            DP140LastSweepArea(
                name="Last sweep area? (via DP 140)",
                icon=None,
                status_dp=RobovacDPs.ROBOVAC_SMART_ROOMS_DPS_ID_140,
                coordinator=coordinator,
            )
        )

        devices.append(
            DP140LastCleanTime(
                name="Last clean time? (via DP 140)",
                icon=None,
                status_dp=RobovacDPs.ROBOVAC_SMART_ROOMS_DPS_ID_140,
                coordinator=coordinator,
            )
        )

    return async_add_devices(devices)


class BaseDPSensorEntity(CoordinatorTuyaDeviceUniqueIDMixin, CoordinatorEntity, SensorEntity):
    status_dp: RobovacDPs

    def __init__(
        self,
        *args,
        name: str,
        icon: str | None,
        status_dp: RobovacDPs,
        coordinator: EufyTuyaDataUpdateCoordinator,
        **kwargs,
    ):
        self._attr_name = name
        self._attr_icon = icon
        self.status_dp = status_dp

        super().__init__(*args, coordinator=coordinator, **kwargs)

    @property
    def native_value(self):
        if self.coordinator.data:
            value = self.coordinator.data.get(self.status_dp)

            if converter := getattr(self, "parse_value", None):
                value = converter(value)

            return value


class BaseDurationSensorEntity(BaseDPSensorEntity):
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = "seconds"
    _attr_state_class = SensorStateClass.TOTAL_INCREASING

    @staticmethod
    def parse_value(value):
        """
        Duration DPs that aren't present should be assumed to be 0.
        """

        if value is None:
            return 0


class BatteryPercentageSensor(CoordinatorTuyaDeviceUniqueIDMixin, CoordinatorEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_name = "Battery percentage"
    _attr_icon = "mdi:battery"

    @property
    def icon(self) -> str:
        charging = (self.coordinator.data or {}).get(RobovacDPs.ROBOVAC_MODE_STATUS_DPS_ID_15, None) in [
            "Charging",
            "completed",
        ]

        return icon_for_battery_level(self.native_value, charging=charging)

    @property
    def native_value(self) -> int | None:
        if self.coordinator.data:
            return self.coordinator.data.get(RobovacDPs.ROBOVAC_ELECTRIC_DPS_ID_104)


class MaintenanceDurationSensor(BaseDurationSensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC


class MaintenanceSensor(BaseDPSensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC


class DP140LastCleanID(BaseDPSensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @staticmethod
    def parse_value(value: str | None):
        if value is not None:
            return value[0:5]


class DP140LastSweepArea(BaseDPSensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @staticmethod
    def parse_value(value: str | None):
        if value is not None:
            return value[5:10]


class DP140LastCleanTime(BaseDPSensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @staticmethod
    def parse_value(value: str | None):
        if value is not None:
            return value[10:15]
