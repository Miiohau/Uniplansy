import sys
import threading
import uuid
from typing import Optional

from uniplansy.util.guid_suppliers.guid_supplier import GUIDSupplier


class UUID1GUIDSupplier(GUIDSupplier):

    def __init__(self, node: Optional[int] = None, clock_seq: Optional[int] = None):
        super().__init__()
        self.node: Optional[int] = node
        self.clock_seq: Optional[int] = clock_seq

    def create_guid(self, prefix: str = "") -> str:
        if self.clock_seq is not None:
            self.clock_seq += 1
        current_node: int = self.node
        if self.node is None:
            current_node = threading.get_ident()
        return prefix + str(uuid.uuid1(current_node, self.clock_seq))

class UUID4GUIDSupplier(GUIDSupplier):
    def create_guid(self, prefix: str = "") -> str:
        return prefix + str(uuid.uuid4())


