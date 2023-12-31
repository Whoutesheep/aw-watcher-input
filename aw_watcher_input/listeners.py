"""
Listeners for aggregated keyboard and mouse events.

This is used for AFK detection on Linux, as well as used in aw-watcher-input to track input activity in general.

NOTE: Logging usage should be commented out before committed, for performance reasons.
"""

import logging
import threading
from abc import ABCMeta, abstractmethod
from collections import defaultdict
from typing import Dict, Any

logger = logging.getLogger(__name__)
# logger.setLevel(logging.DEBUG)


class EventFactory(metaclass=ABCMeta):
    def __init__(self) -> None:
        self.new_event = threading.Event()
        self._reset_data()

    @abstractmethod
    def _reset_data(self) -> None:
        self.event_data: Dict[str, Any] = {}

    def next_event(self) -> dict:
        """Returns an event and prepares the internal state so that it can start to build a new event"""
        self.new_event.clear()
        data = self.event_data
        # self.logger.info(f"Event: {data}")
        self._reset_data()
        return data

    def has_new_event(self) -> bool:
        return self.new_event.is_set()


class KeyboardListener(EventFactory):
    def __init__(self):
        EventFactory.__init__(self)
        self.logger = logger.getChild("keyboard")

    def start(self):
        from pynput import keyboard

        listener = keyboard.Listener(on_press=self.on_press, on_release=self.on_release)
        listener.start()

    def _reset_data(self):
        self.event_data = {"presses": 0}

    def on_press(self, key):
        # self.logger.debug(f"Press: {key}")
        self.event_data["presses"] += 1
        self.new_event.set()

    def on_release(self, key):
        # Don't count releases, only clicks
        # self.logger.debug(f"Release: {key}")
        pass


class MouseListener(EventFactory):
    def __init__(self):
        EventFactory.__init__(self)
        self.logger = logger.getChild("mouse")
        self.pos = None

    def _reset_data(self):
        self.event_data = defaultdict(int)
        self.event_data.update(
            {"clicks": 0, "click_pos" : [], "mouse_pos": [], "scrollX": 0, "scrollY": 0}
        )

    def start(self):
        from pynput import mouse

        listener = mouse.Listener(
            on_move=self.on_move, on_click=self.on_click, on_scroll=self.on_scroll
        )
        listener.start()

    def on_move(self, x, y):
        newpos = (x, y)
        # self.logger.debug("Moved mouse to: {},{}".format(x, y))
        
        if not self.pos:
            self.pos = newpos
        self.event_data["mouse_pos"].append(newpos)
        self.pos = newpos
        self.new_event.set()

    def on_click(self, x, y, button, down):
        # self.logger.debug(f"Click: {button} at {(x, y)}")
        # Only count presses, not releases
        click_pos = (x, y)
        if down:
            self.event_data["clicks"] += 1
            self.event_data["click_pos"].append(click_pos)
            self.new_event.set()

    def on_scroll(self, x, y, scrollx, scrolly):
        # self.logger.debug(f"Scroll: {scrollx}, {scrolly} at {(x, y)}")
        self.event_data["scrollX"] += abs(scrollx)
        self.event_data["scrollY"] += abs(scrolly)
        self.new_event.set()
