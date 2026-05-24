"""Simple APScheduler wrapper for recurring SoundTouch actions."""

from __future__ import annotations

from typing import Callable

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from soundtouchbose.api.client import SoundTouchClient
from soundtouchbose.core.config import ConfigStore
from soundtouchbose.core.station_library import StationLibrary

DAY_NAMES = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]


class SchedulerService:
    """Persist and execute background schedules."""

    def __init__(
        self,
        config_store: ConfigStore,
        station_library: StationLibrary,
        client_factory: Callable[[str], SoundTouchClient] = SoundTouchClient,
    ) -> None:
        self.config_store = config_store
        self.station_library = station_library
        self.client_factory = client_factory
        self.scheduler = BackgroundScheduler()
        self.started = False

    def start(self) -> None:
        if not self.started:
            self.scheduler.start()
            self.started = True
            self.load_jobs()

    def shutdown(self) -> None:
        if self.started:
            self.scheduler.shutdown(wait=False)
            self.started = False

    def load_definitions(self) -> list[dict[str, object]]:
        return self.config_store.load_json("schedule.json", [])

    def save_definitions(self, definitions: list[dict[str, object]]) -> None:
        self.config_store.save_json("schedule.json", definitions)

    def load_jobs(self) -> None:
        for definition in self.load_definitions():
            self._schedule_definition(definition)

    def add_definition(self, definition: dict[str, object]) -> None:
        definitions = [item for item in self.load_definitions() if item.get("id") != definition.get("id")]
        definitions.append(definition)
        self.save_definitions(definitions)
        self._schedule_definition(definition)

    def remove_definition(self, definition_id: str) -> None:
        self.scheduler.remove_job(definition_id)
        remaining = [item for item in self.load_definitions() if item.get("id") != definition_id]
        self.save_definitions(remaining)

    def _schedule_definition(self, definition: dict[str, object]) -> None:
        if not self.started or not definition.get("enabled", True):
            return
        hour, minute = str(definition["time"]).split(":")
        weekdays = [DAY_NAMES[index] for index, enabled in enumerate(definition.get("days", [False] * 7)) if enabled]
        trigger = CronTrigger(hour=int(hour), minute=int(minute), day_of_week=",".join(weekdays or DAY_NAMES))
        self.scheduler.add_job(
            self.run_action,
            trigger=trigger,
            id=str(definition["id"]),
            replace_existing=True,
            kwargs={"definition": definition},
        )

    def run_action(self, definition: dict[str, object]) -> None:
        action = definition.get("action")
        for ip_address in definition.get("devices", []):
            client = self.client_factory(str(ip_address))
            if action == "volume":
                client.set_volume(int(definition.get("volume", 20)))
            elif action == "power_off":
                client.power("off")
            elif action == "station":
                station = self.station_library.get(str(definition.get("station_id")))
                if station:
                    client.select(station)
