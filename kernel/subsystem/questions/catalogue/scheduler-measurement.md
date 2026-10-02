# Questions: Scheduler (measurement set)

- guide: scheduler.md
- title: Scheduler Subsystem

A wide set of questions about the scheduler core and its classes, used to
measure what a model already knows before deciding what the built guide should
spend its words on. The hand-written guide it will replace is 1,392 words and
was never checked against current sources. Load balancing heuristics, NUMA
balancing, PSI and cputime accounting are touched only as places to look.
Format: `../../../docs/subsystem-questions.md`.

# The subsystem

## sched.core-files: Core files

- section: Finding your way
- relevance: 4 - files have been split and moved, and some are not compiled on their own
- words: 120

Which files hold the scheduler core, each scheduling class, the system calls,
load tracking, topology, the cpufreq governor, core scheduling, the BPF
extensible class, and the shared internal header? A table. Start from
`kernel/sched/`.

## sched.build-units: Compilation units

- section: Finding your way
- relevance: 3 - decides what a static function can see
- words: 70

Into how many objects are the files under `kernel/sched/` compiled, which
files are included into another C file instead of being built on their own,
and what follows for a new static helper or a new header? Start from
`kernel/sched/Makefile` and `kernel/sched/build_policy.c`.

## sched.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 110

For each job (pick the next task, wake a task, block a task, fork, exit, the
tick, change policy or priority, change nice, change affinity, move a task to
another group), which function do you start reading from? A table.

## sched.docs-tests: Documentation and tests

- section: Finding your way
- relevance: 2 - where the written rules and the tests are
- words: 70

Which files under `Documentation/scheduler/` are worth reading before changing
the fair class, the deadline class and the BPF extensible class, and which
selftests and example programs in `tools/` exercise the scheduler?

## sched.class-order: Scheduling classes

- section: Finding your way
- relevance: 4 - priority between classes is by position
- words: 80

List the scheduling classes from highest to lowest priority, say how their
order is established and compared, and how a policy and priority are mapped to
a class. Start from `__setscheduler_class()` and `sched_class_above()`.

## sched.class-callbacks: Class callbacks

- section: Finding your way
- relevance: 4 - the contract every class implements
- words: 140

Which callbacks does `struct sched_class` have in this tree, and for the ones
that enqueue, dequeue, pick, put and set a task, what are the arguments, the
return value and the lock held? Say which callbacks a reader of an older
kernel would look for and not find. A table.

# Runqueues and locking

## sched.rq-lock: Runqueue lock

- section: Locks
- relevance: 5 - every scheduler path takes it
- words: 90

What kind of lock protects a runqueue, through which wrappers is it taken and
asserted, and why is the lock behind a runqueue not always the one embedded in
it? Start from `raw_spin_rq_lock_nested()` and `__rq_lockp()`.

## sched.lock-order: Lock order

- section: Locks
- relevance: 5 - deadlocks that lockdep only catches when the path runs
- words: 90

In what order are a task's `pi_lock`, a runqueue lock, a second runqueue lock,
and the timer and mutex locks the scheduler touches taken? How are two
runqueues ordered? Start from the "Serialization rules" comment in
`kernel/sched/core.c` and `rq_order_less()`.

## sched.task-rq-lock: Locking a task's runqueue

- section: Locks
- relevance: 5 - the task can move between reading its CPU and taking the lock
- words: 100

What usage of `task_rq()` or `task_cpu()` is unsafe, and what that looks
similar is correct? How do `task_rq_lock()` and `__task_rq_lock()` make sure
they hold the right runqueue, and which of the two locks keeps which task
fields stable?

## sched.lock-guards: Guards and lock annotations

- section: Locks
- relevance: 3 - new code is written with these and old names are wrappers
- words: 80

Which scoped guards exist for the runqueue lock, for two runqueues and for a
task's runqueue, and which annotations on scheduler functions does the compiler
check? Start from `DEFINE_LOCK_GUARD_1` in `kernel/sched/sched.h` and
`CONTEXT_ANALYSIS` in `kernel/sched/Makefile`.

## sched.rq-pin-clock: Pinning and the runqueue clock

- section: Locks
- relevance: 3 - the warnings people hit when moving code
- words: 90

What does pinning the runqueue lock with `struct rq_flags` protect against,
when must the lock be unpinned, and what are the rules for updating and reading
the runqueue clock that the `clock_update_flags` checks enforce? Start from
`rq_pin_lock()` and `update_rq_clock()`.

## sched.balance-callbacks: Balance callbacks

- section: Locks
- relevance: 3 - work queued under the lock and run as it is dropped
- words: 80

What are balance callbacks for, who queues them and when are they run, and what
must be true of them whenever the runqueue lock is released in the middle of
picking a task? Start from `queue_balance_callback()` and
`__balance_callbacks()`.

## sched.on-rq-states: Task queue state

- section: Task state
- relevance: 5 - these fields are what wake-up and schedule race on
- words: 120

What values do `p->on_rq`, `p->on_cpu`, `p->is_blocked` and
`p->se.sched_delayed` take, who sets each and under which lock, and which
helper should code use to ask whether a task is really runnable? A table. If a
field does not exist in this tree, say so.

## sched.state-consistency: Consistency at unlock

- section: Task state
- relevance: 4 - other CPUs act on these fields the moment the lock drops
- words: 90

Which pieces of a task's state must agree with each other before the runqueue
lock is released, and what does a concurrent wake-up do when they do not? Name
an in-tree path that is deliberately in between (queued but not runnable, or
runnable but marked as migrating) and say why that is safe.

## sched.sched-change: Changing a queued task

- section: Task state
- relevance: 5 - the pattern every attribute change goes through
- words: 110

How does this tree change the priority, class, affinity, group or weight of a
task that may be queued or running: which helper brackets the change, what does
it do on entry and exit, which class callbacks does it call, and which locks
must be held? Start from `sched_change_begin()`.

## sched.enqueue-flags: Enqueue and dequeue flags

- section: Task state
- relevance: 4 - the wrong flag loses state or skips accounting
- words: 120

Give a table of the enqueue and dequeue flags this tree defines and what each
tells the class, and say which must be used as matched pairs. Write each flag
name in full. Start from `ENQUEUE_WAKEUP` and `DEQUEUE_SAVE` in
`kernel/sched/sched.h`.

## sched.donor-curr: Scheduling and execution context

- section: Task state
- relevance: 5 - two fields where older code had one
- words: 90

What is the difference between `rq->donor` and `rq->curr`, when can they
differ, and which of the two should class code use for accounting, for
preemption decisions and for affinity? Start from `rq_set_donor()` and
`task_current_donor()`.

# Sleeping and waking

## sched.sleep-pattern: Sleep and wake ordering

- section: Blocking and waking
- relevance: 4 - a lost wake-up hangs a task for good
- words: 90

What ordering of setting the task state, testing the condition and calling
`schedule()` is unsafe, and what that looks similar is correct? Which barrier
does `set_current_state()` supply and what does the waker pair it with, and
when is `__set_current_state()` enough?

## sched.schedule-steps: The schedule path

- section: Blocking and waking
- relevance: 4 - where a change to the core lands
- words: 120

List in order the main steps of `__schedule()` from disabling interrupts to the
context switch, including how a task that is going to sleep is taken off the
runqueue and what the scheduling modes passed in mean. Start from
`__schedule()` and `try_to_block_task()`.

## sched.ttwu-paths: Wake-up paths

- section: Blocking and waking
- relevance: 4 - the most intricate lockless code in the core
- words: 120

Which paths can `try_to_wake_up()` take depending on whether the task is still
queued, still running on a CPU, or fully blocked, which locks does each take,
and when is the enqueue handed to another CPU? Start from `ttwu_runnable()` and
`ttwu_queue_wakelist()`.

## sched.special-states: Special task states

- section: Blocking and waking
- relevance: 3 - states that must not see a spurious wake-up
- words: 80

Which task states have to be set with `set_special_state()` and why, how does
the core treat them differently when the task blocks, and how is a dead task's
last reference dropped? Start from `is_special_task_state()` and
`do_task_dead()`.

## sched.wake-helpers: Wake-up helpers

- section: Blocking and waking
- relevance: 3 - what callers outside the scheduler use
- words: 80

Which states do `wake_up_process()` and `wake_up_state()` wake, what do they
return, may they be called on a task in any state, and what does a caller need
to hold to keep the task from going away? What is `wake_q_add()` for?

## sched.proxy-exec: Proxy execution

- section: Blocking and waking
- relevance: 4 - a blocked task can stay on the runqueue
- words: 120

What is proxy execution, which configuration option and boot parameter control
it, which `task_struct` fields and locks does it add, and how does
`__schedule()` get from a picked task that is blocked on a mutex to the task it
runs? If this tree has no proxy execution, say so and stop. Start from
`find_proxy_task()`.

## sched.preempt-modes: Preemption models

- section: Blocking and waking
- relevance: 3 - decides when a resched request takes effect
- words: 90

Which preemption models can this tree be built or booted with, what is lazy
preemption, and which classes or paths request a lazy reschedule rather than an
immediate one? Start from `resched_curr_lazy()` and `preempt_model_str()`.

## sched.schedule-context: Calling schedule

- section: Blocking and waking
- relevance: 2 - checked at run time
- words: 60

What must not be held or disabled when `schedule()` is called, what checks does
the core make on entry, and which variants exist for callers that have
preemption disabled or that are idle? Start from `schedule_debug()`.

# Affinity and migration

## sched.affinity-api: Changing affinity

- section: Affinity and migration
- relevance: 4 - several masks and several callers
- words: 110

Which functions change a task's allowed CPUs, what do `cpus_ptr`, `cpus_mask`
and `user_cpus_ptr` each hold, what do the flags in `struct affinity_context`
mean, and which checks can make the change fail? Start from
`__set_cpus_allowed_ptr()`.

## sched.migrate-disable: Migration disable

- section: Affinity and migration
- relevance: 4 - what it guarantees is often overstated
- words: 100

What does `migrate_disable()` guarantee and what does it not (preemption,
sleeping), at what point is the task's CPU mask actually narrowed, and what
does a concurrent affinity change do while a task is migration disabled? Start
from `migrate_disable_switch()` and `affine_move_task()`.

## sched.set-task-cpu: Moving a task between CPUs

- section: Affinity and migration
- relevance: 4 - wrong state or lock corrupts two runqueues
- words: 100

What usage of `set_task_cpu()` is unsafe, and what that looks similar is
correct? In which task states and under which locks may it be called, and what
does the core check? Start from the rules in the "Serialization rules" comment
and `move_queued_task()`.

## sched.percpu-kthreads: Per-CPU kernel threads

- section: Affinity and migration
- relevance: 3 - bound threads are treated specially by hotplug and affinity
- words: 80

When may `kthread_bind()` be called, what marks a kernel thread as per-CPU and
what does that let it do that an ordinary task pinned to one CPU cannot, and
which CPUs does `is_cpu_allowed()` accept for each?

## sched.stopper-migration: Stopper based migration

- section: Affinity and migration
- relevance: 2 - only for a task that is running or migration disabled
- words: 70

When does moving a task need the CPU stopper rather than a plain dequeue and
enqueue, and which stopper callbacks does the scheduler have? Start from
`migration_cpu_stop()` and `push_cpu_stop()`.

# The fair class

## sched.fair-queueing: Fair task queueing

- section: Fair class structure
- relevance: 5 - the shape of the hierarchy decides what every helper walks
- words: 120

With fair group scheduling enabled, in which rbtree does a runnable task's
entity sit and from which is the next task picked, what do group entities and
per-group runqueues still hold, and how is a task's weight across the levels of
the hierarchy arrived at? Start from `enqueue_task_fair()` and
`pick_task_fair()`.

## sched.cfs-rq-counters: Runqueue counters

- section: Fair class structure
- relevance: 4 - renamed, and they count different things
- words: 80

Which counters of tasks and entities does `struct cfs_rq` keep, what does each
count (own level or whole hierarchy, runnable or merely queued, idle policy),
and which does the core compare against `rq->nr_running`?

## sched.entity-fields: Entity fields

- section: Fair class structure
- relevance: 4 - the vocabulary of every fair class patch
- words: 140

Give a table of the fields of `struct sched_entity` that the fair class's
picking and placement use (virtual runtime, deadline, lag, slice, protection,
the tree augmentation, the one-bit flags, the weights) with what each means.
Say whether any of them share storage.

## sched.virtual-time: Virtual time of a runqueue

- section: EEVDF
- relevance: 4 - the fields behind it have changed more than once
- words: 100

How does a fair runqueue track its virtual time: which fields hold the weighted
sum, which function returns the average, what is the reference point the
entity keys are taken from and when does it move? Start from `avg_vruntime()`
and `entity_key()`.

## sched.eevdf-pick: Picking an entity

- section: EEVDF
- relevance: 4 - eligibility and the exceptions to it
- words: 110

How is the next fair entity chosen: what makes an entity eligible, what orders
the eligible ones, and in which cases is the current entity or a buddy returned
without a search? Name the functions. Start from `pick_task_fair()` and
`entity_eligible()`.

## sched.rb-augment: The augmented tree

- section: EEVDF
- relevance: 3 - the invariant behind the O(log n) pick
- words: 70

What is the fair class's rbtree sorted by, which per-subtree values is it
augmented with, and what is each of them used for? Start from
`__enqueue_entity()`.

## sched.slice-deadline: Slices and deadlines

- section: EEVDF
- relevance: 3 - numbers and formulas quoted from memory
- words: 90

How is an entity's virtual deadline computed and when is it recomputed, what is
the default base slice and how does it scale with CPU count, and how does a
task get a slice of its own? Start from `update_deadline()` and
`sysctl_sched_base_slice`.

## sched.slice-protection: Slice protection

- section: EEVDF
- relevance: 3 - decides whether a wake-up preempts
- words: 80

What protects a running entity from being preempted before it has had a minimum
run, which field records it, which features change how long it lasts, and what
cancels it? Start from `set_protect_slice()`.

## sched.lag-placement: Lag and placement

- section: EEVDF
- relevance: 3 - arithmetic that is easy to unbalance
- words: 100

How is an entity's lag computed when it leaves the runqueue and used when it
comes back, why is it scaled on placement, and what is a relative deadline?
Start from `update_entity_lag()` and `place_entity()`.

## sched.delayed-dequeue: Delayed dequeue

- section: EEVDF
- relevance: 5 - a sleeping task that is still on the runqueue
- words: 120

When does a task that goes to sleep stay on the fair runqueue, which flag and
counters record it, how is it later requeued or finally removed, which task
states are exempt, and what must code that tests `p->on_rq` or
`task_on_rq_queued()` also test? Start from `dequeue_task_fair()` and
`requeue_delayed_entity()`.

## sched.wakeup-preempt: Wake-up preemption

- section: EEVDF
- relevance: 3 - heuristics that change often
- words: 90

How does the core decide which class's preemption check to run when a task
wakes, and within the fair class what makes the woken task preempt the running
one? Start from `wakeup_preempt()` and `wakeup_preempt_fair()`.

## sched.reweight: Reweighting

- section: EEVDF
- relevance: 3 - lag and deadline must be rescaled together
- words: 90

What has to happen to an entity's virtual runtime, deadline and lag when its
weight changes, which functions do it for a nice change and for a group share
change, and how are group shares calculated? Start from `reweight_entity()` and
`update_cfs_group()`.

## sched.pelt-signals: Load tracking signals

- section: Load tracking and bandwidth
- relevance: 4 - stale averages misdirect balancing and frequency
- words: 100

Which averages does per-entity load tracking keep and for what (entities, fair
runqueues, the other classes, interrupts), which clock do they advance on, and
where must `update_load_avg()` be called relative to an enqueue, dequeue or
weight change? What do its flags mean?

## sched.pelt-migration: Load tracking across migration

- section: Load tracking and bandwidth
- relevance: 3 - the old runqueue's lock is not held
- words: 80

How is a task's load removed from the runqueue it leaves and added to the one
it joins when it migrates, which of those happens without the old runqueue's
lock, and what marks an entity as not yet attached? Start from
`migrate_task_rq_fair()` and `attach_entity_load_avg()`.

## sched.cfs-bandwidth: Bandwidth throttling

- section: Load tracking and bandwidth
- relevance: 4 - where throttled tasks wait has moved
- words: 120

When a group runs out of CFS bandwidth quota, at what point are its tasks
actually stopped, where do they wait, what happens to one that is woken,
migrated or has its class changed meanwhile, and how are they put back? Start
from `throttle_cfs_rq()`, `throttle_cfs_rq_work()` and `tg_unthrottle_up()`.

## sched.util-clamp: Utilization estimates and clamps

- section: Load tracking and bandwidth
- relevance: 2 - feeds frequency selection
- words: 70

What are the estimated utilization and the utilization clamps, where are they
updated on enqueue and dequeue, and how do they reach the cpufreq governor?
Start from `util_est_enqueue()`, `uclamp_rq_inc()` and `cpufreq_update_util()`.

## sched.load-balance: Load balancing entry points

- section: Balancing
- relevance: 3 - names were changed wholesale
- words: 100

Which functions are the entry points for periodic, new-idle and nohz idle load
balancing, which function decides whether one task may be pulled, and how are
tasks detached and attached? Start from `sched_balance_rq()` and
`can_migrate_task()`.

## sched.select-cpu: Wake-up CPU selection

- section: Balancing
- relevance: 2 - where placement heuristics live
- words: 80

Which paths does the fair class's CPU selection take for a wake-up, a fork and
an exec, when is the energy-aware path used, and where is an idle sibling
searched for? Start from `select_task_rq_fair()`.

## sched.cache-aware: Cache aware scheduling

- section: Balancing
- relevance: 2 - a new configuration option
- words: 70

What does `CONFIG_SCHED_CACHE` add: what is tracked per process and per
runqueue, and where does it influence balancing and wake-up placement? If the
option does not exist in this tree, say so and stop.

## sched.topology: Domains and root domains

- section: Balancing
- relevance: 3 - RCU protected and rebuilt on hotplug and cpuset changes
- words: 90

What are a scheduling domain, a scheduling group and a root domain, what does a
root domain hold for the realtime and deadline classes, and how are they
rebuilt and freed? Start from `build_sched_domains()` and
`struct root_domain`.

# Realtime and deadline classes

## sched.priorities: Priority numbering

- section: Realtime class
- relevance: 3 - inverted scales are easy to mix up
- words: 90

How do a user-visible realtime priority, a nice value and a deadline task map
to the kernel's `prio`, what do `prio`, `normal_prio`, `static_prio` and
`rt_priority` each hold, and which way does each scale run? Start from
`__normal_prio()` and `MAX_RT_PRIO`.

## sched.rt-limits: Realtime bandwidth limits

- section: Realtime class
- relevance: 5 - the default and the mechanism are both misremembered
- words: 100

What stops realtime tasks from monopolising a CPU: what are the defaults of the
realtime period and runtime sysctls, under which configuration is the realtime
throttling code built, and what protects lower classes when it is not? Start
from `sysctl_sched_rt_runtime` and `sched_rt_runtime_exceeded()`.

## sched.rt-push-pull: Realtime push and pull

- section: Realtime class
- relevance: 3 - how realtime tasks spread across CPUs
- words: 80

When does the realtime class push a task to another CPU or pull one in, what
marks a runqueue as overloaded, and how is a target CPU found? Start from
`push_rt_task()`, `pull_rt_task()` and `cpupri_find()`.

## sched.dl-admission: Deadline parameters and admission

- section: Deadline class
- relevance: 4 - the invariant and the test behind it
- words: 100

Which constraints must a deadline task's runtime, deadline and period satisfy,
what is the admission test, over which set of CPUs and with which lock is it
made, and what else consumes that bandwidth? Start from `__checkparam_dl()` and
`sched_dl_overflow()`.

## sched.dl-runtime: Runtime enforcement

- section: Deadline class
- relevance: 3 - timers and flags with subtle interplay
- words: 100

How is a deadline entity's runtime consumed, what happens when it runs out and
when is it replenished, which two timers does an entity have and what is each
for, and what is bandwidth reclaiming? Start from `update_curr_dl_se()` and
`dl_task_timer()`.

## sched.dl-servers: Deadline servers

- section: Deadline class
- relevance: 5 - this is what keeps lower classes from starving
- words: 130

What is a deadline server, which servers does each runqueue have and with what
default runtime and period, when is one started and stopped, what does
deferring it mean, and how does a server hand back a task to run? Start from
`dl_server_start()`, `sched_init_dl_servers()` and `pick_task_dl()`.

## sched.pi-boost: Priority inheritance in the scheduler

- section: Deadline class
- relevance: 3 - the scheduler's half of rt_mutex boosting
- words: 90

What does `rt_mutex_setprio()` change on the boosted task, which locks does it
hold, how is a deadline donor's bandwidth used by the task it boosts, and which
fields record the donor? Start from `pi_top_task` and `pi_se`.

# The BPF extensible class

## sched.scx-files: Layout of the extensible class

- section: Extensible class
- relevance: 4 - the code has been split into a directory
- words: 100

Which files hold the BPF extensible scheduling class and what is in each (the
core, idle tracking, the operations table and internal types, the public task
fields, the documentation, examples and tests)? A table. Start from
`kernel/sched/ext/` and `include/linux/sched/ext.h`.

## sched.scx-dsq: Dispatch queues

- section: Extensible class
- relevance: 3 - ids and ordering rules
- words: 100

What kinds of dispatch queue are there, which built-in ids exist and which of
them may a BPF scheduler name, and what are the rules for first-in first-out
versus virtual time ordering on one queue? Start from `SCX_DSQ_LOCAL` and
`scx_bpf_dsq_insert_vtime()`.

## sched.scx-ops-state: Task ownership state

- section: Extensible class
- relevance: 4 - the handshake between the core and the BPF scheduler
- words: 100

Which values does a task's `scx.ops_state` take, who owns the task in each,
which transitions need release and acquire ordering, and what does the dequeue
path do when it finds a task mid-transition? Start from the comment above
`SCX_OPSS_NONE`.

## sched.scx-direct-dispatch: Direct dispatch

- section: Extensible class
- relevance: 2 - an optimisation with its own marker
- words: 70

What is direct dispatch from the enqueue or CPU selection path, how does the
core know that a dispatch call is for the task being enqueued, and when is the
insertion deferred? Start from `direct_dispatch_task` and
`mark_direct_dispatch()`.

## sched.scx-kfunc-contexts: Kfunc calling contexts

- section: Extensible class
- relevance: 3 - the mechanism has been replaced
- words: 90

How does the extensible class restrict which of its kfuncs may be called from
which operation: is it checked when the program is loaded, when it runs, or
both, and where is the table? Start from `scx_kfunc_context_filter()` and
`scx_kf_allow_flags`.

## sched.scx-exit: Errors, watchdog and bypass

- section: Extensible class
- relevance: 4 - how a broken BPF scheduler is thrown out
- words: 110

What makes the kernel disable a loaded BPF scheduler (errors, a stalled task, a
key sequence), what is bypass mode and where do tasks run while it is on, and
which class do tasks end up in afterwards? Start from `scx_error()`,
`scx_watchdog_workfn()` and `scx_bypass()`.

## sched.scx-sub-cid: Sub-schedulers and cids

- section: Extensible class
- relevance: 3 - new structure a reader will not recognise
- words: 100

What is a sub-scheduler and how does it relate to cgroups and to the root BPF
scheduler, what is a cid as opposed to a CPU number, and which configuration
option and files carry them? If this tree has neither, say so and stop. Start
from `kernel/sched/ext/sub.c` and `kernel/sched/ext/cid.c`.

# CPU hotplug and core scheduling

## sched.hotplug-steps: Hotplug callbacks

- section: Hotplug
- relevance: 4 - each step relies on what the previous one did
- words: 130

List the scheduler's CPU hotplug callbacks in the order they run when a CPU
goes down and when it comes up, and say in a line what each does. A table.
Start from `sched_cpu_deactivate()`, `sched_cpu_wait_empty()`,
`sched_cpu_dying()` and `sched_cpu_activate()`.

## sched.balance-push: Emptying a dying CPU

- section: Hotplug
- relevance: 3 - which tasks may stay and who moves the rest
- words: 80

Once a CPU is marked inactive, what pushes its tasks away, which tasks are
allowed to stay and until when, and what does the final callback warn about?
Start from `balance_push()` and `rq_has_pinned_tasks()`.

## sched.hotplug-timers: Per-CPU timers across hotplug

- section: Hotplug
- relevance: 3 - a timer armed on a CPU that is gone
- words: 100

Which per-CPU timers and servers does the scheduler have to stop when a CPU
goes down and where is each stopped, and what keeps a deadline server from
being started on a CPU that is already offline? What usage is unsafe when
changing the condition that arms such a timer, and what is correct?

## sched.core-sched: Core scheduling

- section: Core scheduling
- relevance: 3 - SMT siblings share one lock and one pick
- words: 90

What is a core scheduling cookie, how does picking a task change when core
scheduling is enabled on a core, and what does it do to the runqueue locks of
SMT siblings? Start from `sched_core_enabled()` and the second
`pick_next_task()` in `kernel/sched/core.c`.
