from abc import ABCMeta
from enum import Enum, auto
from typing import List, Tuple

from uniplansy.plans.plan import Plan, PlanDeltas
from uniplansy.tasks.tasks import Task


class PlanComparisonStrategyToken(Enum):
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

# cost ascending motivation descending
class PlanComparisonStrategy(metaclass=ABCMeta):

    def __init__(self, order: List[PlanComparisonStrategyToken]):
        super().__init__()
        self.order: List[PlanComparisonStrategyToken] = order

    def task_to_tuple_key(self, task: Task) -> Tuple:
        keys = []
        for token in self.order:
            if token == PlanComparisonStrategyToken.motivation_over_min_cost:
                try:
                    keys.append(-task.motivation/task.min_cost)
                except ZeroDivisionError:
                    if task.motivation > 0:
                        keys.append(float('-inf'))
                    elif task.motivation < 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.motivation_over_estimated_cost:
                try:
                    keys.append(-task.motivation/task.estimated_cost)
                except ZeroDivisionError:
                    if task.motivation > 0:
                        keys.append(float('-inf'))
                    elif task.motivation < 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.motivation_over_max_cost:
                try:
                    keys.append(-task.motivation/task.max_cost)
                except ZeroDivisionError:
                    if task.motivation > 0:
                        keys.append(float('-inf'))
                    elif task.motivation < 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.min_cost_over_motivation:
                try:
                    keys.append(task.min_cost/task.motivation)
                except ZeroDivisionError:
                    if task.min_cost < 0:
                        keys.append(float('-inf'))
                    elif task.min_cost > 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.estimated_cost_over_motivation:
                try:
                    keys.append(task.estimated_cost/task.motivation)
                except ZeroDivisionError:
                    if task.estimated_cost < 0:
                        keys.append(float('-inf'))
                    elif task.estimated_cost > 0:
                        keys.append(float('inf'))
                    else:
                        keys.append(float('nan'))
            elif token == PlanComparisonStrategyToken.max_cost_over_motivation:
                try:
                    keys.append(task.max_cost/task.motivation)
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
        # to guarantee a total ordering
        keys.append(str(plan.uid))
        keys.append(id(plan))
        return tuple(keys)