import sys
import logging
from PySide2.QtCore import QThread
import re

''' Custom formatter to find QTThread names '''
class SleipnirFormatter(logging.Formatter):
   __re_dummy = re.compile(r' - Dummy-[0-9]+ - ')

   def __init__(self, fmt):
      logging.Formatter.__init__(self, fmt)

   def format(self, record):
      result = logging.Formatter.format(self, record)
      ''' Replace the Dummy-* thread name with QT thread name '''
      qthread_name = QThread.currentThread().objectName()
      if qthread_name != "": result = self.__re_dummy.sub(' - ' + qthread_name + ' - ', result)

      return result

''' Configure default logger '''
log_root = logging.getLogger()
log_root.setLevel(logging.DEBUG)
log_handler = logging.StreamHandler(sys.stderr)
log_handler.setFormatter(SleipnirFormatter('%(asctime)s -  %(levelname)s - %(name)s - %(threadName)s - %(message)s'))
log_root.addHandler(log_handler)

logging.getLogger("frame_collection").setLevel(logging.INFO)