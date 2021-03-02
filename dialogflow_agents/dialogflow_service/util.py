from google.protobuf.json_format import ParseDict
from google.protobuf import struct_pb2

def dict_to_protobuf(dict_struct):
    return ParseDict(js_dict=dict_struct, message=struct_pb2.Struct())
