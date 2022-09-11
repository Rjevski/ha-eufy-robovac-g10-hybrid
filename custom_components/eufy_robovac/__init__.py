"""
Quick and dirty module to support Eufy Robovac G10 Hybrid.
"""

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant

from .const import CONF_COORDINATOR, CONF_DISCOVERED_DEVICES, DOMAIN, PLATFORMS
from .coordinators import EufyTuyaDataUpdateCoordinator
from .discovery import discover
from .eufy_local_id_grabber.clients import EufyHomeSession, TuyaAPISession

logger = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """
    Set up Eufy Vacuum entities from a config entry.
    """

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN].setdefault(entry.entry_id, {})

    username = entry.data[CONF_EMAIL]
    password = entry.data[CONF_PASSWORD]

    client = EufyHomeSession(username, password)

    try:
        user_info = await hass.async_add_executor_job(client.get_user_info)
        logger.debug("Eufy user info: %s", user_info)
        #
        # eufy_device_list = await hass.async_add_executor_job(client.get_devices)
        # logger.debug("Eufy device list: %s", eufy_device_list)

        tuya_session = TuyaAPISession(username=f'eh-{user_info["id"]}', country_code=user_info["phone_code"])

        homes = await hass.async_add_executor_job(tuya_session.list_homes)
        logger.debug("Tuya homes: %s", homes)

        hass.data[DOMAIN][entry.entry_id].setdefault(CONF_DISCOVERED_DEVICES, {})

        detected_devices = await discover()

        for home in homes:
            devices_for_home = await hass.async_add_executor_job(tuya_session.list_devices, home["groupId"])

            for device in devices_for_home:
                logger.debug("Got Tuya device in home group %s: %s", home["groupId"], device)

                device_id = device["devId"]
                local_key = device["localKey"]

                if discovered_device := detected_devices.pop(device_id):
                    device_ip = discovered_device["ip"]

                    logger.debug(
                        "Found matching discovered device at %s for device ID %s",
                        device_ip,
                        device_id,
                    )

                    hass_entity_id = f'{home["groupId"]}-{device["devId"]}'

                    coordinator = EufyTuyaDataUpdateCoordinator(
                        hass,
                        logger=logger,
                        name=DOMAIN,
                        update_interval=timedelta(seconds=30),
                        host=device_ip,
                        device_id=device_id,
                        local_key=local_key,
                    )

                    await coordinator.async_config_entry_first_refresh()

                    hass.data[DOMAIN][entry.entry_id][CONF_DISCOVERED_DEVICES][hass_entity_id] = {
                        CONF_COORDINATOR: coordinator
                    }
                else:
                    logger.debug(
                        "Could not find device %s on the local network, skipping",
                        device_id,
                    )

    except Exception:
        # TODO: raise proper exception
        logger.exception("Exception when trying to get initial user info and devices")
        raise
    else:
        await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

        return True
