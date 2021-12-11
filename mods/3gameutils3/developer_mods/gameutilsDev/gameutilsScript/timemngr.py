# -*- coding: utf-8 -*-

"""
系统的定时器功能
addTimer是一次性的Timer
addRepeatTimer是重复的Timer
"""

import time
import service.asyncore_with_timer as asyncore_with_timer

uniqueTimeId = 0


def getTimerId():
    global uniqueTimeId
    timerId = uniqueTimeId
    uniqueTimeId = uniqueTimeId + 1
    return timerId


class TimerManager(object):
    def __init__(self):
        self.timers = {}

    def addTimer(self, delay, func, *args, **kwargs):
        timerId = getTimerId()
        self.timers[timerId] = asyncore_with_timer.CallLater(delay, func, *args, **kwargs)
        return timerId

    def addRepeatTimer(self, delay, func, *args, **kwargs):
        timerId = getTimerId()
        self.timers[timerId] = asyncore_with_timer.CallEvery(delay, func, *args, **kwargs)
        return timerId

    def delTimer(self, timerId):
        timer = self.timers.pop(timerId, None)
        if timer:
            timer.cancel()

    def tick(self):
        removeIds = []
        for timerId in self.timers:
            timer = self.timers[timerId]
            if timer.expired:
                timer.cancel()
                removeIds.append(timerId)
        for id in removeIds:
            self.delTimer(id)
        asyncore_with_timer.scheduler()

    def finish(self):
        asyncore_with_timer.close_all()
        self.delTimer = None


timerManager = TimerManager()

if __name__ == '__main__':
    def foo():
        print "I'm called after 2.5 seconds"


    timerManager.addRepeatTimer(3, foo)
    i = 0
    while i < 100:
        timerManager.tick()
        time.sleep(0.2)
