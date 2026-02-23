"""holds all the classes that aren't tied directly to planning but are used internally by uniplansy.

Some may be spun off into their own packages and become dependencies of uniplansy.
CustomCopyable(Interface): a custom copyable is a Protocol to support implementation of __copy__ and __deepcopy__
(mainly __deepcopy__)
uid_suppliers(package): TODO: fill out
persistence: TODO: fill out
FreezableObject(Class) an object that can be frozen and unfrozen.
HasPreferredName(Protocol): a data protocol for having a preferred name
HasUID(Protocol): a data protocol for having a UID
HasOptionalUID(Protocol): a data protocol for having an optional uid
HasRequiredUID(Protocol): a data protocol for having a required uid
IDRegistry(Class): a registry of objects with unique ID
RegistryKeyError(Error): an error raised when there is a problem with a key used in an IDRegistry
RegistryKeyNotFoundError(Error): an error raised when a key is not found in an IDRegistry
RegistryKeyAlreadyExistsError(Error): an error raised when a key already exists in an IDRegistry
id_registry_registry(global): the global registry of IDIDRegistries
"""