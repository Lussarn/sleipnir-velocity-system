import sqlite3
from sqlite3.dbapi2 import OperationalError

from database.DB import DB
from Frame import Frame

import logging
logger = logging.getLogger(__name__)

def store(db: DB, frame: Frame):
    db.acquire_write_lock()
    cur = db.get_conn().cursor()
    try:
        cur.execute('''INSERT INTO frame
            (flight, camera, position, timestamp, image)
            VALUES (?, ?, ?, ?, ?)
            ''',[
            str(frame.get_flight()),
            str(frame.get_camera()),
            str(frame.get_position()),
            str(frame.get_timestamp()),
            frame.get_image()
            ])
        db.get_conn().commit()
    except OperationalError as e:
        logger.error(str(e))
        raise e
    finally:
        cur.close()
        db.release_write_lock()

def load(db: DB, flight: int, cam: int, position: int) -> Frame:
    cur = db.get_conn().cursor()
    try:
        row = cur.execute(
            '''SELECT timestamp, image FROM frame WHERE position=? AND flight=? and camera=?''',
            [str(position),
            str(flight),
            str(cam)]).fetchone()
        if row is None: return None
        return Frame(flight, cam, position, row[0], row[1])
    except sqlite3.Error as e:
        logger.error(str(e))
        raise e
    finally:
        cur.close()

def delete_flight(db: DB, flight: int):
    db.acquire_write_lock()
    cur = db.get_conn().cursor()
    try:
        logger.debug("Deleting frames for flight " + str(flight))
        cur.execute('DELETE FROM frame WHERE flight=?', [str(flight)])
        logger.debug("Deleting announcements for flight " + str(flight))
        cur.execute('DELETE FROM announcement WHERE flight=?', [str(flight)])
        db.get_conn().commit()
    except OperationalError as e:
        logger.error(str(e))
        raise e
    finally:
        cur.close()
        db.release_write_lock()

def load_flight_timestamps(db: DB, flight: int, camera: int):
    cur = db.get_conn().cursor()
    try:
        return cur.execute(
            '''SELECT position, timestamp FROM frame WHERE flight=? AND camera=?''',
            [str(flight),
            str(camera)]).fetchall()
    except sqlite3.Error as e:
        logger.error(str(e))
        raise e
    finally:
        cur.close()

def load_frame_count(db: DB, flight: int, camera: int) -> int:
    cur = db.get_conn().cursor()
    try:
        rs = cur.execute(
            '''SELECT position FROM frame WHERE flight=? AND camera=? ORDER BY id DESC LIMIT 1''',
            [str(flight),
            str(camera)]).fetchone()
        if rs is None: return None
        return int(rs[0])
    except sqlite3.Error as e:
        logger.error(str(e))
        raise e
    finally:
        cur.close()

def load_timestamp(db: DB, flight: int, cam: int, position: int) -> int:
    cur = db.get_conn().cursor()
    try:
        row = cur.execute(
            '''SELECT timestamp FROM frame WHERE position=? AND flight=? and camera=?''',
            [str(position),
            str(flight),
            str(cam)]).fetchone()
        if row is None: return None
        return int(row[0])
    except sqlite3.Error as e:
        logger.error(str(e))
        raise e
    finally:
        cur.close()
