class WatchStore:
    """
    Modify and read from the file list store
    """

    def __init__(self, config_file_path, log):
        self.__config_file_path = config_file_path
        self.__log = log

    def list_files(self):
        """
        List all files being monitored
        :return: the list of files being monitored
        """
        with open(self.__config_file_path, 'r') as config_file:
            return config_file.read().splitlines()

    def add_file(self, file_path):
        """
        Add a file to the list of files being monitored
        :param file_path: the file path to add to the list
        """
        files = self.list_files()
        if file_path not in files:
            files.append(file_path)
            self.__write_files(files)
            self.__log.info(file_path + " added to list of monitored files ...")
        else:
            self.__log.warning("Attempt to add file which is already being monitored ({}), ignoring ...".format(file_path))

    def remove_file(self, file_path):
        """
        Remove a file from the list of files being monitored
        :param file_path: the file path to remove from the list
        """
        files = self.list_files()
        if file_path in self.list_files():
            files.remove(file_path)
            self.__write_files(files)
            self.__log.info(file_path + " removed from list of monitored files ...")
        else:
            self.__log.warning("Cannot remove non-existent file path {}, ignoring ...".format(file_path))

    def __write_files(self, files):
        with open(self.__config_file_path, 'w') as config_file:
            for file in files:
                print(file)
                config_file.write(file + "\n")
