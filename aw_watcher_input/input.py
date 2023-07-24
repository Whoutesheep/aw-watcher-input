import logging
import platform
import os
from datetime import datetime, timedelta, timezone
from time import sleep
from typing import Optional

from aw_core.models import Event
from aw_client import ActivityWatchClient

from .config import load_config

system = platform.system()

if system == "Windows":
    from .windows import seconds_since_last_input
elif system == "Darwin":
    from .macos import seconds_since_last_input
elif system == "Linux":
    from .unix import seconds_since_last_input
else:
    raise Exception(f"Unsupported platform: {system}")


logger = logging.getLogger(__name__)
td1ms = timedelta(milliseconds=1)


class Settings:
    def __init__(self, config_section, timeout=None, poll_time=None):
        # Time without input before we're considering the user as AFK
        self.timeout = timeout or config_section["timeout"]
        # How often we should poll for input activity
        self.poll_time = poll_time or config_section["poll_time"]

        assert self.timeout >= self.poll_time


class INPUTWatcher:
    def __init__(self, args, testing=False):
        # Read settings from config
        self.settings = Settings(
            load_config(testing), timeout=args.timeout, poll_time=args.poll_time
        )

        self.client = ActivityWatchClient(
            "aw-watcher-input", host=args.host, port=args.port, testing=testing
        )
        self.bucketname = "{}_{}".format(
            self.client.client_name, self.client.client_hostname
        )

    def ping(self, mouse: bool, keyboard: bool, timestamp: datetime, duration: float = 0):
        data = {"data_mouse": "Mouse active" if mouse else "Mouse not active",
        "data_keyboard": "Keyboard active" if keyboard else "Keyboard not active"
        }
        e = Event(timestamp=timestamp, duration=duration, data=data)
        pulsetime = self.settings.timeout + self.settings.poll_time
        self.client.heartbeat(self.bucketname, e, pulsetime=pulsetime, queued=True)

    def run(self):
        logger.info("aw-watcher-input started")

        # Initialization
        sleep(1)

        eventtype = "inputstatus"
        self.client.create_bucket(self.bucketname, eventtype, queued=True)

        # Start afk checking loop
        with self.client:
            self.heartbeat_loop()

    def heartbeat_loop(self):
        while True:
            try:
                if system in ["Darwin", "Linux"] and os.getppid() == 1:
                    # TODO: This won't work with PyInstaller which starts a bootloader process which will become the parent.
                    #       There is a solution however.
                    #       See: https://github.com/ActivityWatch/aw-qt/issues/19#issuecomment-316741125
                    logger.info("inputwatcher stopped because parent process died")
                    break

                now = datetime.now(timezone.utc)
                data = seconds_since_last_input() # return data = [(now - self.last_activity).total_seconds(), mouse_event, keyboard_event]
                self.logger.info(data)
                last_input = now - timedelta(seconds=seconds_since_input)
                logger.debug(f"Seconds since last input: {seconds_since_input}")
                
            except KeyboardInterrupt:
                logger.info("aw-watcher-input stopped by keyboard interrupt")
                break
