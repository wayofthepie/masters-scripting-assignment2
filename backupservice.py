import hashlib
import os
import shutil
import time


class BackupService:
    """
    Backup files
    """
    def __init__(self, log):
        self.__log = log
        self.__buffersize = 64000

    def copy_files(self, files, backup_root):
        """
        Copy the list of files into the given backup root directory
        :param files: the list of files
        :param backup_root: the root directory to backup into
        """
        for file in files:
            if file.rstrip():
                self.__copy_file(file, backup_root)

    def __copy_file(self, file, backup_root):
        """
        Copy the given file to the configured backup location. This creates
        the full directory structure of the file being copied, underneath the
        backup_root directory. It will also create a directory named after the file
        itself and when backing up will copy the file into this directory renaming
        the backed up file to the current timestamp. Finally it will create a
        file called "latest" every time we run a backup so we can trivially
        compare the last backed up file with the file on the next backup run.
        :param file: the file to backup.
        """

        def copy_timestamped(f, backup_dir):
            """
            Copy the given file to the directory, named just as a timestamp. Also
            create a latest file, denoting the latest copy of this file.
            :param f: the file to copy
            :param backup_dir: the directory to copy into
            """
            timestamp = time.strftime("%d-%h-%y_%H-%M-%S")
            shutil.copy(f, backup_dir + "/" + timestamp)
            shutil.copy(f, backup_dir + "/latest")
            self.__log.info("Backed up {} into {}".format(file, backup_dir + "/" + timestamp))

        if os.path.isfile(file):
            if not os.path.isabs(file):
                self.__log.warning("{} is a relative path, and is not supported!\n"
                                   "Please remove from file list. Ignoring and continuing.".format(file))
                return

            backup_dir = backup_root + os.path.abspath(file)
            prev_backup = backup_dir + "/latest"
            if os.path.isfile(prev_backup):

                prev_hash = self.__hash_file(prev_backup)
                new_hash = self.__hash_file(file)
                if prev_hash != new_hash:
                    copy_timestamped(file, backup_dir)
                else:
                    self.__log.info("{} is unchanged, not backing up ...".format(file))
            else:
                os.makedirs(backup_dir, exist_ok=True)
                copy_timestamped(file, backup_dir)
        else:
            self.__log.warning("{} does not exist! Please remove from file list. Ignoring and continuing.".format(file))

    def __hash_file(self, file_path):
        """
        Generate the SHA1 hash of a file
        :param file_path: path to the file
        :return: the SHA1 hash as a hexadecimal string
        """
        sha1 = hashlib.sha1()
        with open(file_path, 'rb') as file:
            data = file.read(self.__buffersize)
            while data != b'':
                sha1.update(data)
                data = file.read(self.__buffersize)
        return sha1.hexdigest()
