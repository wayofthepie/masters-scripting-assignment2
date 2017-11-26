import argparse
import logging
import os
import sys
import threading

from backupservice import BackupService
from watchstore import WatchStore

# Global log configuration
log = logging.getLogger()
log.setLevel(logging.DEBUG)
channel = logging.StreamHandler(sys.stdout)
channel.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
channel.setFormatter(formatter)
log.addHandler(channel)


def standalone(watch, backup_service, backup_location):
    """
    Runs a backup of the files in the config every 60 seconds
    :param watch: the watch store object
    :param backup_location: the location to backup to
    """
    log.info("Starting backup ...")
    threading.Timer(60, lambda: standalone(watch, backup_location)).start()
    backup_service.copy_files(watch.list_files(), backup_location)
    log.info("Backup complete ...")


def parse_args():
    """
    Parse the arguments to this script
    :return: the parsed arguments
    """
    parser = argparse.ArgumentParser(description='File watcher.')
    group = parser.add_mutually_exclusive_group(required=False)
    group.add_argument('--add', help='add file to the list of files being watched')
    group.add_argument('--remove', help='remove file from the list of files being watched')
    group.add_argument('--list', action='store_true', help='list files being watched')
    group.add_argument('--standalone', action='store_true', help='launch the app, backing up every minute')
    parser.add_argument('--config-location', default="config.dat", help='location of the config file')
    parser.add_argument('--backup-location', default="backup", help='location of the backup directory')
    return parser.parse_args()


def handle_args(config_location, backup_location, args):
    """
    Handle the arguments passed
    :param config_location: the config file location
    :param backup_location: the config file location
    :param args: the arguments
    """
    watch_store = WatchStore(config_location, log)
    backup_service = BackupService(log)
    if args.add is not None:
        file = args.add
        if os.path.isfile(file):
            if not os.path.isabs(file):
                raise ValueError("Relative paths are not supported!")
            watch_store.add_file(file)
        else:
            raise FileExistsError("File {} does not exist!".format(args.add))
    elif args.remove is not None:
        watch_store.remove_file(args.remove)
    elif args.list:
        log.info("The following files are being monitored: ")
        for file in watch_store.list_files():
            log.info(file)
    elif args.standalone:
        log.info("Scheduling a backup run every minute ...")
        standalone(watch_store, backup_service, backup_location)
    else:
        files = watch_store.list_files()
        if len(files) > 0:
            backup_service.copy_files(files, backup_location)
        else:
            log.warning("Config file {} does not contain any files, nothing to do.".format(config_location))


if __name__ == '__main__':
    args = parse_args()

    # Setup the config location
    config = args.config_location

    if not os.path.isfile(config):
        log.info("Config file does not exist, creating ...")
        open(config, 'w+').close()

    # Setup the backup location
    backup = args.backup_location

    log.info("Backup root path set to {}".format(os.path.abspath(backup)))
    log.info("Config path set to {}".format(os.path.abspath(config)))

    handle_args(config, backup, args)
