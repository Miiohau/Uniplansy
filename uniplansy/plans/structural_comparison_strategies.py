"""defines DepthComparisonStrategy

"""
from fractions import Fraction
from typing import Tuple, Set, Optional, List

from uniplansy.planner.base import PlanningContext, UIDNode
from uniplansy.plans.plan import Plan, PlanDeltas
from uniplansy.plans.plan_comparison_strategy import PlanComparisonStrategy, PlanValueToken
from uniplansy.tasks.tasks import Task


class DepthComparisonStrategy(PlanComparisonStrategy):
    """DepthComparisonStrategy sorts plans based on how deep in the planning tree they are"""

    def __init__(self, planning_context: Optional[PlanningContext],
                 leaves_first: bool = True,
                 ascending: bool = True,
                 ensure_total_ordering: bool = False):
        super().__init__()
        self.planning_context = planning_context
        self.ascending = ascending
        self.ensure_total_ordering = ensure_total_ordering
        self.leaves_first = leaves_first
        self.printed_warning = False

    def task_to_tuple_key(self, task: Task) -> Tuple:
        if self.ensure_total_ordering:
            return tuple(
                [0, task.description.human_understandable_string, task.description.uid, id(task.description), id(task)])
        else:
            return tuple([0])

    def plan_to_tuple_key(self,
                          plan: Plan,
                          planning_context: Optional[PlanningContext] = None,
                          ensure_total_ordering: Optional[bool] = None) -> Tuple:
        if planning_context is None:
            assert self.planning_context is not None, "ERROR: No planning_context provided to DepthComparisonStrategy"
            if self.planning_context is None:
                if not self.printed_warning:
                    print("WARNING: No planning_context provided to DepthComparisonStrategy")
                    self.printed_warning = True
                return tuple([0])
            planning_context = self.planning_context
        current_node: UIDNode = planning_context.plan_uid_node_by_uid[plan.uid]
        steps: int = 0
        step_mod: int = 0
        if self.leaves_first and (len(current_node.children) > 0):
            step_mod = len(planning_context.plan_uid_node_by_uid) + len(planning_context.decomposer_uid_node_by_uid) + 1
        while current_node is not None:
            steps += 1
            current_node = current_node.parent
        if not self.ascending:
            steps *= -1
        steps += step_mod
        should_ensure_total_ordering: bool = self.ensure_total_ordering
        if ensure_total_ordering is not None:
            should_ensure_total_ordering = ensure_total_ordering
        if should_ensure_total_ordering:
            return tuple([steps, str(plan.uid), id(plan)])
        else:
            return tuple([steps])

    def plan_plus_delta_to_tuple_key(self, plan: Plan, deltas: PlanDeltas,
                                     planning_context: Optional[PlanningContext] = None) -> Tuple:
        keys: List[float | Fraction | str] = list(self.plan_to_tuple_key(plan, planning_context, False))
        if self.ascending:
            keys[0] += 1
        else:
            keys[0] -= 1
        if self.ensure_total_ordering:
            # to guarantee a total ordering
            keys.append(str(plan.uid))
            keys.append(str(deltas.decomposer_uid))
            keys.append(str(deltas.uid))
            keys.append(id(plan))
            keys.append(id(deltas))
        return tuple(keys)

    def get_values_needed(self) -> Set[PlanValueToken]:
        return set()