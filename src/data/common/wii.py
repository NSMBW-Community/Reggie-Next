import os


class WiiObject:
    @classmethod
    def load(cls, data, *args, **kwargs):
        self = cls()
        self._load(data, *args, **kwargs)
        return self

    @classmethod
    def loadFile(cls, filename, *args, **kwargs):
        return cls.load(open(filename, 'rb').read(), *args, **kwargs)

    def dump(self, *args, **kwargs):
        return self._dump(*args, **kwargs)

    def dumpFile(self, filename, *args, **kwargs):
        open(filename, 'wb').write(self.dump(*args, **kwargs))
        return filename


class WiiArchive(WiiObject):
    @classmethod
    def loadDir(cls, dirname):
        self = cls()
        self._loadDir(dirname)
        return self

    def dumpDir(self, dirname):
        if not os.path.isdir(dirname):
            os.mkdir(dirname)
        self._dumpDir(dirname)
        return dirname


class WiiHeader:
    def __init__(self, data):
        self.data = data

    def addFile(self, filename):
        open(filename, 'wb').write(self.add())

    def removeFile(self, filename):
        open(filename, 'wb').write(self.remove())

    @classmethod
    def loadFile(cls, filename, *args, **kwargs):
        return cls(open(filename, 'rb').read(), *args, **kwargs)
