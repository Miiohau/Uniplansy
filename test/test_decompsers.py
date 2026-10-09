"""defines a simple goal and simple leaf decomposer"""

from typing import List

from uniplansy.decomposers.core import Goal, DecomposerNode, Decomposer
from uniplansy.planner.core import Planner
from uniplansy.planner.plan_cache_strategy import NullPlanCacheStrategy
from uniplansy.planner.plan_selection_strategy import GreedyPlanSelectionStrategy
from uniplansy.planner.planning_strategy import GreedyPlanningStrategy
from uniplansy.planner.stopping_strategy import NullStoppingStrategy
from uniplansy.plans.plan import Plan
from uniplansy.plans.plan_comparison_strategy import BasicPlanComparisonStrategy, PlanComparisonStrategyToken
from uniplansy.reasoners.graph import ReasonerTemplate, SimpleReasonerBuilder
from uniplansy.tasks.tasks import TaskDescription


class TestWorld:
    pass


class TestGoal(Goal[TestWorld]):

    def __init__(self):
        super().__init__(uid="test_goal_decomposer", goal_task_uid="test_goal", goal_description=TaskDescription(
            uid="test_goal_description",
            human_understandable_string="this is a test", ))


class TestDecomposer(Decomposer[TestWorld]):

    def __init__(self):
        super().__init__(uid="test_decomposer_decomposer")

    # noinspection PyUnusedLocal
    @staticmethod
    def my_act(world, context) -> bool:
        """a test action. exists only for testing purposes."""
        print("this is a test")
        return True

    def convert_to_reasoner_graph(self, node: DecomposerNode,
                                  node_id_to_builder_id: dict[str, str]) -> ReasonerTemplate:
        new_template = SimpleReasonerBuilder(act_delegate=TestDecomposer.my_act)
        new_template.preferred_name = "actor"
        return new_template

    def decompose_tasks(self, plan: Plan, world: TestWorld) -> List[Plan]:
        new_plan = plan.deep_copy_and_unfreeze()
        decomposer_node = DecomposerNode(uid="test_decomposer_node", node_decomposer=self)
        goal_node = new_plan.tasks_by_UID["test_goal_description"]
        goal_node.children.add(decomposer_node)
        goal_node.satisfied_percentage = 1
        decomposer_node.parents.add(goal_node)
        new_plan.add_node(decomposer_node)
        return [new_plan]

    def applicable(self, plan: Plan, world: TestWorld) -> bool:
        if "test_goal_description" in plan.tasks_by_UID.keys():
            return plan.tasks_by_UID["test_goal_description"].satisfied_percentage == 0
        else:
            return False


def test_simple_workflow():
    plan_comparison_strategy = BasicPlanComparisonStrategy(
        order=[
            PlanComparisonStrategyToken.motivation_over_estimated_cost,
            PlanComparisonStrategyToken.motivation_over_min_cost,
            PlanComparisonStrategyToken.motivation_over_max_cost,
            PlanComparisonStrategyToken.motivation,
            PlanComparisonStrategyToken.estimated_cost,
            PlanComparisonStrategyToken.min_cost,
            PlanComparisonStrategyToken.max_cost,
            PlanComparisonStrategyToken.satisfied_percentage_average_asc,
            PlanComparisonStrategyToken.satisfied_percentage_median_asc,
            PlanComparisonStrategyToken.tasks_fully_satisfied_percentage_asc,
            PlanComparisonStrategyToken.concrete_action_percentage_asc
        ]
    )
    planning_strategy = GreedyPlanningStrategy(
        plan_comparison_strategy=plan_comparison_strategy
    )
    final_plan_selection_strategy = GreedyPlanSelectionStrategy(
        plan_comparison_strategy=plan_comparison_strategy
    )
    test_planner = Planner(
        planning_strategy=planning_strategy,
        stopping_strategy=NullStoppingStrategy(),
        final_plan_selection_strategy=final_plan_selection_strategy,
        cache_strategy=NullPlanCacheStrategy(),
        decomposers={TestGoal(), TestDecomposer()}
    )
    world = TestWorld()
    test_planner.resume_planning(world=world)
