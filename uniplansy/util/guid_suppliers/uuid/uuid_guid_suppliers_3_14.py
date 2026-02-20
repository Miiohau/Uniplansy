import uuid

from uniplansy.util.guid_suppliers.guid_supplier import GUIDSupplier


class UUID6GUIDSupplier(GUIDSupplier):

    def __init__(self, node=None, clock_seq=None):
        super().__init__()
        self.node = node
        self.clock_seq = clock_seq

    def create_guid(self, prefix: str = "") -> str:
        return prefix + str(uuid.uuid6(self.node, self.clock_seq))


class UUID7GUIDSupplier(GUIDSupplier):
    def create_guid(self, prefix: str = "") -> str:
        return prefix + str(uuid.uuid7())