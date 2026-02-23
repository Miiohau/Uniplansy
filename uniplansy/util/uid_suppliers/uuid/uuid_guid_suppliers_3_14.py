import threading
import uuid

from uniplansy.util.uid_suppliers.uid_supplier import GUIDSupplier


class UUID6GUIDSupplier(GUIDSupplier):

    def __init__(self, node=None, clock_seq=None):
        super().__init__()
        self.node = node
        self.clock_seq = clock_seq

    def create_guid(self, prefix: str = "") -> str:
        if self.clock_seq is not None:
            self.clock_seq += 1
        current_node: int = self.node
        if self.node is None:
            current_node = threading.get_ident()
        return prefix + str(uuid.uuid6(current_node, self.clock_seq))


class UUID7GUIDSupplier(GUIDSupplier):
    def create_guid(self, prefix: str = "") -> str:
        return prefix + str(uuid.uuid7())