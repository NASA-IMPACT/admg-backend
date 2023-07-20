class temp_disconnect_signal:
    """Context manager for temporarily disconnecting a model from a signal"""

    def __init__(self, signal, receiver, sender, dispatch_uid=None):
        self.signal = signal
        self.receiver = receiver
        self.sender = sender
        self.dispatch_uid = dispatch_uid

    def __enter__(self):
        self.signal.disconnect(
            receiver=self.receiver, sender=self.sender, dispatch_uid=self.dispatch_uid
        )

    def __exit__(self, type, value, traceback):
        self.signal.connect(
            receiver=self.receiver, sender=self.sender, dispatch_uid=self.dispatch_uid
        )
