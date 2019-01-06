import unittest
from datetime import datetime, timedelta
from threading import Thread
from time import sleep
from uuid import uuid4

from test.Promise import Promise
from vnpy.event import Event, EventEngine
from vnpy.event.engine import Timer


class EventEngineTest(unittest.TestCase):

    def setUp(self):
        self.eventengine = EventEngine()
        self.eventengine.start()

    def tearDown(self):
        self.eventengine.stop()
        self.eventengine.join()

    def test_normal_message(self):
        type = 'msg'
        data = uuid4()
        p = Promise()

        def handler(event: Event):
            self.assertEqual(event.type, type)
            self.assertEqual(event.data, data)
            p.set_result(True)
            pass

        def thread_productor():
            self.eventengine.emit(type, data)

        self.eventengine.register('msg', handler)
        thread = Thread(target=thread_productor, )
        thread.start()
        thread.join(timeout=1)
        self.assertTrue(p.get(1))

    def test_timer(self):
        microsecond_unit = 1000000
        tick = 0

        def on_timer():
            nonlocal tick
            tick += 1

        timer = Timer(self.eventengine, 1, on_timer)
        timer.start()
        self.assertEqual(tick, 0)

        start = datetime.now()
        end = start + timedelta(seconds=2.2)

        sleep(1.1)
        while True:
            now = datetime.now()
            if now > end:
                break

            delta = now - start
            expected_tick = delta.seconds
            if expected_tick == tick:
                pass
            elif expected_tick > tick:
                if delta.microseconds - (tick + 1) * microsecond_unit >= 0.0001 * microsecond_unit:
                    self.assertTrue(False, "different too large!")
            elif expected_tick < tick:
                if abs(delta.microseconds - tick * microsecond_unit) >= 0.0001 * microsecond_unit:
                    self.assertTrue(False, "different too large!")

    def test_multiple_timer(self):
        microsecond_unit = 1e6
        n = 10
        interval = 0.1
        max_diff = 0.0001 * microsecond_unit
        ticks = [0 for _ in range(n)]

        def on_timer(index):
            nonlocal ticks
            ticks[index] += 1

        timers = [Timer(self.eventengine, interval=interval, func=on_timer, args=(i,))
                  for i in range(n)]
        for timer in timers:
            timer.start()

        # check initial state
        for i in ticks:
            self.assertEqual(i, 0)

        start = datetime.now()
        duration = 4
        end = start + timedelta(seconds=duration + 0.2)

        sleep(1.1)
        while True:

            now = datetime.now()
            if now > end:
                break

            delta = now - start
            total_microsec = (delta.seconds * microsecond_unit) + delta.microseconds
            expected_tick = total_microsec / (interval * microsecond_unit)
            for tick in ticks:
                if expected_tick == tick:
                    pass
                elif expected_tick > tick:
                    diff = delta.microseconds - (tick + interval) * microsecond_unit
                    if diff >= max_diff:
                        self.assertTrue(
                            False,
                            "different too large! microsec:{}, expected:{}, tick:{} diff:{}, max diff:{}"
                                .format(
                                delta.microseconds, expected_tick, tick, diff,
                                max_diff))
                elif expected_tick < tick:
                    diff = abs(total_microsec / interval - tick * microsecond_unit)
                    if diff >= max_diff:
                        self.assertTrue(
                            False,
                            "different too large! microsec:{}, expected:{}, tick:{} diff:{}, max diff:{}"
                                .format(
                                delta.microseconds, expected_tick, tick, diff,
                                max_diff))


if __name__ == '__main__':
    unittest.main()
