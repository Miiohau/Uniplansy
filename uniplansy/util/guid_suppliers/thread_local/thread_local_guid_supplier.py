import threading
from threading import local

from uniplansy.util.guid_suppliers.guid_supplier import GUIDSupplier

_module_thread_local_data = local()

_module_thread_local_data.sequence = 0

class ThreadLocalGuidSupplier(GUIDSupplier):
    """a GuidSupplier that uses a thread-local sequence number and thread_ids to create unique guids.

    Note:this GuidSupplier simple on purpose to run fast however because of that is unsuitable for long-running
    applications because it will generate increasing large guids."""
    _thread_sequence: int = 0
    _thread_sequence_lock = threading.Lock()

    @staticmethod
    def create_thread_guid(prefix: str = "thread") -> str:
        """
        creates a globally unique id for use as a name of a thread.
        :param prefix: the prefix to give the guid
        """
        with ThreadLocalGuidSupplier._thread_sequence_lock:
            guid: str = prefix + "*" + str(ThreadLocalGuidSupplier._thread_sequence)
            ThreadLocalGuidSupplier._thread_sequence += 1
        return guid

    def create_guid(self, prefix: str = "") -> str:
        """
        creates a guid in the context of the current thread.

        Note: assumes if the current thread is named that name is globally unique (you can create globally unique
        thread names via the create_thread_guid function).
        :param prefix: the prefix to give the guid
        """
        global _module_thread_local_data
        thread_id: str
        current_thread_name = threading.current_thread().name
        current_thread_has_name = current_thread_name and current_thread_name.strip()
        if current_thread_has_name:
            thread_id = current_thread_name
        else:
            thread_id = "thread:" + str(threading.get_ident())
        guid: str = prefix + "$" + thread_id + "#" + str(_module_thread_local_data.sequence)
        _module_thread_local_data.sequence += 1
        return guid