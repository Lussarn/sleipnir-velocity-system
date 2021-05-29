import sqlite3
from sqlite3.dbapi2 import OperationalError

from Announcements import Announcements, Announcement
from database.DB import DB

import logging
logger = logging.getLogger(__name__)

def store(db: DB, flight_number: int, announcements: Announcements):
    db.acquire_write_lock()
    cur = db.get_conn().cursor()
    try:
        cur.execute("DELETE FROM announcement WHERE flight=?", str(flight_number))
        db.get_conn().commit()
        for announcement in announcements.get_announcements():
            cur.execute('''INSERT INTO announcement
                (flight, cam1_position, cam2_position, duration, speed, direction)
                VALUES (?, ?, ?, ?, ?, ?)
                ''',[
                str(flight_number),
                str(announcement.get_cam1_position()),
                str(announcement.get_cam2_position()),
                str(announcement.get_duration()),
                str(announcement.get_speed()),
                str(announcement.get_direction())
                ])
        db.get_conn().commit()
    except sqlite3.Error as e:
        logger.error(str(e))
        raise e
    finally:
        cur.close()
        db.release_write_lock()
 
def fetch(db: DB, flight: int):
    cur = db.get_conn().cursor()
    announcements = Announcements()
    try:
        for row in cur.execute(
            '''SELECT cam1_position, cam2_position, duration, speed, direction FROM announcement WHERE flight=?''',
            [str(flight)]):
                  announcements.append(Announcement(
                     int(row[0]),
                     int(row[1]),
                     int(row[2]),
                     int(row[3]),
                     int(row[4])
                  ))
    except sqlite3.Error as e:
        logger.error(str(e))
        raise e
    finally:
        cur.close()
    return announcements