''' One Announcement row '''
class Announcement:
   def __init__(self,
      cam1_frame_number,
      cam2_frame_number,
      time,
      speed,
      direction):

      self.__cam1_frame_number = cam1_frame_number
      self.__cam2_frame_number = cam2_frame_number
      self.__time = time
      self.__speed = speed
      self.__direction = direction 

   def get_cam1_frame_number(self):
      return self.__cam1_frame_number

   def get_cam2_frame_number(self):
      return self.__cam2_frame_number

   def get_time(self):
      return self.__time

   def get_speed(self):
      return self.__speed

   def get_direction(self):
      return self.__direction

''' Multiple announcement rows for one flight '''
class Announcements:
   def __init__(self):
      self.__announcements = []

   def clear(self):
      self.__announcements = []

   def append(self, announcement: Announcement):
      self.__announcements.append(announcement)

   def get_announcement_by_index(self, index):
      return self.__announcements[index]

   def get_announcements(self):
      return self.__announcements