"""a FreezableObject is an object that can be frozen and unfrozen."""
#TODO: (after upgrading to python 3.12) uncomment @override Decorators
import copy
from dataclasses import FrozenInstanceError
from typing import Self, Optional

from uniplansy.util.custom_copyable import CustomCopyable


class FreezableObject(CustomCopyable):
    """an object that can be frozen and unfrozen.

    This class itself follows the definition of frozen defined by dataclasses as of 2026 January 24.
    However, subclasses are free to add additional semantics to the freeze and unfreeze operations.
    :method freeze: freeze the object. Meaning it is protected from modification.
    :method unfreeze: unfreeze the object. Meaning it is no longer protected from modification.
    :method thaw: alias for unfreeze. Subclasses should override that method,
    if they need to change the unfreeze behavior.
    :method deep_copy_and_unfreeze: copy and unfreeze the copy of the object.
    """

    def __init__(self, cache_prefix: str = "_cache"):
        self.frozen: bool = False
        self._cache_prefix = cache_prefix
        self._temporarily_unfrozen_attribute:Optional[str] = None

    def freeze(self):
        """freeze the object. Meaning it is protected from modification"""
        self.frozen = True

    def unfreeze(self):
        """unfreeze the object. Meaning it is no longer protected from modification"""
        self.frozen = False

    def temporary_selective_unfreeze(self, name: str):
        """temporarily unfreezes one attribute of the FreezableObject.

        Only one attribute can be temporarily unfreezed this way
        :param name: the name of the attribute to unfreeze.
        """
        self._temporarily_unfrozen_attribute = name

    def thaw(self):
        """alias for unfreeze. Subclasses should override that method, if they need to change the unfreeze behavior."""
        self.unfreeze()

    def deep_copy_and_unfreeze(self):
        """
        deep copy and unfreezes the copy of the FreezableObject.

        Should always be safe because a deep copy of a FreezableObject should be completely independent of
        the original object
        """
        new_copy = copy.deepcopy(self)
        new_copy.unfreeze()
        return new_copy

    # noinspection PyUnusedLocal
    # @override
    def set_matching_deep_copy(self,other:Self,memo):
        super().set_matching_deep_copy(other, memo)
        other.frozen = self.frozen

    # @override
    def __setattr__(self, name, value):
        """
        FreezableObject raise a FrozenInstanceError if they are modified while frozen

        exception: attributes starting with cache_prefix can be modified
        :param name: The name of the attribute.
        :param value: The value of the attribute.
        :raises FrozenInstanceError: if they are modified while frozen
        """
        if (self.frozen and not name.startswith(self._cache_prefix)
                and not (name == self._temporarily_unfrozen_attribute)):
            raise FrozenInstanceError()
        super().__setattr__(name, value)
        if name == self._temporarily_unfrozen_attribute:
            self._temporarily_unfrozen_attribute = None

    # @override
    def __delattr__(self, name):
        """
        FreezableObject raise a FrozenInstanceError if they are modified while frozen

        exception: attributes starting with cache_prefix can be modified
        :param name: The name of the attribute.
        :raises FrozenInstanceError: if they are modified while frozen
        """
        if (self.frozen and not name.startswith(self._cache_prefix)
                and not (name == self._temporarily_unfrozen_attribute)):
            raise FrozenInstanceError()
        super().__delattr__(name)
        if name == self._temporarily_unfrozen_attribute:
            self._temporarily_unfrozen_attribute = None