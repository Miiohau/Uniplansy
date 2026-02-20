"""GUIDSuppliers create globally unique IDs for use in IDRegistries or PersistenceManagers

GUIDSupplier(Class): A GUID Supplier creates globally unique IDs for use in IDRegistries or PersistenceManagers
thread_local(package): an implementation of GUIDSupplier based on thread names and a thread global counter
uuid(package): an implementation of GUID Supplier that leverages the python uuid package to generate unique IDs
wrappers(package): wrappers for GUIDSuppliers
"""