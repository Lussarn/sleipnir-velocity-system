import sqlite3
from sqlite3.dbapi2 import OperationalError, connect

class DB:
    def __init__(self):
        self.__db_version = 1
        self.__conn = sqlite3.connect("sleipnir.db")
        self.__check_database()

    def __del__(self):
        self.__conn.close()

    def __check_database(self):
        current_version = self.__current_database_version()
        print ("INFO: DB.__check_database: Current version of DB: " + str(current_version))
        if current_version is None or current_version != self.__db_version:
            print ("WARNING: DB.__check_database: Upgrading DB to version " + str(self.__db_version) + ", this will remove all flight data")
            self.__create_tables()
        else:
            print ("INFO: DB.__check_database: DB Scheme is up to date")

    def __current_database_version(self):
        ''' Do we have a version table at all '''
        cur = self.__conn.cursor()
        try:
            row = cur.execute('SELECT version from version').fetchone()
            if (row is None): return None
            return row[0]
        except OperationalError as e:
            if str(e) == 'no such table: version':
                return None
            print ("ERROR: DB.__current_database_version: " + str(e))
            raise e
        finally:
            cur.close()

    def __create_tables(self):
        cur = self.__conn.cursor()
        try:
            ''' DROP tables '''
            cur.execute('DROP TABLE IF EXISTS version')
            cur.execute('DROP INDEX IF EXISTS image_frame_idx')
            cur.execute('DROP INDEX IF EXISTS image_flight_idx')
            cur.execute('DROP TABLE IF EXISTS image')
            cur.execute('DROP TABLE IF EXISTS announcement')

            ''' CREATE image table '''
            cur.execute('''
                CREATE TABLE image (
                    id INTEGER PRIMARY KEY,
                    flight INTEGER,
                    camera INTEGER,
                    frame INTEGER,
                    timestamp INTEGER,
                    image BLOB
                )
            ''')
            ''' Index needed for retrieval of image '''
            cur.execute('CREATE INDEX image_frame_idx ON image (frame, flight, camera)')
            ''' Index needed for deleting flight '''
            cur.execute('CREATE INDEX image_flight_idx ON image (flight)')

            ''' CREATE announcement table '''
            cur.execute('''
                CREATE TABLE announcement (
                    id INTEGER PRIMARY KEY,
                    flight INTEGER,
                    cam1_frame INTEGER,
                    cam2_frame INTEGER,
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
        except OperationalError as e:
            if str(e) == 'no such table: version':
                return None
            print ("ERROR: DB.__current_database_version: " + str(e))
            raise e
        finally:
            cur.close()

    def get_conn(self):
        return self.__conn