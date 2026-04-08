#TODO: (after updating to python 3.14 (in which Annotations are lazily evaluated by default))
# remove "from __future__ import annotations"
from __future__ import annotations

from typing import Optional, List, Callable

from uniplansy.reasoners.base import Reasoner, Reasoner_Update_Context_Type, ReasonerBuilder, ReasonerState, \
    SubReasonerStruct, ChildFailureException
from uniplansy.reasoners.considerations.core import ReasonerConsideration
from uniplansy.util.global_type_vars import World_Type
from uniplansy.util.id_registry import IDRegistry


# Todo: validate this against a set of requirements


class SimpleReasoner(Reasoner[Reasoner_Update_Context_Type, World_Type]):
    def __init__(self, uid: str, id_registry: IDRegistry[ReasonerBuilder],
                 start_conditions: List[ReasonerConsideration] = None,
                 run_conditions: List[ReasonerConsideration] = None,
                 sense_delegate: Optional[
                     Callable[[World_Type, Reasoner_Update_Context_Type], Reasoner_Update_Context_Type]] = None,
                 act_delegate: Optional[Callable[[World_Type, Reasoner_Update_Context_Type], bool]] = None,
                 ):
        super().__init__(uid=uid, id_registry=id_registry, start_conditions=start_conditions,
                         run_conditions=run_conditions)
        self.sense_delegate = sense_delegate
        self.act_delegate = act_delegate

    # @override
    def sense(self, world: World_Type, update_context: Reasoner_Update_Context_Type) -> Reasoner_Update_Context_Type:
        new_update_context: Reasoner_Update_Context_Type = super().sense(world, update_context)
        if self.sense_delegate is not None:
            new_update_context = self.sense_delegate(new_update_context, new_update_context)
        return new_update_context

    # @override
    def act(self, world: World_Type, update_context: Reasoner_Update_Context_Type):
        finalize: bool = True
        if self.act_delegate is not None:
            finalize = self.act_delegate(world, update_context)
        if finalize:
            super().act(world, update_context)


class CommonConjunctionReasoner(Reasoner[Reasoner_Update_Context_Type, World_Type]):

    def __init__(self, uid: str,
                 id_registry: IDRegistry[ReasonerBuilder],
                 sub_reasoner_uids: Optional[List[str]],
                 short_circuiting: bool = True,
                 all_semantics: bool = True,
                 any_semantics: bool = False,
                 default_finished_state: Optional[ReasonerState] = None,
                 start_conditions: List[ReasonerConsideration] = None,
                 run_conditions: List[ReasonerConsideration] = None):
        super().__init__(uid=uid, id_registry=id_registry, start_conditions=start_conditions,
                         run_conditions=run_conditions)
        self.short_circuiting: bool = short_circuiting
        self.child_failure_count: int = 0
        self.child_successes_count: int = 0
        self.all_semantics: bool = all_semantics
        self.any_semantics: bool = any_semantics
        self.default_finished_state: Optional[ReasonerState] = default_finished_state
        if sub_reasoner_uids is not None:
            self.sub_reasoner_uids: List[str] = sub_reasoner_uids
        else:
            self.sub_reasoner_uids: List[str] = []

    # noinspection PyUnusedLocal
    def handle_active_reasoner_consideration_failure(self,
                                                     child: SubReasonerStruct[Reasoner_Update_Context_Type, World_Type],
                                                     failed_considerations: list[ReasonerConsideration],
                                                     update_context: Reasoner_Update_Context_Type,
                                                     failure_context: Optional[Exception]):
        self.child_failure_count += 1
        if self.all_semantics:
            if self.short_circuiting:
                self.state = ReasonerState.Failed
                self.failure_context = failure_context
            else:
                new_failure_context: ChildFailureException = ChildFailureException(child=child.reasoner)
                new_failure_context.__cause__ = failure_context
                self._build_failure_context(new_failure_context, self.failure_context)

    # noinspection PyUnusedLocal
    def handle_child_failure(self, child: SubReasonerStruct[Reasoner_Update_Context_Type, World_Type],
                             update_context: Reasoner_Update_Context_Type, failure_context: Optional[Exception]):
        self.child_failure_count += 1
        if self.all_semantics:
            if self.short_circuiting:
                self.state = ReasonerState.Failed
                new_failure_context: ChildFailureException = ChildFailureException(child=child.reasoner)
                new_failure_context.__cause__ = failure_context
                self.failure_context = new_failure_context
            else:
                new_failure_context: ChildFailureException = ChildFailureException(child=child.reasoner)
                new_failure_context.__cause__ = failure_context
                self._build_failure_context(new_failure_context, self.failure_context)

    def handle_child_success(self, child: SubReasonerStruct[Reasoner_Update_Context_Type, World_Type],
                             update_context: Reasoner_Update_Context_Type):
        self.child_successes_count += 1
        if self.any_semantics and self.short_circuiting:
            self.state = ReasonerState.Done

    def act(self, world: World_Type, update_context: Reasoner_Update_Context_Type):
        if self.all_semantics:
            if self.child_failure_count > 0:
                self.state = ReasonerState.Failed
            if self.default_finished_state is not None:
                self.state = self.default_finished_state
            else:
                self.state = ReasonerState.Done
        elif self.any_semantics:
            if self.child_successes_count > 0:
                self.state = ReasonerState.Done
            if self.default_finished_state is not None:
                self.state = self.default_finished_state
            else:
                self.state = ReasonerState.Failed
        else:
            self.state = ReasonerState.Done

    def run_children(self, active_sub_reasoners: List[SubReasonerStruct[Reasoner_Update_Context_Type, World_Type]],
                     world: World_Type, update_context: Reasoner_Update_Context_Type):
        for curChild in active_sub_reasoners:
            self.run_child(curChild, world, update_context)
            if self.short_circuiting and self.state.is_finalized_state:
                break


class PrioritySequenceReasoner(CommonConjunctionReasoner[Reasoner_Update_Context_Type, World_Type]):

    def __init__(self, uid: str,
                 id_registry: IDRegistry[ReasonerBuilder],
                 sub_reasoner_uids: List[str],
                 short_circuiting: bool = True,
                 all_semantics: bool = True,
                 any_semantics: bool = False,
                 default_finished_state: Optional[ReasonerState] = ReasonerState.Done,
                 start_conditions: List[ReasonerConsideration] = None,
                 run_conditions: List[ReasonerConsideration] = None):
        super().__init__(uid=uid, id_registry=id_registry, sub_reasoner_uids=sub_reasoner_uids,
                         start_conditions=start_conditions, run_conditions=run_conditions,
                         short_circuiting=short_circuiting, all_semantics=all_semantics, any_semantics=any_semantics,
                         default_finished_state=default_finished_state)
        self.built_sub_reasoners: bool = False

    # @override
    def think(self, update_context: Reasoner_Update_Context_Type) -> List[
        SubReasonerStruct[Reasoner_Update_Context_Type, World_Type]]:
        if (len(self.active_sub_reasoners) <= 0) and (not self.built_sub_reasoners):
            new_sub_reasoners: List[SubReasonerStruct[Reasoner_Update_Context_Type, World_Type]] = []
            for current_sub_reasoner_uid in self.sub_reasoner_uids:
                builder: ReasonerBuilder = self.id_registry.fetch(current_sub_reasoner_uid)
                new_sub_reasoners.append(SubReasonerStruct[Reasoner_Update_Context_Type, World_Type](
                    builder.build(id_registry=self.id_registry)))
            self.built_sub_reasoners = True
            return new_sub_reasoners
        else:
            return []

    # @override
    def run_children(self, active_sub_reasoners: List[SubReasonerStruct[Reasoner_Update_Context_Type, World_Type]],
                     world: World_Type, update_context: Reasoner_Update_Context_Type):
        for curChild in active_sub_reasoners:
            child_state: ReasonerState = self.run_child(curChild, world, update_context)
            if child_state is ReasonerState.Running:
                break


class SequenceReasoner(CommonConjunctionReasoner[Reasoner_Update_Context_Type, World_Type]):

    def __init__(self, uid: str,
                 id_registry: IDRegistry[ReasonerBuilder],
                 sub_reasoner_uids: List[str],
                 short_circuiting: bool = True,
                 default_finished_state: Optional[ReasonerState] = ReasonerState.Done,
                 start_conditions: List[ReasonerConsideration] = None,
                 run_conditions: List[ReasonerConsideration] = None):
        super().__init__(uid=uid, id_registry=id_registry, sub_reasoner_uids=sub_reasoner_uids,
                         start_conditions=start_conditions, run_conditions=run_conditions,
                         short_circuiting=short_circuiting, default_finished_state=default_finished_state,
                         all_semantics=True, any_semantics=False,)
        self.child_index: int = 0

    def think(self, update_context: Reasoner_Update_Context_Type) -> List[
        SubReasonerStruct[Reasoner_Update_Context_Type, World_Type]]:
        if (len(self.active_sub_reasoners) <= 0) and (self.child_index < len(self.active_sub_reasoners)):
            current_sub_reasoner_uid: str = self.sub_reasoner_uids[self.child_index]
            builder: ReasonerBuilder = self.id_registry.fetch(current_sub_reasoner_uid)
            self.child_index += 1
            return [SubReasonerStruct[Reasoner_Update_Context_Type, World_Type](
                builder.build(id_registry=self.id_registry))]
        else:
            return []


class ThreadableCommonConjunctionReasoner(CommonConjunctionReasoner[Reasoner_Update_Context_Type, World_Type]):

    def __init__(self, uid: str, id_registry: IDRegistry[ReasonerBuilder], sub_reasoner_uids: Optional[List[str]],
                 short_circuiting: bool = True,
                 multithreaded: bool = False,
                 all_semantics: bool = True,
                 any_semantics: bool = False,
                 default_finished_state: Optional[ReasonerState] = None,
                 start_conditions: List[ReasonerConsideration] = None,
                 run_conditions: List[ReasonerConsideration] = None):
        super().__init__(uid=uid,
                         id_registry=id_registry,
                         sub_reasoner_uids=sub_reasoner_uids,
                         start_conditions=start_conditions,
                         run_conditions=run_conditions,
                         short_circuiting=short_circuiting,
                         all_semantics=all_semantics,
                         any_semantics=any_semantics,
                         default_finished_state=default_finished_state, )
        self.multithreaded: bool = multithreaded
        if multithreaded:
            self.built_sub_reasoners: bool = False
        else:
            self.child_index: int = 0

    def think(self, update_context: Reasoner_Update_Context_Type) -> List[
        SubReasonerStruct[Reasoner_Update_Context_Type, World_Type]]:
        if len(self.active_sub_reasoners) <= 0:
            if self.multithreaded and (not self.built_sub_reasoners):
                new_sub_reasoners: List[SubReasonerStruct[Reasoner_Update_Context_Type, World_Type]] = []
                for current_sub_reasoner_uid in self.sub_reasoner_uids:
                    builder: ReasonerBuilder = self.id_registry.fetch(current_sub_reasoner_uid)
                    new_sub_reasoners.append(SubReasonerStruct[Reasoner_Update_Context_Type, World_Type](
                        builder.build(id_registry=self.id_registry)))
                self.built_sub_reasoners = True
                return new_sub_reasoners
            elif self.child_index < len(self.active_sub_reasoners):
                current_sub_reasoner_uid: str = self.sub_reasoner_uids[self.child_index]
                builder: ReasonerBuilder = self.id_registry.fetch(current_sub_reasoner_uid)
                self.child_index += 1
                return [SubReasonerStruct[Reasoner_Update_Context_Type, World_Type](
                    builder.build(id_registry=self.id_registry))]
            else:
                return []
        else:
            return []


class AnyReasoner(ThreadableCommonConjunctionReasoner[Reasoner_Update_Context_Type, World_Type]):
    def __init__(self, uid: str, id_registry: IDRegistry[ReasonerBuilder], sub_reasoner_uids: Optional[List[str]],
                 short_circuiting: bool = True,
                 multithreaded=False,
                 default_finished_state: Optional[ReasonerState] = ReasonerState.Done,
                 start_conditions: List[ReasonerConsideration] = None,
                 run_conditions: List[ReasonerConsideration] = None):
        super().__init__(uid=uid, id_registry=id_registry, sub_reasoner_uids=sub_reasoner_uids,
                         start_conditions=start_conditions, run_conditions=run_conditions,
                         short_circuiting=short_circuiting, multithreaded=multithreaded, all_semantics=False,
                         any_semantics=True, default_finished_state=default_finished_state)


class AllReasoner(ThreadableCommonConjunctionReasoner[Reasoner_Update_Context_Type, World_Type]):
    def __init__(self, uid: str, id_registry: IDRegistry[ReasonerBuilder], sub_reasoner_uids: Optional[List[str]],
                 short_circuiting: bool = True,
                 multithreaded=False,
                 default_finished_state: Optional[ReasonerState] = ReasonerState.Failed,
                 start_conditions: List[ReasonerConsideration] = None,
                 run_conditions: List[ReasonerConsideration] = None):
        super().__init__(uid=uid, id_registry=id_registry, sub_reasoner_uids=sub_reasoner_uids,
                         start_conditions=start_conditions, run_conditions=run_conditions,
                         short_circuiting=short_circuiting, multithreaded=multithreaded, all_semantics=True,
                         any_semantics=False, default_finished_state=default_finished_state)
