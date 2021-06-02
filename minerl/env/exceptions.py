class EnvException(Exception):
    """A special exception thrown in the creation of an environment's Malmo mission XML.

    Args:
        message (str): The exception message.
    """

    def __init__(self, message):
        super(EnvException, self).__init__(message)


class MissionInitException(Exception):
    """An exception thrown when a mission fails to initialize

    Args:
        message (str): The exception message.
    """

    def __init__(self, message):
        super(MissionInitException, self).__init__(message)


class SlowOperationException(Exception):
    """
    Exception thrown when we step the environment too slowly, which can cause java timeouts.
    """

    def __init__(self, message):
        super(SlowOperationException, self).__init__(message)


class BadObservationException(Exception):
    """
    Exception thrown when observations received from java are malformed and can't be processed.
    """

    def __init__(self, message):
        super(BadObservationException, self).__init__(message)
