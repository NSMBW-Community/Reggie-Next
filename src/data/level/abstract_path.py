class AbstractPath:
    """
    Abstract base class for the path manager. Provides only necessary fields and methods.
    Mainly used for instance checks while preventing circular imports.
    """
    def __init__(self):
        self._nodes = []
