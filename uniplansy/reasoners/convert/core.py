"""Contains the classes involved in convertion a Plan into a Reasoner graph.

Converter(class): Manages the convertion of a plan to a ReasonerBuilder
PlanGraphNodeToReasonerStrategy(class): defines how to convert a PlanGraphNode to ReasonerBuilder
ConvertionFinalizationStrategy(class): defines how to join parentless nodes into one ReasonerBuilder
AndPlanGraphNodeToReasonerStrategy(PlanGraphNodeToReasonerStrategy): joins children of the passed in node with a
AndReasonerBuilder
OrPlanGraphNodeToReasonerStrategy(PlanGraphNodeToReasonerStrategy): joins children of the passed in node with a
OrReasonerBuilder
AndConvertionFinalizationStrategy(ConvertionFinalizationStrategy): joins parentless node with a AndReasonerBuilder
OrConvertionFinalizationStrategy(ConvertionFinalizationStrategy): joins parentless node with a OrReasonerBuilder
"""
from abc import ABCMeta, abstractmethod
from typing import Set, Iterable

from uniplansy.decomposers.core import DecomposerNode
from uniplansy.plans.plan import Plan, PlanGraphNode
from uniplansy.reasoners.graph import ReasonerBuilder, CommonConjunctionReasonerBuilder
from uniplansy.tasks.tasks import Task
from uniplansy.util.id_registry import IDRegistry
from uniplansy.util.uid_suppliers.counter_based.thread_local_guid_supplier import ThreadLocalGuidSupplier
from uniplansy.util.uid_suppliers.wrappers.wrappers import UniqueInIDRegistryUIDSupplierWrapper
from collections import deque

class PlanGraphNodeToReasonerStrategy(metaclass=ABCMeta):
    """defines how to convert a PlanGraphNode to ReasonerBuilder"""

    @abstractmethod
    def convert(self, current_node: PlanGraphNode, node_id_to_builder_id: dict[str, str]) -> ReasonerBuilder:
        """converts a PlanGraphNode to a ReasonerBuilder

        :param current_node: the node to convert
        :param node_id_to_builder_id: a dictionary that maps node UIDs to builder UIDs
        :return: the reasoner template that will be used to create the Reasoner
        """
        pass


class ConvertionFinalizationStrategy(metaclass=ABCMeta):
    """defines how to join parentless nodes into one ReasonerBuilder"""

    @abstractmethod
    def finalize(self, roots: Set[PlanGraphNode], node_id_to_builder_id: dict[str, str]) -> ReasonerBuilder:
        """joins parentless nodes into one ReasonerBuilder

        :param roots: the list of parentless nodes
        :param node_id_to_builder_id: a dictionary that maps node UIDs to builder UIDs
        :return: the reasoner template that will be used to create the Reasoner
        """
        pass


class AndPlanGraphNodeToReasonerStrategy(PlanGraphNodeToReasonerStrategy):
    """joins children of the passed in node with a AndReasonerBuilder"""

    def convert(self, current_node: PlanGraphNode, node_id_to_builder_id: dict[str, str]) -> ReasonerBuilder:
        and_builder: CommonConjunctionReasonerBuilder = (
            CommonConjunctionReasonerBuilder(all_semantics=True,
                                             any_semantics=False
                                             )
        )
        for current_child in current_node.children:
            and_builder.uid.append(node_id_to_builder_id[current_child.uid])
        if isinstance(current_node, Task):
            and_builder.preferred_name = current_node.description.human_understandable_string
        else:
            and_builder.preferred_name = current_node.uid
        return and_builder


class OrPlanGraphNodeToReasonerStrategy(PlanGraphNodeToReasonerStrategy):
    """joins children of the passed in node with a OrReasonerBuilder"""

    def convert(self, current_node: PlanGraphNode, node_id_to_builder_id: dict[str, str]) -> ReasonerBuilder:
        or_builder: CommonConjunctionReasonerBuilder = (
            CommonConjunctionReasonerBuilder(all_semantics=False,
                                             any_semantics=True
                                             )
        )
        for current_child in current_node.children:
            or_builder.uid.append(node_id_to_builder_id[current_child.uid])
        if isinstance(current_node, Task):
            or_builder.preferred_name = current_node.description.human_understandable_string
        else:
            or_builder.preferred_name = current_node.uid
        return or_builder


class AndConvertionFinalizationStrategy(ConvertionFinalizationStrategy):
    """joins parentless node with a AndReasonerBuilder"""

    def finalize(self, roots: Set[PlanGraphNode], node_id_to_builder_id: dict[str, str]) -> ReasonerBuilder:
        and_builder: CommonConjunctionReasonerBuilder = (
            CommonConjunctionReasonerBuilder(all_semantics=True,
                                             any_semantics=False
                                             )
        )
        for current_child in roots:
            and_builder.uid.append(node_id_to_builder_id[current_child.uid])
        and_builder.preferred_name = "root"
        return and_builder


class OrConvertionFinalizationStrategy(ConvertionFinalizationStrategy):
    """joins parentless node with a OrReasonerBuilder"""

    def finalize(self, roots: Set[PlanGraphNode], node_id_to_builder_id: dict[str, str]) -> ReasonerBuilder:
        or_builder: CommonConjunctionReasonerBuilder = (
            CommonConjunctionReasonerBuilder(all_semantics=False,
                                             any_semantics=True
                                             )
        )
        for current_child in roots:
            or_builder.uid.append(node_id_to_builder_id[current_child.uid])
        or_builder.preferred_name = "root"
        return or_builder

class Converter:
    """Manages the convertion of a plan to a ReasonerBuilder"""

    def __init__(self,
                 task_to_reasoner_strategy: PlanGraphNodeToReasonerStrategy = AndPlanGraphNodeToReasonerStrategy(),
                 fallback_convertion_strategy: PlanGraphNodeToReasonerStrategy = AndPlanGraphNodeToReasonerStrategy(),
                 convertion_finalization_strategy: ConvertionFinalizationStrategy = AndConvertionFinalizationStrategy(),
                 ):
        self.task_to_reasoner_strategy = task_to_reasoner_strategy
        self.fallback_convertion_strategy = fallback_convertion_strategy
        self.convertion_finalization_strategy = convertion_finalization_strategy

    def _create_builder(self, current_node: PlanGraphNode, node_id_to_builder_id: dict[str, str]) -> ReasonerBuilder:
        if isinstance(current_node, DecomposerNode):
            return current_node.node_decomposer.convert_to_reasoner_graph(current_node,node_id_to_builder_id)
        elif isinstance(current_node, Task):
            return self.task_to_reasoner_strategy.convert(current_node,node_id_to_builder_id)
        else:
            return self.fallback_convertion_strategy.convert(current_node,node_id_to_builder_id)

    @staticmethod
    def _all_children_already_processed(current_node: PlanGraphNode,
                                        processed_node_uids:Iterable[str]
                                        ) -> bool:
        for current_child in current_node.children:
            if current_child.uid not in processed_node_uids:
                return False
        return True

    def convert(self, plan: Plan) -> ReasonerBuilder:
        """converts a plan into a ReasonerBuilder

        :param plan: the plan to convert
        :return: the reasoner builder
        """
        reasoner_id_registry: IDRegistry = IDRegistry()
        reasoner_id_registry.guid_supplier = UniqueInIDRegistryUIDSupplierWrapper(
            registry=reasoner_id_registry,
            delegate=ThreadLocalGuidSupplier()
        )
        queue: deque[PlanGraphNode] = deque()
        for current_node in plan.nodes_by_UID.values():
            if len(current_node.children) <= 0:
                queue.append(current_node)
        node_id_to_builder_id: dict[str, str] = dict()
        roots: Set[PlanGraphNode] = set()
        while len(queue) > 0:
            current_node = queue.popleft()
            current_builder: ReasonerBuilder = self._create_builder(current_node, node_id_to_builder_id)
            if current_builder.uid is None:
                current_builder.fill_unset_fields(id_registry=reasoner_id_registry)
            reasoner_id_registry.register(current_builder.uid, current_builder)
            node_id_to_builder_id[current_node.uid] = current_builder.uid
            if len(current_node.parents) <= 0:
                roots.add(current_node)
            else:
                for current_parent in current_node.parents:
                    if self._all_children_already_processed(current_parent, node_id_to_builder_id.keys()):
                        queue.append(current_parent)
        return self.convertion_finalization_strategy.finalize(roots, node_id_to_builder_id)

