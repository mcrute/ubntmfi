import json
import copy
import struct
import binascii
from Crypto.Cipher import AES
from cStringIO import StringIO


class BinaryDataStream(object):
    """Directional binary data stream

    Reads and writes binary data from any stream-like object. This object is
    not bi-directional. Does no interpertation just unpacking and packing.
    """

    def __init__(self, data):
        self.data = data

    @classmethod
    def for_output(cls):
        return cls(StringIO())

    def read_int(self):
        return struct.unpack(">i", self.data.read(4))[0]

    def read_short(self):
        return struct.unpack(">h", self.data.read(2))[0]

    def read_string(self, length):
        return self.data.read(length)

    def write_int(self, data):
        self.data.write(struct.pack(">i", data))

    def write_short(self, data):
        self.data.write(struct.pack(">h", data))

    def write_string(self, data):
        self.data.write(data)

    def get_output(self):
        return self.data.getvalue()


class Cryptor(object):
    """AES encryption strategy

    Handles AES crypto by wrapping pycrypto. Does padding and un-padding as
    well as key conversions when needed.
    """

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

    def encrypt(self, payload):
        return self.cipher.encrypt(self.pad(payload))


class InformPacket(object):
    """Inform model object

    Holds basic, parsed, inform packet data. Does some interpertation for
    fields like flags. Can be passed to and from the serialiser. This class
    only fully supports version 1 of the inform data protocol. Version 0
    payload parsing is not supported.
    """

    ENCRYPTED_FLAG = 0x1
    COMPRESSED_FLAG = 0x2

    def __init__(self):
        self.magic_number = None
        self.version = None
        self.mac_addr = None
        self.flags = None
        self.iv = None
        self.data_version = None
        self.data_length = None
        self.raw_payload = None
        self._used_key = None

    def response_copy(self):
        """Copy object for use in response

        Generates a deep copy of the object and removes the payload so that it
        can be used to respond to the station that send this inform request.
        """
        new_obj = copy.deepcopy(self)
        new_obj.raw_payload = None
        return new_obj

    @staticmethod
    def _format_mac_addr(mac_bytes):
        return ":".join([binascii.hexlify(i) for i in mac_bytes])

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
    def payload(self):
        if self.data_version == 1:
            return json.loads(self.raw_payload.decode("latin-1"))
        else:
            return self.raw_payload

    @payload.setter
    def payload(self, value):
        self.raw_payload = json.dumps(value)


class InformSerializer(object):
    """Inform protocol version 1 parser/serializer

    Handles the parsing of the inform binary protocol to python objects and
    seralization of python objects to inform binary protocol. Handles
    cryptography and data formats. Compatible only with version 1 of the data
    format.
    """

    MASTER_KEY = "ba86f2bbe107c7c57eb5f2690775c712"
    PROTOCOL_MAGIC = 1414414933
    MAX_VERSION = 1

    def __init__(self, key=None, key_bag=None):
        self.key = key
        self.key_bag = key_bag or {}

    def _decrypt_payload(self, packet):
        i = 0
        key = self.key_bag.get(packet.formatted_mac_addr)

        for key in (key, self.key, self.MASTER_KEY):
            if key is None:
                continue

            decrypted = Cryptor(key, packet.iv).decrypt(packet.raw_payload)

            json.loads(decrypted.decode("latin-1"))
            packet.raw_payload = decrypted
            packet._used_key = key
            break

    def parse(self, input):
        input_stream = BinaryDataStream(input)

        packet = InformPacket()

        packet.magic_number = input_stream.read_int()
        assert packet.magic_number == self.PROTOCOL_MAGIC

        packet.version = input_stream.read_int()
        assert packet.version < self.MAX_VERSION

        packet.mac_addr = input_stream.read_string(6)
        packet.flags = input_stream.read_short()
        packet.iv = input_stream.read_string(16)
        packet.data_version = input_stream.read_int()
        packet.data_length = input_stream.read_int()

        packet.raw_payload = input_stream.read_string(packet.data_length)

        if packet.is_encrypted:
            self._decrypt_payload(packet)

        return packet

    def _encrypt_payload(self, packet):
        if packet.data_version != 1:
            raise ValueError("Can no encrypt contents of pre 1.0 packets")

        key = packet._used_key if packet._used_key else self.MASTER_KEY
        return Cryptor(key, packet.iv).encrypt(json.dumps(packet.payload))

    def serialize(self, packet):
        output = BinaryDataStream.for_output()

        output.write_int(packet.magic_number)
        output.write_int(packet.version)
        output.write_string(packet.mac_addr)
        output.write_short(packet.flags)
        output.write_string(packet.iv)
        output.write_int(packet.data_version)
        output.write_int(packet.data_length)
        output.write_string(self._encrypt_payload(packet))

        return output.get_output()
