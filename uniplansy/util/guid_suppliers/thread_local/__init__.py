"""an implementation of GUIDSupplier based on thread names and a thread global counter

ThreadLocalGuidSupplier(class): a GuidSupplier that uses a thread-local sequence number and
thread_ids to create unique guids.
"""