class OfflineError(Exception):
    ''' Raised when cameras ar offline '''
    def __init__(self, message):
        self.message = message

class IllegalStateError(Exception):
    ''' Raised when a state is incorrect '''
    def __init__(self, message):
        self.message = message

class NotFoundError(Exception):
    ''' Raised when a state is incorrect '''
    def __init__(self, message):
        self.message = message
