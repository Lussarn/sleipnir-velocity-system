import functools
import logging
import time
import sys
import inspect
from threading import Lock

logger = logging.getLogger(__name__)

'''
--- Sample usages ---

@timer("Message", logging.DEBUG)
def foo(bar):
    pass

@timer("Message", logging.INFO, 'bar', 1000)
def foo(bar):
    pass
'''
__averages = {}
__mutex = Lock()

def timer(message: str, level: int = logging.INFO , identifier = None, average: int = 1):
    def decorator_timer(func):
        @functools.wraps(func)
        def wrapper_timer(*args, **kwargs):
            ''' benchmark '''
            start_time = time.perf_counter()
            ret = func(*args, **kwargs)
            run_time = (time.perf_counter() - start_time) * 1000
            ''' Do not average '''
            if (average == 1):
                ''' Do the actual logging '''
                logger_func = logging.getLogger(sys.modules[func.__module__].__name__)
                logger_func.log(level, message + f" [timer: {run_time:.3f}ms]")
                return ret

            key = sys.modules[func.__module__].__name__ + "." + func.__name__ + "." + str(func.__hash__())

            if identifier != None:                
                kwargs_in = locals()['kwargs']
                if identifier in kwargs_in: 
                    ''' Check the identifier in kwargs (named)'''
                    key += "." + str(kwargs_in[identifier])
                    arg = identifier + "=" + str(kwargs_in[identifier])
                else:
                    ''' Check the identifier in args (positional) '''
                    try:
                        index = inspect.getfullargspec(func).args.index(identifier)
                    except ValueError as e:
                        logger.error("identifier '" + identifier + "' not present in function arguments" )
                        return ret
                    key += "." + str(args[index])
                    arg = identifier + "=" + str(args[index])
            else:
                arg = "---"

            ''' Average over several runs '''
            __mutex.acquire()
            if not key in __averages:
                ''' Register a new key '''
                __averages[key] = {}
                __averages[key]['count'] = 0
                __averages[key]['run_time_total'] = 0

            __averages[key]['count'] += 1
            __averages[key]['run_time_total'] += run_time

            if (__averages[key]['count'] == average):
                count = __averages[key]['count']
                run_time_average = __averages[key]['run_time_total'] / count
                ''' reset the key '''
                __averages[key]['count'] = 0
                __averages[key]['run_time_total'] = 0
                ''' release lock as early as possible '''
                __mutex.release()
                ''' Do the actual logging '''
                logger_func = logging.getLogger(sys.modules[func.__module__].__name__)
                logger_func.log(level, message + f" [timer: ({arg}) (avg={count}) {run_time_average:.3f}ms]")
            else:
                __mutex.release()

            return ret
        return wrapper_timer
    return decorator_timer

