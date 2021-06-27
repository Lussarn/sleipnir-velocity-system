''' One Announcement row '''
class Announcement:
   def __init__(self,
      cam1_position,
      cam2_position,
      duration,
      speed,
      direction):

      self.__cam1_position = cam1_position
      self.__cam2_position = cam2_position
      self.__time = duration
      self.__speed = speed
      self.__direction = direction 

   def get_cam1_position(self):
      return self.__cam1_position

   def get_cam2_position(self):
      return self.__cam2_position

   def get_duration(self):
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

   def get_announcement_by_index(self, index: int) -> Announcement:
      return self.__announcements[index]

   def get_announcements(self):
      return self.__announcements

   def remove_announcement_by_index(self, index):
      del self.__announcements[index]

   def count(self):
      return len(self.__announcements)