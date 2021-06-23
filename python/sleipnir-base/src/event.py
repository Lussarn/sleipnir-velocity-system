import queue

from PySide2 import QtCore
from pymitter import EventEmitter

''' Global Event system through the application '''
'''
The implementation sets up a timer on QT main thread and dispatches all event from there

Any thread is able to emit events
'''
class Evt:
    def __init__(self, event, args, kwargs):
        self.event = event
        self.args = args
        self.kwargs = kwargs

class EventServer:
    def __init__(self, qobject):
        self.__ee = EventEmitter()
        self.__evt_queue = queue.Queue()

        self.__timer = QtCore.QTimer(qobject)
        self.__timer.timeout.connect(self.__timer_dispatch)
        ''' Run the event system 200 times per second '''
        self.__timer.start(5)

    def on(self, event, func=None, ttl=-1):
        self.__ee.on(event, func, ttl)

    def off(self, event, func=None):
        self.__ee.off(event, func)

    def emit(self, event, args, kwargs):
        self.__evt_queue.put(
            Evt(event, args, kwargs)
        )

    def __timer_dispatch(self):
        while(True):
            try:
                evt = self.__evt_queue.get_nowait()
                if (evt is None): continue
            except queue.Empty:
                return
#            print(evt.event)
            evt2 = evt
            self.__ee.emit(evt2.event, *evt2.args, **evt2.kwargs)
            self.__evt_queue.task_done()

__event_server__ = None

def create_event_server(qobject):
    global __event_server__
    __event_server__ = EventServer(qobject)

def on(event, func=None, ttl=-1):
    global __event_server__
    __event_server__.on(event, func, ttl)

def off(event, func=None):
    global __event_server__
    __event_server__.off(event, func)

def emit(event, *args, **kwargs):
    global __event_server__
    __event_server__.emit(event, args, kwargs)
