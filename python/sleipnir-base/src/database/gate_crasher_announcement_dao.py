from typing import List

import sqlite3
from sqlite3.dbapi2 import OperationalError

from gate_crasher_announcement import GateCrasherAnnouncement
from database.db import DB

import logging
logger = logging.getLogger(__name__)

def store(db: DB, flight: int, announcements: List[GateCrasherAnnouncement]):
    db.acquire_write_lock()
    cur = db.get_conn().cursor()
    try:
        cur.execute("DELETE FROM gate_crasher_announcement WHERE flight=?", [str(flight)])
        db.get_conn().commit()
        for announcement in announcements:
            cur.execute('''INSERT INTO gate_crasher_announcement
                (flight, level_name, gate_number, camera, position, timestamp, direction, angle, altitude, time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',[
                str(flight),
                announcement.get_level_name(),
                str(announcement.get_gate_number()),
                str(1 if announcement.get_cam() == 'cam1' else 2),
                str(announcement.get_position()),
                str(announcement.get_timestamp()),
                str(-1 if announcement.get_direction() == 'LEFT' else 1),
                str(1 if announcement.get_angle() == 'ANGLE' else 0),
                str(0 if announcement.get_altitude() == 'LOW' else 1),
                str(announcement.get_time_ms())
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
    announcements = []
    try:
        for row in cur.execute(
            '''SELECT level_name, gate_number, camera, position, timestamp, direction, angle, altitude, time FROM gate_crasher_announcement WHERE flight=?''',
            [str(flight)]):
                announcements.append(GateCrasherAnnouncement(
                    row[0],
                    int(row[1]),
                    'cam1' if row[2] == 1 else 'cam2',
                    int(row[3]),
                    int(row[4]),
                    'LEFT' if row[5] == -1 else 'RIGHT',
                    'ANGLE' if row[6] == 1 else 'FLAT',
                    'LOW' if row[7] == 0 else 'HIGH',
                    int(row[8])
                 ))
    except sqlite3.Error as e:
        logger.error(str(e))
        raise e
    finally:
        cur.close()
    return announcements

def delete_flight(db: DB, flight: int):
    db.acquire_write_lock()
    cur = db.get_conn().cursor()
    try:
        logger.debug("Deleting gate crasher announcements for flight " + str(flight))
        cur.execute('DELETE FROM gate_crasher_announcement WHERE flight=?', [str(flight)])
        db.get_conn().commit()
    except OperationalError as e:
        logger.error(str(e))
        db.release_write_lock()
        raise e
    finally:
        cur.close()
        db.release_write_lock()
