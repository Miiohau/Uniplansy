#TODO: (after upgrading to python 3.12) uncomment @override Decorators
import copy
from dataclasses import FrozenInstanceError
from typing import Self

from uniplansy.util.custom_copyable import CustomCopyable


class FreezableObject(CustomCopyable):
    """an object that can be frozen and unfrozen. This class itself follows definition of frozen defined by dataclasses as of 2026 January 24. However, subclasses are free to add additional semantics to the freeze and unfreeze operations."""

    def __init__(self):
        self.frozen:bool = False

    def freeze(self):
        """freeze the object. Meaning it is protected from modification"""
        self.frozen = True

    def unfreeze(self):
        """unfreeze the object. Meaning it is no longer protected from modification"""
        self.frozen = False

    def thaw(self):
        """alias for unfreeze. Subclasses should override that method, if they need to change the unfreeze behavior."""
        self.unfreeze()

    def deep_copy_and_unfreeze(self):
        """deep copy and unfreezes the copy of the FreezableObject. Should always be safe because a deep copy of a FreezableObject should be completely independent of the original object"""
        new_copy = copy.deepcopy(self)
        new_copy.unfreeze()
        return new_copy

    # noinspection PyUnusedLocal
    # @override
    def set_matching_deep_copy(self,other:Self,memo):
        other.frozen = self.frozen


    # @override
    def __setattr__(self, name, value):
        """FreezableObject raise a FrozenInstanceError if they are modified while frozen"""
        if self.frozen:
            raise FrozenInstanceError()
        super().__setattr__(name, value)

    # @override
    def __delattr__(self, name):
        """FreezableObject raise a FrozenInstanceError if they are modified while frozen"""
        if self.frozen:
            raise FrozenInstanceError()
        super().__delattr__(name)