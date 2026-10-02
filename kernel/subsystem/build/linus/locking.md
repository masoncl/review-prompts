# Locking and Synchronization

## Main structures

### Objects and how they relate

- `struct rt_mutex_base` (`include/linux/rtmutex.h`): the priority-inheritance
  lock core. `struct rt_mutex` is only `struct rt_mutex_base` plus a
  `struct lockdep_map`.
- Under `CONFIG_PREEMPT_RT`, `spinlock_t` and `struct mutex` embed
  `struct rt_mutex_base` directly, not `struct rt_mutex`. Of the lock types
  substituted on RT, only `struct ww_mutex` wraps `struct rt_mutex`.
- `struct futex_pi_state` in `kernel/futex/futex.h`: embeds
  `struct rt_mutex_base` directly too, with or without `CONFIG_PREEMPT_RT`.
- `struct rwbase_rt` (`include/linux/rwbase_rt.h`): a reader count plus a
  `struct rt_mutex_base`. Under `CONFIG_PREEMPT_RT` both `rwlock_t` and
  `struct rw_semaphore` are built on it.
- Waiter queues of non-RT `struct mutex`, non-RT `struct rw_semaphore` and
  `struct semaphore`: the lock holds only a `first_waiter` pointer. There is
  no list head in the lock (no `wait_list` member); the waiters' `list`
  members form a ring.
  - A sole waiter has an empty `list`; `__mutex_remove_waiter()` and
    `__rwsem_del_waiter()` use `list_empty(&waiter->list)` to mean "last
    waiter".
  - A walk ends when it reaches `first_waiter` again; see
    `__ww_waiter_next()` in `kernel/locking/ww_mutex.h` and `next_waiter()`
    in `kernel/locking/rwsem.c`.
- `blocked_on` in `struct task_struct`: the `struct mutex` the task is
  waiting for. `__mutex_lock_common()` sets it on every non-RT build, not
  only with `CONFIG_SCHED_PROXY_EXEC`.
- `blocked_lock` in `struct task_struct`: the `raw_spinlock_t` that
  serialises `blocked_on`. `__mutex_lock_common()` takes it inside the
  mutex's `wait_lock`.
- `blocked_donor` in `struct task_struct`: back link from a mutex owner to
  the task blocked on that mutex in the chain that `find_proxy_task()`
  followed; set by `find_proxy_task()` in `kernel/sched/core.c`. When
  `sched_proxy_exec()` is true and it is set, `__mutex_unlock_slowpath()`
  forces a handoff and prefers the donor over `first_waiter` if the donor is
  blocked on this mutex.
- `blocker` in `struct task_struct` (`CONFIG_DETECT_HUNG_TASK_BLOCKER`): the
  address of the mutex, semaphore or rwsem the task sleeps on, with the kind
  in the low two bits; see `include/linux/hung_task.h`.
- `struct semaphore`: `last_holder` under `CONFIG_DETECT_HUNG_TASK_BLOCKER`
  is a debugging hint, not an owner.
- `struct lockdep_map`: not in every lock. `struct semaphore` and
  `struct rt_mutex_base` have none, and `kernel/locking/semaphore.c` makes no
  lockdep call; only the semaphore's inner `raw_spinlock_t` is tracked. In
  `raw_spinlock_t`, `spinlock_t`, `rwlock_t`, `struct mutex`,
  `struct rw_semaphore` and `struct rt_mutex`, `dep_map` exists only under
  `CONFIG_DEBUG_LOCK_ALLOC`.
- `context_lock_struct()` (`include/linux/compiler-context-analysis.h`):
  defines the lock types, for example `context_lock_struct(mutex)` in
  `include/linux/mutex_types.h`. A search under `include/` for the plain
  struct definition of `struct mutex`, `struct rw_semaphore`, `spinlock_t`,
  `raw_spinlock_t`, `rwlock_t`, `seqlock_t`, `local_lock_t` or
  `struct ww_mutex` finds nothing.
- `struct semaphore`, `struct percpu_rw_semaphore` and
  `struct rt_mutex_base`: not declared with `context_lock_struct()`.
- `__guarded_by()`: ties a member to the lock that protects it, for example
  `first_waiter` to `wait_lock` in `struct mutex`.
- `scoped_guard (raw_spinlock_init, &lock->wait_lock)` in
  `__mutex_init_generic()`: `raw_spinlock_init` is a guard class that
  initialises the lock; this is initialisation, not a critical section.
- `struct percpu_rw_semaphore`: `block` gives writer-writer exclusion and
  stops new readers; blocked readers and writers both queue on `waiters`;
  `writer` is where the one writer that holds `block` waits for readers to
  drain.
- `rqspinlock_t` (`include/asm-generic/rqspinlock.h`,
  `kernel/bpf/rqspinlock.c`): a spinlock outside `kernel/locking/` whose
  `res_spin_lock()` returns `int`. Under `CONFIG_QUEUED_SPINLOCKS` it reuses
  `struct qnode` and `_Q_MAX_NODES` from `kernel/locking/qspinlock.h` with
  its own per-CPU `rqnodes` array.

## Where to look

**Core files**

| Job | File | Easy to miss |
|---|---|---|
| spinlock and rwlock API layers | `include/linux/spinlock.h` and the headers it includes | `include/linux/spinlock_api.h`, `include/linux/mutex_api.h`, `include/linux/seqlock_api.h` and `include/linux/lockdep_api.h` are each a single `#include` of the main header, not a layer. UP rwlock API has no file of its own: it is in `include/linux/spinlock_api_up.h`. |
| queued spinlock | `kernel/locking/qspinlock.c`, `kernel/locking/qspinlock.h` | `qspinlock.c` includes itself under `CONFIG_PARAVIRT_SPINLOCKS` to build `__pv_queued_spin_lock_slowpath()`, so the slowpath body is compiled twice. |
| rtmutex | `kernel/locking/rtmutex.c` | Not an object in `kernel/locking/Makefile`. It is `#include`d by `kernel/locking/rtmutex_api.c`, `kernel/locking/spinlock_rt.c`, `kernel/locking/ww_rt_mutex.c` and the `CONFIG_PREEMPT_RT` half of `kernel/locking/rwsem.c`; each defines `RT_MUTEX_BUILD_MUTEX` or `RT_MUTEX_BUILD_SPINLOCKS` first. |
| PREEMPT_RT `spinlock_t` and `rwlock_t` | `kernel/locking/spinlock_rt.c` | `kernel/locking/rwbase_rt.c` is not an object either: it is `#include`d by `spinlock_rt.c` and `rwsem.c`. |
| PREEMPT_RT `struct mutex` | no file of its own: the `#ifdef CONFIG_PREEMPT_RT` part of `kernel/locking/rtmutex_api.c` | The lock code in `kernel/locking/mutex.c` is inside `#ifndef CONFIG_PREEMPT_RT`. |
| PREEMPT_RT `struct rw_semaphore` | no file of its own: the `#else` half of `kernel/locking/rwsem.c` | Not in `kernel/locking/rtmutex_api.c`. |
| PREEMPT_RT `struct ww_mutex` | `kernel/locking/ww_rt_mutex.c` | It defines `WW_RT`, which makes `rtmutex.c` include `kernel/locking/ww_mutex.h`. |
| scope-based guard macros | `include/linux/cleanup.h`; per-lock definitions in the lock's header | `rwlock_t` guards are in `include/linux/spinlock.h`, not `include/linux/rwlock.h`. `include/linux/ww_mutex.h` and `include/linux/rtmutex.h` define no guards. |
| compiler lock annotations | `include/linux/compiler-context-analysis.h` | `__acquires()`, `__releases()`, `__must_hold()` and `__guarded_by()` are defined here; `include/linux/compiler_types.h` only includes it. They expand to nothing unless `WARN_CONTEXT_ANALYSIS` is defined, and to nothing under `__CHECKER__`. |
| compiler lock annotations: build switch | `scripts/Makefile.context-analysis`, `scripts/Makefile.lib`, `CONFIG_WARN_CONTEXT_ANALYSIS` in `lib/Kconfig.debug` | Opt-in per object or per directory, for example `CONTEXT_ANALYSIS_mutex.o := y` in `kernel/locking/Makefile`. Test in `lib/test_context-analysis.c`. |

**Authoritative documentation**

| Subject | Document | Easy to miss |
|---|---|---|
| compiler-based lock annotations | `Documentation/dev-tools/context-analysis.rst` | Its keyword reference is kernel-doc pulled from `include/linux/compiler-context-analysis.h`. `Documentation/dev-tools/sparse.rst` has no text on lock annotations. |
| memory barriers | `Documentation/memory-barriers.txt` | The file calls itself "not a specification" and refers doubts to `tools/memory-model/`. |
| memory model | `tools/memory-model/Documentation/explanation.txt` | `tools/memory-model/Documentation/README` says which file answers which need. |
| memory model: lock-protected variables accessed outside the critical section | `tools/memory-model/Documentation/locking.txt` | |

## Contexts and what excludes what

**bh, irq and irqsave variants**

- `spin_lock_bh()` on PREEMPT_RT: excludes softirq handlers on this CPU only
  with `CONFIG_PREEMPT_RT_NEEDS_BH_LOCK` (off unless selected by hand).
- `spin_lock_bh()` on PREEMPT_RT without that option: a softirq handler can
  run in another task on this CPU while the lock is held; it is kept out of
  the data only by taking the same lock.
- `local_lock_nested_bh()`: the `local_lock_t` form for per-CPU data touched
  in BH-disabled code; lockdep-only on a normal kernel, a per-CPU
  `spin_lock()` on PREEMPT_RT.
- A fifth form exists beside plain, bh, irq and irqsave:

| Acquire | Release | Normal kernel | PREEMPT_RT |
|---|---|---|---|
| `raw_spin_lock_irq_disable()` | `raw_spin_unlock_irq_enable()` | as irqsave, no `flags` argument | same |
| `spin_lock_irq_disable()` | `spin_unlock_irq_enable()` | as irqsave, no `flags` argument | same as `spin_lock()`; interrupts stay on, can sleep |
| `spin_trylock_irq_disable()` | `spin_unlock_irq_enable()` | the interrupt disable is kept only on success | same as `spin_trylock()` |

- The irq_disable forms nest: see "Nesting under irq-disabling locks".
- `rwlock_t` and `local_lock_t` have no irq_disable form.
- In-tree callers of the irq_disable forms: only `rust/helpers/spinlock.c`;
  `kernel/irq/refcount_interrupt_test.c` exercises
  `local_interrupt_disable()`.

**Preemption, migration and interrupt disabling**

- `preempt_disable()` on PREEMPT_RT: also keeps softirq handlers off this
  CPU, because RT runs them only in task context (`invoke_softirq()` only
  wakes `ksoftirqd`).
- `local_bh_disable()` on PREEMPT_RT, sleeping: the region holds
  `rcu_read_lock()`, so `might_sleep()` complains; only blocking on a
  `spinlock_t`, `rwlock_t` or `local_lock_t` is accepted
  (`rtlock_might_resched()` in `kernel/locking/spinlock_rt.c`).
- `local_interrupt_disable()` in `include/linux/interrupt_rc.h`: a fifth
  primitive; guarantees as `local_irq_disable()` on both kernels, and it
  nests: interrupts return to the state saved by the first call only at the
  matching last `local_interrupt_enable()`.
- `local_interrupt_disable()`: warns when called in NMI; raises
  `preempt_count()`, so the region is also non-preemptible by count.
- `spinlock_t` inside `preempt_disable()` or `local_irq_disable()`: lockdep
  does not report it on a normal kernel; `check_wait_context()` sees held
  locks and hardirq or softirq context only.
- `CONFIG_PROVE_RAW_LOCK_NESTING`: reports a `spinlock_t` taken under a
  `raw_spinlock_t` or in a non-threaded hard interrupt handler; it never
  checks a trylock.

**RCU readers implied by locks**

- `rcu_dereference()`: accepts `rcu_read_lock()` only
  (`rcu_read_lock_held()` tests `rcu_lock_map`); preemption, BH or
  interrupts disabled, or a non-RT spinlock, give a lockdep complaint.
- `rcu_dereference_all()` in `include/linux/rcupdate.h`: accepts
  `rcu_read_lock()`, `rcu_read_lock_bh()`, `rcu_read_lock_sched()` or
  `!preemptible()`; use it where the protection differs by configuration.

| Protection | Accepted by |
|---|---|
| `preempt_disable()`, `raw_spinlock_t`, non-RT `spinlock_t` | `rcu_dereference_sched()`, `rcu_dereference_all()` |
| interrupts disabled, non-RT BH disabled | those two and `rcu_dereference_bh()` |
| PREEMPT_RT `spinlock_t`, `rwlock_t`, `local_lock_t` | `rcu_dereference()`, `rcu_dereference_all()` |
| PREEMPT_RT `local_bh_disable()` from preemptible code | `rcu_dereference()`, `rcu_dereference_bh()`, `rcu_dereference_all()` |

- PREEMPT_RT `spin_lock_irqsave()` on a `spinlock_t`: fails
  `rcu_dereference_sched()` and `rcu_dereference_bh()`, since neither
  preemption nor interrupts are off.
- Without `CONFIG_PREEMPT_COUNT`: `preemptible()` is the constant 0, so the
  `rcu_dereference_sched()` and `rcu_dereference_all()` checks do not catch
  preemptible code.

**Context predicates**

- `preempt_count()` layout: bits 16-23 are `HARDIRQ_DISABLE_MASK`, the
  nesting count of `local_interrupt_disable()`; `HARDIRQ_MASK` is bits
  24-27; `NMI_BITS` is 4 with `CONFIG_HAS_SEPARATE_PREEMPT_RESCHED_BITS`,
  else 1 with nesting kept in the per-CPU `nmi_nesting`.
- `in_atomic()` inside `local_interrupt_disable()` or a
  `raw_spin_lock_irq_disable()` region: true, with or without
  `CONFIG_PREEMPT_COUNT`.
- `in_atomic()` inside `local_irq_disable()`: still false;
  `preempt_count()` is unchanged, and only `irqs_disabled()`, and
  `preemptible()` through it, see the disable.
- `in_interrupt()` and `in_task()`: do not look at `HARDIRQ_DISABLE_MASK`.
- `in_softirq()` true on PREEMPT_RT: says only that this task has a
  BH-disabled count; without `CONFIG_PREEMPT_RT_NEEDS_BH_LOCK` a softirq
  handler may still run on this CPU in another task.
- `CONFIG_PREEMPT_COUNT`: search Kconfig files for
  `select PREEMPT_COUNT`; `PROVE_LOCKING` selects it too, except on
  `ARCH_NO_PREEMPT`.

**Trylocks from any context**

- `can_spin_trylock()` in `mm/internal.h`: the run-time test; false on
  PREEMPT_RT in NMI or hardirq, false on `!CONFIG_SMP` in NMI, true
  otherwise, including with interrupts disabled.
- `free_one_page()` in `mm/page_alloc.c`: decides at run time; with
  `FPI_NOLOCK` it needs `can_spin_trylock()` and `spin_trylock_irqsave()` to
  succeed, else it queues the page on `zone->trylock_free_pages`.
- `alloc_nolock_allowed()` in `mm/page_alloc.c` and
  `__kmalloc_nolock_noprof()` in `mm/slub.c`: return failure when
  `can_spin_trylock()` is false.
- There is no ALLOC_TRYLOCK, FPI_TRYLOCK, pcp_trylock_prepare() or
  try_alloc_pages() here; the names are `ALLOC_NOLOCK`, `FPI_NOLOCK` and
  `alloc_pages_nolock()`, and on `!CONFIG_SMP` `pcp_spin_trylock()` is
  defined as `NULL`.
- `gfpflags_allow_spinning()`: not what the page allocator or slub test;
  they test `ALLOC_NOLOCK` and `alloc_flags_allow_spinning()`.
- `consume_stock()` in `mm/memcontrol.c`: always uses `local_trylock()`.
- `__bpf_ringbuf_reserve()`: takes `raw_res_spin_lock_irqsave()` and fails
  when that fails; it has no `in_nmi()` test.
- `local_lock_is_locked()`: defined, no caller in this tree.
- `local_trylock()` and `local_trylock_irqsave()` on PREEMPT_RT: may be
  called in NMI and hardirq; they return 0 there without touching the lock.
- **Potentially unsafe usage**: `spin_trylock()` on a `spinlock_t` from
  hardirq or NMI.
  - Unsafe: on PREEMPT_RT; `rt_spin_trylock()` records `current`, the
    interrupted task, as owner. `write_trylock()` on a `rwlock_t` is unsafe
    there in the same way: `rt_write_trylock()` takes the rtmutex for
    `current` through `rwbase_write_trylock()` in
    `kernel/locking/rwbase_rt.c`.
  - Unsafe: on `!CONFIG_SMP` without `CONFIG_DEBUG_SPINLOCK`, from NMI, or
    from hardirq when a holder leaves interrupts enabled; the trylock in
    `include/linux/spinlock_api_up.h` returns 1 without testing anything.
  - Safe: after `can_spin_trylock()` returned true, on a lock that every
    holder takes with interrupts disabled, as `free_one_page()` does with
    `zone->lock`.
  - Safe: on PREEMPT_RT with interrupts disabled or a `raw_spinlock_t` other
    than `pi_lock` of `struct task_struct` held, outside hardirq and NMI;
    `can_spin_trylock()` allows it. `rt_spin_trylock()` has no might-sleep
    check, and `rt_mutex_slowtrylock()` in `kernel/locking/rtmutex.c` takes
    `wait_lock` with `raw_spin_lock_irqsave()`.

**Locks shared with interrupt handlers**

- `Documentation/locking/spinlocks.rst`: Lesson 1 gives
  `spin_lock_irqsave()` as always safe; Lesson 3 allows the plain form only
  for a lock never used in interrupt handlers.
- `Documentation/kernel-hacking/locking.rst`, "Locking Between Hard IRQ and
  Softirqs/Tasklets": the place that lets the handler use plain
  `spin_lock()`; "Table of Minimum Requirements" has every pairing.
- `drivers/net/ethernet/realtek/8139too.c`, `tp->lock`: shows all three;
  `rtl8139_interrupt()` plain, `rtl8139_poll()` irqsave,
  `rtl8139_set_mac_address()` `spin_lock_irq()`.
- **Potentially unsafe usage**: plain `spin_lock()` on a `spinlock_t` in a
  hard interrupt handler.
  - Unsafe: when the handler is requested with `IRQF_NO_THREAD`,
    `IRQF_PERCPU` or `IRQF_ONESHOT`, or `irq_settings_can_thread()` is false
    for the descriptor; forced threading is skipped, so on PREEMPT_RT the
    handler stays in hard interrupt context, where `rt_spin_lock()` can
    sleep.
  - Safe: when requested without those flags on a descriptor for which
    `irq_settings_can_thread()` is true, as `rtl8139_interrupt()` with
    `IRQF_SHARED`; `__handle_irq_event_percpu()` warns if a handler returns
    with interrupts enabled, and on PREEMPT_RT the handler runs in a thread.
  - Safe: when force-threaded on a normal kernel; `irq_forced_thread_fn()`
    runs the handler with BH and interrupts disabled.
- `thread_fn` of `request_threaded_irq()`: `irq_thread_fn()` calls it with
  nothing disabled; it is process context and needs the irq form against
  the primary handler.
- `struct hrtimer` callback on a normal kernel: hard interrupt context unless
  `HRTIMER_MODE_SOFT`, so `spin_lock_bh()` in process context is not enough;
  see `__hrtimer_setup()`.
- `struct hrtimer` callback on PREEMPT_RT: softirq expiry unless
  `HRTIMER_MODE_HARD`.

**Nesting under irq-disabling locks**

- `spin_lock_irq_disable()` with `spin_unlock_irq_enable()`, on a normal
  kernel: the nesting is counted in `preempt_count()`, so two locks taken
  this way may be released in either order; interrupts return to the first
  saved state at the last release.
- Counted forms, precondition: both locks must use them; an outer
  `spin_unlock_irq_enable()` with a plain inner lock still held drops the
  count to zero and restores interrupts.
- PREEMPT_RT, `spinlock_t`: the outer `spin_lock_irqsave()` sets `flags` to 0
  and masks nothing, so the inner region has interrupts enabled; only
  `raw_spinlock_t` irq forms mask.
- **Unsafe usage**: inner `spin_lock_irq()` and `spin_unlock_irq()` inside a
  region that must stay irq-off.
  - Unsafe: `__raw_spin_unlock_irq()` calls `local_irq_enable()`
    unconditionally, so interrupts come on with the outer lock held.
  - Safe: plain `spin_lock()` and `spin_unlock()` inside, as
    `cgroup_leave_frozen()` takes `siglock` under `css_set_lock`.
- **Unsafe usage**: outer released first, last unlock restores `flags` saved
  by an inner `spin_lock_irqsave()`.
  - Unsafe: those `flags` record interrupts off, so interrupts stay off after
    both locks are dropped.
  - Safe: outer plain `raw_spin_unlock()`, last unlock carries the outer
    state, as `rt_mutex_adjust_prio_chain()` does with `pi_lock` then
    `wait_lock`.

**CPU hotplug exclusion**

- `migrate_disable()`: keeps the current CPU in `cpu_online_mask` under
  `CONFIG_HOTPLUG_CPU`; `sched_cpu_wait_empty()` waits until
  `rq_has_pinned_tasks()` is false.
- `migrate_disable()`, limit: the CPU may already be out of
  `cpu_active_mask`, and teardown callbacks of states above
  `CPUHP_AP_SCHED_WAIT_EMPTY` have already run on it.
- `preempt_disable()` and `local_irq_disable()`: also keep every other CPU in
  `cpu_online_mask`; `takedown_cpu()` uses `stop_machine_cpuslocked()`,
  which needs the stopper thread to run on every online CPU before
  `take_cpu_down()` runs.
- `preempt_disable()` and `local_irq_disable()`, limit: on other CPUs the
  teardown callbacks above `CPUHP_TEARDOWN_CPU` still run, and a CPU can
  still come online.
- `cpus_read_trylock()`: does not sleep; `percpu_down_read_trylock()` has no
  `might_sleep()` and fails instead of waiting. It has no caller in this
  tree.
- `Documentation/core-api/cpu_hotplug.rst`: does not mention
  `cpus_read_lock()`; the rules are in `kernel/cpu.c` and
  `include/linux/percpu-rwsem.h`.

## Kinds of lock and nesting

**Lock categories**

- Bit spinlocks on PREEMPT_RT: stay spinning; `locktypes.rst` ("bit spinlocks")
  applies the `raw_spinlock_t` caveats to them, and says some users switch to
  `spinlock_t` under `#ifdef` at the usage site.
- RT `rwlock_t`: built on `struct rwbase_rt` (`include/linux/rwlock_types.h`);
  there is no struct rt_rwlock in this tree.
- `local_trylock_t`: not listed in `locktypes.rst`; changes category exactly
  like `local_lock_t` (both are `typedef spinlock_t` under `CONFIG_PREEMPT_RT`
  in `include/linux/local_lock_internal.h`).

**Raw spinlocks**

- Section length: `Documentation/locking/locktypes.rst` has no sentence asking
  that `raw_spinlock_t` sections be short or bounded; its only wording is that
  the type "can sometimes also be used when the critical section is tiny, thus
  avoiding RT-mutex overhead", which permits a use and limits nothing.
- `Documentation/core-api/real-time/differences.rst`: says nothing about raw
  section length either; under "Locking" it only names where raw locks are used
  (interrupt handling, scheduler, timers).
- Freeing memory: `locktypes.rst` ("raw_spinlock_t on RT") names only
  allocation; the ban on `kfree()` and `free_pages()` in non-preemptible
  sections is in `differences.rst`, "Memory allocation".
- **Potentially unsafe usage**: allocating or freeing memory while holding a
  `raw_spinlock_t`.
  - Unsafe: through `kmalloc()`, `kfree()` or the page allocator with any gfp
    mask, `GFP_ATOMIC` included, because the allocator takes `spinlock_t`; the
    failing example in `locktypes.rst` uses `GFP_ATOMIC`.
  - Safe: `kmalloc_nolock()` (`include/linux/slab.h`, implemented by
    `__kmalloc_nolock_noprof()` in `mm/slub.c`) and `kfree_nolock()` in
    `mm/slub.c`, which only trylock; `kmalloc_nolock()` can return NULL (always
    for sizes above `KMALLOC_MAX_CACHE_SIZE`, and on RT in hardirq or NMI via
    `can_spin_trylock()`), and the limits of `kfree_nolock()` are in the
    comment above it. On PREEMPT_RT not with `pi_lock` of
    `struct task_struct` held; see "Local trylocks".

**Nesting by lock type**

- `spinlock_t`, `rwlock_t` and `local_lock_t`: one level; each may be taken
  while holding any of the others (all carry `LD_WAIT_CONFIG`).
- `Documentation/locking/locktypes.rst` ("Lock type nesting rules"): states the
  rule for the lock rows only; the file never mentions RCU.
- RCU rows: stated in `Documentation/RCU/Design/Requirements/Requirements.rst`,
  quick quiz "What about sleeping locks?": sleeping locks are forbidden in a
  read-side section, RT `spinlock_t` is allowed, and `mutex_trylock()` is legal
  there.
- `Documentation/RCU/checklist.rst`: does not say which lock types may be
  taken in a read-side section; item 13 says only that blocking is permitted
  in SRCU readers, unlike most flavors of RCU.
- RCU flavours differ:

| Held | `raw_spinlock_t` | `spinlock_t`, `rwlock_t`, `local_lock_t` | `struct mutex` |
|---|---|---|---|
| `rcu_read_lock()` | ok | ok | no |
| `rcu_read_lock_bh()` | ok | ok | no |
| `rcu_read_lock_sched()` | ok | no | no |

- Full matrix, hardirq and softirq contexts included: the comment table above
  `wait_context_tests()` in `lib/locking-selftest.c`; those tests run only with
  `CONFIG_PROVE_RAW_LOCK_NESTING`.

**Lockdep wait types**

- Wait types that are easy to get wrong (outer `LD_WAIT_INV` means "use
  inner"):

| Map | inner | outer |
|---|---|---|
| `rcu_lock_map` | `LD_WAIT_CONFIG` | `LD_WAIT_FREE` |
| `rcu_bh_lock_map` | `LD_WAIT_CONFIG` | `LD_WAIT_FREE` |
| `rcu_sched_lock_map` | `LD_WAIT_SPIN` | `LD_WAIT_FREE` |
| `local_lock_t` (lock type `LD_LOCK_PERCPU`) | `LD_WAIT_CONFIG` | `LD_WAIT_INV` |
| SRCU `dep_map` | `LD_WAIT_INV` | `LD_WAIT_INV` |
| `struct percpu_rw_semaphore` | `LD_WAIT_INV` | `LD_WAIT_INV` |

- SRCU and `struct percpu_rw_semaphore`: initialised without a wait type
  (plain `lockdep_init_map()`, or a static initialiser that sets only
  `.name`), so acquiring them is never wait-context checked and holding them
  never lowers the context.
- `struct semaphore` and bit spinlocks: no lockdep map of their own, so
  `check_wait_context()` never sees them.
- Hardirq context: `LD_WAIT_SPIN` only when neither `current->hardirq_threaded`
  nor `current->irq_config` is set; otherwise `LD_WAIT_CONFIG`
  (`task_wait_context()` in `kernel/locking/lockdep.c`).
- `hardirq_threaded`: set by `__handle_irq_event_percpu()` when
  `irq_settings_can_thread()` is true and the action has none of
  `IRQF_NO_THREAD`, `IRQF_PERCPU`, `IRQF_ONESHOT`.
- `irq_config`: set by `lockdep_hrtimer_enter()` for non-hard timers, by
  `lockdep_irq_work_enter()` without `IRQ_WORK_HARD_IRQ`, and by
  `lockdep_posixtimer_enter()` (`include/linux/irqflags.h`).
- Read acquisitions: checked like any other; `check_wait_context()` does not
  test `read`.
- `check == 0` acquisitions: still checked; the RCU maps are acquired with
  `check` 0 and go through `check_wait_context()`.
- Skipped besides inner `LD_WAIT_INV` and trylock: maps keyed
  `__lockdep_no_track__`, and an acquisition with a `nest_lock` whose class
  equals that of the top held lock, which `__lock_acquire()` folds into the
  held lock and returns before the check.
- Held trylocks: only the lock being acquired is exempt as a trylock; a lock
  that was taken by trylock and is still held lowers the context for later
  acquisitions in the same irq context.

**Raw lock nesting checks**

- `CONFIG_PROVE_RAW_LOCK_NESTING=y`: `LD_WAIT_CONFIG` is its own value between
  `LD_WAIT_SPIN` and `LD_WAIT_SLEEP`.
- `CONFIG_PROVE_RAW_LOCK_NESTING=n`: `LD_WAIT_CONFIG = LD_WAIT_SPIN`
  (`include/linux/lockdep_types.h`); it never equals `LD_WAIT_SLEEP`, so under
  `CONFIG_PROVE_LOCKING` a sleeping lock under a spinning lock is reported
  either way.
- Default depends on the architecture (`lib/Kconfig.debug`): with
  `ARCH_SUPPORTS_RT` the option has no prompt and is `y` whenever
  `CONFIG_PROVE_LOCKING` is on; without `ARCH_SUPPORTS_RT` it has a prompt and
  no default, so it is off unless chosen.
- `ARCH_SUPPORTS_RT`: defined in `arch/Kconfig`; search `arch/` for
  `select ARCH_SUPPORTS_RT`, for example x86 and arm64.
- Also controlled by the option: `lockdep_assert_RT_in_threaded_ctx()`
  (`include/linux/lockdep.h`, used by `complete_all()`) is empty without it,
  and `wait_context_tests()` in `lib/locking-selftest.c` is not run.

**Wait type override maps**

- Users: search for `DEFINE_WAIT_OVERRIDE_MAP`; there is no put_task_map in
  this tree and no override map under `kernel/rcu/`.
- Wait type: the macro accepts any value; in-tree maps use `LD_WAIT_FREE`,
  `LD_WAIT_CONFIG` and `LD_WAIT_SLEEP`, none uses `LD_WAIT_SPIN`.
- Two opposite uses: raising the limit (`fill_pool_map`, `printk_legacy_map`,
  `vmbus_map`, `kfree_rcu_sheaf_map` at `LD_WAIT_CONFIG`; `tick_freeze_map` at
  `LD_WAIT_SLEEP`) and lowering it so that locks of a higher wait type taken
  inside get reported (`sched_map` in `sched_submit_work()` at
  `LD_WAIT_CONFIG`, in task context; `rv_react_map` in `rv_react()` at
  `LD_WAIT_FREE`).
- `rv_react_map` at `LD_WAIT_FREE`: every checked non-trylock lock taken in a
  reactor is reported, `raw_spinlock_t` included; maps whose outer type is
  `LD_WAIT_FREE` pass, such as the RCU read-side maps.
- Scope of the relaxation: `check_wait_context()` is the only reader of
  `LD_LOCK_WAIT_OVERRIDE`; runtime checks such as `__might_resched()` in
  `rt_spin_lock()` (`kernel/locking/spinlock_rt.c`) are not relaxed.
- Storage: the map must be static; the macro sets no key, so
  `assign_lock_key()` uses the map address and, for a non-static object, prints
  "trying to register non-static key" and turns lockdep off.
- **Potentially unsafe usage**: raising the wait type around a `spinlock_t` or
  sleeping-lock acquisition made under a `raw_spinlock_t` or in hardirq
  context.
  - Unsafe: when the map is taken on PREEMPT_RT in that context and the lock
    can be held by someone else; lockdep stays silent and the RT lock blocks in
    atomic context.
  - Safe: the map is not taken on RT, so lockdep there still checks the
    wrapped code, as in `printk_legacy_allow_spinlock_enter()` (empty under
    `CONFIG_PREEMPT_RT`), `vmbus_isr()` (RT branch wakes a thread instead) and
    `__kfree_rcu_sheaf()` (map taken only if `!IS_ENABLED(CONFIG_PREEMPT_RT)`).
  - Safe: on RT the wrapped call is reached only when `can_fill_pool()` in
    `lib/debugobjects.c` allows it: `preemptible()`, or before
    `SYSTEM_SCHEDULING` outside hardirq; `debug_objects_fill_pool()` does this.
  - Safe: the acquisition cannot block because nothing else runs;
    `tick_freeze()` and `tick_unfreeze()` take the map only when
    `tick_freeze_depth == num_online_cpus()`, on RT too.
- **Unsafe usage**: acquiring an override map with `lock_map_acquire()`; the
  map is then itself checked against the current context and reported as
  invalid wait context when it raises the type.
  - Safe: `lock_map_acquire_try()`, which `check_wait_context()` skips, as
    every in-tree user does.

## PREEMPT_RT and local locks

**Substitutions on PREEMPT_RT**

- `struct rw_semaphore` reader release by another task: works on RT;
  `up_read_non_owner()` in `kernel/locking/rwsem.c` is common to both
  configurations and on RT drops the reader count without an owner test.
- `rwlock_t` and `struct rw_semaphore` readers on RT: several hold the lock
  at once; `rwbase_read_trylock()` in `kernel/locking/rwbase_rt.c` only
  increments a count while `READER_BIAS` is set.
- `struct mutex` and `spinlock_t` waiters on RT: do not always sleep; the top
  waiter spins in `rtmutex_spin_on_owner()` (`kernel/locking/rtmutex.c`,
  `CONFIG_SMP`) while the owner is running on a CPU.
- `struct semaphore`: unchanged on RT, as `raw_spinlock_t` is;
  `kernel/locking/semaphore.c` has no `CONFIG_PREEMPT_RT` branch.

**spinlock_t on PREEMPT_RT**

- `spin_lock_bh()` on RT: calls `local_bh_disable()` and then
  `rt_spin_lock()`; `read_lock_bh()` and `write_lock_bh()` call
  `local_bh_disable()` and then `rt_read_lock()` or `rt_write_lock()`. What
  that excludes is under "Bottom halves and per-CPU data".
- Migration and RCU protection: start only after the lock is acquired;
  `__rt_spin_lock()` calls `rcu_read_lock()` and `migrate_disable()` after
  `rtlock_lock()` returns, so a task blocked on the lock has neither.
- `rt_spin_unlock()`, `rt_read_unlock()`, `rt_write_unlock()`: call
  `rcu_read_unlock()` last, so a lock inside an RCU-freed object stays valid
  until the rtmutex release has finished.

**Hard interrupt context on PREEMPT_RT**

- `IRQF_ONESHOT`: a handler registered with it is not force-threaded;
  `irq_setup_forced_threading()` in `kernel/irq/manage.c` returns early for
  `IRQF_NO_THREAD`, `IRQF_PERCPU` and `IRQF_ONESHOT`.
- Primary handler given with `IRQF_ONESHOT` and a `thread_fn`: runs in hard
  interrupt context on RT; without `IRQF_ONESHOT` it is threaded too.
- Descriptor opt-out: `__setup_irq()` skips forced threading when
  `irq_settings_can_thread()` is false (`_IRQ_NOTHREAD`).
- `force_irqthreads()`: constant true only with `CONFIG_PREEMPT_RT` and
  `CONFIG_IRQ_FORCED_THREADING`; the architecture selects the latter,
  `config PREEMPT_RT` selects only `PREEMPTION`.
- `TIMER_IRQSAFE` timers: run from a thread on RT (`run_ktimerd()` in
  `kernel/softirq.c`), but `kernel/time/timer.c` calls the callback with
  interrupts disabled, so the callback is atomic and cannot take a
  `spinlock_t`.
- Sleeper hrtimers on RT: `__hrtimer_setup_sleeper()` adds
  `HRTIMER_MODE_HARD` when `rt_or_dl_task_policy(current)` is true and
  `HRTIMER_MODE_SOFT` was not requested.
- `lockdep_assert_RT_in_threaded_ctx()` in `include/linux/lockdep.h`: warns
  under `CONFIG_PROVE_RAW_LOCK_NESTING` when in hard interrupt context that
  is marked neither `hardirq_threaded` nor `irq_config`.

**Usage that breaks on PREEMPT_RT**

- **Potentially unsafe usage**: `spin_lock()`, `read_lock()`, `write_lock()`
  or `local_lock()` (any suffix) where preemption or interrupts are disabled
  on RT: after `preempt_disable()`, `local_irq_save()` or `get_cpu_ptr()`,
  under a `raw_spinlock_t` or `bit_spin_lock()`, or in a handler that stays
  in hard interrupt context.
  - Unsafe: when another task or CPU can hold the lock;
    `rtlock_slowlock_locked()` in `kernel/locking/rtmutex.c` then calls
    `schedule_rtlock()`.
  - Safe: when nothing else can run and hold the lock, as under
    `tick_freeze()` and `tick_unfreeze()` in `kernel/time/tick-common.c` once
    `tick_freeze_depth == num_online_cpus()`; `__might_resched()` returns
    early while `system_state > SYSTEM_RUNNING`.
  - Safe: `spin_lock_irqsave()` on its own, as `add_wait_queue()` in
    `kernel/sched/wait.c` does; `rtlock_might_resched()` in
    `kernel/locking/spinlock_rt.c` requires `preempt_count()` zero and
    interrupts enabled, and the RT irq forms disable nothing.
  - Safe: inside `rcu_read_lock()` or a BH-disabled section, as
    `gro_cells_receive()` does; `RTLOCK_RESCHED_OFFSETS` allows the RCU
    depth, and RT `softirq_count()` is kept in `softirq_disable_cnt` of the
    task, not in `preempt_count()`.
  - Safe: `local_lock()` and then `this_cpu_ptr()` in place of
    `get_cpu_ptr()`, as `mlock_folio()` in `mm/mlock.c` does.
- **Potentially unsafe usage**: `kmalloc()` or `kfree()` under a
  `raw_spinlock_t` or with preemption or interrupts disabled on RT.
  - Unsafe: once other tasks or CPUs run and can hold the allocator's locks;
    `list_lock` in `mm/slub.c` is a `spinlock_t`.
  - Safe: in early boot with interrupts still off, as
    `workqueue_init_early()` called from `start_kernel()`; nothing else runs,
    and `__might_resched()` returns while `system_state == SYSTEM_BOOTING`.
  - Safe: `kmalloc_nolock()` and `kfree_nolock()` (not with `pi_lock` of
    `struct task_struct` held), or allocate while holding only a
    `spinlock_t`.
- Detection on RT: `rtlock_might_resched()` reports the preempt-off and
  irq-off cases, and only with `CONFIG_DEBUG_ATOMIC_SLEEP`.

**Local trylocks**

- Non-RT marker: the field is `acquired` (`u8`) in `local_trylock_t`,
  `include/linux/local_lock_internal.h`.
- `local_lock_irq()` and `local_unlock_irq()`: accept both types; the
  `_Generic` in `__local_lock_acquire()` and `__local_lock_release()` covers
  all three lock and unlock forms.
- `local_lock_nested_bh()`: `local_lock_t` only; non-RT
  `__local_lock_nested_bh()` calls `local_lock_acquire()` directly and never
  writes `acquired`.
- Guard classes in `include/linux/local_lock.h` that take the lock: defined
  for `local_lock_t __percpu` only; `local_trylock_t` has only the
  `local_trylock_init` class.
- `local_lock_is_locked()`: non-RT reads `acquired`, so `local_trylock_t`
  only; RT tests whether `current` owns the rtmutex.
- Type checking: non-RT only; on RT both types are `typedef spinlock_t`, so
  `local_trylock()` on a `local_lock_t` compiles there.
- RT, task or softirq context: `local_trylock()` is `migrate_disable()` plus
  `spin_trylock()`, whose slow path takes the rtmutex `wait_lock`.
- RT with `pi_lock` of `struct task_struct` held: `local_trylock()` is not
  usable; `mm/slab_common.c` skips `kfree_rcu_sheaf()` on RT for this reason.
- `mm/page_alloc.c`: has no `local_trylock_t`; its nolock paths gate
  `spin_trylock_irqsave()` with `can_spin_trylock()`.
- **Potentially unsafe usage**: `local_lock()`, `local_lock_irq()` or
  `local_lock_irqsave()` on a `local_trylock_t` on non-RT.
  - Unsafe: from a context that can interrupt a holder on this CPU;
    `__local_lock_acquire()` sets `acquired` whatever its value, and only its
    `lockdep_assert()`, under `CONFIG_LOCKDEP`, tests it.
  - Safe: from task context only, as `drain_local_memcg_stock()` in
    `mm/memcontrol.c`, which returns unless `in_task()`; `__local_lock()`
    disables preemption, so no other task-context holder exists on the CPU.
  - Safe: `local_trylock()` with a fallback on failure, as `consume_stock()`
    in `mm/memcontrol.c` does.

**Bottom halves and per-CPU data**

- `CONFIG_PREEMPT_RT_NEEDS_BH_LOCK`: has no `default` in
  `kernel/Kconfig.preempt`, so it is off unless selected by hand.
- Option off: first-level `__local_bh_disable_ip()` from `preemptible()`
  code calls `migrate_disable()` and `rcu_read_lock()` and takes no lock;
  BH-disabled sections of different tasks on one CPU interleave.
- Option on: first-level `__local_bh_disable_ip()` from `preemptible()` code
  takes `local_lock(&softirq_ctrl.lock)`, which serialises them.
- Softirq handlers with the option off: can run on the CPU while another
  task is preempted inside its BH-disabled section; `__local_bh_enable_ip()`
  decides from `current->softirq_disable_cnt`.
- `Documentation/locking/locktypes.rst` on `_bh` ("use a per-CPU lock for
  serialization"): true only with `CONFIG_PREEMPT_RT_NEEDS_BH_LOCK`.
- `local_lock_nested_bh()` on RT: takes the per-CPU `spinlock_t` with
  `spin_lock()`; with the option off `local_bh_disable()` adds no
  serialisation to it.
- RT `__local_lock_nested_bh()`: omits the `migrate_disable()` that
  `__local_lock()` does before `this_cpu_ptr()`; the caller's BH-disabled
  state pins the CPU. `rt_spin_lock()` still calls `migrate_disable()`.
- `lockdep_assert_in_softirq()`: the precondition check; needs
  `in_softirq()` and neither `in_hardirq()` nor `in_nmi()`, and exists only
  with `CONFIG_PROVE_LOCKING`.
- `__local_lock_nested_bh()`: takes an already resolved pointer instead of a
  `__percpu` one, as `gro_cell_poll()` in `net/core/gro_cells.c` does.
- Allocated per-CPU data: call `local_lock_init()` on each CPU's lock, as
  `gro_cells_init()` does; static data uses `INIT_LOCAL_LOCK()`.
- **Potentially unsafe usage**: per-CPU data touched under
  `local_bh_disable()` or in softirq with no lock of its own, on RT.
  - Unsafe: without `CONFIG_PREEMPT_RT_NEEDS_BH_LOCK`, when the data needs
    more than one access to stay consistent; `__local_bh_disable_ip()` then
    takes no lock, so another task can run a BH-disabled section on the CPU
    in between.
  - Safe: a `local_lock_t` in the structure, taken with
    `local_lock_nested_bh()` on every access, as `napi_alloc_cache` in
    `net/core/skbuff.c` is.
  - Safe: a single `this_cpu_*()` operation, as `netdev_core_stats_inc()` in
    `net/core/dev.c`; the generic `this_cpu_generic_to_op()` runs under
    `raw_local_irq_save()`.

**Converting to local locks**

- `this_cpu_*()` and `__this_cpu_*()` on data the lock covers: valid inside
  the section on RT; `check_preemption_disabled()` in
  `lib/smp_processor_id.c` accepts `current->migration_disabled`.
- Acquire form: `local_lock()`, `local_lock_irq()` and `local_lock_irqsave()`
  are the same operation on RT, so choose by what non-RT needs; a wrong
  choice shows only on non-RT.
- Initialisation: non-RT `local_lock_t` is an empty struct without
  `CONFIG_DEBUG_LOCK_ALLOC`, so a missing `local_lock_init()` shows only on
  RT or with lockdep.
- **Unsafe usage**: `local_lock_irq()` or `local_lock_irqsave()` followed by
  `raw_spin_lock()` as a stand-in for `raw_spin_lock_irq()`; the nesting is
  allowed by lock type, but on RT `__local_lock_irq()` is `__local_lock()`,
  which disables neither interrupts nor preemption
  (`Documentation/locking/locktypes.rst`, "local_lock on RT").
  - Safe: follow the local lock with a `spinlock_t`, as `kcov_remote_start()`
    in `kernel/kcov.c` does with `kcov_remote_lock`; on RT `spin_lock()` is
    `rt_spin_lock()` and needs no interrupt disabling.
  - Safe: use `raw_spin_lock_irq()` directly where interrupts must be off.

## Sleeping and reader-writer locks

**Mutex rules**

- `CONFIG_DEBUG_MUTEXES` by itself: of the rules listed in
  `Documentation/locking/mutex-design.rst` it checks only initialisation
  through the API (`lock->magic`) and owner-only unlock, which also catches a
  second unlock. The sentence there that the option fully enforces the list
  does not hold; the option can be set without lockdep.
- Owner at unlock: `MUTEX_WARN_ON(__owner_task(owner) != current)` in
  `__mutex_unlock_slowpath()` and `__mutex_handoff()` in
  `kernel/locking/mutex.c`.
- `debug_mutex_unlock()` in `kernel/locking/mutex-debug.c`: tests only
  `lock->magic`, and runs only when the unlock goes on to take `wait_lock`.
- Held mutex reinitialised: `mutex_init_lockdep()` calls
  `debug_check_no_locks_freed()`, under `CONFIG_DEBUG_LOCK_ALLOC`;
  `debug_mutex_init()` only sets `lock->magic`.
- Recursive locking: reported by `check_deadlock()` in
  `kernel/locking/lockdep.c`, which needs `CONFIG_PROVE_LOCKING`; on non-RT
  `CONFIG_DEBUG_LOCK_ALLOC` alone does not report it.
- Exit with a mutex held, and freeing memory that holds one:
  `debug_check_no_locks_held()` and `debug_check_no_locks_freed()` are lockdep
  functions, empty stubs without `CONFIG_LOCKDEP` in
  `include/linux/debug_locks.h`; nothing under `CONFIG_DEBUG_MUTEXES` checks
  either.
- One holder at a time: enforced in every configuration; on non-RT by the
  cmpxchg on `owner`.
- `mutex_trylock()` in interrupt context: `check_wait_context()` returns early
  for a trylock, and the non-RT `mutex_trylock()` tests only `lock->magic`.
- PREEMPT_RT: `CONFIG_DEBUG_MUTEXES` depends on `!PREEMPT_RT` and
  `struct mutex` has no `magic` member; the owner check is
  `debug_rt_mutex_unlock()` under `CONFIG_DEBUG_RT_MUTEXES`.
- PREEMPT_RT `mutex_trylock()` in `kernel/locking/rtmutex_api.c`: under
  `CONFIG_DEBUG_RT_MUTEXES` it warns when `in_task()` is false and returns 0.

**Unlocking and object lifetime**

- `struct rw_semaphore`: the same requirement as for a mutex. `__up_read()`
  and `__up_write()` in `kernel/locking/rwsem.c` call `rwsem_wake()`, which
  takes `sem->wait_lock`, after the atomic that releases `sem->count`.
- `struct rw_semaphore` on PREEMPT_RT: `rwbase_read_unlock()` takes
  `rtmutex.wait_lock` in `__rwbase_read_unlock()` after the
  `atomic_dec_and_test()` that drops the last reader.
- Where it is stated for rwsems: in
  `Documentation/locking/mutex-design.rst` ("most other sleeping locks like
  rwsems"); `up_read()` and `up_write()` carry no such comment.
- `spinlock_t` on PREEMPT_RT: `rt_spin_unlock()` does not touch the lock after
  releasing it. Its last access is the release cmpxchg or
  `rt_mutex_slowunlock()`, whose comment shows the lock, decrement, unlock,
  `kfree()` pattern it is written to allow.
- `spinlock_t` with debugging: `debug_spin_unlock()` and `spin_release()` run
  before the releasing store; see also the comment in
  `__pv_queued_spin_unlock_slowpath()`, which treats the lock memory as
  possibly freed right after the store.
- `refcount_dec_and_mutex_lock()`, and `kref_put_mutex()` built on it: the
  slow path that returns false calls `mutex_unlock()` after its own
  decrement, so they do not lift the requirement for a mutex that is freed
  with the object.
- Queue that the unlock slow paths of `struct mutex` and
  `struct rw_semaphore` read after the release: `first_waiter`.

**Reader-writer semaphores**

- New reader with a writer queued, in `rwsem_down_read_slowpath()`: it queues
  only if `count` has `RWSEM_WRITER_LOCKED` or `RWSEM_FLAG_HANDOFF`, or the
  lock is reader-owned with another reader counted. Otherwise it takes the
  lock ahead of the queued writer.
- Read recursion follows from that: the second `down_read()` sees
  `RWSEM_FLAG_WAITERS`, `RWSEM_READER_OWNED` and its own first count, so it
  queues behind the writer.
- Readers do not spin: only `rwsem_down_write_slowpath()` calls
  `rwsem_optimistic_spin()`.
- `rwsem_mark_wake()` with a reader at the head: grants the lock to readers
  anywhere in the queue, skipping writers, up to `MAX_READERS_WAKEUP`; a
  reader queued behind a writer gets the lock before that writer.
- `down_read_non_owner()` and `up_read_non_owner()`: functions only under
  `CONFIG_DEBUG_LOCK_ALLOC`; otherwise macros for `down_read()` and
  `up_read()` in `include/linux/rwsem.h`.
- Read lock released by another task: reported only by lockdep, in
  `lock_release()`. `CONFIG_DEBUG_RWSEMS` in `__up_read()` tests that the lock
  is reader-owned, not which task calls.
- PREEMPT_RT, `__rwbase_read_lock()` in `kernel/locking/rwbase_rt.c`: every
  reader that misses the fast path goes through the rtmutex slow lock and
  waits for the writer that owns it. The header comment of that file (step 3,
  "not writer fair") does not match the body.
- PREEMPT_RT, effect: once a writer owns the rtmutex and has removed
  `READER_BIAS`, `down_read_trylock()` fails and new readers wait until that
  writer releases the rtmutex.
- PREEMPT_RT read recursion: deadlocks the same way; the second read blocks on
  the rtmutex while the writer waits for the first read to end.
- PREEMPT_RT priority inheritance: a reader blocked on the rtmutex boosts the
  writer that owns it, through `task_blocks_on_rt_mutex()`; a writer waiting
  for readers to drain boosts nobody.
- PREEMPT_RT spinning: there is no handoff bit, but the top waiter on the
  rtmutex spins on a running owner in `rtmutex_spin_on_owner()` under
  `CONFIG_SMP`.

**Reader-writer spinlocks**

- Lockdep and `read_lock()`: `rwlock_acquire_read()` records a recursive
  read only when `read_lock_is_recursive()` is true. With
  `CONFIG_QUEUED_RWLOCKS` a process-context `read_lock()` is a non-recursive
  read, so `check_deadlock()` reports a nested one under
  `CONFIG_PROVE_LOCKING`.
- `in_interrupt()` is also true in a BH-disabled section, so `read_lock_bh()`
  and a `read_lock()` under `local_bh_disable()` take the non-queueing path in
  `queued_read_lock_slowpath()` and count as recursive for lockdep.
- `read_lock_irq()` and `read_lock_irqsave()` in process context:
  `in_interrupt()` is false, so they queue behind a waiting writer like a
  plain `read_lock()`.
- `queued_read_trylock()`: fails on any bit of `_QW_WMASK`, a waiting writer
  included, and has no `in_interrupt()` exception.
- PREEMPT_RT read recursion: not safe. `rt_read_lock()` uses the same
  `rwbase_read_lock()` as described under "Reader-writer semaphores", so a
  second read blocks once a writer owns the rtmutex and has removed
  `READER_BIAS`.
- PREEMPT_RT and lockdep: `CONFIG_QUEUED_RWLOCKS` depends on `!PREEMPT_RT`, so
  `read_lock_is_recursive()` is always true and lockdep records every
  `rt_read_lock()` as a recursive read. It does not report a nested read
  there, although the lock can deadlock on one.

## Lockdep

**Meaning of a lockdep report**

- Wait-context rule: `check_wait_context()` in `kernel/locking/lockdep.c` is
  built under `CONFIG_PROVE_LOCKING` and reports "Invalid wait context", for
  example for a mutex taken under a spinlock.
- Static lock with no key: `assign_lock_key()` uses the address of the lock
  itself as the key.
- Per-CPU static lock: the key is the canonical address with the per-CPU
  offset removed, so the copies on all CPUs are one class.
- Trylock acquisition: `validate_chain()` records no "held lock -> new lock"
  edge for it and runs no recursion check.
- Lock held through a trylock: `check_prevs_add()` still uses it as the source
  of an edge to a lock taken later without trylock.
- First lock taken in a new irq context: `separate_irq_context()` makes it a
  chain head, so no edge is recorded from the locks of the interrupted
  context; the irq usage bits cover that case.

**Interrupt safety states**

- `kernel/locking/lockdep_states.h`: lists `HARDIRQ` and `SOFTIRQ` only;
  reclaim is not a state and has no usage bits.
- Usage characters: `get_usage_chars()` returns four, in the order hardirq
  write, hardirq read, softirq write, softirq read.
- `-{n:n}` after the usage characters: outer and inner wait type from
  `enum lockdep_wait_type`, printed by `print_lock_name()`; it is not irq
  state.
- `LOCK_ENABLED_*` bits: `mark_held_locks()` also sets them on every held lock
  with `check` set at the moment interrupts are enabled, not only on locks
  acquired with interrupts on.
- `LOCK_ENABLED_SOFTIRQ`: `mark_usage()` sets it only if hardirqs are on as
  well, so a class that is only ever held with hardirqs off never becomes
  softirq-unsafe.
- Trylock in interrupt context: `mark_usage()` sets no `LOCK_USED_IN_*` bit;
  it still sets the `LOCK_ENABLED_*` bits.
- Hardirq-enabled at acquire: `lock_acquire()` takes it from the CPU flags
  saved by `raw_local_irq_save()`; in-hardirq, in-softirq and
  softirq-enabled come from lockdep's own per-CPU and per-task state.
- Two-lock inversion: `check_irq_usage()` looks for any irq-safe class that
  reaches the held lock and any irq-unsafe class reachable from the new lock,
  so the two classes named in the report need not be the two being nested.
- Reports for one inversion:

  | Found when | Function | Heading |
  |---|---|---|
  | the edge is added | `check_irq_usage()` | "-safe -> -unsafe lock order detected" |
  | a usage bit is set later | `check_usage_forwards()`, `check_usage_backwards()` | "possible irq lock inversion dependency detected" |

- NMI: `verify_lock_unused()` reports a non-trylock acquire in NMI of a class
  that already has `LOCK_USED` set (or `LOCK_USED_READ`, for a write
  acquire), as "inconsistent {INITIAL USE} -> {IN-NMI} usage"; it keeps no
  usage bit for NMI.

**Subclasses and nest locks**

- Variants that end in _nested: two locks taken with the same subclass and
  held together are one class, and `check_deadlock()` reports "possible
  recursive locking detected".
- Variants that end in _nested, not checked: that a given instance gets the
  same subclass on every path; swapped instances with unswapped subclasses
  look identical to lockdep.
- Nest lock, what is checked: `__lock_acquire()` tests only that the current
  task holds the named lock, else "Nested lock was not taken".
- Nest lock, what is not checked: that the named lock excludes every other
  task that takes several locks of the class; `mm_take_all_locks()` in
  `mm/vma.c` names `mm->mmap_lock` and also takes `mm_all_locks_mutex`.
- Nest lock position: it must sit below the first held lock of the class in
  the held stack; `check_deadlock()` otherwise reports recursion.
- Nest lock with another lock of the class already held: `validate_chain()`
  skips `check_prevs_add()`, so that acquisition records no edge from any held
  lock, of any class.
- `lock_set_cmp_fn()`, when it runs: `cmp_fn` is tested only in
  `check_deadlock()` and `check_prev_add()`, which run only when the chain is
  not yet in the chain cache.
- `lock_set_cmp_fn()`, consequence: the chain key hashes class and read mode,
  not the instance, so once a chain of held classes has passed, a later
  nesting with the same chain in the wrong instance order is not compared.
- `cmp_fn` result of 0 or more: treated as not allowed; the report adds "and
  the lock comparison function returns".
- `lockdep_set_lock_cmp_fn()`: sets `cmp_fn` on one `struct lock_class`, so an
  acquisition with another subclass is not covered.
- `lock_set_cmp_fn()` without `CONFIG_PROVE_LOCKING`: expands to nothing.

**Subclass number limit**

- `spin_lock_nested()` or `mutex_lock_nested()` with a subclass of
  `MAX_LOCKDEP_SUBCLASSES` or more: `__lock_acquire()` hits
  `DEBUG_LOCKS_WARN_ON(subclass >= MAX_LOCKDEP_SUBCLASSES)` and returns before
  any class lookup.
- Log text on that path: the `DEBUG_LOCKS_WARN_ON()` warning, not "BUG:
  looking up invalid subclass".
- `DEBUG_LOCKS_WARN_ON()`: calls `debug_locks_off()`, so lockdep is off for
  the whole system from then on.
- "BUG: looking up invalid subclass": printed by `look_up_lock_class()`, which
  is reached with an unchecked subclass from `lockdep_init_map_type()` (for
  example `lockdep_set_subclass()`), `__lock_set_class()` and
  `verify_lock_unused()`.
- Without `CONFIG_DEBUG_LOCK_ALLOC`: the variants that end in _nested drop the
  subclass, so an out-of-range value is never seen; see
  `include/linux/spinlock.h` and `include/linux/mutex.h`.

**Lock pinning**

- Pin warnings: plain `WARN()`; they do not turn lockdep off and the release
  still happens.
- Wrong cookie: `__lock_unpin_lock()` warns "pin count corrupted" only if the
  cookie is larger than `pin_count`; a smaller wrong cookie leaves the entry
  pinned.
- `__lock_set_class()` and `__lock_downgrade()`: have no pin test;
  `reacquire_held_locks()` carries `pin_count` over.
- Entry that takes the pin: `__lock_pin_lock()` walks the held stack from the
  bottom and pins the first entry that `match_held_lock()` accepts.
- Entry with `references` set: `match_held_lock()` accepts any lock whose
  class equals the class of the entry, so pin, unpin and release of any
  instance of the class all act on that one entry.
- Entries merge only if the top of the held stack has the same class and a
  nest lock is passed; see `__lock_acquire()`.
- **Unsafe usage**: releasing any lock of the class while a held-lock entry
  shared through a nest lock is pinned; `__lock_release()` warns "releasing a
  pinned lock" before it drops `references`.
  - Safe: call `lockdep_unpin_lock()` with the cookie before any instance of
    the class is released, and `lockdep_repin_lock()` after.
  - Safe: pinning a lock that is never taken with a nest lock, so its entry
    matches one instance only, as `rq_pin_lock()` and `rq_unpin_lock()` in
    `kernel/sched/sched.h` do.
- **Unsafe usage**: releasing a lock that sits between two entries of the
  class in the held stack while the upper entry, taken with a nest lock, is
  pinned; `reacquire_held_locks()` merges the upper entry into the lower one
  and the merge path of `__lock_acquire()` drops its `pin_count`.
  - Safe: release in reverse order of acquisition while pinned, so
    `__lock_release()` returns before `reacquire_held_locks()`.

**Disabling lockdep checks**

- Reports that end validation: those that call `debug_locks_off()`, which
  includes every `DEBUG_LOCKS_WARN_ON()` and every table overflow.
- Reports that leave lockdep on: the held asserts (`WARN_ON()`), the pin
  warnings and `lockdep_rcu_suspicious()`; the first two can repeat,
  `RCU_LOCKDEP_WARN()` reports once per call site.
- After `debug_locks` is 0: `lock_acquire()` and `lock_release()` return at
  once, so the held-lock stack is frozen, not maintained.
- After `debug_locks` is 0: `lockdep_hardirqs_on()` and
  `lockdep_hardirqs_off()` return at once too, so irq state is no longer
  tracked.
- `rwsem_assert_held()` in a lockdep build after `debug_locks` is 0: checks
  nothing; it does not fall back to the count test.

| Call | Switched off | Still done |
|---|---|---|
| `lockdep_off()` | acquire, release, pin and softirq tracking for the task; held asserts pass; RCU lockdep checks | hardirq tracking, `lockdep_assert_irqs_disabled()`, `lockdep_assert_preemption_disabled()`, the NMI test in `verify_lock_unused()` |
| `lockdep_set_novalidate_class()` | dependency edges, recursion check, irq usage bits | held-stack entry, `check_wait_context()`, nest-lock test, unlock balance, held asserts |
| `lockdep_set_notrack_class()` | everything in `__lock_acquire()` and `lock_release()` | nothing; `lockdep_assert_held()` on the lock warns |

- `lockdep_off()`: raises `current->lockdep_recursion`, which stays with the
  task; the irq asserts test the per-CPU `lockdep_recursion` instead.
- `lockdep_set_notrack_class()`: has no caller in this tree.
- `lockdep_set_notrack_class()` on a lock the task holds: `lock_release()`
  returns early on the new key, so the held-stack entry is never removed.
- Class change on a held lock: use `lock_set_class()`, or
  `lock_set_novalidate_class()` as `device_lock_reset_class()` in
  `include/linux/device.h` does.
- **Unsafe usage**: a lock acquired on one side of `lockdep_off()` or
  `lockdep_on()` and released on the other.
  - Unsafe: acquired inside and released outside, `__lock_release()` finds no
    entry and reports "bad unlock balance detected".
  - Unsafe: acquired outside and released inside, the entry stays on the held
    stack.
  - Safe: acquire and release both inside the region, as `start_report()` and
    `end_report()` in `mm/kasan/report.c` do with `report_lock`;
    `lock_acquire()` and `lock_release()` both test `lockdep_enabled()`.

**fs_reclaim lockdep map**

- Map name: `__fs_reclaim_map` in `mm/page_alloc.c`; the class is printed as
  "fs_reclaim".
- `__need_reclaim()`: returns false without `__GFP_DIRECT_RECLAIM`, with
  `PF_MEMALLOC` set on the task, or with `__GFP_NOLOCKDEP`; nothing is
  recorded then.
- `__GFP_IO`: never tested by `fs_reclaim_acquire()`; there is no lockdep map
  for I/O.
- `memalloc_noio_save()`: has the same effect on lockdep as
  `memalloc_nofs_save()`, because `current_gfp_context()` strips `__GFP_FS`
  for both.
- `__mmu_notifier_invalidate_range_start_map`: with `CONFIG_MMU_NOTIFIER`,
  `fs_reclaim_acquire()` acquires and releases it for every allocation that
  passes `__need_reclaim()`, with or without `__GFP_FS`.
- `GFP_NOFS`, `GFP_NOIO` and the nofs and noio scopes: still record "held
  locks -> MMU notifier map"; they skip only `__fs_reclaim_map`.
- kswapd: `balance_pgdat()` calls `__fs_reclaim_acquire()` with no flag test.
- Direct reclaim and direct compaction: `__perform_reclaim()` and
  `__alloc_pages_direct_compact()` call `fs_reclaim_acquire(gfp_mask)`, so
  they hold the map only for an allocation with `__GFP_FS`.
- `fs_reclaim_acquire()` and `fs_reclaim_release()`: each re-reads the task
  flags, so `PF_MEMALLOC` or a nofs scope must not change between the two;
  `__perform_reclaim()` sets `PF_MEMALLOC` after the acquire and clears it
  before the release.

**Assertion helpers**

| Helper | Built under | Check when built | Otherwise |
|---|---|---|---|
| `lockdep_assert_held()` | `CONFIG_LOCKDEP` | `WARN_ON()` on every failing call unless the task has a matching held-lock entry, any mode | no run-time check |
| `lockdep_assert_held_write()` | `CONFIG_LOCKDEP` | as above, entry must have `read` 0 | no run-time check |
| `lockdep_assert_held_read()` | `CONFIG_LOCKDEP` | as above, entry must have `read` 1 or 2 | no run-time check |
| `lockdep_assert_not_held()` | `CONFIG_LOCKDEP` | `WARN_ON()` if an entry matches | nothing |
| `lockdep_assert_irqs_disabled()` | `CONFIG_PROVE_LOCKING` | `WARN_ON_ONCE()` if per-CPU `hardirqs_enabled` is set | nothing |
| `lockdep_assert_preemption_disabled()` | `CONFIG_PROVE_LOCKING` | `WARN_ON_ONCE()` if `preempt_count()` is 0 and `hardirqs_enabled` is set; nothing without `CONFIG_PREEMPT_COUNT` | nothing |
| `rwsem_assert_held()` | `CONFIG_LOCKDEP` | `lockdep_assert_held()` | `rwsem_assert_held_nolockdep()`: `WARN_ON()` if nobody holds it |
| `assert_spin_locked()` | every build | `BUG_ON()` if nobody holds it | nothing on UP without `CONFIG_DEBUG_SPINLOCK` |

- `CONFIG_LOCKDEP` without `CONFIG_PROVE_LOCKING` (for example
  `CONFIG_LOCK_STAT` alone): the held asserts check, the irq and preemption
  asserts are empty.
- `lockdep_assert_held()`, `lockdep_assert_held_write()` and
  `lockdep_assert_held_read()`: also expand `__assume_ctx_lock()` or
  `__assume_shared_ctx_lock()` in both builds, which tells the compiler's
  context analysis to assume the lock is held; see
  `include/linux/compiler-context-analysis.h`.
- `lockdep_assert_not_held()` and `lockdep_assert_held_once()`: do not expand
  `__assume_ctx_lock()`.
- Held-lock entry shared through a nest lock: `match_held_lock()` matches by
  class, so `lockdep_assert_held()` passes for any lock of that class, held or
  not.

**Documented lock orders**

- `Documentation/filesystems/locking.rst`: gives the locks held around each
  VFS method; it states no lock order.
- Inode lock order: `Documentation/filesystems/directory-locking.rst` and the
  comment above `enum inode_i_mutex_lock_class` in `include/linux/fs.h`.
- `fs/namespace.c`: has no lock-order block at the top of the file;
  `fs/dcache.c` ("Ordering:") and `fs/inode.c` ("Lock ordering:") do.
- `Documentation/mm/process_addrs.rst`, section "Lock ordering": reproduces
  the comments at the top of `mm/rmap.c` and `mm/filemap.c`.
- Scheduler: two "Lock order:" comments in `kernel/sched/core.c`, one above
  `raw_spin_rq_lock_nested()` and one above `find_proxy_task()` that adds
  `mutex->wait_lock` and `p->blocked_lock`.
- Networking: `Documentation/networking/netdevices.rst` says which of
  `rtnl_lock` and the instance lock is held for each operation.
- Netdev instance lock order: "take after rtnl_lock", and for queue leasing
  the virtual device's lock before the physical device's, are in the comment
  on `lock` in `struct net_device`, `include/linux/netdevice.h`.
- Two netdev instance locks of one lockdep class: `netdev_lock_cmp_fn()` in
  `include/net/netdev_lock.h` allows them together only under `rtnl_lock`;
  it is set only by `netdev_lockdep_set_classes()`, which gives each call
  site its own class.
- `double_rq_lock()`: orders by `rq_order_less()`, which compares CPU numbers
  (the core's CPU first under `CONFIG_SCHED_CORE`), not addresses.
- `double_rq_lock()`, same-object case: it compares `__rq_lockp()` of the two
  runqueues, since two runqueues can share one lock.
- `unix_state_double_lock()` in `net/unix/af_unix.c`: orders by address and
  uses plain lock calls; the annotation is `unix_state_lock_cmp_fn()` set on
  the class, not a subclass at the call site.

## Guards and annotations

**Guard class names**

- Naming: no rule is enforced; the class name is the first argument of the
  defining macro. Many classes keep `_lock` in the name, for example
  `read_lock`, `write_lock`, `local_lock`, `task_lock`, `mmap_read_lock`,
  `cpus_read_lock`, `console_lock`.
- `mutex`: defined with `DEFINE_LOCK_GUARD_1()` in `include/linux/mutex.h`,
  not with `DEFINE_GUARD()`; its class type is a struct with a `lock` member.
- Generated typedefs: `class_##_name##_t` and `lock_##_name##_t` (the lock
  type); there is no lock_guard_ struct.
- Killable suffix: `_kill`, defined for `mutex_kill` and `rwsem_write_kill`
  only.
- rwsem conditional classes: read has `_try` and `_intr`; write has `_try`
  and `_kill`.
- rwlock classes (`read_lock`, `write_lock` and their irq forms): no
  conditional forms.
- Suffix is free-form: for example `_try_enabled` in
  `include/linux/pm_runtime.h`, `_try_direct` in `include/linux/iio/iio.h`.
- `DEFINE_GUARD_COND()` and `DEFINE_LOCK_GUARD_1_COND()`: optional fourth
  argument is the success test on `_RET`; with three arguments success is
  `_RET` non-zero (trylock style); errno-style lock functions pass
  `_RET == 0`.
- `_init` classes (`mutex_init`, `spinlock_init`, `raw_spinlock_init`,
  `rwlock_init`, `rwsem_init`, `seqlock_init`, `local_lock_init`,
  `local_trylock_init`): the constructor initialises the lock, the destructor
  is empty; they take no lock and exist so context analysis treats guarded
  members as accessible during initialisation.
- Context analysis companion: a `DEFINE_LOCK_GUARD_1()` class is visible to
  the analysis only if it also has `DECLARE_LOCK_GUARD_1_ATTRS()` and a
  `#define` of its constructor to `WITH_LOCK_GUARD_1_ATTRS()`; a
  `DEFINE_LOCK_GUARD_0()` class needs only `DECLARE_LOCK_GUARD_0_ATTRS()`, as
  `rcu` has; each conditional class needs its own pair under its full name,
  as for `mutex_try` in `include/linux/mutex.h`.
- `cpus_read_lock`: defined in `include/linux/cpuhplock.h`.
- `migrate`: defined in `include/linux/sched.h`.
- Definition sites outside `include/linux/`: `.c` files and private headers
  define classes too, for example `core_lock` in `kernel/sched/core.c`;
  search for the `DEFINE_` macro names.
- `DEFINE_LOCK_GUARD_2()`: exists only in `kernel/sched/sched.h`.

**Scope-based lock guards**

- `scoped_cond_guard()`: present in `include/linux/cleanup.h`; only for
  conditional classes, its fail branch holds
  `BUILD_BUG_ON(!__is_cond_ptr(_name))`.
- `scoped_cond_guard()` whose fail statement does not leave (an assignment):
  the body is skipped and execution continues after the block, as in
  `margining_eye_write()` in `drivers/thunderbolt/debugfs.c`.
- `ACQUIRE_ERR()` on failure: returns `-EBUSY` when the class uses the
  default success test (for example `mutex_try`); for classes defined with
  `_RET == 0` it returns the negative errno that the lock function returned.
- Networking code: `Documentation/process/maintainer-netdev.rst` discourages
  `guard()` in a function longer than 20 lines, prefers `scoped_guard()`, and
  weakly prefers plain lock and unlock over both.

**Guard hazards**

- **Potentially unsafe usage**: `goto` in a function that uses `guard()`.
  - Unsafe: when the `goto` is before the `guard()` and its label is after it
    in the same scope; the jump skips the constructor and the destructor
    still runs at scope exit.
  - Safe: when the `guard()` comes before every `goto`, as in
    `stat_seq_init()` in `kernel/trace/trace_stat.c`.
  - Safe: when the lock is taken with `scoped_guard()` or
    `scoped_cond_guard()` and the labels are outside its body, as in
    `input_register_device()`.
- `goto` and cleanup helpers: the comment in `include/linux/cleanup.h` states
  "never mixed" as an expectation; `scripts/checkpatch.pl` has no test for
  it.
- **Unsafe usage**: `guard()` with a conditional class (suffix such as
  `_try`, `_intr`, `_kill`); the result is not tested and the code runs
  without the lock.
  - Safe: `scoped_cond_guard()`, as in `input_register_device()`, or
    `ACQUIRE()` followed by a test of `ACQUIRE_ERR()`, as in
    `drivers/pci/tsm.c`; `guard()` is "not recommended for conditional locks"
    in `include/linux/cleanup.h`.
- **Potentially unsafe usage**: `scoped_guard()` with a conditional class.
  - Unsafe: when the code after the block assumes the body ran.
  - Safe: when the body returns and the code after the block is the failure
    path, as in `margining_eye_show()` in `drivers/thunderbolt/debugfs.c`.
  - Safe: when skipping the body is the intended result of a failed trylock
    and the code after the block is right either way, as in
    `tsc200x_esd_work()`.
- **Potentially unsafe usage**: `break` or `continue` inside
  `scoped_guard()` or `scoped_cond_guard()`.
  - Unsafe: when it is meant for an enclosing loop or `switch`; both only
    leave the guard, because the macro is a `for` loop.
  - Safe: when it is meant to leave the guard early, as in
    `try_to_wake_up()` and `get_modules_for_addrs()`.
- **Potentially unsafe usage**: a `__free()` variable declared `= NULL`
  before a `guard()` in the same scope.
  - Unsafe: when the cleanup function needs the lock; it runs after the
    unlock, since cleanup is in reverse order of declaration.
  - Safe: when the cleanup needs no lock, such as `kfree()` in
    `osnoise_cpus_read()`.
  - Safe: `guard()` first, then declare and initialise the `__free()`
    variable in one statement, as the comment in `include/linux/cleanup.h`
    shows.
- **Unsafe usage**: `guard()` directly under a `case` label without braces;
  `guard()` is a declaration and its scope would run over the later cases.
  - Safe: `case X: { guard(...)(...); ... }`, as in `adxl367_read_raw()`.
- **Unsafe usage**: a lock argument with side effects, for a class whose
  constructor is defined to `WITH_LOCK_GUARD_1_ATTRS()` (for example `mutex`
  and `spinlock`; search for the macro name); the macro evaluates the
  argument twice.
  - Safe: an address expression such as `&obj->lock`.
  - Safe: a getter without side effects, such as `pf_migration_mutex()` in
    `drivers/gpu/drm/xe/xe_sriov_packet.c`.
- Context analysis and conditional classes: where a conditional class has
  `DECLARE_LOCK_GUARD_1_ATTRS()`, its constructor is declared
  `__acquires(_T)` or `__acquires_shared(_T)`, not `__cond_acquires()`, so
  the compiler is told the lock is held even when acquisition failed; it does
  not replace the `ACQUIRE_ERR()` test.
- `return expr;` under a guard: `expr` is evaluated before the destructor
  runs; `return_ptr()` in `include/linux/cleanup.h` relies on this order.

**Compiler context analysis**

- Compiler: Clang 23 or later; `CONFIG_WARN_CONTEXT_ANALYSIS` in
  `lib/Kconfig.debug` has `depends on CC_IS_CLANG && CLANG_VERSION >= 230000`.
- `CONFIG_WARN_CONTEXT_ANALYSIS`: `default y`, and also depends on
  `!TRACE_BRANCH_PROFILING`.
- Opt-in: `CONTEXT_ANALYSIS := y` in the Makefile of a directory, or per
  object, for example `CONTEXT_ANALYSIS_mutex.o := y` in
  `kernel/locking/Makefile`; search Makefiles for `CONTEXT_ANALYSIS` to see
  what is opted in.
- File not opted in: `WARN_CONTEXT_ANALYSIS` is not defined, so every
  annotation in `include/linux/compiler-context-analysis.h` expands to
  nothing; no attribute reaches the compiler.
- File opted in: gets `CFLAGS_CONTEXT_ANALYSIS` from
  `scripts/Makefile.context-analysis`, which defines `WARN_CONTEXT_ANALYSIS`
  and enables `-Wthread-safety`, `-Wthread-safety-pointer` and
  `-Wthread-safety-beta`.
- Headers in an opted-in file: warnings located in `include/linux/`,
  `include/net/`, `include/acpi/`, `include/asm-generic/` and arch include
  directories are suppressed by `scripts/context-analysis-suppression.txt`,
  except the headers that file lists with `=emit`.
- Opt-out: a value of the same Makefile variables starting with `n` works;
  see the `patsubst` in `scripts/Makefile.lib`. Per-file `n` overrides
  directory `y`; per-file `y` overrides directory `n`; directory `n`
  overrides `CONFIG_WARN_CONTEXT_ANALYSIS_ALL`.
- `CONFIG_WARN_CONTEXT_ANALYSIS_ALL`: depends on `EXPERT && !COMPILE_TEST`,
  applies only where `is-kernel-object` is set, and drops the suppression
  file.

**Annotation keywords**

- Sparse: checks none of these; under `__CHECKER__` (and `__GENKSYMS__`)
  every annotation in `include/linux/compiler-context-analysis.h` is empty,
  and `__acquire()` and `__release()` are empty statements.
- Clang context analysis: the only tool in this tree that reads them, and
  only in a file that is opted in.
- Build without the analysis: the preprocessor discards the annotation
  arguments, so a wrong lock expression is not even parsed.
- `__cond_acquires()` and `__cond_acquires_shared()`: the first argument is
  pasted into a macro name and must be one of the tokens `true`, `false`,
  `nonzero`, `0`, `nonnull`, `NULL`; any other token breaks the build in
  every configuration.
- `__cond_acquires()` in use: `true` for trylock-style functions, `0` for
  errno-style ones such as `mutex_lock_interruptible()`.
- `__guarded_by()` and `__pt_guarded_by()`: accept several locks; reading
  under any one of them and writing under all of them is accepted, see
  `test_mutex_multiguard()` in `lib/test_context-analysis.c`.
- Function that needs the lock only on some paths: use
  `lockdep_assert_held()`, `lockdep_assert_held_write()` or
  `lockdep_assert_held_read()` in the body instead of `__must_hold()`; they
  expand to `__assume_ctx_lock()` or `__assume_shared_ctx_lock()`.

## Reference counts and object lifetime

**Reference count types**

- `rcuref_t`, get after the last put: fails only once the count is
  `RCUREF_DEAD`. The last put leaves `RCUREF_NOREF` and
  `rcuref_put_slowpath()` in `lib/rcuref.c` then tries to mark it dead; a
  `rcuref_get()` in that window succeeds, and the put returns false if the
  count is no longer `RCUREF_NOREF`.
- `rcuref_t`, overflow: `rcuref_get_slowpath()` sets `RCUREF_SATURATED`, warns
  once and returns true; the object is leaked.
- `rcuref_t`, memory: a failed `rcuref_get()` still writes the counter, so an
  object that a `rcuref_get()` can still reach has to be freed through RCU
  after `rcuref_put()` returns true.
- `rcuref_put()`: does `preempt_disable()` itself. `rcuref_put_rcusafe()`
  does not; under `CONFIG_PROVE_RCU` `__rcuref_put()` warns unless the caller
  is in `rcu_read_lock()` or not preemptible. `rcuref_get()` asserts nothing.
- `percpu_ref_tryget()`: fails only when the ref is in atomic mode and the
  count is zero. After `percpu_ref_kill()` it still succeeds while other
  references remain.
- `percpu_ref_tryget_live()`: certain to fail only after the callback given to
  `percpu_ref_kill_and_confirm()` has run; return of `percpu_ref_kill()` is
  not enough.
- `struct percpu_ref`, overflow: `atomic_long_t` plus `unsigned long` per-CPU
  counters, 32 bits wide on a 32-bit kernel; no get tests for overflow or
  saturates.
- `struct percpu_ref`, lookup: every get and put needs the ref to be between
  `percpu_ref_init()` and `percpu_ref_exit()`, and `percpu_ref_kill()` implies
  no grace period before the release callback. A lookup under RCU needs the
  containing object freed through RCU by its user, as `fs/aio.c` does.
- `struct lockref`: `lockref_get_not_zero()` fails at count `<= 0`;
  `lockref_get_not_dead()` fails only at count `< 0`, so it takes a
  reference on a live object whose count is 0.

**Decrement and lock helpers**

- `refcount_dec_and_lock()` returning false: the count was not always
  decremented. `refcount_dec_not_one()` in `lib/refcount.c` leaves a count of
  `REFCOUNT_SATURATED` or 0 unchanged and the helper returns false.
- False from the slow path: the count was 1 when sampled, the lock was taken,
  the decrement did not reach zero, and the lock was dropped again. The
  caller sees no difference from the fast path.
- `atomic_dec_and_lock()`: a function in `lib/dec_and_lock.c`, not a macro.
  Only `atomic_dec_and_lock_irqsave()` and `atomic_dec_and_raw_lock_irqsave()`
  are macros, in `include/linux/spinlock.h`.
- **Potentially unsafe usage**: a lookup under the lock passed to
  `refcount_dec_and_lock()` that takes a plain `refcount_inc()` on what it
  finds.
  - Unsafe: when the releaser unlocks before it unlinks the object; the
    lookup then finds a zero count, and `refcount_inc()` warns and saturates.
  - Safe: when the releaser unlinks before it unlocks, as `free_uid()` does
    through `free_user()` in `kernel/user.c` (with
    `refcount_dec_and_lock_irqsave()`), with `uid_hash_find()` as the lookup.
    The helper only promises that the 1 to 0 transition happens with the lock
    held; `kref_put_lock()` in `include/linux/kref.h` calls `release` with
    the lock held.

**Reference count ordering**

- A lookup needs more than the control dependency of
  `refcount_inc_not_zero()` when the memory can be reused for another object
  while the reader holds the pointer, as with `SLAB_TYPESAFE_BY_RCU`. The
  identity check after the increment is a load, which the control dependency
  does not order.
- For that case: `refcount_inc_not_zero_acquire()` or
  `refcount_add_not_zero_acquire()` on the reader side, paired with
  `refcount_set_release()` after the new object is fully initialised. All
  three are in `include/linux/refcount.h`.
- After `refcount_set_release()` on memory that can be reused: the object
  counts as visible to other tasks even before it is linked anywhere, because
  a reader may still hold the address from the previous object.
- In-tree pair: `vma_mark_attached()` in `include/linux/mmap_lock.h` uses
  `refcount_set_release()` on `vma->vm_refcnt`; the RCU reader
  `vma_start_read()` in `mm/mmap_lock.c` uses
  `__refcount_inc_not_zero_limited_acquire()`.

**Keeping an object alive**

- **Potentially unsafe usage**: an unconditional get (`refcount_inc()`,
  `kref_get()`) on an object found under `rcu_read_lock()`.
  - Unsafe: when the last reference can be dropped before the grace period,
    with only the free deferred. The reader can then find a zero count;
    `refcount_inc()` warns and saturates.
  - Safe: when a reference is itself dropped only from an RCU callback after
    the object is unpublished. `get_pid_task()` and
    `find_get_task_by_vpid()` in `kernel/pid.c` call `get_task_struct()`;
    `put_task_struct_rcu_user()` in `kernel/exit.c` defers `put_task_struct()`
    to `delayed_put_task_struct()` through `call_rcu()`, and `release_task()`
    calls it after `__exit_signal()` has unhashed the task.
- Conditional get, then identity re-check: `__inet_lookup_established()` in
  `net/ipv4/inet_hashtables.c`, `__fget_files_rcu()` in `fs/file.c`
  (`file_ref_get()`), `filemap_get_entry()` in `mm/filemap.c`.
- `igrab()` in `fs/inode.c`: tries `atomic_add_unless(&inode->i_count, 1, 0)`
  first; only on failure does it take `inode->i_lock` and test `I_FREEING`
  and `I_WILL_FREE`.
- `kfree_rcu()` release that a reader inside its section survives:
  `netif_set_alias()` in `net/core/dev.c`, read by `dev_get_alias()`.
  `dev_set_alias()` is a wrapper in `net/core/dev_api.c`.
- `kfree_rcu()` member type: `struct rcu_head` or `struct kvfree_rcu_head`
  (`include/linux/types.h`); `kvfree_rcu_arg_2()` in
  `include/linux/rcupdate.h` casts either.

**Dropping and retaking a lock**

- There is no pipe_read() here; `anon_pipe_read()` in `fs/pipe.c` does that.
  It drops `pipe->mutex` to wait, and after retaking it reads `pipe->head` and
  `pipe->tail` again at the top of its loop.
- `find_lock_lowest_rq()` in `kernel/sched/rt.c`: re-checks the task only when
  `double_lock_balance()` returns nonzero, which is its report that it
  dropped the lock.
- The re-check there fails on `is_migration_disabled(task)`, on
  `lowest_rq->cpu` not in `task->cpus_mask`, or on
  `task != pick_next_pushable_task(rq)`. On failure it unlocks `lowest_rq`
  with `double_unlock_balance()` and gives up; `rq` stays locked.
- `find_inode()` in `fs/inode.c`: `__wait_on_freeing_inode()` drops
  `inode->i_lock`, the RCU read lock and, if held, `inode_hash_lock`; after
  it returns, `find_inode()` restarts the hash chain walk from the head.

**Checking before locking**

- `list_empty_careful()` on the removed entry returning true: everything the
  remover wrote before `list_del_init_careful()` is visible to the caller.
  The `smp_load_acquire()` of `head->next` pairs with the
  `smp_store_release()` in `list_del_init_careful()`, both in
  `include/linux/list.h`.
- With plain `list_del_init()` on the other side there is no such ordering;
  only the two-pointer test remains.
- **Potentially unsafe usage**: acting under the lock on the result of an
  unlocked test, without testing again.
  - Unsafe: when the action is wrong if the state changed between the test
    and the lock.
  - Safe: when the locked action is harmless in either state. `finish_wait()`
    in `kernel/sched/wait.c` takes `wq_head->lock` and calls
    `list_del_init()`, which leaves an already removed entry self-linked.
- Check, lock, re-check: `pte_alloc()` in `include/linux/mm.h` tests
  `pmd_none()` unlocked; `pmd_install()` in `mm/memory.c` tests it again
  under `pmd_lock()`, and `__pte_alloc()` frees the unused table.
- `list_empty_careful()` skipping the lock: `finish_wait()` with
  `autoremove_wake_function()`, which removes the entry with
  `list_del_init_careful()`.

**Cancelling timers and work items**

- There is no del_timer_sync() here; `timer_delete_sync()` in
  `kernel/time/timer.c` does that.
- `timer_delete_sync()` and a handler that re-arms itself with `mod_timer()`:
  handled. On return the timer is not pending and not running; only other
  code can arm it afterwards.
- **Unsafe usage**: a timer handler that calls `add_timer_on()` on its own
  timer, when the timer is stopped with `timer_delete_sync()`.
  `add_timer_on()` changes the base of the timer without testing
  `base->running_timer`, so the wait on `base->running_timer` can miss the
  running handler.
  - Safe: re-arm from the handler with `mod_timer()`; `__mod_timer()` keeps
    the base while `base->running_timer == timer`.
- Context of `timer_delete_sync()` and `timer_shutdown_sync()`:
  `__timer_delete_sync()` warns in `in_hardirq()` unless the timer is
  `TIMER_IRQSAFE`. On `CONFIG_PREEMPT_RT` a timer that is not `TIMER_IRQSAFE`
  also needs preemption enabled.
- After `timer_shutdown_sync()`: the timer has to be initialised again before
  it can be used.
- Context of `cancel_work_sync()`, `disable_work_sync()` and the delayed
  forms: sleepable if the item was last queued on a non-BH workqueue. If it
  was last queued on a `WQ_BH` workqueue, atomic context except hardirq, with
  interrupts enabled: `start_flush_work()` uses `raw_spin_lock_irq()` and
  `raw_spin_unlock_irq()`. On `CONFIG_PREEMPT_RT` the wait in
  `__flush_work()` also takes the `spinlock_t` `cb_lock` of the pool, so
  preemption must be enabled there too. See `__cancel_work_sync()` in
  `kernel/workqueue.c`.
- `cancel_work_sync()` while it runs: the item is disabled, so a concurrent
  `queue_work()` returns false and the request is dropped. `enable_work()`
  runs before return, so later queueing succeeds.
- **Unsafe usage**: `cancel_work_sync()` on the `work` member of a
  `struct delayed_work` whose timer is pending. The timer is not deleted, and
  `work_grab_pending()` spins on `-EAGAIN` from `try_to_grab_pending()` until
  the timer has fired.
  - Safe: `cancel_delayed_work_sync()`, which passes `WORK_CANCEL_DELAYED`.
  - Safe: when the timer cannot be pending, as in
    `ip_vs_control_net_cleanup_sysctl()` in `net/netfilter/ipvs/ip_vs_ctl.c`,
    which calls it right after `cancel_delayed_work_sync()` on the same item
    and nothing queues the item again; `try_to_grab_pending()` then claims
    `WORK_STRUCT_PENDING_BIT` at once.

**RCU callbacks and interrupt handlers**

- `rcu_barrier()` in `kernel/rcu/tree.c`: sleeps on
  `rcu_state.barrier_mutex` and a completion. It does not take
  `cpus_read_lock()`.
- `rcu_barrier()` and `kfree_rcu()`: with `CONFIG_KVFREE_RCU_BATCHED`
  (default y, off with `CONFIG_TINY_RCU`, `CONFIG_SLUB_TINY` or
  `CONFIG_RCU_STRICT_GRACE_PERIOD`) the objects are batched in
  `mm/slab_common.c` and not queued with `call_rcu()` one by one;
  `rcu_barrier()` does not wait for them, `kvfree_rcu_barrier()` and
  `kvfree_rcu_barrier_on_cache()` do. Without it `kvfree_call_rcu()` uses
  `call_rcu()` and `kvfree_rcu_barrier()` calls `rcu_barrier()`.
- `kmem_cache_destroy()`: calls `kvfree_rcu_barrier_on_cache()` itself, so
  pending `kfree_rcu()` objects of that cache need no barrier from the
  caller.
- Callbacks queued with `call_rcu()` that call `kmem_cache_free()`:
  `kvfree_rcu_barrier_on_cache()` also calls `rcu_barrier()` in both
  configurations; in-tree callers still run `rcu_barrier()` themselves before
  `kmem_cache_destroy()`, for example `destroy_inodecache()` in
  `fs/ext4/super.c`.
- `kfree_rcu_mightsleep()`: when it cannot batch the pointer it calls
  `synchronize_rcu()` and `kvfree()` before it returns; no barrier covers a
  call that has not returned yet.

**Per-CPU state and hotplug callbacks**

- **Unsafe usage**: `migrate_disable()` as the only protection for a sleeping
  user of state torn down at `CPUHP_AP_ONLINE_DYN`. On the way down that
  teardown runs before `sched_cpu_wait_empty()` at
  `CPUHP_AP_SCHED_WAIT_EMPTY`, which is the step that waits for pinned
  tasks.
  - Safe: `cpus_read_lock()` around the use; `_cpu_down()` in `kernel/cpu.c`
    takes `cpus_write_lock()` before any teardown runs.
  - Safe: state that hotplug never tears down. `mm/zswap.c` registers
    `zswap_cpu_comp_prepare()` with a NULL teardown, so `zswap_compress()` can
    sleep on `acomp_ctx->mutex`; `zswap_pool_destroy()` calls
    `acomp_ctx_free()` only after `cpuhp_state_remove_instance()`.
- Where a callback runs: for states above `CPUHP_TEARDOWN_CPU`, such as
  `CPUHP_AP_ONLINE_DYN`, in `cpuhp_thread_fun()` on the CPU itself; for
  states up to `CPUHP_BRINGUP_CPU`, such as `CPUHP_BP_PREPARE_DYN`, on the CPU
  that controls the operation. See `cpuhp_is_ap_state()`.
- `preempt_disable()` for a non-sleeping local user: enough only where the
  callbacks run on the CPU itself; not for states up to `CPUHP_BRINGUP_CPU`.
- `cpuhp_setup_state()` startup calls: made for each present CPU whose
  hotplug state has reached the new state. For states that run on the CPU
  itself `cpuhp_invoke_ap_callback()` skips a CPU that is not online.
- Return value: the allocated state number, positive, for both
  `CPUHP_AP_ONLINE_DYN` and `CPUHP_BP_PREPARE_DYN`; 0 for a fixed state.

## Memory ordering

**Ordering of atomic operations**

- `atomic_dec_and_test()`, `atomic_sub_and_test()`, `atomic_inc_and_test()`,
  `atomic_add_negative()`: not conditional; they always perform the RMW and
  are fully ordered whatever they return.
- Conditional ops (unordered when they do not store): the generated kerneldoc
  in `include/linux/atomic/atomic-arch-fallback.h` marks each one with
  "relaxed ordering is provided" for the case where `@v` is not modified; for
  example `raw_atomic_add_unless()`, `raw_atomic_inc_not_zero()`,
  `raw_atomic_try_cmpxchg()`.
- "Unordered" in `Documentation/atomic_t.txt`: unordered against other memory
  locations; address dependencies from the value read still hold.
- Bitops are sorted by `Documentation/atomic_bitops.txt`, not
  `Documentation/atomic_t.txt`, and the conditional rule differs: conditional
  RMW bitops are fully ordered.
- `test_and_set_bit()` on an already-set bit: still fully ordered; the generic
  `arch_test_and_set_bit()` in `include/asm-generic/bitops/atomic.h` always
  does `raw_atomic_long_fetch_or()`.
- `test_and_set_bit_lock()`: ACQUIRE only when it sets the bit; the generic
  version in `include/asm-generic/bitops/lock.h` returns after a `READ_ONCE()`
  when the bit is already set.

**Publishing initialised data**

- `READ_ONCE()` gives the reader the same ordering as `rcu_dereference()`:
  `__rcu_dereference_check()` in `include/linux/rcupdate.h` is `READ_ONCE()`
  plus `RCU_LOCKDEP_WARN()` and `rcu_check_sparse()`, nothing stronger.
- `READ_ONCE()` instead of `rcu_dereference()`: allowed by
  `Documentation/RCU/rcu_dereference.rst` only where data is added but never
  removed while readers access the structure.
- There is no smp_read_barrier_depends() macro here; Alpha's `__READ_ONCE()`
  in `arch/alpha/include/asm/rwonce.h` contains `mb()` under `CONFIG_SMP`.
- Documents, and what each says:
  - `Documentation/RCU/rcu_dereference.rst`: the `READ_ONCE()` case above, and
    the rules that keep the compiler from breaking the dependency (comparison
    with NULL is safe; with another non-NULL address it is not, with listed
    exceptions).
  - `Documentation/memory-barriers.txt`, item "(2) Address-dependency barriers
    (historical)" and section "ADDRESS-DEPENDENCY BARRIERS (HISTORICAL)":
    `READ_ONCE()` and `rcu_dereference()` provide the implicit
    address-dependency barrier; both defer to
    `Documentation/RCU/rcu_dereference.rst`.
  - `tools/memory-model/Documentation/explanation.txt`, "AND THEN THERE WAS
    ALPHA": a plain load of the pointer is not ordered; a `READ_ONCE()` is.
  - `tools/memory-model/Documentation/control-dependencies.txt`: a control
    dependency does not order a later load.
- **Potentially unsafe usage**: storing the pointer with `RCU_INIT_POINTER()`,
  which is `WRITE_ONCE()` with no release ordering.
  - Unsafe: when readers can already load the pointer and the object has
    reader-visible stores since it was last published; readers may see the
    fields from before initialisation.
  - Safe: storing NULL, as `swevent_hlist_release()` in
    `kernel/events/core.c` does; `rcu_assign_pointer()` itself uses
    `WRITE_ONCE()` for a constant NULL.
  - Safe: when the structure that holds the pointer is not yet reachable by
    readers, as `copy_sighand()` in `kernel/fork.c` does for a task that
    `copy_process()` has not linked yet; the kerneldoc above
    `RCU_INIT_POINTER()` in `include/linux/rcupdate.h` lists the cases.

**Sleeping and waking**

- `set_current_state()`: `smp_store_mb()` on `current->__state`; it pairs with
  `smp_mb__after_spinlock()` after `p->pi_lock` is taken in
  `try_to_wake_up()` in `kernel/sched/core.c`, which runs before
  `ttwu_state_match()` reads `p->__state`.
- `try_to_wake_up()` with `p == current`: takes no `pi_lock` and executes no
  `smp_mb__after_spinlock()`; it relies on program order.
- The pairing orders only the state against the condition; data stored before
  the condition needs its own `smp_wmb()` and `smp_rmb()` (or release and
  acquire) when the sleeper sees the condition without sleeping; see "SLEEP
  AND WAKE-UP FUNCTIONS" in `Documentation/memory-barriers.txt`.
- `prepare_to_wait()`, `prepare_to_wait_exclusive()`,
  `prepare_to_wait_event()`: call `set_current_state()`, not
  `__set_current_state()`, although they hold `wq_head->lock`; the caller
  tests the condition after the unlock, and an unlock does not stop that load
  moving up.
- **Potentially unsafe usage**: `__set_current_state()` with a sleeping state
  before the condition test.
  - Unsafe: when the condition is tested outside the lock under which the
    state was stored, or the waker changes the condition without that lock.
  - Safe: state store and condition test are in one critical section of a
    lock, and the waker changes the condition under that lock, as
    `___down_common()` and `__up()` do with `sem->lock` in
    `kernel/locking/semaphore.c`; the wakeup may follow the unlock, as in
    `up()`.
  - Safe: no condition, only a timeout, as `schedule_timeout_interruptible()`
    in `kernel/time/sleep_timeout.c`.
- **Potentially unsafe usage**: testing the condition before storing the
  state.
  - Unsafe: when the waker can set the condition and call the wakeup between
    the test and the state store; the wakeup finds `TASK_RUNNING` and is lost.
  - Safe: test and state store are under the lock that the waker holds to
    change the condition, as in `___down_common()`.
  - Safe: the condition is a pending signal and the state is one that
    `signal_pending_state()` honours, as `sigsuspend()` in `kernel/signal.c`;
    `__schedule()` executes `smp_mb__after_spinlock()` after `rq_lock()` and
    `try_to_block_task()` tests `signal_pending_state()` again.
- **Potentially unsafe usage**: a condition test that can block (takes a
  mutex, allocates with `GFP_KERNEL`) between `set_current_state()` and
  `schedule()`.
  - Unsafe: when the call blocks often; it returns in `TASK_RUNNING`, so
    `schedule()` does not block and the loop spins; `__might_sleep()` warns
    under `CONFIG_DEBUG_ATOMIC_SLEEP`.
  - Safe: the block is rare and an extra loop pass is harmless, annotated with
    `sched_annotate_sleep()`, as `resolve_symbol()` in `kernel/module/main.c`.
  - Safe: `wait_woken()` with `woken_wake_function()` in
    `kernel/sched/wait.c`; the condition is tested in `TASK_RUNNING` and
    `WQ_FLAG_WOKEN` carries the wakeup.

**Marked accesses and data races**

- `data_race()` cases in
  `tools/memory-model/Documentation/access-marking.txt`, all four:
  - diagnostic reads;
  - reads whose value is checked against a later marked load, such as the
    seed of a `cmpxchg()` loop;
  - reads that feed error-tolerant heuristics;
  - writes that set values feeding error-tolerant heuristics.
- Lock-protected writes whose only lockless readers are diagnostic: the
  writes stay plain and the read uses `data_race()`; `WRITE_ONCE()` on the
  writer is for lockless readers that the algorithm depends on.
- `data_race(READ_ONCE(x))`: not redundant; `READ_ONCE()` restricts the
  compiler, `data_race()` stops KCSAN reporting the read against plain
  lock-protected writes.
- Asking to replace `data_race()` by `READ_ONCE()` on a diagnostic read is
  wrong when the writers are plain under a lock: KCSAN then reports the read
  wherever the plain write is not assumed atomic (see the last bullet), and
  marking the writers to quiet it hides buggy lockless accesses.
- `data_race()` on a heuristic read: only where something else, such as
  `barrier()` or a lock acquisition, forces a reload; if any possible bogus
  value could break the heuristic, use `READ_ONCE()`.
- `__data_racy`: `volatile` under `CONFIG_KCSAN`, empty otherwise
  (`include/linux/compiler_types.h`); in a non-KCSAN build it gives no
  protection against tearing or fusing.
- `ASSERT_EXCLUSIVE_WRITER()`: does not replace a marking; with lockless
  readers the write stays `WRITE_ONCE()` and the assertion sits beside it, to
  catch a second writer even if that writer is marked.
- `ASSERT_EXCLUSIVE_ACCESS()`: goes with plain accesses, such as
  single-threaded initialisation or after the last reference is dropped; it
  reports a concurrent access even if that access is marked.
- Plain writes and KCSAN in a default build: `is_atomic()` in
  `kernel/kcsan/core.c` treats aligned, non-compound plain writes up to word
  size as atomic under `CONFIG_KCSAN_ASSUME_PLAIN_WRITES_ATOMIC` (default y
  unless `CONFIG_KCSAN_STRICT`), so a race of such a write with another such
  write or with a marked read is not reported; an assertion is never treated
  as atomic and still catches it.

## Sequence counters

**Sequence counter types**

- Lock-associated types: four, generated by `SEQCOUNT_LOCKNAME()`:
  `seqcount_raw_spinlock_t`, `seqcount_spinlock_t`, `seqcount_rwlock_t`,
  `seqcount_mutex_t`.
- There is no seqcount_ww_mutex_t type; only the initializer macro
  `SEQCNT_WW_MUTEX_ZERO()` and a line in `Documentation/locking/seqlock.rst`
  mention it.
- `seqcount_latch_t`: defined in `include/linux/seqlock.h`, not in
  `include/linux/seqlock_types.h`.
- `lock` member of the associated types: exists only with `CONFIG_LOCKDEP` or
  `CONFIG_PREEMPT_RT`, see `__SEQ_LOCK()`; with neither, the only effect left
  is the `preempt_disable()` for `seqcount_mutex_t` writers.
- Behaviour is selected by `_Generic` on the static type of the pointer, in
  `__seqprop()`; passing the inner `seqcount_t` of an associated type gets
  plain `seqcount_t` behaviour: no held-lock assert, no RT lock wait.
- PREEMPT_RT, writer: `seqprop_preemptible()` returns false for every type,
  so `seqcount_mutex_t` writers also stay preemptible, like spinlock and
  rwlock ones.
- PREEMPT_RT, reader: for the spinlock, rwlock and mutex types and for
  `seqlock_t`, an odd count makes the reader acquire and release the
  associated lock, so the reader can block.
- `seqcount_raw_spinlock_t` and `seqcount_t` readers never take a lock; for
  example `tk_core.seq` and `jiffies_seq` are `seqcount_raw_spinlock_t`.
- Latch writers: use `write_seqcount_latch_begin()`, `write_seqcount_latch()`,
  `write_seqcount_latch_end()`; `raw_write_seqcount_latch()` has no caller
  outside `include/linux/seqlock.h`.

**Reader variants**

| Form | What this tree does |
|---|---|
| `read_seqcount_begin()` | Ordering comes from `smp_load_acquire()` in `seqprop_sequence()`, not from `smp_rmb()`; `smp_rmb()` is on the retry side, in `do_read_seqcount_retry()`. |
| `raw_read_seqcount_begin()` | Is `__read_seqcount_begin()`: waits for even, has the acquire load. Differs from `read_seqcount_begin()` only by `seqcount_lockdep_reader_access()`, which exists under `CONFIG_DEBUG_LOCK_ALLOC`. Used in ordinary code, for example `hrtimer_active()`. |
| `raw_read_seqcount()` | Returns the count as read, possibly odd. On PREEMPT_RT with a spinlock, rwlock or mutex type it first locks and unlocks the associated lock when the count is odd, so it can block. |
| `raw_seqcount_try_begin()` | Is `raw_read_seqcount()` plus the odd test, so it has the same PREEMPT_RT lock wait before it returns false. |
| `scoped_seqlock_read()` | First pass is always lockless. Target `ss_lockless`: retries lockless without bound. Target `ss_lock` or `ss_lock_irqsave`: one more pass under `sl->lock`, then done. |

- `__read_seqcount_retry()`: the only non-latch read form without a barrier;
  `__read_seqcount_begin()` has the same ordering as the other begin forms.
- Odd value from `raw_read_seqcount()`: passed unchanged to
  `read_seqcount_retry()` it validates a section that ran inside a write
  section; `raw_seqcount_begin()` clears bit 0 so the retry fails.
- `scoped_seqlock_read()` body left with `break`: the lock is released by
  `__scoped_seqlock_cleanup()`, but `read_seqretry()` is not run, so a
  lockless pass is not validated.
- `afs_lookup_volume_rcu()` in `fs/afs/callback.c` leaves that way, after it
  has taken a reference on the volume it found.
- `scoped_seqlock_read()` target `ss_done`: calls
  `__scoped_seqlock_invalid_target()`, which is declared in
  `include/linux/seqlock.h` and defined nowhere.

**Sequence counter read side**

- Sleeping in a lockless section: allowed, the reader holds no lock and does
  not disable preemption; `__alloc_pages_slowpath()` in `mm/page_alloc.c`
  keeps a `read_mems_allowed_begin()` cookie across direct reclaim.
- Body shared with a locked pass (`read_seqbegin_or_lock()`,
  `scoped_seqlock_read()` with `ss_lock`): runs under a `spinlock_t` on the
  second pass, so it must not sleep.
- KCSAN: plain loads in the section are treated as atomic, up to
  `KCSAN_SEQLOCK_REGION_MAX` accesses; begin calls
  `kcsan_atomic_next(KCSAN_SEQLOCK_REGION_MAX)` and retry calls
  `kcsan_atomic_next(0)`, for `read_seqbegin()` as well.
- `ktime_get()` in `kernel/time/timekeeping.c` reads with plain loads.
- **Potentially unsafe usage**: leaving the section, or acting on what it
  read, without the retry check.
  - Unsafe: when the result needs two or more loads to come from the same
    write generation; a writer can change one between them.
  - Safe: when one load alone proves the result, as `hrtimer_active()` in
    `kernel/time/hrtimer.c` returns true on either flag; `base->seq` is
    there only to rule out a false negative.
  - Safe: when the object was validated under its own lock and pinned, as
    `d_lookup()` in `fs/dcache.c` leaves on a hit; `__d_lookup()` compares
    under `d_lock` and takes the reference.
- `get_fs_root()` and `get_fs_pwd()` in `include/linux/fs_struct.h`: locking
  readers with `read_seqlock_excl()`, not retry loops.

**Sequence counter write side**

| Form | Assert | Lockdep acquire | `preempt_disable()` if `seqprop_preemptible()` |
|---|---|---|---|
| `write_seqcount_begin()`, `write_seqcount_begin_nested()` | yes | yes | yes |
| `raw_write_seqcount_begin()` | no | no | yes |
| `do_write_seqcount_begin()`, used by `write_seqlock()` | no | yes | no |
| `do_raw_write_seqcount_begin()` | no | no | no |
| `write_seqcount_invalidate()` | no | no | no |
| `raw_write_seqcount_barrier()` | no | no | no |

- `seqcount_mutex_t` write section on non-PREEMPT_RT: runs with preemption
  disabled by `write_seqcount_begin()`, so it must not sleep although the
  mutex is held.
- **Potentially unsafe usage**: a write section that can be preempted.
  - Unsafe: when any reader spins until the count is even, as
    `read_seqcount_begin()`, `raw_read_seqcount_begin()` and `read_seqbegin()`
    do outside the PREEMPT_RT case below; `__read_seqcount_begin()` spins
    while the count is odd.
  - Safe: when every reader uses a form that does not wait.
    `copy_page_range()` in `mm/memory.c` writes `write_protect_seq` with
    `raw_write_seqcount_begin()`; its reader `gup_fast()` uses
    `raw_seqcount_try_begin()`.
  - Safe: `ri_timer()` in `kernel/events/uprobes.c`, whose reader
    `free_ret_instance()` uses `raw_seqcount_try_begin()`, which does not
    wait.
  - Safe: on PREEMPT_RT, when the counter is a `seqcount_spinlock_t`,
    `seqcount_rwlock_t`, `seqcount_mutex_t` or `seqlock_t` and the writer
    holds the associated lock, as `write_seqlock()` does; on an odd count
    `seqprop_sequence()` locks and unlocks that lock, so the reader blocks
    until the writer is done.
- The raw form is what lets `copy_page_range()` and `ri_timer()` pass:
  `write_seqcount_begin()` on a `seqcount_t` would trip
  `lockdep_assert_preemption_disabled()`, for `ri_timer()` on PREEMPT_RT
  only.
- `write_seqcount_invalidate()`: `smp_wmb()`, then adds 2; the count stays
  even, so no reader waits and every section already open fails its retry.
- `write_seqcount_invalidate()` is used repeatedly on live objects:
  `__d_drop()` in `fs/dcache.c` on unhash, and
  `intel_gt_invalidate_tlb_full()` in `drivers/gpu/drm/i915/gt/intel_tlb.c`.
- `raw_write_seqcount_barrier()` users: `__run_hrtimer()` in
  `kernel/time/hrtimer.c` and `unix_peek_fpl()` in `net/unix/garbage.c`; not
  the dcache and not `mm_lock_seq`, which uses
  `do_raw_write_seqcount_begin()`.
- **Unsafe usage**: calling `write_seqcount_invalidate()` or
  `raw_write_seqcount_barrier()` from two writers at once; both do plain
  non-atomic increments and check nothing.
  - Safe: under the lock that serializes the counter's writers;
    `unix_peek_fpl()` takes a spinlock only for that, `__run_hrtimer()` holds
    `cpu_base->lock`.

## The lock implementations

**Builds that include rtmutex.c**

- `kernel/locking/rtmutex.c`: never an object of its own; `kernel/locking/Makefile`
  has no entry for it, and every copy comes from `#include "rtmutex.c"`.
- Includers: four, found by searching for `#include "rtmutex.c"`.

| Includer | Built when | Defines before the include |
|---|---|---|
| `kernel/locking/rtmutex_api.c` | `CONFIG_RT_MUTEXES` | `RT_MUTEX_BUILD_MUTEX` |
| `kernel/locking/ww_rt_mutex.c` | `CONFIG_PREEMPT_RT` | `RT_MUTEX_BUILD_MUTEX`, `WW_RT` |
| `kernel/locking/spinlock_rt.c` | `CONFIG_PREEMPT_RT` | `RT_MUTEX_BUILD_SPINLOCKS` |
| `kernel/locking/rwsem.c` | `CONFIG_PREEMPT_RT` branch only | `RT_MUTEX_BUILD_MUTEX` |

- Copies per kernel: none without `CONFIG_RT_MUTEXES`, one on a non-RT kernel
  with it, four with `CONFIG_PREEMPT_RT`.
- `RT_MUTEX_BUILD_SPINLOCKS`: the macro name ends in S; `rt_spin_lock()` is in
  `kernel/locking/spinlock_rt.c`, not in `kernel/locking/rtmutex_api.c`.
- `RT_MUTEX_BUILD_SPINLOCKS` also changes shared code: only in that build does
  `rt_mutex_steal()` let a waiter of equal priority steal the lock, and only
  when the waiter is not RT or deadline priority.
- `kernel/locking/ww_mutex.h`: built once per kernel. There are two include
  sites and they exclude each other: `kernel/locking/mutex.c` inside
  `#ifndef CONFIG_PREEMPT_RT`, and `kernel/locking/rtmutex.c` under `WW_RT`,
  reached only through `kernel/locking/ww_rt_mutex.c`.
- Without `WW_RT`, the ww hooks at the top of `kernel/locking/rtmutex.c`
  return 0 or are empty; they do not call `BUG()`.
- `WW_RT` in `kernel/locking/rtmutex.c`: search for `build_ww_mutex()`. The
  part that is easy to miss is `task_blocks_on_rt_mutex()`: a waiter with a
  `ww_ctx` skips the early `-EDEADLK` return for `owner == task`.
- `WW_RT` in `__waiter_less()`: equal-priority waiters are ordered by ww stamp,
  and a waiter with a `ww_ctx` sorts before one without.
- `__ww_waiter_add()` under `WW_RT`: empty. `task_blocks_on_rt_mutex()` has
  already enqueued the waiter, and dequeues it if `__ww_mutex_add_waiter()`
  fails.
- `__ww_ctx_less()` under `WW_RT`: compares RT and deadline priority before
  the stamp; the non-RT build compares the stamp only.

**Spinlock API layers**

- Debug `do_raw_spin_lock()`: in `kernel/locking/spinlock_debug.c`; there is no
  spinlock_debug.c under `lib/`.
- `include/linux/spinlock_api_up.h`: used only when `CONFIG_SMP` and
  `CONFIG_DEBUG_SPINLOCK` are both off.
- UP with lockdep: `CONFIG_DEBUG_LOCK_ALLOC` and `CONFIG_PROVE_LOCKING` select
  `CONFIG_DEBUG_SPINLOCK`, so the call goes through `__raw_spin_lock()` in
  `include/linux/spinlock_api_smp.h` and does call `spin_acquire()`;
  `arch_spin_lock()` still comes from `include/linux/spinlock_up.h`.
- `CONFIG_GENERIC_LOCKBREAK` without `CONFIG_DEBUG_LOCK_ALLOC`: replaces the
  `__raw_spin_lock()` layer. The header version is compiled out and
  `BUILD_LOCK_OPS()` in `kernel/locking/spinlock.c` generates a loop of
  `preempt_disable()`, `do_raw_spin_trylock()`, `preempt_enable()`,
  `arch_spin_relax()`; it does not call `spin_acquire()` or `LOCK_CONTENDED()`.
- `CONFIG_GENERIC_LOCKBREAK` is live: several arch Kconfig files define it for
  `SMP && PREEMPTION`, for example `arch/powerpc/Kconfig` when
  `PPC_QUEUED_SPINLOCKS` is off.
- `CONFIG_INLINE_SPIN_LOCK`: cannot be set with `CONFIG_DEBUG_SPINLOCK` or
  `CONFIG_GENERIC_LOCKBREAK` (`kernel/Kconfig.locks`), so every lockdep kernel
  keeps the out-of-line `_raw_spin_lock()` in `kernel/locking/spinlock.c`.

**Mutex internals**

- Waiter queue: a circular list through the `list` member of each
  `struct mutex_waiter`, with no list head. `first_waiter` is the front, the
  entry before it is the tail, and NULL means no waiters.
- Queue helpers: `__mutex_add_waiter()` takes a `pos` waiter instead of a list
  head (NULL means tail) and moves `first_waiter` when inserting before the
  front. See also `__ww_waiter_next()` in `kernel/locking/ww_mutex.h`, which
  ends the walk when it comes back round to `first_waiter`.
- `MUTEX_FLAG_WAITERS`: set by `__mutex_add_waiter()` only when the queue goes
  from empty to one waiter.
- `__mutex_remove_waiter()`: when the last waiter leaves, clears all of
  `MUTEX_FLAGS`, not only `MUTEX_FLAG_WAITERS`.
- Fast path (`__mutex_trylock_fast()`, `__mutex_unlock_fast()`): compiled out
  by `CONFIG_DEBUG_LOCK_ALLOC`, not by `CONFIG_DEBUG_MUTEXES`. With
  `CONFIG_DEBUG_MUTEXES` alone the fast path is built.
- `CONFIG_MUTEX_SPIN_ON_OWNER`: `depends on SMP && ARCH_SUPPORTS_ATOMIC_RMW` in
  `kernel/Kconfig.locks`; it does not depend on `CONFIG_DEBUG_MUTEXES`, so
  debug kernels spin too.
- Handoff without `MUTEX_FLAG_HANDOFF`: `__mutex_unlock_slowpath()` takes the
  handoff path whenever `sched_proxy_exec()` is true and
  `current->blocked_donor` is set (`CONFIG_SCHED_PROXY_EXEC`).
- Handoff target: `current->blocked_donor` if that task is blocked on this
  mutex, otherwise the task of `first_waiter`. The task named with
  `MUTEX_FLAG_PICKUP` is therefore not always the first waiter.
- `__mutex_handoff()` with a NULL task: an ordinary release that keeps
  `MUTEX_FLAG_WAITERS`; this happens on the forced path when nobody waits.
- Per-task tracking: `__mutex_lock_common()` records the mutex in
  `current->blocked_on` with `__set_task_blocked_on()`, under
  `current->blocked_lock` taken inside `wait_lock`.
  `__mutex_unlock_slowpath()` clears it for the task it wakes.
- First-waiter spin: `__mutex_lock_common()` clears `blocked_on` and drops both
  locks before `mutex_optimistic_spin()`, then sets it again afterwards.

**Adding a lock operation**

- Lockdep entry point: `_mutex_lock_killable(lock, subclass, nest_lock)`. Under
  `CONFIG_DEBUG_LOCK_ALLOC`, `mutex_lock_killable()`,
  `mutex_lock_killable_nested()` and `mutex_lock_killable_nest_lock()` are all
  macros over it in `include/linux/mutex.h`; no function is named
  `mutex_lock_killable_nested()`.
- Definitions: four. `mutex_lock_killable()` and `_mutex_lock_killable()` each
  exist in `kernel/locking/mutex.c` and again in
  `kernel/locking/rtmutex_api.c` under `CONFIG_PREEMPT_RT`.
- `__mutex_lock_common()` in `kernel/locking/rtmutex_api.c`: a separate static
  function with the same name as the one in `kernel/locking/mutex.c`, taking
  five arguments and calling `__rt_mutex_lock()`.
- `__cond_acquires(0, lock)` on both prototypes: checked by Clang context
  analysis under `CONFIG_WARN_CONTEXT_ANALYSIS`. `kernel/locking/Makefile`
  turns it on per object, for example `CONTEXT_ANALYSIS_mutex.o := y`.
- Guard class: three lines in `include/linux/mutex.h`, needed by
  `scoped_cond_guard()` and `ACQUIRE()` users and by context analysis:
  `DEFINE_LOCK_GUARD_1_COND(mutex, _kill, ...)`,
  `DECLARE_LOCK_GUARD_1_ATTRS(mutex_kill, ...)` and
  `class_mutex_kill_constructor()`.
- Rust: `mutex_lock_killable()` is a macro under `CONFIG_DEBUG_LOCK_ALLOC`, so
  a Rust caller would need a wrapper; `rust/helpers/mutex.c` wraps
  `mutex_lock()` and `mutex_trylock()` and has none for it.
- `lib/locking-selftest.c`: `ww_test_normal()` calls `mutex_lock_killable()`
  through `ww_mutex_base_lock_killable()`; with `CONFIG_PREEMPT_RT` that macro
  is `rt_mutex_lock_killable()` instead.
- `lib/test_context-analysis.c` (`CONFIG_CONTEXT_ANALYSIS_TEST`): compile-only;
  `test_mutex_trylock()` covers `mutex_lock_killable()`, and nothing there uses
  the `mutex_kill` guard.
- `kernel/locking/locktorture.c` and `kernel/locking/test-ww_mutex.c`: do not
  call `mutex_lock_killable()`; the mutex torture type takes `mutex_lock()`.

## Model gaps

### Other mistakes models make

- Models take `lockdep_assert_held()`, `lockdep_assert_held_write()` and
  `lockdep_assert_held_read()` to compile to nothing without lockdep. With
  or without lockdep, in a file opted into context analysis a wrong
  assertion silences the compiler from that point on. `rwsem_assert_held()`
  does the same.
- Models take a spinning lock acquisition to always succeed. `rqspinlock_t`
  in `include/asm-generic/rqspinlock.h` does not: `raw_res_spin_lock()` and
  `raw_res_spin_lock_irqsave()` return `-EDEADLK` or `-ETIMEDOUT` with
  preemption and interrupts restored, and the caller must test the result.
- Models take `CONFIG_PREEMPT_COUNT` off to be an ordinary configuration.
  In `kernel/Kconfig.preempt`, `CONFIG_PREEMPT_NONE` depends on
  `ARCH_NO_PREEMPT` and `CONFIG_PREEMPT_VOLUNTARY` on
  `!ARCH_HAS_PREEMPT_LAZY`; with the remaining choices
  `CONFIG_PREEMPT_BUILD` is set, which selects `CONFIG_PREEMPT_COUNT`
  through `CONFIG_PREEMPTION`.
- Models take the mutex unlock slow path to hold `wait_lock` only.
  `__mutex_unlock_slowpath()` also takes `blocked_lock` of
  `struct task_struct` inside `wait_lock`.
- Models know `__cond_acquires()` only. `__cond_releases()` also exists and
  is used on `__mutex_unlock_fast()`.
- Models expect a guard class for each spinlock form. No guard class wraps
  `spin_lock_irq_disable()`.
- Models cite bcachefs as the user of `lockdep_set_notrack_class()`.
  bcachefs is not in the tree.
