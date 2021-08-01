class MissingModule:
    """A shim class that throws errors only when a user tries to use a missing
    optional dependency."""
    def __init__(self, error_msg):
        self.error_msg = error_msg
    def __getattr__(self, name):
        raise RuntimeError(self.error_msg)
