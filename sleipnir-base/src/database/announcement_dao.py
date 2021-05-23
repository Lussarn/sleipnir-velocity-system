import sqlite3
from sqlite3.dbapi2 import OperationalError

from Announcements import Announcements, Announcement
from database.DB import DB

def store(db: DB, flight_number: int, announcements: Announcements):
    cur = db.get_conn().cursor()
    try:
        cur.execute("DELETE FROM announcement WHERE flight=?", str(flight_number))
        db.get_conn().commit()
        for announcement in announcements.get_announcements():
            cur.execute('''INSERT INTO announcement
                (flight, cam1_frame, cam2_frame, duration, speed, direction)
                VALUES (?, ?, ?, ?, ?, ?)
                ''',[
                str(flight_number),
                str(announcement.get_cam1_frame_number()),
                str(announcement.get_cam2_frame_number()),
                str(announcement.get_time()),
                str(announcement.get_speed()),
                str(announcement.get_direction())
                ])
        db.get_conn().commit()
    except OperationalError as e:
        print ("ERROR: announcement_dao.store: " + str(e))
        raise e
    finally:
        cur.close()
 
def fetch(db: DB, flight_number: int):
    cur = db.get_conn().cursor()
    announcements = Announcements()
    try:
        for row in cur.execute(
            '''SELECT flight, cam1_frame, cam2_frame, duration, speed, direction FROM announcement WHERE flight=?''',
            str(flight_number)):
                  announcements.append(Announcement(
                     int(row[0]),
                     int(row[1]),
                     int(row[2]),
                     int(row[3]),
                     int(row[4])
                  ))
    except OperationalError as e:
        print ("ERROR: announcement_dao.fetch: " + str(e))
        raise e
    finally:
        cur.close()
    return announcements