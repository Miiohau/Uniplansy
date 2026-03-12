"""defines PlanComparisonStrategy and its supporting and basic subclasses

"""
from abc import ABCMeta, abstractmethod
from enum import Enum, auto
from typing import List, Tuple, Set

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

    def __init__(self, order: List[PlanComparisonStrategyToken]):
        super().__init__()
        self.order: List[PlanComparisonStrategyToken] = order
        self._values_needed: Set[PlanValueToken] = set()

    def task_to_tuple_key(self, task: Task) -> Tuple:
        keys = []
        for token in self.order:
            if token == PlanComparisonStrategyToken.motivation_over_min_cost:
                try:
                    keys.append(-task.motivation / task.min_cost)
                except ZeroDivisionError:
                    if task.motivation > 0:
                        keys.append(float('-inf'))
                    elif task.motivation < 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.motivation_over_estimated_cost:
                try:
                    keys.append(-task.motivation / task.estimated_cost)
                except ZeroDivisionError:
                    if task.motivation > 0:
                        keys.append(float('-inf'))
                    elif task.motivation < 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.motivation_over_max_cost:
                try:
                    keys.append(-task.motivation / task.max_cost)
                except ZeroDivisionError:
                    if task.motivation > 0:
                        keys.append(float('-inf'))
                    elif task.motivation < 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.min_cost_over_motivation:
                try:
                    keys.append(task.min_cost / task.motivation)
                except ZeroDivisionError:
                    if task.min_cost < 0:
                        keys.append(float('-inf'))
                    elif task.min_cost > 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.estimated_cost_over_motivation:
                try:
                    keys.append(task.estimated_cost / task.motivation)
                except ZeroDivisionError:
                    if task.estimated_cost < 0:
                        keys.append(float('-inf'))
                    elif task.estimated_cost > 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.max_cost_over_motivation:
                try:
                    keys.append(task.max_cost / task.motivation)
                except ZeroDivisionError:
                    if task.max_cost < 0:
                        keys.append(float('-inf'))
                    elif task.max_cost > 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.motivation:
                keys.append(-task.motivation)
            elif token == PlanComparisonStrategyToken.min_cost:
                keys.append(task.min_cost)
            elif token == PlanComparisonStrategyToken.estimated_cost:
                keys.append(task.estimated_cost)
            elif token == PlanComparisonStrategyToken.max_cost:
                keys.append(task.max_cost)
            elif token == PlanComparisonStrategyToken.satisfied_percentage_average_asc:
                keys.append(task.satisfied_percentage)
            elif token == PlanComparisonStrategyToken.satisfied_percentage_median_asc:
                keys.append(task.satisfied_percentage)
            elif token == PlanComparisonStrategyToken.satisfied_percentage_average_des:
                keys.append(-task.satisfied_percentage)
            elif token == PlanComparisonStrategyToken.satisfied_percentage_median_des:
                keys.append(-task.satisfied_percentage)
            elif token == PlanComparisonStrategyToken.tasks_fully_satisfied_percentage_asc:
                keys.append(task.satisfied_percentage)
            elif token == PlanComparisonStrategyToken.tasks_fully_satisfied_percentage_des:
                keys.append(-task.satisfied_percentage)
            elif token == PlanComparisonStrategyToken.concrete_action_percentage_asc:
                if len(task.children) > 0:
                    keys.append(task.satisfied_percentage - 1)
                else:
                    keys.append(task.satisfied_percentage)
            elif token == PlanComparisonStrategyToken.concrete_action_percentage_des:
                if len(task.children) > 0:
                    keys.append(1 - task.satisfied_percentage)
                else:
                    keys.append(-task.satisfied_percentage)
        # to guarantee a total ordering
        keys.append(task.description.human_understandable_string)
        keys.append(task.description.uid)
        # it actually should be totally ordered by this point but just to make extra sure.
        keys.append(id(task.description))
        keys.append(id(task))
        return tuple(keys)

    def plan_to_tuple_key(self, plan: Plan) -> Tuple:
        keys = []
        for token in self.order:
            if token == PlanComparisonStrategyToken.motivation_over_min_cost:
                try:
                    keys.append(-plan.total_motivation() / plan.min_cost())
                except ZeroDivisionError:
                    if plan.total_motivation() > 0:
                        keys.append(float('-inf'))
                    elif plan.total_motivation() < 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.motivation_over_estimated_cost:
                try:
                    keys.append(-plan.total_motivation() / plan.estimated_cost())
                except ZeroDivisionError:
                    if plan.total_motivation() > 0:
                        keys.append(float('-inf'))
                    elif plan.total_motivation() < 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.motivation_over_max_cost:
                try:
                    keys.append(-plan.total_motivation() / plan.max_cost())
                except ZeroDivisionError:
                    if plan.total_motivation() > 0:
                        keys.append(float('-inf'))
                    elif plan.total_motivation() < 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.min_cost_over_motivation:
                try:
                    keys.append(plan.min_cost() / plan.total_motivation())
                except ZeroDivisionError:
                    if plan.min_cost() < 0:
                        keys.append(float('-inf'))
                    elif plan.min_cost() > 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.estimated_cost_over_motivation:
                try:
                    keys.append(plan.estimated_cost() / plan.total_motivation())
                except ZeroDivisionError:
                    if plan.estimated_cost() < 0:
                        keys.append(float('-inf'))
                    elif plan.estimated_cost() > 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.max_cost_over_motivation:
                try:
                    keys.append(plan.max_cost() / plan.total_motivation())
                except ZeroDivisionError:
                    if plan.max_cost() < 0:
                        keys.append(float('-inf'))
                    elif plan.max_cost() > 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.motivation:
                keys.append(-plan.total_motivation())
            elif token == PlanComparisonStrategyToken.min_cost:
                keys.append(plan.min_cost())
            elif token == PlanComparisonStrategyToken.estimated_cost:
                keys.append(plan.estimated_cost())
            elif token == PlanComparisonStrategyToken.max_cost:
                keys.append(plan.max_cost())
            elif token == PlanComparisonStrategyToken.satisfied_percentage_average_asc:
                keys.append(plan.average_satisfied_percentage())
            elif token == PlanComparisonStrategyToken.satisfied_percentage_median_asc:
                keys.append(plan.median_satisfied_percentage())
            elif token == PlanComparisonStrategyToken.satisfied_percentage_average_des:
                keys.append(-plan.average_satisfied_percentage())
            elif token == PlanComparisonStrategyToken.satisfied_percentage_median_des:
                keys.append(-plan.median_satisfied_percentage())
            elif token == PlanComparisonStrategyToken.tasks_fully_satisfied_percentage_asc:
                keys.append(plan.tasks_fully_satisfied_percentage())
            elif token == PlanComparisonStrategyToken.tasks_fully_satisfied_percentage_des:
                keys.append(-plan.tasks_fully_satisfied_percentage())
            elif token == PlanComparisonStrategyToken.concrete_action_percentage_asc:
                keys.append(plan.concrete_action_percentage())
            elif token == PlanComparisonStrategyToken.concrete_action_percentage_des:
                keys.append(-plan.concrete_action_percentage())
        # to guarantee a total ordering
        keys.append(id(plan))
        return tuple(keys)

    def plan_plus_delta_to_tuple_key(self, plan: Plan, deltas: PlanDeltas) -> Tuple:
        keys = []
        for token in self.order:
            if token == PlanComparisonStrategyToken.motivation_over_min_cost:
                try:
                    keys.append(-(plan.total_motivation() + deltas.total_motivation_delta) /
                                (plan.min_cost() + deltas.min_cost_delta))
                except ZeroDivisionError:
                    if (plan.total_motivation() + deltas.total_motivation_delta) > 0:
                        keys.append(float('-inf'))
                    elif (plan.total_motivation() + deltas.total_motivation_delta) < 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.motivation_over_estimated_cost:
                try:
                    keys.append(-(plan.total_motivation() + deltas.total_motivation_delta) /
                                (plan.estimated_cost() + deltas.estimated_cost_delta))
                except ZeroDivisionError:
                    if (plan.total_motivation() + deltas.total_motivation_delta) > 0:
                        keys.append(float('-inf'))
                    elif (plan.total_motivation() + deltas.total_motivation_delta) < 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.motivation_over_max_cost:
                try:
                    keys.append(-(plan.total_motivation() + deltas.total_motivation_delta) /
                                (plan.max_cost() + deltas.max_cost_delta))
                except ZeroDivisionError:
                    if (plan.total_motivation() + deltas.total_motivation_delta) > 0:
                        keys.append(float('-inf'))
                    elif (plan.total_motivation() + deltas.total_motivation_delta) < 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.min_cost_over_motivation:
                try:
                    keys.append((plan.min_cost() + deltas.min_cost_delta) /
                                (plan.total_motivation() + deltas.total_motivation_delta))
                except ZeroDivisionError:
                    if (plan.min_cost() + deltas.min_cost_delta) < 0:
                        keys.append(float('-inf'))
                    elif (plan.min_cost() + deltas.min_cost_delta) > 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.estimated_cost_over_motivation:
                try:
                    keys.append((plan.estimated_cost() + deltas.estimated_cost_delta) /
                                (plan.total_motivation() + deltas.total_motivation_delta))
                except ZeroDivisionError:
                    if (plan.estimated_cost() + deltas.estimated_cost_delta) < 0:
                        keys.append(float('-inf'))
                    elif (plan.estimated_cost() + deltas.estimated_cost_delta) > 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.max_cost_over_motivation:
                try:
                    keys.append((plan.max_cost() + deltas.max_cost_delta) /
                                (plan.total_motivation() + deltas.total_motivation_delta))
                except ZeroDivisionError:
                    if (plan.max_cost() + deltas.max_cost_delta) < 0:
                        keys.append(float('-inf'))
                    elif (plan.max_cost() + deltas.max_cost_delta) > 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.motivation:
                keys.append(-(plan.total_motivation() + deltas.total_motivation_delta))
            elif token == PlanComparisonStrategyToken.min_cost:
                keys.append(plan.min_cost() + deltas.min_cost_delta)
            elif token == PlanComparisonStrategyToken.estimated_cost:
                keys.append(plan.estimated_cost() + deltas.estimated_cost_delta)
            elif token == PlanComparisonStrategyToken.max_cost:
                keys.append(plan.max_cost() + deltas.max_cost_delta)
            elif token == PlanComparisonStrategyToken.satisfied_percentage_average_asc:
                keys.append(plan.average_satisfied_percentage(deltas))
            elif token == PlanComparisonStrategyToken.satisfied_percentage_median_asc:
                keys.append(plan.median_satisfied_percentage(deltas))
            elif token == PlanComparisonStrategyToken.satisfied_percentage_average_des:
                keys.append(-plan.average_satisfied_percentage(deltas))
            elif token == PlanComparisonStrategyToken.satisfied_percentage_median_des:
                keys.append(-plan.median_satisfied_percentage(deltas))
            elif token == PlanComparisonStrategyToken.tasks_fully_satisfied_percentage_asc:
                keys.append(plan.tasks_fully_satisfied_percentage(deltas))
            elif token == PlanComparisonStrategyToken.tasks_fully_satisfied_percentage_des:
                keys.append(-plan.tasks_fully_satisfied_percentage(deltas))
            elif token == PlanComparisonStrategyToken.concrete_action_percentage_asc:
                keys.append(plan.concrete_action_percentage(deltas))
            elif token == PlanComparisonStrategyToken.concrete_action_percentage_des:
                keys.append(-plan.concrete_action_percentage(deltas))
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