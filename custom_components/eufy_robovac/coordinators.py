import logging

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .tuya import Message, TuyaDevice

logger = logging.getLogger(__name__)


class EufyTuyaDataUpdateCoordinator(DataUpdateCoordinator):
    def __init__(self, *args, host: str, device_id: str, local_key: str, **kwargs):
        super().__init__(*args, **kwargs)

        self.tuya_client = TuyaDevice(device_id=device_id, local_key=local_key, host=host)

        extra_handler_list = [self.handle_tuya_message]

        for message_type in [Message.GET_COMMAND, Message.GRATUITOUS_UPDATE]:
            if message_type not in self.tuya_client._handlers:
                self.tuya_client._handlers[message_type] = extra_handler_list
            else:
                self.tuya_client._handlers[message_type] += extra_handler_list

    def handle_new_dps(self, new_dps: dict, async_set_updated_data_upon_change: bool = False):
        existing_dps = (self.data or {}).copy()

        changed = new_dps != existing_dps

        if changed:
            existing_dps.update(new_dps)

            if async_set_updated_data_upon_change:
                # only do this if there were changes as to not spam the state machine
                self.async_set_updated_data(existing_dps)

        return existing_dps

    async def handle_tuya_message(self, message, _):
        self.handle_new_dps(dict(message.payload["dps"]), async_set_updated_data_upon_change=True)

    async def _async_update_data(self):
        # note: this will call the tuya message handler above
        # which will in turn call handle_tuya_message and may cause an extra update to the state machine
        # TODO: this all needs to be cleaned up
        dps = dict((await self.tuya_client.async_get()) or {})

        return self.handle_new_dps(
            dps,
        )
