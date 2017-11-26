import argparse
import hashlib
import logging
import os
import shutil
import sys
import threading
import time

from watchstore import WatchStore

"""
Defaults for the backup and config file locations.
"""
STORE = "backup"
CONFIG_FILE = "config.dat"

# Global log configuration
log = logging.getLogger()
log.setLevel(logging.DEBUG)
channel = logging.StreamHandler(sys.stdout)
channel.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
channel.setFormatter(formatter)
log.addHandler(channel)


def standalone(watch, backup):
    """
    Runs a backup of the files in the config every 60 seconds
    :param watch: the watch store object
    :param backup: the location to backup to
    """
    log.info("Starting backup ...")
    threading.Timer(60, lambda: standalone(watch, backup)).start()
    copy_files(watch.list_files(), backup)
    log.info("Backup complete ...")


def parse_args():
    """
    Parse the arguments to this script
    :return: the parsed arguments
    """
    parser = argparse.ArgumentParser(description='File watcher.')
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--add', nargs=1, help='add file to the list of files being watched')
    group.add_argument('--remove', nargs=1, help='remove file from the list of files being watched')
    group.add_argument('--list', action='store_true', help='list files being watched')
    group.add_argument('--standalone', action='store_true', help='launch the app, backing up every minute')
    parser.add_argument('--config-location', nargs=1, help='location of the config file')
    parser.add_argument('--backup-location', nargs=1, help='location of the backup directory')
    return parser.parse_args()


def hash_file(file_path):
    """
    Generate a SHA1 hash of a file
    :param file_path: path to the file
    :return: the SHA1 hash as a hexadecimal string
    """
    buffersize = 64000
    sha1 = hashlib.sha1()
    with open(file_path, 'rb') as file:
        data = file.read(buffersize)
        while data != b'':
            sha1.update(data)
            data = file.read(buffersize)
    return sha1.hexdigest()


def copy_file(file, backup_root):
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
        log.info("Backed up {} into {}".format(file, backup_dir + "/" + timestamp))

    if os.path.isfile(file):
        if not os.path.isabs(file):
            log.warning("{} is a relative path, and is not supported!\n"
                        "Please remove from file list. Ignoring and continuing.".format(file))
            return

        backup_dir = backup_root + os.path.abspath(file)
        prev_backup = backup_dir + "/latest"
        if os.path.isfile(prev_backup):

            prev_hash = hash_file(prev_backup)
            new_hash = hash_file(file)
            if prev_hash != new_hash:
                copy_timestamped(file, backup_dir)
            else:
                log.info("{} is unchanged, not backing up ...".format(file))
        else:
            os.makedirs(backup_dir, exist_ok=True)
            copy_timestamped(file, backup_dir)
    else:
        log.warning("{} does not exist! Please remove from file list. Ignoring and continuing.".format(file))


def copy_files(files, backup_root):
    """
    Copy the list of files into the given backup root directory
    :param files: the list of files
    :param backup_root: the root directory to backup into
    """
    for file in files:
        if file.rstrip():
            copy_file(file, backup_root)


if __name__ == '__main__':
    args = parse_args()

    # Setup the config location
    config = CONFIG_FILE
    if args.config_location is not None:
        config = args.config_location[0]
        log.info("Config path set to ".format(os.path.abspath(config)))

    if not os.path.isfile(config):
        log.info("Config file does not exist, creating ...")
        open(config, 'w+')

    # Setup the backup location
    backup = STORE
    if args.backup_location is not None:
        backup = args.backup_location[0]
        log.info("Backup root path set to {}".format(os.path.abspath(backup)))

    watch = WatchStore(config, log)

    if args.add is not None:
        file = args.add[0]
        if os.path.isfile(file):
            if not os.path.isabs(file):
                raise ValueError("Relative paths are not supported!")
            watch.add_file(file)
        else:
            raise FileExistsError("File {} does not exist!".format(args.add[0]))
    elif args.remove is not None:
        watch.remove_file(args.remove[0])
    elif args.list:
        log.info("The following files are being monitored: ")
        for file in watch.list_files():
            log.info(file)
    elif args.standalone:
        log.info("Scheduling a backup run every minute ...")
        standalone(watch, backup)
    else:
        files = watch.list_files()
        if len(files) > 0:
            copy_files(files, backup)
        else:
            log.warning("Config file {} does not contain any files, nothing to do.".format(config))
