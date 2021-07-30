
class MissingModule:
    def __init__(self, error_msg):
        self.error_msg = error_msg
    def __getattr__(self, name):
        raise RuntimeError(self.error_msg)

