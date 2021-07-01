from threading import Lock
import os

import sqlite3

import logging

logger = logging.getLogger(__name__)

class DB():
    __write_lock = Lock()

    def __init__(self, save_path):
        self.__db_version = 2
        logger.info("Opening database" + os.path.join(save_path, 'sleipnir.db'))
        self.__conn = sqlite3.connect(os.path.join(save_path, 'sleipnir.db'), check_same_thread = False)

        ''' Disable auto vacuum '''
        cur = self.__conn.cursor()
        cur.execute('PRAGMA auto_vacuum = NONE')
        cur.execute('PRAGMA JOURNAL_MODE = WAL')
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
            cur.execute('DROP TABLE IF EXISTS frame')
            cur.execute('DROP TABLE IF EXISTS speed_trap_frame')
            cur.execute('DROP TABLE IF EXISTS gate_crasher_frame')
            cur.execute('DROP TABLE IF EXISTS announcement')
            cur.execute('DROP TABLE IF EXISTS speed_trap_announcement')
            cur.execute('DROP TABLE IF EXISTS gate_crasher_gate_hit')

            ''' CREATE frame tables for the games '''
            for game in ['align', 'speed_trap', 'gate_crasher']:
                cur.execute('''
                    CREATE TABLE %s_frame (
                        id INTEGER PRIMARY KEY,
                        flight INTEGER,
                        camera INTEGER,
                        position INTEGER,
                        timestamp INTEGER,
                        image BLOB
                    )
                ''' % game)
                ''' Index needed for retrieval of image '''
                cur.execute("CREATE INDEX %s_frame_position_idx ON %s_frame (position, flight, camera)" % (game, game))
                ''' Index needed for deleting flight '''
                cur.execute('CREATE INDEX %s_frame_flight_idx ON %s_frame (flight)' % (game, game))

            ''' CREATE speed trap announcement table '''
            cur.execute('''
                CREATE TABLE speed_trap_announcement (
                    id INTEGER PRIMARY KEY,
                    flight INTEGER,
                    cam1_position INTEGER,
                    cam2_position INTEGER,
                    duration INTEGER,
                    speed REAL,
                    direction INTEGER
                )
            ''')

            ''' CREATE gate table for gate crasher '''
            cur.execute(''' 
                CREATE TABLE gate_crasher_announcement (
                    id INTEGER PRIMARY KEY,
                    flight INTEGER,
                    level_name TEXT,
                    gate_number INTEGER,
                    camera INTEGER,
                    position INTEGER,
                    timestamp INTEGER,
                    direction INTEGER,
                    angle INTEGER,
                    altitude INTEGER,
                    time INTEGER
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
