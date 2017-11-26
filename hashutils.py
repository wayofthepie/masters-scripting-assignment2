import hashlib


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


def hash_string(string):
    """
    Compute the sha1 hash of the given string
    :param string: the string to compute the hash from
    :return: the hash value
    """
    sha1 = hashlib.sha1()
    sha1.update(string)
    return sha1.hexdigest()


def is_sha1_hash(hex_string):
    """
    Computes whether the given hex string is a sha1 hash by converting
    the string to an
    :param hex_string:
    :return:
    """
    return int.from_bytes(bytearray.fromhex(hex_string), 'big').bit_length() == 160
