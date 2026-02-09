#TODO: (after upgrading to python 3.12) uncomment @override Decorators
from dataclasses import dataclass
from typing import Any, Self

from immutabledict import immutabledict

from uniplansy.plans.plan import PlanGraphNode


@dataclass(frozen=True, repr=True)
class TaskDescription:
    guid:str
    human_understandable_string:str
    context:immutabledict[str, Any] = immutabledict({})

    # @override
    def __str__(self) -> str:
        return f"{self.human_understandable_string}"

    # @override
    def __eq__(self, other):
        if isinstance(other, TaskDescription):
            if __debug__ and (self.guid == other.guid):
                assert self.human_understandable_string == other.human_understandable_string, f"by guid \"{self.human_understandable_string}\" {self.guid} should equal \"{other.human_understandable_string}\" {self.guid} but they have different human understandable strings"
                assert self.context == other.context, f"by guid \"{self.human_understandable_string}\" \"{self.guid}\" should equal \"{other.human_understandable_string}\" \"{other.guid}\" but \"{self.human_understandable_string}\" has context {self.context} and \"{other.human_understandable_string}\" has context {other.context}"
            return self.guid == other.guid
        return NotImplemented

    # @override
    def __hash__(self) -> int:
        return hash(self.guid)

    # @override
    def __copy__(self):
        return self

    # @override
    def __deepcopy__(self, memo):
        return self

@dataclass
class Task(PlanGraphNode):
    description:TaskDescription
    motivation:float = 0.0
    estimated_cost: float = 0.0
    min_cost:float = 0.0
    max_cost:float = float("inf")
    satisfied_percentage:float = 0.0

    def get_clamped_satisfied_percentage(self,min_value:float,max_value:float):
        return min(max(self.satisfied_percentage,min_value),max_value)

    # @override
    def is_compatible_with(self, other:PlanGraphNode)-> bool:
        if isinstance(other, Task):
            return self.description == other.description
        return NotImplemented

    def set_matching_deep_copy(self,other:Self,memo):
        super().set_matching_deep_copy(other,memo)
        self.description = other.description
        self.motivation = other.motivation
        self.estimated_cost = other.estimated_cost
        self.min_cost = other.min_cost
        self.max_cost = other.max_cost
        self.satisfied_percentage = other.satisfied_percentage