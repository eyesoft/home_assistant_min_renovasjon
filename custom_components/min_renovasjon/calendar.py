import logging

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import callback
from homeassistant.util.dt import parse_datetime, as_utc, now
from datetime import datetime
from .const import (DOMAIN)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    min_renovasjon = hass.data[DOMAIN]["data"]
    async_add_entities([MinRenovasjonCalendarEntity("Min Renovasjon Calendar", config_entry, min_renovasjon)])


class MinRenovasjonCalendarEntity(CalendarEntity):
    """Representation of a MinRenovasjon Calendar Entity."""

    def __init__(self, calendar_name, config_entry, min_renovasjon):
        """Initialize the calendar entity."""
        self._calendar_name = calendar_name
        self._config_entry = config_entry
        self._min_renovasjon = min_renovasjon
        self._events = []

    @property
    def name(self):
        """Return the name of the calendar entity."""
        return self._calendar_name

    @property
    def event(self):
        """Return the next upcoming event."""
        return self._get_next_event()

    @property
    def unique_id(self):
        """Return a unique ID to use for this entity."""
        return f"{self._config_entry.entry_id}"

    async def async_get_events(self, hass, start_date: datetime, end_date: datetime) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        start_date = as_utc(start_date)
        end_date = as_utc(end_date)
        event_list = []

        for event in self._events:
            if event:
                if start_date.date() <= event.start <= end_date.date():
                    event_list.append(event)

        return event_list

    async def async_update(self):
        """Update the calendar with new events from the API."""
        self._events = await self._fetch_events()

    async def _fetch_events(self):
        """Call Min Renovasjon to fetch delivery dates."""
        events = []
        calendar_list = await self._min_renovasjon.async_get_calendar_list()

        for entry in calendar_list:
            if entry:
                fraction_name = entry[1]
                pickup_dates = entry[5]

                for pickup_date in pickup_dates:
                    if pickup_date:
                        pickup_date_formatted = datetime.strptime(pickup_date, "%Y-%m-%dT%H:%M:%S")

                        events.append(CalendarEvent(
                            summary=fraction_name,
                            start=pickup_date_formatted.date(),
                            end=pickup_date_formatted.date()
                        ))

        self._events = events
        return events

    def _get_next_event(self):
        """Return the next upcoming event."""
        if not self._events:
            return None
        return self._events[0]
