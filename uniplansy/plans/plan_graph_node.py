from __future__ import annotations
import copy
from dataclasses import dataclass, field
from typing import Optional, Self, Any

from uniplansy.util.FreezableObject import FreezableObject
from uniplansy.util.has_uid import HasRequiredUID
from uniplansy.util.id_registry import IDRegistry, id_registry_registry

@dataclass
class PlanGraphNode(FreezableObject, HasRequiredUID):
    """a graph node of the plan

    todo: finished docstring
    """
    uid: str
    node_id_context: Optional[IDRegistry[PlanGraphNode]] = field(default=None)
    children: set[PlanGraphNode] = field(default_factory=set, kw_only=True, compare=False)
    parents: set[PlanGraphNode] = field(default_factory=set, kw_only=True, compare=False)
    frozen_children: Optional[frozenset[PlanGraphNode]] = field(default=None, init=False, compare=False)
    frozen_parents: Optional[frozenset[PlanGraphNode]] = field(default=None, init=False, compare=False)

    def __init__(self,
                 uid: str,
                 node_id_context: Optional[IDRegistry[PlanGraphNode]] = None,
                 cache_prefix: str = "_cache",
                 *,
                 children: Optional[set[PlanGraphNode]] = None,
                 parents: Optional[set[PlanGraphNode]] = None,
                 ):
        super().__init__(cache_prefix=cache_prefix)
        self.uid = uid
        self.node_id_context = node_id_context
        if children is None:
            self.children = set()
        else:
            self.children = children
        if parents is None:
            self.parents = set()
        else:
            self.parents = parents

    # @override
    def __getattribute__(self, name):
        if name == "frozen":
            return super().__getattribute__(name)
        elif not self.frozen:
            return super().__getattribute__(name)
        elif name == "children":
            if self.frozen_children is None:
                self.frozen_children = frozenset(super().__getattribute__(name))
            return self.frozen_children
        elif name == "parents":
            if self.frozen_parents is None:
                self.frozen_parents = frozenset(super().__getattribute__(name))
            return self.frozen_parents
        else:
            return super().__getattribute__(name)

    # @override
    def unfreeze(self):
        """ unfreezes the plan"""
        super().unfreeze()
        self.frozen_children = None
        self.frozen_parents = None

    def is_compatible_with(self, other: PlanGraphNode) -> bool:
        """return true if PlanGraphNode is compatible with other

        :param other: the other PlanGraphNode
        """
        return self.could_be_equal(other)

    def set_matching_deep_copy(self, other: Self, memo):
        """takes a raw instance of PlanGraphNode and
        fills its fields from this instance in the context of a deep copy.

        :param other: the raw Plan
        :param memo: a blackbox used internally by the copy package.
        See https://docs.python.org/3/library/copy.html#object.__deepcopy__for more information
        """
        super().set_matching_deep_copy(other, memo)
        other.frozen_parents = copy.deepcopy(self.frozen_parents, memo)
        other.frozen_children = copy.deepcopy(self.frozen_children, memo)
        other.children = copy.deepcopy(self.children, memo)
        other.parents = copy.deepcopy(self.parents, memo)
        other.node_id_context = self.node_id_context

    # @override
    def __deepcopy__(self, memo):
        new_copy = type(self)(uid=self.uid)
        self.set_matching_deep_copy(new_copy, memo)
        return new_copy

    def __getstate__(self):
        state = self.__dict__.copy()
        state['node_id_context_id'] = self.node_id_context.uid
        del state['node_id_context']
        return state

    def __setstate__(self, state):
        self.__dict__.update(state)
        self.node_id_context = id_registry_registry.fetch(state['node_id_context_id'])
        del self.__dict__['node_id_context_id']

    def could_be_equal(self, other) -> bool:
        """returns true if self and other could be equal

        :param other: the other PlanPlanGraphNode
        :return: true if self and other could be equal
        """
        if not isinstance(other, type(self)):
            return False
        #uids aren't compared here because matching uids on PlanGraphNodes imply compatibility not equality
        #conversely two nodes could be equal even if their uids don't match
        if self.node_id_context_id != other.node_id_context_id:
            return False
        return True

    # possible algorithms
    # vf2 algorithm
    # Weisfeiler Leman graph isomorphism test
    def _are_children_equal(self, other, memo: dict[str, Any]) -> bool:
        are_equal: bool = True
        for cur_self_child in self.children:
            possible_matches: set[str] = set()
            for cur_other_child in other.children:
                if cur_self_child.could_be_equal(cur_other_child):
                    possible_matches.add(cur_other_child.uid)
            orig_possible_matches: Optional[set[str]] = memo["possible mappings"][cur_self_child.uid]
            if orig_possible_matches is not None:
                possible_matches = possible_matches.intersection(orig_possible_matches)
            memo["possible mappings"][cur_self_child.uid] = possible_matches
            if len(possible_matches) == 0:
                are_equal = False
                break
            found_match: bool = False
            if cur_self_child.uid in memo["visited nodes"]:
                found_match = True
            else:
                for cur_other_child in other.children:
                    if cur_other_child in possible_matches:
                        if cur_self_child.are_equal(cur_other_child, memo):
                            found_match = True
                            break
            if not found_match:
                are_equal = False
                break
        return are_equal

    def _are_parents_equal(self, other, memo: dict[str, Any]) -> bool:
        are_equal: bool = True
        for cur_self_parent in self.parents:
            if cur_self_parent.uid in memo["visited nodes"]:
                found_match: bool = False
                for cur_other_parent in other.parents:
                    if cur_self_parent.could_be_equal(cur_other_parent):
                        found_match = True
                        break
                if not found_match:
                    are_equal = False
                    break
            else:
                found_match: bool = False
                for cur_other_parent in other.parents:
                    if cur_self_parent.are_equal(cur_other_parent, memo):
                        found_match = True
                        break
                if not found_match:
                    are_equal = False
                    break
        return are_equal

    def are_equal(self, other, memo: dict[str, Any]) -> bool:
        """ does best effort equality check

        :param other: the other PlanGraphNode
        :param memo: a dict to record information on the possible equality of this and the other plans nodes
        :return: true if self and other are equal
        """
        if not self.could_be_equal(other):
            return False
        if not "visited nodes" in memo:
            memo["visited nodes"] = set()
        if not "possible mappings" in memo:
            memo["possible mappings"] = dict[str, set[str]]()
        memo["visited nodes"].add(self.uid)
        if not self._are_children_equal(other, memo):
            return False
        if not self._are_parents_equal(other, memo):
            return False
        return True

    def __eq__(self, other) -> bool:
        if not isinstance(other, type(self)):
            return False
        return self.are_equal(other, dict())

    def __str__(self):
        return str(self.uid)

