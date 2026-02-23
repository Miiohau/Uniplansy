"""an implementation of GUID Supplier that leverages the python uuid package to generate unique IDs

TODO:finish doc
"""
import sys

# noinspection PyUnreachableCode
if sys.version_info >= (3, 14):
    __all__ = ['uuid_guid_suppliers', 'uuid_guid_suppliers_3_14']
else:
    __all__ = ['uuid_guid_suppliers']