# General planner system
## concepts  
Planner
Executor - takes the plan after it been converted into a Reasoner graph and executes it.
Task- a goal that a plan can satisfy. Either Inmutable once created and is wrapped in a satisfaction wrapper or copied on write.
External task- a leaf task that needs not be decomposed any further because either corresponds to a pre-built reasoner graph or is handled by a different planner
Decomposer - something that decomposes tasks into subtasks
null Decomposer- “decomposes” a task in to 0 subtasks. Used to gracefully remove already accomplished tasks from plans. Can still place constraints on the plan.
Plan - a possible plan of action aka an acrylic graph of tasks plus constrains any continuation needs to satisfy. Can have child plans as options.
Partial plan - a plan that intentionally leaves uncertain required variables until later even at the risk of invalidating parts of the plan
Constrains - constrains that planner need to comply with or things that need to be true for the plan to be valid. Maybe a subclass of Planner Consideration  or Consideration
Options - mutually exclusive plans that need to be selected between
Consideration - 
Planner Consideration -
Reasoner Consideration -
Active Reasoner Consideration - a consideration that has to remain true for the current Reasoner stack to remain valid, if it fails execution returns to the reasoner that owns this Consideration
Picker - selects between things
Priority/Motivation Propagator - specify how priority/motivation travels down from supertasks to subtasks
Reasoner - the runtime counterpart to a Decomposer oversees the execution of the a small part of the plan
Weight functions -
Priority - how important the task is
Motivation - how much the agent wants to do the task

## Standard tasks
“Win the game” - possible root task. Decomposers for this task represent different ways of winning.

## Example Consideration
only once - makes sure this sub tree is run only once by putting its guid on the blackboard in the execution context
## Types of planners
All plans all the time - what I used in my mudai
Select a single Decomposer for each task - traditional HTN planning
Each Decomposer need not fully satisfy a task instead it can partially plan for a task (and lower the priority/motivation)
Create all possible plans and then select the best one
### Pre planning
Level 1: Generate all plans that don’t depend on world state
Level 2: generate all plans that only depend on world state changes (change in seasons, days of the week, yearly changes, etc.) that are sure to happen and preload them as their constraints are satisfied.
Level 3: generate plans based on last seen world state
Modifier a: store plans that are only invalid because of a state change (change in seasons, days of the week, yearly changes, etc.) that is going reverse eventually 
Modifier b: Expand level 1 and 2 plans based on any permanent state changes (new game features unlocked, etc.). Update currently inactive plans based on any permanent state changes.
### How to select which plan to expand next
Lowest possible cost
*Lowest estimated cost (this should be the best because it corresponds to how AStar works)
Lowest unsatisfied priority/motivation
Remove duplicates (i.e check if the next plan equals previous selected plan but isn’t actually the same plan and if so mark it as finished and skip it (under some selection criteria you should only need to check the last few plans or even just the last one))
### How to select which planner to apply next to a plan
Select all applicable Decomposers. The results of each Decomposer is an option.
Select the Decomposer that hasn’t already been used on this plan that plans for the most total priority/motivation of tasks on the task list.
Gather Decomposer that can plan for tasks on the task list then select the planner that hasn’t already been used on this plan that plans for the most total priority/motivation of unsatisfied for tasks in the plan
Narrow the task list to possible first tasks then use another method to select a Decomposer or Decomposers to use. Mark plan as finished if there are no applicable Decomposer
Narrow the task list to unsatisfied tasks tied for the highest priority/motivation then use another method to select a Decomposer or Decomposers to use. Select next highest if there are no applicable Decomposers. Unsatisfied Tasks with higher priority/motivation are considered for methods that look at more than one task.
Apply any applicable null Decomposers
## Ways to avoid circular planning
Tasks record what Decomposers led to them and those Decomposers are deprioritized for that task
Assign tasks abstraction levels and enforce they can only be decomposed to tasks at abstraction levels strictly lower than themselves
Assign Decomposers abstraction levels which is passed to any subtasks and only Decomposers of lower abstraction levels can decompose those tasks
Tasks have a time to live and aren’t planned for if their time to live is 0 or less
Decomposes must add at least a small minimum cost to the plan
### Deprioritizetion formula
A is some constant greater than 0
B is a constant between 0 and 1
N is the max times the Decomposer has been used so far planing for any task the Decomposer is satisfying.

By a A/(A+N) factor
By 1 minus the hyperbolic tan function of N (1-tanh(N))
By a (A - N)/A factor for values of N below A then 0 otherwise
By a B^N factor
## Selecting a plan to execute
Select plan with lowest Possible cost
Select plan with lowest estimated cost
Select plan with lowest concrete cost 
Select plan with lowest concrete cost by next planning time
Select plan with max concrete satisfied priority/motivation divided by concrete cost
Select plan with max concrete satisfied priority/motivation divided by concrete cost by next planning time
Filter for plans with at least N actions or no unsatisfied tasks
Filter out plans that don’t have enough concrete actions to reach the next planning period
Filter out invalid plans

## When to switch plans to execute
At natural breaks (example: in game days)
After a certain period of time
After a certain number of terminal task succeed or fail
After a certain number of task succeed or fail
If the plan becomes invalid
Select a set of root tasks and replan after they all succeed or fail
## Resume planning
Remove tasks that actually got done from all plans , add any new tasks to all plans and update the priority/motivation of existing tasks then resume planning 

## Structure of the base reasoner
### Think method
Outputs a list of Active Reasoner Considerations and a sub Reasoner
### Update method 
Call own sense method
Checks the currently Active Reasoner Considerations 
If any fail call the exit method of the currently active sub Reasoner and call own handle Active Reasoner Consideration failure
if they succeed call the update method of the currently active sub Reasoner if the sub Reasoner is done or fails clear the Active Reasoner Considerations and sub Reasoner
If the sub reasoner failed call own handle child failure method
if not in fail state and didn’t call a sub Reasoner call own think method if it yields Active Reasoner Considerations and sub Reasoner assign them to the instance variables
If in finished or fail state return the current state of this Reasoner
If  sub reasoner is null Call own act method 
If in finished or fail state call own exit method and return the current state of this Reasoner
At the end of each loop yield the current state of this Reasoner
## Implementation notes
A Reasoner should be able pass a map<string, object> copy on write map for transinit data.

#Steamer