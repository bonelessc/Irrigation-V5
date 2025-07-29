"""pump classs."""

import asyncio
import logging

from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_CLOSE_VALVE,
    SERVICE_OPEN_VALVE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_track_state_change_event

from .const import CONST_OFF_DELAY, CONST_SWITCH

_LOGGER = logging.getLogger(__name__)


class PumpClass:
    """Pump class."""

    def __init__(self, hass: HomeAssistant, pump, zones, program=None) -> None:  # noqa: D107
        self.hass = hass
        self._pump = pump
        self._zones = zones
        self._stop = False
        self._off_delay = CONST_OFF_DELAY
        self._program = program

        # turn off the pump on start
        loop = asyncio.get_event_loop()
        background_tasks = set()
        task = loop.create_task(self.async_stop())
        background_tasks.add(task)
        task.add_done_callback(background_tasks.discard)

        self._unsub_monitor = async_track_state_change_event(
            self.hass, tuple(zones), self.run_pump
        )

    async def run_pump(self, entity=None, old_status=None, new_status=None):
        """Toggle the pump."""
        if self._program.is_on:
            newstate = entity.data.get("new_state").state
            if newstate in ("on", "open"):
                await self.async_start()

        for zone in self._zones:
            if self.hass.states.get(zone).state in ("on", "open"):
                break
        else:
            # vent the lines for 3 seconds and turn off
            await asyncio.sleep(3)
            await self.async_stop()

    @property
    def zones(self) -> list:
        """Return list of zones."""
        return self._zones

    @property
    def pump(self) -> list:
        """Return pump."""
        return self._pump

    @property
    def pump_running(self) -> list:
        """Return pump state."""
        return self.hass.states.get(self._pump).state in ("on", "open")

    async def async_stop(self):
        """Turn off pump monitoring."""
        state = self.hass.states.get(self._pump).state
        if state == "on":
            await self.hass.services.async_call(
                CONST_SWITCH, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: self._pump}
            )
        if state == "open":
            await self.hass.services.async_call(
                "valve", SERVICE_CLOSE_VALVE, {ATTR_ENTITY_ID: self._pump}
            )

    async def async_start(self):
        """Turn on the pump."""
        state = self.hass.states.get(self._pump).state
        if state == "off":
            await self.hass.services.async_call(
                CONST_SWITCH, SERVICE_TURN_ON, {ATTR_ENTITY_ID: self._pump}
            )
        if state == "closed":
            await self.hass.services.async_call(
                "valve", SERVICE_OPEN_VALVE, {ATTR_ENTITY_ID: self._pump}
            )

    # async def async_monitor(self):
    #     """Monitor running zones to determine if pump is required."""
    #     self._stop = False

    #     def zone_running():
    #         return any(
    #             self.hass.states.get(zone).state in ("on", "open")
    #             for zone in self._zones
    #         )

    #     def pump_running():
    #         return self.hass.states.get(self._pump).state in ("on", "open")

    #     # Monitor the required zones
    #     while not self._stop:
    #         # check if any of the zones are running
    #         if zone_running():
    #             state = self.hass.states.get(self._pump).state
    #             if state == "off":
    #                 await self.hass.services.async_call(
    #                     CONST_SWITCH, SERVICE_TURN_ON, {ATTR_ENTITY_ID: self._pump}
    #                 )
    #             if state == "closed":
    #                 await self.hass.services.async_call(
    #                     "valve", SERVICE_OPEN_VALVE, {ATTR_ENTITY_ID: self._pump}
    #                 )

    #         # check if the zone is running,
    #         if not zone_running() and pump_running():
    #             # delay incase another zone starts
    #             await asyncio.sleep(self._off_delay)
    #             # turn off the pump
    #             if not zone_running():
    #                 state = self.hass.states.get(self._pump).state
    #                 if state == "on":
    #                     await self.hass.services.async_call(
    #                         CONST_SWITCH, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: self._pump}
    #                     )
    #                 if state == "open":
    #                     await self.hass.services.async_call(
    #                         "valve", SERVICE_CLOSE_VALVE, {ATTR_ENTITY_ID: self._pump}
    #                     )

    #         await asyncio.sleep(1)
    #     # reset for next call
    #     self._stop = False

    # async def async_stop_monitoring(self):
    #     """Flag turn off pump monitoring."""
    #     self._stop = True
    #     state = self.hass.states.get(self._pump).state
    #     if state == "on":
    #         await self.hass.services.async_call(
    #             CONST_SWITCH, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: self._pump}
    #         )
    #     if state == "open":
    #         await self.hass.services.async_call(
    #             "valve", SERVICE_CLOSE_VALVE, {ATTR_ENTITY_ID: self._pump}
    #         )
