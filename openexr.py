#!/usr/bin/env python
#encoding:utf-8
#pylint:disable-msg=C0111,R0903

import struct

## Definitons

class Compression:
    NO = 0
    RLE = 1
    ZIPS = 2
    ZIP = 3
    PIZ = 4
    PXR24 = 5
    B44 = 6
    B44A = 7

    LOOKUP = ["NO", "RLE", "ZIPS", "ZIP", "PIZ", "PXR24", "B44", "B44A"]

    def __init__(self, value):
        self.value = value
        self.name = self.LOOKUP[value]

    def __repr__(self):
        return self.LOOKUP[self.value]

class LineOrder:
    INCREASING_Y = 0
    DECREASING_Y = 1
    RANDOM_Y = 2

    LOOKUP = ["INCREASING_Y", "DECREASING_Y", "RANDOM_Y"]

    def __init__(self, value):
        self.value = value
        self.name = self.LOOKUP[value]

    def __repr__(self):
        return self.name

class PixelType:
    UINT = 0
    HALF = 1
    FLOAT = 2

    LOOKUP = ["UINT", "HALF", "FLOAT"]

    def __init__(self, value):
        self.value = value
        self.name = self.LOOKUP[value]

    def __repr__(self):
        return self.name

## Exceptions
class NotAnExr(Exception):
    pass
class UnsupportedVersion(Exception):
    pass
class UnimplementedDatatype(Exception):
    pass
class UnimplementedCompression(Exception):
    pass

## Helpers
def str_hexseq(input_seq):
    return "".join([chr(x) for x in input_seq])

def read_null_term_str(f):
    cur_str = []
    while 1:
        cur_byte = f.read(1)
        if ord(cur_byte) == 0x00:
            return "".join(cur_str)
        else:
            cur_str.append(cur_byte)

def _parse_datatype(datatype, value):
    known = ["string", "float", "compression", "box2i", "lineOrder", "chlist"]

    if datatype not in known:
        raise UnimplementedDatatype(
            "Cannot parse datatype %s" % (datatype)
        )

    if datatype == "string":
        return value

    if datatype == "float":
        return struct.unpack('f', value)[0]

    if datatype == "compression":
        # return COMPRESSION[ord(value)]
        return Compression(ord(value))

    if datatype == "box2i":
        # box2i is 4 floats.
        # A float is 4 bytes, which can be struct.unpack'd

        #return [_parse_datatype("float",
        #                        value[x * 4 : (x * 4) + 4])
        #        for x in range(4)]

        ret = []
        for number in range(4):
            index_start = number * 4
            index_end = index_start + 4

            cur_float = value[index_start : index_end]

            ret.append(
                _parse_datatype("float", cur_float)
            )
        return ret

    if datatype == "lineOrder":
        return LineOrder(ord(value))

    if datatype == "chlist":
        from StringIO import StringIO
        s = StringIO(value)

        # Channel layout:
        # name (null terminated string)
        # pixel type (int, UINT = 0, HALF = 1, FLOAT = 2)
        # pLinear (char, either 0 or 1)
        # reserved (3 char, should all be zero)
        # xSampling (int)
        # ySampling (int)
        print len(value)
        channels = []
        while 1:
            if not s.read(1):
                break
            s.seek(-1, 1)

            name = read_null_term_str(s)
            pixel_type = ord(s.read(1))
            pLinear = ord(s.read(1)) == True
            reserved = s.read(3)
            try:
                xSampling = ord(s.read(1))
                ySampling = ord(s.read(1))
            except TypeError:
                print "Skipping"
                continue

            channels.append({
                'name': name,
                'pixel_type': pixel_type,
                'pLinear': pLinear,
                'xSampling': xSampling,
                'ySampling': ySampling
            })

        print channels
        return channels

## Main class
class OpenEXR(object):
    def __init__(self, fh):
        self.fh = fh

        self.headers = {}
        self.version = None

        self._end_of_header = None

    def _set_header(self, name, attr_type, attr_value):
        self.headers[name] = {
            'value': attr_value,
            'type': attr_type
        }

    def parse_headers(self):
        f = self.fh

        ## Check for "Magic Number"
        # First four bytes of the file should be
        # 0x76 0x2f 0x31 0x01
        magic_number = f.read(4)
        if not magic_number == str_hexseq([0x76, 0x2f, 0x31, 0x01]):
            raise NotAnExr("Could not find Magic Number")

        ## Parse "Version Field"
        # Version field is 4 bytes.
        # First byte is an int, of the version number:
        # Version 1 was an interal ILM version
        # Version 2 is the current

        version_field = f.read(4)

        version = ord(version_field[0])
        if version != 2:
            raise UnsupportedVersion(
                "Only version 2 is supported, detected %s" % (version)
            )
        self.version = version

        # Remaining 3 bytes are unused boolean flags, should all be zero
        if [ord(x) for x in version_field[1:4]] != [0, 0, 0]:
            # Ignore them
            pass

        ## Parse header
        # Header is a sequence of attributes, then a null byte (0x00)
        #
        # Each attribute contains: name, type, size, value
        # "name" and "type" are null-terminated strings
        # "size" is an integer, which represents the size of "value" in bytes
        # "value" is the next x bytes of data (where x is "size")
        #
        # For example:
        # [comments]\0x00[string]\0x00[5][hello]
        # ..is to be parsed into:
        # "name": comments
        # "type": string
        # "size": 5
        # "value": hello

        f.read(3) # Required so there are not 3 null bytes, for some reason

        while 1:
            attr_name = read_null_term_str(f)
            attr_type = read_null_term_str(f)
            attr_size = ord(f.read(4)[0])
            attr_content = f.read(attr_size)

            try:
                parsed_content = _parse_datatype(attr_type, attr_content)
            except UnimplementedDatatype:
                parsed_content = attr_content
            self._set_header(attr_name, attr_type, parsed_content)

            # Check if next byte is null, if so, it's the end of the header
            end = f.read(1)
            f.seek(-1, 1)
            if ord(end) == 0x00:
                self._end_of_header = f.tell() # Store where headers end
                break
        #end while

    def parse_data(self):
        f = self.fh

        if self._end_of_header is None:
            self.parse_headers()

        f.seek(self._end_of_header + 1) # Seek to end of headers

        if self.headers['compression']['value'].value == Compression.NO:
            y_coord = ord(f.read(1))
            data_size = ord(f.read(1))
            print "Coord:", y_coord
            print "size", data_size
            data = f.read(data_size)
            print [ord(x) for x in data]
        elif self.headers['compression']['value'].value == Compression.PIZ:
            print "PIZ!!"
        else:
            raise UnimplementedCompression("Cannot decompress %s" % (
                self.headers['compression']['value'].name
            ))
    #end parsed


if __name__ == "__main__":
    for fname in ["tests/blah_scanline_none.exr",
                         "tests/blah_scanline_zip.exr",
                         "tests/blah_block_zip.exr"]:
        print
        print
        print "*" * 5,  fname, "*" * 5

        fh = open(fname, "rb")
        exr = OpenEXR(fh)
        exr.parse_headers()

        print "version:", exr.version
        print "headers:"
        from pprint import pprint
        pprint(exr.headers)

        try:
            print "Prasing data"
            exr.parse_data()
            print "..done"
        except UnimplementedCompression, errormsg:
            print "Error:"
            print errormsg

        fh.close()
