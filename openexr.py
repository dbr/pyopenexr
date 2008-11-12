#!/usr/bin/env python
#encoding:utf-8
#pylint:disable-msg=C0111,R0903

import struct

## Definitons
COMPRESSION = {
    0 : 'NO_COMPRESSION',
    1 : 'RLE_COMPRESSION',
    2 : 'ZIPS_COMPRESSION',
    3 : 'ZIP_COMPRESSION',
    4 : 'PIZ_COMPRESSION',
    5 : 'PXR24_COMPRESSION',
    6 : 'B44_COMPRESSION',
    7 : 'B44A_COMPRESSION'
}


## Exceptions
class NotAnExr(Exception):
    pass
class UnsupportedVersion(Exception):
    pass
class UnimplementedDatatype(Exception):
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
    known = ["string", "float", "compression", "box2i"]

    if datatype not in known:
        raise UnimplementedDatatype(
            "Cannot parse datatype %s" % (datatype)
        )

    if datatype == "string":
        return value

    if datatype == "float":
        return struct.unpack('f', value)[0]

    if datatype == "compression":
        return COMPRESSION[ord(value)]
    
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
        
## Main class
class OpenEXR:
    def __init__(self):
        self.headers = {}
        self.version = None
    
    def _set_header(self, name, attr_type, attr_value):
        self.headers[name] = {
            'value': attr_value,
            'type': attr_type
        }
    
    def parse(self, f):
        ## Check for "Magic Number"
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
            print "Things not null"
        f.read(3)
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
            
            # Check if next byte is null
            end = f.read(1)
            f.seek(-1, 1)
            if ord(end) == 0x00:
                # If so, this is the end of the header!
                break
        
        
        
for cur_filename in ["blah_scanline.exr",
                     "blah_block.exr", 
                     "table.56.exr",
                     "goldfish.020.exr"]:
    print
    print
    print "*" * 5,  cur_filename, "*" * 5
    
    current_file = open(cur_filename, "rb")
    exr = OpenEXR()
    exr.parse(current_file)
    print "version:", exr.version
    print "headers:"
    import pprint
    pprint.pprint(exr.headers)
    
    current_file.close()
