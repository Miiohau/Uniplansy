#TODO: (after upgrading to python 3.12) uncomment @override Decorators
from dataclasses import dataclass, field
from decimal import Decimal
from fractions import Fraction
from math import isfinite
from typing import Any, Self, Optional, ClassVar

from immutabledict import immutabledict

from uniplansy.plans.plan import PlanGraphNode
from uniplansy.util.has_uid import HasRequiredUID
from uniplansy.util.id_registry import IDRegistry, id_registry_registry


@dataclass(frozen=True, repr=True)
class TaskDescription(HasRequiredUID):
    """TODO: Docstring for TaskDescription."""
    uid: str
    human_understandable_string: str
    context: immutabledict[str, Any] = immutabledict({})

    # @override
    def __str__(self) -> str:
        return f"{self.human_understandable_string}"

    # @override
    def __eq__(self, other):
        if isinstance(other, TaskDescription):
            if self.uid == other.uid:
                if __debug__ :
                    assert self.human_understandable_string == other.human_understandable_string, \
                        (f"by guid \"{self.human_understandable_string}\" {self.uid} "
                         f"should equal \"{other.human_understandable_string}\" {self.uid} but "
                         f"they have different human understandable strings")
                    assert self.context == other.context, \
                        (f"by guid \"{self.human_understandable_string}\" \"{self.uid}\" should equal "
                         f"\"{other.human_understandable_string}\" \"{other.uid}\" but "
                         f"\"{self.human_understandable_string}\" has context {self.context} and "
                         f"\"{other.human_understandable_string}\" has context {other.context}")
                return True
            return (self.human_understandable_string == other.human_understandable_string and
                    self.context == other.context)
        return NotImplemented

    # @override
    def __hash__(self) -> int:
        return hash(self.uid)

    # @override
    def __copy__(self):
        return self

    # @override
    def __deepcopy__(self, memo):
        return self

@dataclass
class Task(PlanGraphNode):
    """TODO: Docstring for Task."""
    description:TaskDescription
    task_description_id_context: Optional[IDRegistry[TaskDescription]] = field(default=None, init=False)
    motivation: float | Fraction = 0.0
    estimated_cost: float | Fraction = 0.0
    min_cost: float | Fraction = 0.0
    max_cost: float | Fraction = float("inf")
    satisfied_percentage: float | Fraction = 0.0

    def get_clamped_satisfied_percentage(self,
                                         min_value: float | Fraction,
                                         max_value: float | Fraction) -> float | Fraction:
        """TODO: Docstring for get_clamped_satisfied_percentage.

        :param min_value:
        :param max_value:
        :return:
        """
        if isinstance(self.satisfied_percentage, Fraction):
            min_value = Fraction(min_value)
            max_value = Fraction(max_value)
        elif isinstance(self.satisfied_percentage, float):
            min_value = float(min_value)
            max_value = float(max_value)
        return min(max(self.satisfied_percentage, min_value), max_value)

    # @override
    def is_compatible_with(self, other: PlanGraphNode) -> bool:
        if isinstance(other, Task):
            return self.description == other.description
        return NotImplemented

    def could_be_equal(self, other) -> bool:
        if not super().could_be_equal(other):
            return False
        if self.description != other.description:
            return False
        if self.task_description_id_context != other.task_description_id_context:
            return False
        return ((self.motivation == other.motivation) and
                (self.estimated_cost == other.estimated_cost) and
                (self.min_cost == other.min_cost) and
                (self.max_cost == other.max_cost) and
                (self.satisfied_percentage == other.satisfied_percentage))

    def set_matching_deep_copy(self,other:Self,memo):
        super().set_matching_deep_copy(other,memo)
        self.motivation = other.motivation
        self.estimated_cost = other.estimated_cost
        self.min_cost = other.min_cost
        self.max_cost = other.max_cost
        self.satisfied_percentage = other.satisfied_percentage
        self.task_description_id_context = other.task_description_id_context

    def __deepcopy__(self, memo):
        new_copy = type(self)(uid=self.uid, description=self.description)
        self.set_matching_deep_copy(new_copy, memo)
        return new_copy

    def __getstate__(self):
        state = super().__getstate__()
        state['task_description_id_context_id'] = self.task_description_id_context.uid
        del state['task_description_id_context']
        state['description_id'] = self.description.uid
        del state['description']
        return state

    # TODO:see if we can find a way to connect unpickled Tasks to their old notes
    def __setstate__(self,state):
        super().__setstate__(state)
        self.task_description_id_context = id_registry_registry.fetch(state['task_description_id_context_id'])
        del self.__dict__['task_description_id_context_id']
        self.description = self.task_description_id_context.fetch(state['description_id'])
        del self.__dict__['description_id']

    if __debug__:
        NO_SPECIAL_VALUES_ALLOWED_ATTRIBUTES: ClassVar[list[str]] = ['motivation', 'estimated_cost', 'min_cost',
                                                                     'max_cost','satisfied_percentage']

        def __setattr__(self, name, value):
            if name in Task.NO_SPECIAL_VALUES_ALLOWED_ATTRIBUTES:
                if isinstance(value, float) and not isfinite(value):
                    raise TypeError(f"{value} is not finite. floats assigned to {name} must be finite")
            super().__setattr__(name, value)