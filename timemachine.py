import argparse
import logging
import os
import shutil
import sys
import threading
import time
from pathlib import Path

import hashutils
from watchstore import WatchStore

"""
Defaults for the backup and config file locations.
"""
STORE = "backup"
CONFIG_FILE = "config.dat"
log = logging.getLogger()

# Global log configuration
log.setLevel(logging.DEBUG)
channel = logging.StreamHandler(sys.stdout)
channel.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
channel.setFormatter(formatter)
log.addHandler(channel)


def standalone(watch, backup):
    log.info(" Starting backup ...")
    threading.Timer(60, lambda: standalone(watch, backup)).start()
    copy_files(watch.list_files(), backup)
    log.info(" Backup complete ...")


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


def copy_file(file, backup_root):
    """
    Copy the given file to the configured backup location
    :param file:
    :return:
    """

    def copy_timestamped(f, backup_dir):
        """
        Copy the given file to the directory, as a timestamp. Also
        create a latest file, denoting the latest copy of this file.
        :param f: the file to copy
        :param backup_dir: the directory to copy into
        """
        timestamp = time.strftime("%d-%h-%y_%H-%M-%S")
        shutil.copy(f, backup_dir + "/" + timestamp)
        shutil.copy(f, backup_dir + "/latest")
        log.info("Backed up " + f + " into " + backup_dir + "/" + timestamp)

    if os.path.isfile(file):
        backup_dir = backup_root + os.path.abspath(file)
        prev_backup = backup_dir + "/latest"
        if os.path.isfile(prev_backup):
            prev_hash = hashutils.hash_file(prev_backup)
            new_hash = hashutils.hash_file(file)
            if prev_hash != new_hash:
                copy_timestamped(file, backup_dir)
            else:
                log.info(file + " is unchanged, not backing up ...")
        else:
            os.makedirs(backup_dir, exist_ok=True)
            copy_timestamped(file, backup_dir)
    else:
        log.warning("\"" + file + "\"" + " does not exist! Please remove from file list. Ignoring and continuing.")


def copy_files(files, backup_root):
    """
    Copy the list of files into the given backup root directory
    :param files: the list of files
    :param backup_root: the root directory to backup into
    """
    for file in files:
        copy_file(file, backup_root)


if __name__ == '__main__':
    args = parse_args()

    # Setup the config location
    config = CONFIG_FILE
    if args.config_location is not None:
        config = args.config_location[0]
        log.info("Config path set to " + os.path.abspath(config))

    if not os.path.isfile(config):
        log.info("Config file does not exist, creating ...")
        Path(config).touch()

    # Setup the backup location
    backup = STORE
    if args.backup_location is not None:
        backup = args.backup_location[0]
        log.info("Backup root path set to " + os.path.abspath(backup))

    watch = WatchStore(config, log)

    if args.add is not None:
        file = args.add[0]
        if os.path.isfile(file):
            watch.add_file(file)
        else:
            raise FileExistsError("File " + args.add[0] + " does not exist!")
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
        copy_files(watch.list_files(), backup)
