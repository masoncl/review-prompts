# Questions: Scheduler Subsystem

- guide: scheduler.md
- title: Scheduler Subsystem

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/scheduler-measurement.md` is the
wider set the readers were measured on and `catalogue/scheduler-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## sched.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## sched.file-map: Core files

- section: Finding your way
- relevance: 4 - files have been split and moved, and some are not compiled on their own

A table and nothing else, job to file: the scheduler core; each scheduling class; the system
calls; load tracking; topology; the cpufreq governor; core scheduling; the shared internal header;
and for the BPF extensible class its core, idle tracking, sub-schedulers, the operations table and
internal types, and the public task fields. Say in the row which files are not compiled on their
own, and where the tree has no file for a job or one file does several jobs. Start from
`kernel/sched/`, `kernel/sched/ext/` and `include/linux/sched/ext.h`.

# Scheduling classes

## sched.class-order: Order of the classes

- section: Scheduling classes
- relevance: 4 - priority between classes is by position

How is the order of the scheduling classes established and compared, where does the extensible
class sit relative to the fair class, and how are a policy and a priority mapped to a class?
Start from `__setscheduler_class()` and `sched_class_above()`.

## sched.class-callbacks: Class callbacks

- section: Scheduling classes
- relevance: 4 - the contract every class implements

For the callbacks of `struct sched_class` that enqueue, dequeue, pick, put and set a task, what
does each promise the core: what it is handed, what it returns and which lock is held?

## sched.enqueue-flags: Enqueue and dequeue flags

- section: Scheduling classes
- relevance: 4 - the wrong flag loses state or skips accounting

A table of the enqueue and dequeue flags to choose between: what each tells the class. Then
which must be used as matched pairs around a change, and what is lost when they are not. Start
from `ENQUEUE_WAKEUP` and `DEQUEUE_SAVE` in `kernel/sched/sched.h`.

## sched.sched-change: Changing a queued task

- section: Scheduling classes
- relevance: 5 - the pattern every attribute change goes through

What do `sched_change_begin()` and `sched_change_end()` guarantee about the task on entry and on
exit, and which locks must the caller hold? What are the requirements for code that changes a
scheduling attribute, such as the priority or the affinity, of a task that may be queued or
running, in order to assure safe usage? Start from `sched_change_begin()`.

# Task state

## sched.on-rq-states: on_rq, on_cpu and is_blocked

- section: Task state
- relevance: 5 - these fields are what wake-up and schedule race on

A table of `p->on_rq`, `p->on_cpu`, `p->is_blocked` and `p->se.sched_delayed`: what each value
means and under which lock it changes. Then which helper tells code whether a task is runnable. If
a field does not exist in this tree, say so.

## sched.donor-curr: rq->donor and rq->curr

- section: Task state
- relevance: 5 - two fields where older code had one

What is the difference between `rq->donor` and `rq->curr`, when can they differ, and which of
the two should class code use for accounting, for preemption decisions and for affinity? Start
from `rq_set_donor()` and `task_current_donor()`.

## sched.state-consistency: Consistency at unlock

- section: Task state
- relevance: 4 - other CPUs act on these fields the moment the lock drops

Which fields of a `struct task_struct` that `try_to_wake_up()` reads must agree with each other
before the runqueue lock is released, and what does a concurrent `try_to_wake_up()` do when they
do not? Name an in-tree path that releases the runqueue lock while they disagree, and say what
makes that safe.

## sched.delayed-dequeue: Delayed dequeue

- section: Task state
- relevance: 5 - a sleeping task that is still on the runqueue

When does `dequeue_task_fair()` leave a task that goes to sleep on the runqueue, and how does such
a task later leave the runqueue or become runnable again? What must code that tests `p->on_rq` or
`task_on_rq_queued()` also test? Start from `dequeue_task_fair()` and `requeue_delayed_entity()`.

## sched.proxy-exec: Proxy execution

- section: Task state
- relevance: 4 - a blocked task can stay on the runqueue

What controls whether proxy execution is on, and what may scheduler code not assume about a task
blocked on a mutex while it is on? How does `find_proxy_task()` get from a picked task that is
blocked to the task that runs, when the mutex owner is on this CPU and when it is on another? If
this tree has no proxy execution, say so and stop. Start from `find_proxy_task()`.

# Locks, affinity and migration

## sched.rq-lock: Runqueue lock

- section: Locks, affinity and migration
- relevance: 5 - every scheduler path takes it

What kind of lock protects a runqueue, and through which wrappers is it taken and asserted? Which
lock does `__rq_lockp()` return, and when is that not the lock embedded in the `struct rq`? Start
from `raw_spin_rq_lock_nested()` and `__rq_lockp()`.

## sched.lock-order: Lock order

- section: Locks, affinity and migration
- relevance: 5 - deadlocks that lockdep only catches when the path runs

In what order are a task's `pi_lock`, a runqueue lock and a second runqueue lock taken, and which
other locks does the scheduler take inside a runqueue lock? How does `rq_order_less()` order two
runqueues? Start from the "Serialization rules" comment above `raw_spin_rq_lock_nested()` in
`kernel/sched/core.c` and `rq_order_less()`.

## sched.task-rq-lock: Locking a task's runqueue

- section: Locks, affinity and migration
- relevance: 5 - the task can move between reading its CPU and taking the lock

What are the requirements for code that calls `task_rq()` or `task_cpu()` in order to assure safe
usage? How do `task_rq_lock()` and `__task_rq_lock()` make sure they hold the right runqueue, and
which task fields does `p->pi_lock` keep stable and which the runqueue lock?

## sched.set-task-cpu: Moving a task between CPUs

- section: Locks, affinity and migration
- relevance: 4 - wrong state or lock corrupts two runqueues

What are the requirements for a call of `set_task_cpu()` in order to assure safe usage: in which
task states and under which locks may it be called? What does `set_task_cpu()` itself check? Start
from the "Serialization rules" comment above `raw_spin_rq_lock_nested()` in `kernel/sched/core.c`
and `move_queued_task()`.

## sched.affinity-api: Changing affinity

- section: Locks, affinity and migration
- relevance: 4 - several masks and several callers

What do a task's `cpus_ptr`, `cpus_mask` and `user_cpus_ptr` each hold, and which must code read
for which purpose? What can make `__set_cpus_allowed_ptr()` fail or wait? Start from
`__set_cpus_allowed_ptr()`.

## sched.migrate-disable: Migration disable

- section: Locks, affinity and migration
- relevance: 4 - what it guarantees is often overstated

What does `migrate_disable()` guarantee to its caller, and may the caller be preempted or sleep
before `migrate_enable()`? What does `affine_move_task()` do for a task that is migration
disabled? Start from `migrate_disable_switch()` and `affine_move_task()`.

## sched.migrate-disable-switch: CPU mask under migration disable

- section: Locks, affinity and migration
- relevance: 4 - code that reads the mask of a migration disabled task has to know what the mask holds

What does `migrate_disable_switch()` change for a task that is migration disabled, and at what
point is it called? Start from `migrate_disable_switch()`.

# Blocking and waking

## sched.schedule-steps: The schedule path

- section: Blocking and waking
- relevance: 4 - where a change to the core lands

Which steps of `__schedule()` between taking the runqueue lock and picking the next task rely on
an earlier step having run? What does each `SM_` mode passed to `__schedule()` change, and up to
which point can a signal or a wake-up still cancel the sleep? Start from `__schedule()` and
`try_to_block_task()`.

## sched.ttwu-paths: Wake-up paths

- section: Blocking and waking
- relevance: 4 - the most intricate lockless code in the core

Which paths can `try_to_wake_up()` take depending on whether the task is still queued, still
running on a CPU, or fully blocked, which locks does each take, and when is the enqueue handed
to another CPU? Start from `ttwu_runnable()` and `ttwu_queue_wakelist()`.

## sched.sleep-pattern: Sleep and wake ordering

- section: Blocking and waking
- relevance: 4 - a lost wake-up hangs a task for good

What are the requirements for the order in which a sleeper sets the task state, tests its
condition and calls `schedule()`, in order to assure safe usage? Which barrier does
`set_current_state()` supply and what does the waker pair it with, and when is
`__set_current_state()` enough?

# Fair class

## sched.fair-queueing: Fair task queueing

- section: Fair class
- relevance: 5 - the shape of the hierarchy decides what every helper walks

With `CONFIG_FAIR_GROUP_SCHED` enabled, on which `struct cfs_rq` does `enqueue_task_fair()` put a
task's entity, and from which `struct cfs_rq` does `pick_task_fair()` pick? How is a task's weight
across the levels of the group hierarchy arrived at? Start from `enqueue_task_fair()` and
`pick_task_fair()`.

## sched.group-entities: Group entities and runqueues

- section: Fair class
- relevance: 5 - a helper that walks the group hierarchy has to know what each level holds

With `CONFIG_FAIR_GROUP_SCHED` enabled, what is the `struct sched_entity` of a task group used
for, and what does the `struct cfs_rq` of a task group hold? Start from `enqueue_task_fair()`.

## sched.cfs-rq-counters: cfs_rq task counters

- section: Fair class
- relevance: 4 - renamed, and they count different things

What does each counter of tasks or entities in `struct cfs_rq` count, and which must code test for
which purpose? Which of them does the core compare against `rq->nr_running`?

## sched.entity-fields: Entity fields

- section: Fair class
- relevance: 4 - the vocabulary of every fair class patch

Do the fields of `struct sched_entity` that hold an entity's lag and its slice protection share
storage? What does the augmented rbtree of a `struct cfs_rq` carry in each node, and how is lag
clamped?

## sched.virtual-time: Virtual time of a runqueue

- section: Fair class
- relevance: 4 - the fields behind it have changed more than once

From which fields of `struct cfs_rq` does `avg_vruntime()` compute a fair runqueue's virtual time?
Relative to which value does `entity_key()` take an entity's key, and when does that value move?
Start from `avg_vruntime()` and `entity_key()`.

## sched.eevdf-pick: Picking an entity

- section: Fair class
- relevance: 4 - eligibility and the exceptions to it

How is the next fair entity chosen: what makes an entity eligible, what orders the eligible
ones, and in which cases is the current entity or a buddy returned without a search? Name the
functions. Start from `pick_task_fair()` and `entity_eligible()`.

## sched.pelt-signals: Load tracking signals

- section: Fair class
- relevance: 4 - stale averages misdirect balancing and frequency

What are the requirements for a call of `update_load_avg()` by code that changes which entities a
`struct cfs_rq` holds or what they weigh, in order to assure safe usage? On which clock do the
load tracking averages advance?

## sched.cfs-bandwidth: Bandwidth throttling

- section: Fair class
- relevance: 4 - where throttled tasks wait has moved

When a group runs out of CFS bandwidth quota, at what point does each of its tasks stop running,
and where is a task kept until `tg_unthrottle_up()` puts it back? What does the fair class do when
a throttled task is enqueued or dequeued before its group is unthrottled? Start from
`throttle_cfs_rq()`, `throttle_cfs_rq_work()` and `tg_unthrottle_up()`.

## sched.cache-aware: Cache aware scheduling

- section: Fair class
- relevance: 2 - a new configuration option

What does `CONFIG_SCHED_CACHE` change about where tasks are placed, and which placement paths
does it leave alone? If the option does not exist in this tree, say so and stop.

# Realtime, deadline and servers

## sched.rt-limits: Realtime bandwidth limits

- section: Realtime, deadline and servers
- relevance: 5 - the default and the mechanism are both misremembered

What stops realtime tasks from monopolising a CPU: what are the defaults of the realtime period
and runtime sysctls, under which configuration is the realtime throttling code built, and what
protects lower classes when it is not? Start from `sysctl_sched_rt_runtime` and
`sched_rt_runtime_exceeded()`.

## sched.dl-servers: Deadline servers

- section: Realtime, deadline and servers
- relevance: 5 - this is what keeps lower classes from starving

Which deadline servers does each runqueue have, and when is a server started and when is it
stopped? What does `dl_defer` of a `struct sched_dl_entity` change? Start from
`dl_server_start()`, `sched_init_dl_servers()` and `pick_task_dl()`.

## sched.dl-admission: Deadline parameters and admission

- section: Realtime, deadline and servers
- relevance: 4 - the invariant and the test behind it

Which constraints does `__checkparam_dl()` put on a deadline task's runtime, deadline and period?
Against what capacity does `sched_dl_overflow()` test a task, and under which lock? Start from
`__checkparam_dl()` and `sched_dl_overflow()`.

## sched.dl-bandwidth-users: Deadline bandwidth accounting

- section: Realtime, deadline and servers
- relevance: 4 - bandwidth that the admission test does not count can be given out twice

What does the total that `sched_dl_overflow()` tests against hold besides the bandwidth of
deadline tasks? Start from `sched_dl_overflow()`.

# Extensible class

## sched.scx-exit: Errors, watchdog and bypass

- section: Extensible class
- relevance: 4 - how a broken BPF scheduler is thrown out

Which events make the kernel disable a loaded BPF scheduler? What does `scx_bypass()` change about
where tasks are queued and picked, and in which class are tasks after the BPF scheduler is
disabled? Start from `scx_error()`, `scx_watchdog_workfn()` and `scx_bypass()`.

## sched.scx-sub-cid: Sub-schedulers and cids

- section: Extensible class
- relevance: 3 - new structure a reader will not recognise

How does a sub-scheduler relate to a cgroup and to the root BPF scheduler? How does a cid differ
from a CPU number? What enables each of the two? If this tree has neither, say so and stop. Start
from `kernel/sched/ext/sub.c` and `kernel/sched/ext/cid.c`.

## sched.scx-kfunc-contexts: Kfunc calling contexts

- section: Extensible class
- relevance: 3 - the mechanism has been replaced

How does the extensible class restrict which of its kfuncs may be called from which operation:
is it checked when the program is loaded, when it runs, or both, and where is the table? Start
from `scx_kfunc_context_filter()` and `scx_kf_allow_flags`.

## sched.scx-ops-state: Task ownership in ops_state

- section: Extensible class
- relevance: 4 - the handshake between the core and the BPF scheduler

A table of the values of a task's `scx.ops_state`: who owns the task in each. Then which
transitions need release and acquire ordering, and what the dequeue path does when it finds a
task in the middle of one. Start from the comment above `SCX_OPSS_NONE`.

# CPU hotplug

## sched.hotplug-steps: Hotplug callbacks

- section: CPU hotplug
- relevance: 4 - each step relies on what the previous one did

In what order do the scheduler's CPU hotplug callbacks run when a CPU goes down and when it
comes up, what does each rely on the previous one having done, and what happens when one fails
part way? Start from `sched_cpu_deactivate()`, `sched_cpu_wait_empty()`, `sched_cpu_dying()`
and `sched_cpu_activate()`.

## sched.hotplug-timers: Per-CPU timers across hotplug

- section: CPU hotplug
- relevance: 3 - a timer armed on a CPU that is gone

In which hotplug callback does the scheduler stop each of its per-CPU timers and deadline servers
when a CPU goes down? What keeps `dl_server_start()` from starting a server on a CPU that is
already offline? What are the requirements for code that arms one of these timers in order to
assure safe usage?

# Model gaps

## sched.model-gaps: Other mistakes models make

- drafts: all
- relevance: 5 - a model that is told how it is wrong can correct for it

Going by what each reader said from memory for every question in this guide, which is given
below, what do models believe about this code that is wrong in this tree? One bullet per mistake:
the belief, put plainly as a model would hold it, then what is true here and where to see it.
Cover names that are gone and what does the job now, numbers and limits that have changed,
behaviour that has changed, rules the readers state more broadly than the code supports, and what
is new that none of them knew. Most consequential first: a belief that would make a reviewer
approve a bug or reject correct code comes before a file that moved. Leave out what the readers
had right, and a slip only one of them made that the others show is not a belief. One or two lines to
a bullet: the belief and the truth. Every section of this guide already corrects what models
get wrong about its subject, and what a section covers is taken out of this list afterwards, so what
matters most here is what no question above asks about.
