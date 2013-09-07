import struct
import binascii
from Crypto.Cipher import AES


class BinaryDataStream(object):

    def __init__(self, data):
        self.data = data

    def read_int(self):
        return struct.unpack(">i", self.data.read(4))[0]

    def read_short(self):
        return struct.unpack(">h", self.data.read(2))[0]

    def read_string(self, length):
        return self.data.read(length)


class Cryptor(object):

    def __init__(self, key, iv):
        self.iv = iv
        self.key = key
        self.cipher = AES.new(key.decode("hex"), AES.MODE_CBC, iv)

    @staticmethod
    def unpad(s):
        return s[0:-ord(s[-1])]

    @staticmethod
    def pad(s, BS=16):
        return s + (BS - len(s) % BS) * chr(BS - len(s) % BS) 

    def decrypt(self, payload):
        return self.unpad(self.cipher.decrypt(payload))


class InformParser(object):

    PROTOCOL_MAGIC = 1414414933
    MAX_VERSION = 1

    ENCRYPTED_FLAG = 0x1
    COMPRESSED_FLAG = 0x2

    def __init__(self, input_stream, key):
        self.input_stream = input_stream
        self.key = key

        self.magic_number = None
        self.version = None
        self.mac_addr = None
        self.flags = None
        self.iv = None
        self.data_version = None
        self.data_length = None
        self.payload = None

    @classmethod
    def open(cls, filename, key):
        return cls(BinaryDataStream(open(filename, "rb")), key)

    @staticmethod
    def _format_mac_addr(mac_bytes):
        return "-".join([binascii.hexlify(i) for i in mac_bytes])

    def _has_flag(self, flag):
        return self.flags & flag != 0

    @property
    def formatted_mac_addr(self):
        return self._format_mac_addr(self.mac_addr)

    @property
    def is_encrypted(self):
        return self._has_flag(self.ENCRYPTED_FLAG)

    @property
    def is_compressed(self):
        return self._has_flag(self.COMPRESSED_FLAG)

    @property
    def decrypted_payload(self):
        return Cryptor(self.key, self.iv).decrypt(self.payload)

    def parse(self):
        self.magic = self.input_stream.read_int()
        assert self.magic == self.PROTOCOL_MAGIC

        self.version = self.input_stream.read_int()
        assert self.version < self.MAX_VERSION

        self.mac_addr = self.input_stream.read_string(6)
        self.flags = self.input_stream.read_short()
        self.iv = self.input_stream.read_string(16)
        self.data_version = self.input_stream.read_int()
        self.data_length = self.input_stream.read_int()
        self.payload = self.input_stream.read_string(self.data_length)

        return self
