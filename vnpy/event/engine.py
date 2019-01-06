import heapq
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from queue import Empty, Queue
from threading import (Lock, Thread)
from typing import Any, Callable, Dict, Generic, List, Optional, Tuple, TypeVar

EVENT_TIMER = "eTimer"


@dataclass
class Event:
    """
    Event object consists of a type string which is used 
    by event engine for distributing event, and a data 
    object which contains the real data. 
    """
    type: str
    data: Any


# Defines handler function to be used in event engine.
HandlerType = Callable[[Event], None]

P = TypeVar('P')
T = TypeVar('T')


class PriorityQueue(Generic[P, T]):

    def __init__(self):
        self._data: List[T] = []
        self._counter = 0

    def push(self, val: T, priority: P, first=False):
        """
        :param priority: smaller one gets higher priority
        """
        if first:
            heapq.heappush(self._data, (priority, 0, val))
        else:
            heapq.heappush(self._data, (priority, self._counter, val))
            self._counter += 1

    def pop(self) -> T:
        priority, _, task = heapq.heappop(self._data)
        return priority, task

    def peek(self) -> Tuple[P, T]:
        priority, _, task = self._data[0]
        return priority, task

    def __bool__(self):
        return bool(self._data)


n = 0

class EventEngine:
    """
    Event engine distributes event object based on its type 
    to those handlers registered.

    It also generates timer event by every interval seconds,
    which can be used for timing purpose.
    """

    def __init__(self):
        """
        """
        self._queue: Queue[Event] = Queue()
        self._handlers: Dict[str, List[HandlerType]] = defaultdict(list)
        self._single_shots: PriorityQueue[datetime, Callable] = PriorityQueue()
        self._new_single_shots: List[Tuple[datetime, Callable]] = []
        self._new_single_shots_lock = Lock()
        self._loop_thread: Thread = None
        self._keep_alive = False

    def start(self):
        self._keep_alive = True
        self._loop_thread = Thread(target=self._loop)
        self._loop_thread.start()

    def stop(self):
        self._keep_alive = False

    def join(self):
        self._loop_thread.join()

    def register(self, type: str, handler: HandlerType):
        """
        :note unregister is currently not supported
        """
        self._handlers[type].append(handler)

    def emit(self, type: str, data: Any):
        self._queue.put(Event(type, data), block=False)

    def single_shot(self, func: Callable, delay: float = 0, timepoint: Optional[datetime] = None):
        """
        :param delay: delay in seconds.
        """
        if not timepoint:
            timepoint = datetime.now() + timedelta(seconds=delay)
        with self._new_single_shots_lock:
            self._new_single_shots.append((timepoint, func))

    def _loop(self):
        while self._keep_alive:
            # push all new single_shots first
            self._push_all_single_shot()

            # check if there is single shots:
            if self._single_shots:
                now = datetime.now()
                trigger_point, func = self._single_shots.peek()
                if trigger_point <= now:
                    # timer should be triggered
                    self._single_shots.pop()
                    self._dispatch_single_shot(func)
                    global n
                    n += 1
                else:
                    max_delay = trigger_point - now
                    try:
                        task = self._queue.get(True, max_delay.seconds)
                        self._dispatch(task)
                    except Empty:
                        # no normal task, dispatch timer
                        pass
            else:
                try:
                    task = self._queue.get(False)
                    self._dispatch(task)
                except Empty:
                    pass
        return

    def _dispatch_single_shot(self, func):
        func()
        pass

    def _push_all_single_shot(self):
        with self._new_single_shots_lock:
            items = self._new_single_shots
            self._new_single_shots = []
        for timepoint, func in items:
            self._single_shots.push(func, timepoint)

    def _dispatch(self, task: Event):
        for func in self._handlers[task.type]:
            func(task)


class Timer:

    def __init__(self, event_engine: EventEngine, interval: float, func: Callable,
                 args=None, kwargs=None):
        """
        :param interval: interval in seconds
        """
        if args is None:
            args = []
        if kwargs is None:
            kwargs = {}

        self.func = func
        self.interval = interval
        self.event_engine = event_engine

        self.args = args
        self.kwargs = kwargs

        self._last_triggered: datetime = None

    def start(self):
        self._last_triggered = datetime.now()
        self.event_engine.single_shot(
            self.on_timeout,
            timepoint=self._last_triggered + timedelta(seconds=self.interval)
        )

    def on_timeout(self):
        self._last_triggered = datetime.now()
        self.event_engine.single_shot(
            self.on_timeout,
            timepoint=self._last_triggered + timedelta(seconds=self.interval)
        )
        self.func(*self.args, **self.kwargs)
