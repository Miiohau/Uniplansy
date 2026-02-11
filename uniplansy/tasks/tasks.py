#TODO: (after upgrading to python 3.12) uncomment @override Decorators
from dataclasses import dataclass, field
from typing import Any, Self, Optional

from immutabledict import immutabledict

from uniplansy.plans.plan import PlanGraphNode
from uniplansy.util.id_registry import IDRegistry, id_registry_registry


@dataclass(frozen=True, repr=True)
class TaskDescription:
    uid:str
    human_understandable_string:str
    context:immutabledict[str, Any] = immutabledict({})

    # @override
    def __str__(self) -> str:
        return f"{self.human_understandable_string}"

    # @override
    def __eq__(self, other):
        if isinstance(other, TaskDescription):
            if __debug__ and (self.uid == other.uid):
                assert self.human_understandable_string == other.human_understandable_string, f"by guid \"{self.human_understandable_string}\" {self.uid} should equal \"{other.human_understandable_string}\" {self.uid} but they have different human understandable strings"
                assert self.context == other.context, f"by guid \"{self.human_understandable_string}\" \"{self.uid}\" should equal \"{other.human_understandable_string}\" \"{other.uid}\" but \"{self.human_understandable_string}\" has context {self.context} and \"{other.human_understandable_string}\" has context {other.context}"
            return self.uid == other.uid
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
    description:TaskDescription
    task_description_id_context: Optional[IDRegistry[TaskDescription]] = field(default=None, init=False)
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
        self.motivation = other.motivation
        self.estimated_cost = other.estimated_cost
        self.min_cost = other.min_cost
        self.max_cost = other.max_cost
        self.satisfied_percentage = other.satisfied_percentage
        self.task_description_id_context = other.task_description_id_context

    def __deepcopy__(self, memo):
        new_copy = Task(uid=self.uid,description=self.description)
        self.set_matching_deep_copy(new_copy, memo)
        return new_copy

    def __getstate__(self):
        state = super().__getstate__()
        state['task_description_id_context_id'] = self.task_description_id_context.uid
        del state['task_description_id_context']
        state['description_id'] = self.description.uid
        del state['description']
        return state

    # TODO:see if we can find a way to connect unpickled DecomposerNodes to their old notes
    def __setstate__(self,state):
        super().__setstate__(state)
        self.task_description_id_context = id_registry_registry.fetch(state['task_description_id_context_id'])
        del self.__dict__['task_description_id_context_id']
        self.description = self.task_description_id_context.fetch(state['description_id'])
        del self.__dict__['description_id']