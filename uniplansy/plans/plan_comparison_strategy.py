"""defines PlanComparisonStrategy and its supporting and basic subclasses

"""
from abc import ABCMeta, abstractmethod
from enum import Enum, auto
from fractions import Fraction
from typing import List, Tuple, Set, Optional

from uniplansy.plans.plan import Plan, PlanDeltas
from uniplansy.tasks.tasks import Task


class PlanComparisonStrategyToken(Enum):
    """the set of common tokens used in PlanComparisonStrategy Tuple keys"""
    motivation_over_min_cost = auto()
    motivation_over_estimated_cost = auto()
    motivation_over_max_cost = auto()
    min_cost_over_motivation = auto()
    estimated_cost_over_motivation = auto()
    max_cost_over_motivation = auto()
    min_cost = auto()
    estimated_cost = auto()
    max_cost = auto()
    motivation = auto()
    satisfied_percentage_average_asc = auto()
    satisfied_percentage_average_des = auto()
    satisfied_percentage_median_asc = auto()
    satisfied_percentage_median_des = auto()
    tasks_fully_satisfied_percentage_asc = auto()
    tasks_fully_satisfied_percentage_des = auto()
    concrete_action_percentage_asc = auto()
    concrete_action_percentage_des = auto()


class PlanValueToken(Enum):
    """the set of tokens returned by PlanComparisonStrategy.get_values_needed"""
    min_cost = auto()
    estimated_cost = auto()
    max_cost = auto()
    motivation = auto()
    satisfied_percentage_average = auto()
    satisfied_percentage_median = auto()
    tasks_fully_satisfied_percentage = auto()
    concrete_action_percentage = auto()


# cost ascending motivation descending
class PlanComparisonStrategy(metaclass=ABCMeta):
    """a Strategy to compare (sort) Tasks, Plans and Plan PlanDeltas pairs

    task_to_tuple_key(method): creates a tuple key for a Task
    plan_to_tuple_key(method): creates a tuple key for a Plan
    plan_plus_delta_to_tuple_key(method): creates a tuple key for a Plan PlanDeltas pair
    get_values_needed(method): returns the set of common values used by this PlanComparisonStrategy
    """

    @abstractmethod
    def task_to_tuple_key(self, task: Task) -> Tuple:
        """creates a tuple key for a Task

        :param task: the Task to create a tuple key for
        :return: a tuple key for the Task
        """
        pass

    @abstractmethod
    def plan_to_tuple_key(self, plan: Plan) -> Tuple:
        """creates a tuple key for a plan

        :param plan: the plan to create a tuple key for
        :return: a tuple key for the Plan
        """
        pass

    @abstractmethod
    def plan_plus_delta_to_tuple_key(self, plan: Plan, deltas: PlanDeltas) -> Tuple:
        """creates a tuple key for a Plan PlanDeltas pair.

        This method is often used to sort Plan Decomposer pairs
        :param plan: the Plan part of the Plan PlanDeltas pair
        :param deltas: the PlanDeltas part of the Plan PlanDeltas pair
        :return: a tuple key for the Plan PlanDeltas pair
        """
        pass

    @abstractmethod
    def get_values_needed(self) -> Set[PlanValueToken]:
        """returns the set of common values used by this PlanComparisonStrategy

        :return: the set of common values used by this PlanComparisonStrategy
        """
        pass


class BasicPlanComparisonStrategy(PlanComparisonStrategy):
    """a PlanComparisonStrategy that uses a raw list of PlanComparisonStrategyToken to create its Tuple keys"""

    def __init__(self, order: List[PlanComparisonStrategyToken],
                 preferred_type: Optional[float | Fraction | type[float | Fraction]] = None):
        super().__init__()
        self.order: List[PlanComparisonStrategyToken] = order
        self._values_needed: Set[PlanValueToken] = set()
        self.preferred_type = preferred_type

    def _generate_standard_keys(self,
                                summary_dict:dict[PlanValueToken, float | Fraction]
                                ) -> List[float | Fraction | str]:
        keys: List[float | Fraction | str] = []
        for token in self.order:
            if token == PlanComparisonStrategyToken.motivation_over_min_cost:
                try:
                    keys.append(-summary_dict[PlanValueToken.motivation] / summary_dict[PlanValueToken.min_cost])
                except ZeroDivisionError:
                    if summary_dict[PlanValueToken.motivation] > 0:
                        keys.append(float('-inf'))
                    elif summary_dict[PlanValueToken.motivation] < 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.motivation_over_estimated_cost:
                try:
                    keys.append(-summary_dict[PlanValueToken.motivation] / summary_dict[PlanValueToken.estimated_cost])
                except ZeroDivisionError:
                    if summary_dict[PlanValueToken.motivation] > 0:
                        keys.append(float('-inf'))
                    elif summary_dict[PlanValueToken.motivation] < 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.motivation_over_max_cost:
                try:
                    keys.append(-summary_dict[PlanValueToken.motivation] / summary_dict[PlanValueToken.max_cost])
                except ZeroDivisionError:
                    if summary_dict[PlanValueToken.motivation] > 0:
                        keys.append(float('-inf'))
                    elif summary_dict[PlanValueToken.motivation] < 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.min_cost_over_motivation:
                try:
                    keys.append(summary_dict[PlanValueToken.min_cost] / summary_dict[PlanValueToken.motivation])
                except ZeroDivisionError:
                    if summary_dict[PlanValueToken.min_cost] < 0:
                        keys.append(float('-inf'))
                    elif summary_dict[PlanValueToken.min_cost] > 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.estimated_cost_over_motivation:
                try:
                    keys.append(summary_dict[PlanValueToken.estimated_cost] / summary_dict[PlanValueToken.motivation])
                except ZeroDivisionError:
                    if summary_dict[PlanValueToken.estimated_cost] < 0:
                        keys.append(float('-inf'))
                    elif summary_dict[PlanValueToken.estimated_cost] > 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.max_cost_over_motivation:
                try:
                    keys.append(summary_dict[PlanValueToken.max_cost] / summary_dict[PlanValueToken.motivation])
                except ZeroDivisionError:
                    if summary_dict[PlanValueToken.max_cost] < 0:
                        keys.append(float('-inf'))
                    elif summary_dict[PlanValueToken.max_cost] > 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.motivation:
                keys.append(-summary_dict[PlanValueToken.motivation])
            elif token == PlanComparisonStrategyToken.min_cost:
                keys.append(summary_dict[PlanValueToken.min_cost])
            elif token == PlanComparisonStrategyToken.estimated_cost:
                keys.append(summary_dict[PlanValueToken.estimated_cost])
            elif token == PlanComparisonStrategyToken.max_cost:
                keys.append(summary_dict[PlanValueToken.max_cost])
            elif token == PlanComparisonStrategyToken.satisfied_percentage_average_asc:
                keys.append(summary_dict[PlanValueToken.satisfied_percentage_average])
            elif token == PlanComparisonStrategyToken.satisfied_percentage_median_asc:
                keys.append(summary_dict[PlanValueToken.satisfied_percentage_median])
            elif token == PlanComparisonStrategyToken.satisfied_percentage_average_des:
                keys.append(-summary_dict[PlanValueToken.satisfied_percentage_average])
            elif token == PlanComparisonStrategyToken.satisfied_percentage_median_des:
                keys.append(-summary_dict[PlanValueToken.satisfied_percentage_median])
            elif token == PlanComparisonStrategyToken.tasks_fully_satisfied_percentage_asc:
                keys.append(summary_dict[PlanValueToken.tasks_fully_satisfied_percentage])
            elif token == PlanComparisonStrategyToken.tasks_fully_satisfied_percentage_des:
                keys.append(-summary_dict[PlanValueToken.tasks_fully_satisfied_percentage])
            elif token == PlanComparisonStrategyToken.concrete_action_percentage_asc:
                keys.append(summary_dict[PlanValueToken.concrete_action_percentage])
            elif token == PlanComparisonStrategyToken.concrete_action_percentage_des:
                keys.append(-summary_dict[PlanValueToken.concrete_action_percentage])
        return keys

    def task_to_tuple_key(self, task: Task) -> Tuple:
        summary_dict: dict[PlanValueToken, float | Fraction] = {}
        for token in self.get_values_needed():
            if token == PlanValueToken.motivation:
                if self.preferred_type is not None:
                    if (isinstance(self.preferred_type, float) or
                            issubclass(self.preferred_type, float) or
                            self.preferred_type is float):
                        summary_dict[token] = float(task.motivation)
                    else:
                        summary_dict[token] = Fraction(task.motivation)
                else:
                    summary_dict[token] = task.motivation
            elif token == PlanValueToken.min_cost:
                if self.preferred_type is not None:
                    if (isinstance(self.preferred_type, float) or
                            issubclass(self.preferred_type, float) or
                            self.preferred_type is float):
                        summary_dict[token] = float(task.motivation)
                    else:
                        summary_dict[token] = Fraction(task.motivation)
                else:
                    summary_dict[token] = task.motivation
            elif token == PlanValueToken.estimated_cost:
                if self.preferred_type is not None:
                    if (isinstance(self.preferred_type, float) or
                            issubclass(self.preferred_type, float) or
                            self.preferred_type is float):
                        summary_dict[token] = float(task.motivation)
                    else:
                        summary_dict[token] = Fraction(task.motivation)
                else:
                    summary_dict[token] = task.motivation
            elif token == PlanValueToken.max_cost:
                if self.preferred_type is not None:
                    if (isinstance(self.preferred_type, float) or
                            issubclass(self.preferred_type, float) or
                            self.preferred_type is float):
                        summary_dict[token] = float(task.motivation)
                    else:
                        summary_dict[token] = Fraction(task.motivation)
                else:
                    summary_dict[token] = task.motivation
            elif token == PlanValueToken.tasks_fully_satisfied_percentage:
                if self.preferred_type is not None:
                    if (isinstance(self.preferred_type, float) or
                            issubclass(self.preferred_type, float) or
                            self.preferred_type is float):
                        summary_dict[token] = float(task.satisfied_percentage)
                    else:
                        summary_dict[token] = Fraction(task.satisfied_percentage)
                else:
                    summary_dict[token] = task.satisfied_percentage
            elif token == PlanValueToken.concrete_action_percentage:
                if self.preferred_type is not None:
                    flux_concrete_action_percentage: float | Fraction
                    if (isinstance(self.preferred_type, float) or
                            issubclass(self.preferred_type, float) or
                            self.preferred_type is float):
                        if len(task.children) > 0:
                            flux_concrete_action_percentage = float(task.satisfied_percentage) - float(1)
                        else:
                            flux_concrete_action_percentage = float(task.satisfied_percentage)
                        summary_dict[token] = flux_concrete_action_percentage
                    else:
                        if len(task.children) > 0:
                            flux_concrete_action_percentage = Fraction(task.satisfied_percentage) - Fraction(1)
                        else:
                            flux_concrete_action_percentage = Fraction(task.satisfied_percentage)
                        summary_dict[token] = flux_concrete_action_percentage
                else:
                    if len(task.children) > 0:
                        flux_concrete_action_percentage = task.satisfied_percentage - 1
                    else:
                        flux_concrete_action_percentage = task.satisfied_percentage
                    summary_dict[token] = flux_concrete_action_percentage
            elif token == PlanValueToken.satisfied_percentage_average:
                if self.preferred_type is not None:
                    if (isinstance(self.preferred_type, float) or
                            issubclass(self.preferred_type, float) or
                            self.preferred_type is float):
                        summary_dict[token] = float(task.satisfied_percentage)
                    else:
                        summary_dict[token] = Fraction(task.satisfied_percentage)
                else:
                    summary_dict[token] = task.satisfied_percentage
            elif token == PlanValueToken.satisfied_percentage_median:
                if self.preferred_type is not None:
                    if (isinstance(self.preferred_type, float) or
                            issubclass(self.preferred_type, float) or
                            self.preferred_type is float):
                        summary_dict[token] = float(task.satisfied_percentage)
                    else:
                        summary_dict[token] = Fraction(task.satisfied_percentage)
                else:
                    summary_dict[token] = task.satisfied_percentage
        keys = self._generate_standard_keys(summary_dict)
        # to guarantee a total ordering
        keys.append(task.description.human_understandable_string)
        keys.append(task.description.uid)
        # it actually should be totally ordered by this point but just to make extra sure.
        keys.append(id(task.description))
        keys.append(id(task))
        return tuple(keys)

    def plan_to_tuple_key(self, plan: Plan) -> Tuple:
        summary_dict: dict[PlanValueToken, float | Fraction] = {}
        for token in self.get_values_needed():
            if token == PlanValueToken.motivation:
                summary_dict[token] = plan.total_motivation(preferred_type=self.preferred_type)
            elif token == PlanValueToken.min_cost:
                summary_dict[token] = plan.min_cost(preferred_type=self.preferred_type)
            elif token == PlanValueToken.estimated_cost:
                summary_dict[token] = plan.estimated_cost(preferred_type=self.preferred_type)
            elif token == PlanValueToken.max_cost:
                summary_dict[token] = plan.max_cost(preferred_type=self.preferred_type)
            elif token == PlanValueToken.satisfied_percentage_median:
                summary_dict[token] = plan.satisfied_percentage_median(preferred_type=self.preferred_type)
            elif token == PlanValueToken.satisfied_percentage_average:
                summary_dict[token] = plan.satisfied_percentage_average(preferred_type=self.preferred_type)
            elif token == PlanValueToken.concrete_action_percentage:
                if self.preferred_type is not None and (isinstance(self.preferred_type, float) or
                                                        issubclass(self.preferred_type, float) or
                                                        self.preferred_type is float):
                    summary_dict[token] = float(plan.concrete_action_percentage())
                else:
                    summary_dict[token] = plan.concrete_action_percentage()
            elif token == PlanValueToken.tasks_fully_satisfied_percentage:
                if self.preferred_type is not None and (isinstance(self.preferred_type, float) or
                                                        issubclass(self.preferred_type, float) or
                                                        self.preferred_type is float):
                    summary_dict[token] = float(plan.tasks_fully_satisfied_percentage())
                else:
                    summary_dict[token] = plan.tasks_fully_satisfied_percentage()
        keys = self._generate_standard_keys(summary_dict)
        # to guarantee a total ordering
        keys.append(id(plan))
        return tuple(keys)

    def plan_plus_delta_to_tuple_key(self, plan: Plan, deltas: PlanDeltas) -> Tuple:
        # TODO:make this
        keys = []
        summary_dict:dict[PlanValueToken, float | Fraction] = {}
        for token in self.get_values_needed():
            if token == PlanValueToken.motivation:
                if self.preferred_type is not None:
                    if (isinstance(self.preferred_type, float) or
                            issubclass(self.preferred_type, float) or
                            self.preferred_type is float):
                        summary_dict[token] = (plan.total_motivation(preferred_type=self.preferred_type) +
                                               float(deltas.total_motivation_delta))
                    else:
                        summary_dict[token] = (plan.total_motivation(preferred_type=self.preferred_type) +
                                               Fraction(deltas.total_motivation_delta))
                else:
                    summary_dict[token] = (plan.total_motivation(preferred_type=self.preferred_type) +
                                           deltas.total_motivation_delta)
            elif token == PlanValueToken.min_cost:
                if self.preferred_type is not None:
                    if (isinstance(self.preferred_type, float) or
                            issubclass(self.preferred_type, float) or
                            self.preferred_type is float):
                        summary_dict[token] = (plan.min_cost(preferred_type=self.preferred_type) +
                                               float(deltas.min_cost_delta))
                    else:
                        summary_dict[token] = (plan.min_cost(preferred_type=self.preferred_type) +
                                               Fraction(deltas.min_cost_delta))
                else:
                    summary_dict[token] = (plan.min_cost(preferred_type=self.preferred_type) +
                                           deltas.min_cost_delta)
            elif token == PlanValueToken.estimated_cost:
                if self.preferred_type is not None:
                    if (isinstance(self.preferred_type, float) or
                            issubclass(self.preferred_type, float) or
                            self.preferred_type is float):
                        summary_dict[token] = (plan.estimated_cost(preferred_type=self.preferred_type) +
                                               float(deltas.estimated_cost_delta))
                    else:
                        summary_dict[token] = (plan.estimated_cost(preferred_type=self.preferred_type) +
                                               Fraction(deltas.estimated_cost_delta))
                else:
                    summary_dict[token] = (plan.estimated_cost(preferred_type=self.preferred_type) +
                                           deltas.estimated_cost_delta)
            elif token == PlanValueToken.max_cost:
                if self.preferred_type is not None:
                    if (isinstance(self.preferred_type, float) or
                            issubclass(self.preferred_type, float) or
                            self.preferred_type is float):
                        summary_dict[token] = (plan.max_cost(preferred_type=self.preferred_type) +
                                               float(deltas.max_cost_delta))
                    else:
                        summary_dict[token] = (plan.max_cost(preferred_type=self.preferred_type) +
                                               Fraction(deltas.max_cost_delta))
                else:
                    summary_dict[token] = (plan.max_cost(preferred_type=self.preferred_type) +
                                           deltas.max_cost_delta)
            elif token == PlanValueToken.satisfied_percentage_median:
                summary_dict[token] = plan.satisfied_percentage_median(deltas, preferred_type=self.preferred_type)
            elif token == PlanValueToken.satisfied_percentage_average:
                summary_dict[token] = plan.satisfied_percentage_average(deltas, preferred_type=self.preferred_type)
            elif token == PlanValueToken.concrete_action_percentage:
                if self.preferred_type is not None and (isinstance(self.preferred_type, float) or
                                                        issubclass(self.preferred_type, float) or
                                                        self.preferred_type is float):
                    summary_dict[token] = float(plan.concrete_action_percentage(deltas))
                else:
                    summary_dict[token] = plan.concrete_action_percentage(deltas)
            elif token == PlanValueToken.tasks_fully_satisfied_percentage:
                if self.preferred_type is not None and (isinstance(self.preferred_type, float) or
                                                        issubclass(self.preferred_type, float) or
                                                        self.preferred_type is float):
                    summary_dict[token] = float(plan.tasks_fully_satisfied_percentage(deltas))
                else:
                    summary_dict[token] = plan.tasks_fully_satisfied_percentage(deltas)
        keys = self._generate_standard_keys(summary_dict)
        # to guarantee a total ordering
        keys.append(str(plan.uid))
        keys.append(id(plan))
        return tuple(keys)

    def get_values_needed(self) -> Set[PlanValueToken]:
        if len(self._values_needed) == 0:
            for cur_token in self.order:
                if cur_token == PlanComparisonStrategyToken.motivation_over_min_cost:
                    self._values_needed.add(PlanValueToken.motivation)
                    self._values_needed.add(PlanValueToken.min_cost)
                elif cur_token == PlanComparisonStrategyToken.motivation_over_estimated_cost:
                    self._values_needed.add(PlanValueToken.motivation)
                    self._values_needed.add(PlanValueToken.estimated_cost)
                elif cur_token == PlanComparisonStrategyToken.motivation_over_max_cost:
                    self._values_needed.add(PlanValueToken.motivation)
                    self._values_needed.add(PlanValueToken.max_cost)
                elif cur_token == PlanComparisonStrategyToken.min_cost_over_motivation:
                    self._values_needed.add(PlanValueToken.motivation)
                    self._values_needed.add(PlanValueToken.min_cost)
                elif cur_token == PlanComparisonStrategyToken.estimated_cost_over_motivation:
                    self._values_needed.add(PlanValueToken.motivation)
                    self._values_needed.add(PlanValueToken.estimated_cost)
                elif cur_token == PlanComparisonStrategyToken.max_cost_over_motivation:
                    self._values_needed.add(PlanValueToken.motivation)
                    self._values_needed.add(PlanValueToken.max_cost)
                elif cur_token == PlanComparisonStrategyToken.min_cost:
                    self._values_needed.add(PlanValueToken.min_cost)
                elif cur_token == PlanComparisonStrategyToken.estimated_cost:
                    self._values_needed.add(PlanValueToken.estimated_cost)
                elif cur_token == PlanComparisonStrategyToken.max_cost:
                    self._values_needed.add(PlanValueToken.max_cost)
                elif cur_token == PlanComparisonStrategyToken.motivation:
                    self._values_needed.add(PlanValueToken.motivation)
                elif cur_token == PlanComparisonStrategyToken.satisfied_percentage_average_asc:
                    self._values_needed.add(PlanValueToken.satisfied_percentage_average)
                elif cur_token == PlanComparisonStrategyToken.satisfied_percentage_average_des:
                    self._values_needed.add(PlanValueToken.satisfied_percentage_average)
                elif cur_token == PlanComparisonStrategyToken.satisfied_percentage_median_asc:
                    self._values_needed.add(PlanValueToken.satisfied_percentage_median)
                elif cur_token == PlanComparisonStrategyToken.satisfied_percentage_median_des:
                    self._values_needed.add(PlanValueToken.satisfied_percentage_median)
                elif cur_token == PlanComparisonStrategyToken.tasks_fully_satisfied_percentage_asc:
                    self._values_needed.add(PlanValueToken.tasks_fully_satisfied_percentage)
                elif cur_token == PlanComparisonStrategyToken.tasks_fully_satisfied_percentage_des:
                    self._values_needed.add(PlanValueToken.tasks_fully_satisfied_percentage)
                elif cur_token == PlanComparisonStrategyToken.concrete_action_percentage_asc:
                    self._values_needed.add(PlanValueToken.concrete_action_percentage)
                elif cur_token == PlanComparisonStrategyToken.concrete_action_percentage_des:
                    self._values_needed.add(PlanValueToken.concrete_action_percentage)
        return self._values_needed