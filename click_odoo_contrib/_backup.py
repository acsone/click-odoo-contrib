# Copyright 2018 ACSONE SA/NV.
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).
import os
import shutil
import tempfile
import zipfile
from contextlib import contextmanager


class AbstractBackup(object):
    """Abstract class with methods to open, read, write, close,
    a backup
    """

    def __init__(self, path, mode):
        """
        :param path: Either the path to the file, or a file-like object, or a folder
                     or ... .
        :param mode: The mode can be either read "r", write "w" or append "a"
        """
        self._path = path
        self._mode = mode

    def addtree(self, src, arcname):
        """Recursively add a directory tree into the backup.
        :param dirname: Directory to copy from
        :param arcname: the root path of copied files into the archive
        """
        raise NotImplementedError()  # pragma: no cover

    def addfile(self, filename, arcname):
        """Add a file to the backup.

        :param filename: the path to the souce file
        :param arcname: the path into the backup
        """
        raise NotImplementedError()  # pragma: no cover

    def write(self, stream, arcname):
        """Write a stream into the backup.

        :param arcname: the path into the backup
        """
        raise NotImplementedError()  # pragma: no cover

    def close(self):
        """Close the backup
        """
        raise NotImplementedError()  # pragma: no cover

    def delete(self):
        """Deelte the backup
        """
        raise NotImplementedError()  # pragma: no cover


class ZipBackup(AbstractBackup):

    format = "zip"

    def __init__(self, path, mode):
        super(ZipBackup, self).__init__(path, mode)
        self._zipFile = zipfile.ZipFile(
            self._path, self._mode, compression=zipfile.ZIP_DEFLATED, allowZip64=True
        )

    def addtree(self, src, arcname):
        len_prefix = len(src) + 1
        for dirpath, _dirnames, filenames in os.walk(src):
            for fname in filenames:
                path = os.path.normpath(os.path.join(dirpath, fname))
                if os.path.isfile(path):
                    _arcname = os.path.join(arcname, path[len_prefix:])
                    self._zipFile.write(path, _arcname)

    def addfile(self, filename, arcname):
        self._zipFile.write(filename, arcname)

    def write(self, stream, arcname):
        with tempfile.NamedTemporaryFile() as f:
            shutil.copyfileobj(stream, f)
            f.seek(0)
            self._zipFile.write(f.name, arcname)

    def close(self):
        self._zipFile.close()

    def delete(self):
        try:
            self.close()
        finally:
            os.unlink(self._path)


class FolderBackup(AbstractBackup):

    format = "folder"

    def __init__(self, path, mode):
        super(FolderBackup, self).__init__(path, mode)
        os.mkdir(self._path)

    def addtree(self, src, arcname):
        dest = os.path.join(self._path, arcname)
        shutil.copytree(src, dest)

    def addfile(self, filename, arcname):
        shutil.copyfile(filename, os.path.join(self._path, arcname))

    def write(self, stream, arcname):
        with open(os.path.join(self._path, arcname), "wb") as f:
            shutil.copyfileobj(stream, f)

    def close(self):
        pass

    def delete(self):
        shutil.rmtree(self._path)


BACKUP_FORMAT = {ZipBackup.format: ZipBackup, FolderBackup.format: FolderBackup}


@contextmanager
def backup(format, path, mode):
    backup_class = BACKUP_FORMAT.get(format)
    if not backup_class:  # pragma: no cover
        raise Exception(
            "Format {} not supported. Available formats: {}".format(
                format, "|".join(BACKUP_FORMAT.keys())
            )
        )
    _backup = backup_class(path, mode)
    try:
        yield _backup
        _backup.close()
    except Exception as e:
        _backup.delete()
        raise e
