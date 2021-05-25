from threading import Lock
import time
import os

import sqlite3
from sqlite3.dbapi2 import OperationalError, connect

import logging
logger = logging.getLogger(__name__)

class DB():
    __write_lock = Lock()

    def __init__(self, save_path):
        self.__db_version = 1
        logger.info("Opening database" + os.path.join(save_path, 'sleipnir.db'))
        self.__conn = sqlite3.connect(os.path.join(save_path, 'sleipnir.db'), check_same_thread = False)

        ''' Disable auto vacuum '''
        cur = self.__conn.cursor()
        cur.execute('PRAGMA auto_vacuum = NONE')
#        cur.execute('PRAGMA JOURNAL_MODE = MEMORY')
        cur.execute('PRAGMA JOURNAL_MODE = WAL')
#        cur.execute('PRAGMA SYNCHRONOUS = OFF')
        cur.execute('PRAGMA SYNCHRONOUS = NORMAL')
        self.__conn.commit()
        cur.close()
        self.__check_database()

    def acquire_write_lock(self):
        self.__write_lock.acquire()

    def release_write_lock(self):
        self.__write_lock.release()

    def __check_database(self):
        current_version = self.__current_database_version()
        logger.info("Current version of DB: " + str(current_version))
        if current_version is None or current_version != self.__db_version:
            logger.warning("Upgrading DB to version " + str(self.__db_version) + ", this will remove all flight data")
            self.__create_tables()
        else:
            logger.info("DB Scheme is up to date")

    def __current_database_version(self):
        ''' Do we have a version table at all '''
        cur = self.__conn.cursor()
        try:
            row = cur.execute('SELECT version from version').fetchone()
            if (row is None): return None
            return row[0]
        except sqlite3.Error as e:
            if str(e) == 'no such table: version':
                return None
            logger.error(str(e))
            raise e
        finally:
            cur.close()

    def __create_tables(self):
        self.acquire_write_lock()
        cur = self.__conn.cursor()
        try:
            ''' DROP tables '''
            cur.execute('DROP TABLE IF EXISTS version')
            cur.execute('DROP INDEX IF EXISTS frame_position_idx')
            cur.execute('DROP INDEX IF EXISTS frame_flight_idx')
            cur.execute('DROP TABLE IF EXISTS frame')
            cur.execute('DROP TABLE IF EXISTS announcement')

            ''' CREATE image table '''
            cur.execute('''
                CREATE TABLE frame (
                    id INTEGER PRIMARY KEY,
                    flight INTEGER,
                    camera INTEGER,
                    position INTEGER,
                    timestamp INTEGER,
                    image BLOB
                )
            ''')
            ''' Index needed for retrieval of image '''
            cur.execute('CREATE INDEX frame_position_idx ON frame (position, flight, camera)')
            ''' Index needed for deleting flight '''
            cur.execute('CREATE INDEX frame_flight_idx ON frame (flight)')

            ''' CREATE announcement table '''
            cur.execute('''
                CREATE TABLE announcement (
                    id INTEGER PRIMARY KEY,
                    flight INTEGER,
                    cam1_position INTEGER,
                    cam2_position INTEGER,
                    duration INTEGER,
                    speed INTEGER,
                    direction INTEGER
                )
            ''')

            ''' CREATE version table last '''
            cur.execute('''
                CREATE TABLE version (
	                version INTEGER PRIMARY KEY
                )
                ''')
            cur.execute('INSERT INTO version (version) VALUES(?)', str(self.__db_version))
            self.__conn.commit()
        except sqlite3.Error as e:
            if str(e) == 'no such table: version':
                return None
            logger.error(str(e))
            raise e
        finally:
            cur.close()
            self.release_write_lock()

    def get_conn(self):
        return self.__conn

    def stop(self):
        logger.info("Closing database")
        self.__conn.close()
