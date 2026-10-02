# RCU Subsystem

## Main structures

### Objects and how they relate

- `struct rcu_gp_seq` (`include/linux/rcupdate.h`): a pair of grace-period
  cookies, `norm` for the normal sequence and `exp` for the expedited one.
  There is no rcu_gp_oldstate type in this tree; every `_full()` polling
  function takes `struct rcu_gp_seq`.
- `struct rcu_segcblist` segments: each is tagged with a `struct rcu_gp_seq`,
  not one number.
- `call_rcu()` callback readiness: a segment moves to done when either the
  normal or the expedited grace period it was tagged with has completed; see
  `rcu_segcblist_advance()` in `kernel/rcu/rcu_segcblist.c`.
- Expedited completion and callbacks: queuing a callback requests only the
  normal grace period (`rcu_accelerate_cbs()` passes `gs.norm` to
  `rcu_start_this_gp()`); an expedited one that happens to finish first
  releases the callback early.
- Tree SRCU and Tasks callback lists: same `struct rcu_segcblist`, but
  through `srcu_segcblist_advance()` and `srcu_segcblist_accelerate()`, which
  use only `norm` and set `exp` to `RCU_GET_STATE_NOT_TRACKED`.
- `struct rcu_tasks`: two instances only, `rcu_tasks` and `rcu_tasks_rude`
  in `kernel/rcu/tasks.h`.
- Tasks Trace RCU: has no holdout list of its own; the only holdout list in
  `struct task_struct` is `rcu_tasks_holdout_list`, under `CONFIG_TASKS_RCU`.
- Tasks Trace reader state in `struct task_struct`: `trc_reader_nesting` and
  `trc_reader_scp`, the latter holding the `struct srcu_ctr __percpu *` that
  `__srcu_read_lock_fast()` returned.
- `struct srcu_node` tree: a domain may have none.
  `init_srcu_struct_fields()` leaves `node` in `struct srcu_usage` NULL with
  `srcu_size_state` at `SRCU_SIZE_SMALL` unless `convert_to_big` asks for
  the tree at init.
- `struct kfree_rcu_cpu`: defined in `mm/slab_common.c` under
  `CONFIG_KVFREE_RCU_BATCHED`, not under `kernel/rcu/`.
- `struct kvfree_rcu_head` (`include/linux/types.h`): what
  `kvfree_call_rcu()` takes, not `struct rcu_head`.
- `struct rcu_synchronize` in `synchronize_rcu()`: by default not queued with
  `call_rcu()`. `rcu_sr_normal_add_req()` puts it on the `srs_next` list in
  `struct rcu_state`, and the grace-period kthread or `srs_cleanup_work`
  completes it.
- `struct sr_wait_node`: a marker node that the grace-period kthread inserts
  into `srs_next` to separate waiters of one grace period from the next.
- Offloaded `cblist` in `struct rcu_data`: protected by `nocb_lock` taken
  with interrupts disabled, not by the lock instead of disabling interrupts;
  `rcu_lockdep_assert_cblist_protected()` asserts both.
- Callback invocation on a non-offloaded CPU: `rcu_core()` runs from
  `RCU_SOFTIRQ`, or from the per-CPU rcuc kthread (`rcu_cpu_kthread()`) when
  `use_softirq` is false, the default on `CONFIG_PREEMPT_RT`.

## Read-side critical sections

**PREEMPT_RCU and Tiny builds**

- `CONFIG_PREEMPT_RCU`: has no prompt and no `depends on`; it is
  `default y if (PREEMPT || PREEMPT_RT || PREEMPT_DYNAMIC)` and
  `select TREE_RCU`. It does not follow `CONFIG_PREEMPTION`.
- `CONFIG_PREEMPT_LAZY` without `CONFIG_PREEMPT_DYNAMIC` and
  `CONFIG_PREEMPT_RT`: gives `CONFIG_PREEMPTION=y`, `CONFIG_PREEMPT_COUNT=y`
  and `CONFIG_PREEMPT_RCU=n`. The kernel is preemptible, readers are not.
- The same configuration on `!SMP`: gives `CONFIG_TINY_RCU` and
  `CONFIG_TINY_SRCU` with `CONFIG_PREEMPTION=y`; `__srcu_read_lock()` in
  `include/linux/srcutiny.h` disables preemption around its counter update
  for that case.
- `kernel/Kconfig.preempt`: `PREEMPT_NONE` depends on `ARCH_NO_PREEMPT` and
  `PREEMPT_VOLUNTARY` on `!ARCH_HAS_PREEMPT_LAZY`. On an architecture that
  selects `ARCH_HAS_PREEMPT_LAZY`, the lazy build above is the only one with
  `CONFIG_PREEMPT_RCU=n`.
- `rcu_read_lock_dont_migrate()` and `rcu_read_unlock_migrate()` in
  `include/linux/rcupdate.h`: add `migrate_disable()` and `migrate_enable()`
  only under `CONFIG_PREEMPT_RCU`; use them where a reader must stay on one
  CPU in every build.
- Tiny `synchronize_rcu()` in `kernel/rcu/tiny.c`: does not call
  `might_sleep()`; its only check is the `RCU_LOCKDEP_WARN()` on the three
  RCU lockdep maps, so a call from any other atomic context is not reported.
- Tiny SRCU (`include/linux/srcutiny.h`): `srcu_check_read_flavor()` is
  empty, the fast readers are `__srcu_read_lock()`, and
  `synchronize_srcu_expedited()` and `srcu_barrier()` are
  `synchronize_srcu()`.
- `CONFIG_NEED_SRCU_NMI_SAFE`: is
  `HAVE_NMI && !ARCH_HAS_NMI_SAFE_THIS_CPU_OPS && !TINY_SRCU`. When unset,
  `__srcu_read_lock_nmisafe()` is `__srcu_read_lock()`; on Tree SRCU that is
  the default build for architectures that select
  `ARCH_HAS_NMI_SAFE_THIS_CPU_OPS`, where only
  `CONFIG_FORCE_NEED_SRCU_NMI_SAFE` sets it.

**Inside a read-side section**

- What reports a reader that sleeps, and what each check needs:

| Check | Needs | Reports |
|---|---|---|
| `rcu_note_context_switch()` in `kernel/rcu/tree_plugin.h` | `CONFIG_PREEMPT_RCU` only | `WARN_ONCE()` "Voluntary context switch within RCU read-side critical section!" |
| `rcu_preempt_sleep_check()` via `rcu_sleep_check()` | `CONFIG_PROVE_RCU` and `CONFIG_PREEMPT_RCU=n` | "Illegal context switch in RCU read-side critical section" |
| `__might_resched()` | `CONFIG_DEBUG_ATOMIC_SLEEP` | "sleeping function called from invalid context", in both builds |
| `schedule_debug()` | `CONFIG_PREEMPT_COUNT` and `CONFIG_PREEMPT_RCU=n` | "scheduling while atomic", no debug option needed |
| `check_wait_context()` in `kernel/locking/lockdep.c` | `CONFIG_PROVE_LOCKING` | "[ BUG: Invalid wait context ]" |

- `rcu_preempt_sleep_check()`: is empty under `CONFIG_PREEMPT_RCU`, so
  `rcu_sleep_check()` never reports on `rcu_lock_map` there.
- `rcu_sleep_check()`: is defined under `CONFIG_PROVE_RCU`, not
  `CONFIG_DEBUG_ATOMIC_SLEEP`. `schedule_debug()` calls it too, so with
  `CONFIG_PROVE_RCU` alone it still runs at every `__schedule()`.
- `__might_resched()` under `CONFIG_PREEMPT_RCU`: `resched_offsets_ok()` adds
  `rcu_preempt_depth()` to the count it compares, so `might_sleep()` inside
  `rcu_read_lock()` is reported although `preempt_count()` is 0.
- `check_wait_context()`: `rcu_lock_map` has
  `wait_type_inner = LD_WAIT_CONFIG`, so acquiring a `LD_WAIT_SLEEP` lock
  such as a mutex inside `rcu_read_lock()` is reported at the acquisition, in
  every RCU build, whether or not the lock is contended; a trylock is not
  checked.
- `CONFIG_PREEMPT_RT`, blocking on `spinlock_t` or `rwlock_t`:
  `schedule_rtlock()` passes `SM_RTLOCK_WAIT`, which `__schedule()` treats as
  a preemption, so `rcu_note_context_switch()` does not warn.
- `rtlock_might_resched()` in `kernel/locking/spinlock_rt.c`: passes the
  current `rcu_preempt_depth()` as the expected depth, so RCU nesting never
  fails it; a nonzero `preempt_count()` or disabled interrupts do.

**Implicit readers**

- `CONFIG_PREEMPT_RT`: `local_bh_disable()` and `spin_lock()` sections stay
  readers although they are preemptible, because `__local_bh_disable_ip()` in
  `kernel/softirq.c` and `rt_spin_lock()` call `rcu_read_lock()`.
- `__local_bh_disable_ip()` on `CONFIG_PREEMPT_RT`: calls `rcu_read_lock()`
  only on the task's first BH-disable and only if `preemptible()`; from a
  non-preemptible caller the region is a reader through that caller's state.
- Threaded interrupt handlers: a forced-threaded handler runs inside
  `local_bh_disable()` in `irq_forced_thread_fn()`, so it is a reader. A
  handler that runs through `irq_thread_fn()` alone is not.
- `rcu_softirq_qs()` in `kernel/rcu/tree.c`: is a quiescent state inside a
  BH-disabled region; `synchronize_rcu()` waits only up to that call.
- `handle_softirqs()` in `kernel/softirq.c`: calls `rcu_softirq_qs()` after
  each pass over the pending handlers when run from ksoftirqd on non-RT, so a
  reader there does not span two passes.
- `rcu_softirq_qs_periodic()`: calls `rcu_softirq_qs()` at most once per
  `HZ / 10`, and never on `CONFIG_PREEMPT_RT`, between passes of long-running
  softirq-like loops; for example `napi_threaded_poll_loop()` in
  `net/core/dev.c`.
- `lockdep_assert_in_rcu_reader()` in `include/linux/rcupdate.h`: the
  assertion that accepts implicit readers; it passes on any of the three
  lockdep maps or `!preemptible()`.

**BH and sched readers**

- `rcu_read_lock_bh()` on `CONFIG_PREEMPT_RT`: `__local_bh_disable_ip()`
  takes `softirq_ctrl.lock` only under `CONFIG_PREEMPT_RT_NEEDS_BH_LOCK`.
  Without that option it does `migrate_disable()` and `rcu_read_lock()`, the
  task stays preemptible, and the section is not serialized against other
  BH-disabled sections on that CPU.
- `rcu_read_lock_sched()`: is `preempt_disable()` in every build, also on
  `CONFIG_PREEMPT_RT`; `rcu_sched_lock_map` has
  `wait_type_inner = LD_WAIT_SPIN`, so under
  `CONFIG_PROVE_RAW_LOCK_NESTING` lockdep reports a `spinlock_t` taken
  inside it.
- `rcu_sleep_check()`: skips the `rcu_bh_lock_map` test when
  `CONFIG_PREEMPT_RT` is set, and keeps the `rcu_sched_lock_map` test.

**RCU not watching**

- `rcu_is_watching()` in `kernel/rcu/tree.c`: reads only the
  `CT_RCU_WATCHING` bit of the per-CPU `struct context_tracking`; it says
  nothing about whether the CPU is online to RCU.
- `rcutree_report_cpu_dead()`: does not change the context-tracking state,
  so `rcu_is_watching()` can return true on a CPU that RCU no longer waits
  for.
- `rcu_lockdep_current_cpu_online()`: is the offline test. It is real only
  under `CONFIG_PROVE_RCU` and `CONFIG_HOTPLUG_CPU`, otherwise constant true,
  and it returns true `in_nmi()` and before `rcu_scheduler_fully_active`.
- Tiny RCU: `rcu_is_watching()` is constant true in
  `include/linux/rcutiny.h`, and `irqentry_enter_from_kernel_mode()` skips
  `ct_irq_enter()`.
- `rcu_is_watching()`: is `notrace`, not `noinstr`.
  `rcu_is_watching_curr_cpu()` in `include/linux/context_tracking.h` is the
  `__always_inline` form that context-tracking code calls.
- There is no RCU_NONIDLE() and no _rcuidle tracepoint variant in this tree.
- `rcu_read_lock_sched_notrace()`: only skips lockdep; it does not make RCU
  watch, and a preempt-disabled region where RCU is not watching is not a
  reader.
- `irqentry_enter()` from kernel mode: calls `ct_irq_enter()` only if
  `is_idle_task(current)` or `arch_in_rcu_eqs()`; otherwise it expects RCU to
  be watching already.
- `irq_enter()`: calls `ct_irq_enter()`; `irq_enter_rcu()` does not.
- `ct_irq_enter_irqson()`: has one caller, `__trace_stack()` in
  `kernel/trace/trace.c`, which reaches it only when RCU is not watching, and
  before that warns and returns under `CONFIG_GENERIC_ENTRY` and returns
  `in_nmi()`.
- `srcu_read_lock()`: has no `RCU_LOCKDEP_WARN(!rcu_is_watching(), ...)`.
  `srcu_read_lock_fast()`, `srcu_read_lock_fast_updown()` and
  `srcu_down_read_fast()` have it.
- `lock_acquire()` under `CONFIG_LOCKDEP` and `CONFIG_TRACEPOINTS`: calls
  `trace_lock_acquire()`, which has `WARN_ONCE(!rcu_is_watching(), ...)`, so
  the lockdep annotation in `srcu_read_lock()` and in `rcu_read_lock_trace()`
  still warns where RCU is not watching.
- SRCU-fast grace periods: `srcu_readers_active_idx_check()` in
  `kernel/rcu/srcutree.c` calls `synchronize_rcu()` or
  `synchronize_rcu_expedited()` where the other flavours use `smp_mb()`,
  which is why those readers need RCU watching.
- `rcu_read_lock_trace()`: at the outermost nesting level calls
  `__srcu_read_lock_fast()` on `rcu_tasks_trace_srcu_struct` followed by
  `smp_mb()`. It has no `RCU_LOCKDEP_WARN()`; the `smp_mb()` is compiled out
  under `CONFIG_TASKS_TRACE_RCU_NO_MB`.

**rcu_read_lock_held family**

- `rcu_read_lock_sched_held()` and `rcu_read_lock_any_held()` without
  `CONFIG_DEBUG_LOCK_ALLOC`: return `!preemptible()`, not 1. `preemptible()`
  is constant 0 without `CONFIG_PREEMPT_COUNT`, so there they return 1.
- `rcu_read_lock_bh_held()` with lockdep working: returns
  `in_softirq() || irqs_disabled()` and never looks at `rcu_bh_lock_map`; it
  is true in any BH-disabled or irq-disabled region.
- `srcu_read_lock_held()`: tests `debug_lockdep_rcu_enabled()`, then
  `lock_is_held(&ssp->dep_map)`. It has no watching test and no online test.
- `rcu_read_lock_trace_held()`: is
  `srcu_read_lock_held(&rcu_tasks_trace_srcu_struct)` under
  `CONFIG_DEBUG_LOCK_ALLOC` and `CONFIG_TASKS_TRACE_RCU`, otherwise 1.
- `rcu_read_lock_held_common()` in `kernel/rcu/update.c`: tests
  `debug_lockdep_rcu_enabled()` first, so with lockdep switched off the four
  RCU predicates return 1 even where RCU is not watching.
- `debug_lockdep_rcu_enabled()`: also requires
  `current->lockdep_recursion == 0`, so the predicates return 1 when called
  from inside lockdep.
- Offline CPU: the four RCU predicates return 0 only where
  `rcu_lockdep_current_cpu_online()` is real, that is under
  `CONFIG_PROVE_RCU` and `CONFIG_HOTPLUG_CPU`, and not `in_nmi()`.
- `lockdep_assert_in_rcu_read_lock()`,
  `lockdep_assert_in_rcu_read_lock_bh()` and
  `lockdep_assert_in_rcu_read_lock_sched()` in `include/linux/rcupdate.h`:
  test the lockdep map itself, so `local_bh_disable()` or
  `preempt_disable()` alone does not satisfy the bh and sched forms. They
  generate no check without `CONFIG_PROVE_RCU`.
- `lock_is_held()`: without `CONFIG_LOCKDEP` it is declared and not defined,
  so it only builds where the compiler drops the call, as inside
  `RCU_LOCKDEP_WARN()`. With lockdep built and disabled it returns
  `LOCK_STATE_UNKNOWN`, which is nonzero.
- **Potentially unsafe usage**: letting the result of a predicate choose a
  code path, a GFP mask or whether to take a lock.
  - Unsafe: when the path taken on a nonzero result is correct only inside a
    reader. It runs outside any reader when `CONFIG_DEBUG_LOCK_ALLOC` is off
    or `debug_lockdep_rcu_enabled()` is false, because the stubs in
    `include/linux/rcupdate.h` and `rcu_read_lock_held_common()` return 1
    there.
  - Safe: when the path taken on a nonzero result is correct in any context.
    `rxrpc_alloc_ack()` in `net/rxrpc/output.c` picks `GFP_ATOMIC` on a
    nonzero result, so a wrong 1 only gives up the sleeping allocation.
  - Safe: warn only on a zero result, as `percpu_ref_tryget_live_rcu()` does
    with `WARN_ON_ONCE(!rcu_read_lock_held())`; a wrong 1 only loses the
    warning.
  - Safe: pass the predicate as the condition of `rcu_dereference_check()`,
    which puts it inside `RCU_LOCKDEP_WARN()`, as `task_storage_lookup()` in
    `kernel/bpf/bpf_task_storage.c` does.
  - Safe: `rcu_preempt_depth()` for a real nesting count, under
    `CONFIG_PREEMPT_RCU` only, as `rcu_preempt_need_deferred_qs()` in
    `kernel/rcu/tree_plugin.h` does; it is constant 0 in the other builds.
- **Unsafe usage**: asserting that no reader is active by warning on a
  nonzero result, as in `WARN_ON(rcu_read_lock_held())`.
  - Unsafe: the warning fires on every call without
    `CONFIG_DEBUG_LOCK_ALLOC`, where `rcu_read_lock_held()` is constant 1.
  - Safe: `RCU_LOCKDEP_WARN(lock_is_held(&rcu_lock_map), ...)`, as
    `synchronize_rcu()` does; `RCU_LOCKDEP_WARN()` tests
    `debug_lockdep_rcu_enabled()` before and after the condition.

## Pointers and lists

**Pointer load primitives:** All in `include/linux/rcupdate.h` except the SRCU
form. `rcu_dereference()`, `rcu_dereference_bh()`, `rcu_dereference_sched()`,
`rcu_dereference_all()` and `srcu_dereference()` pass `c` = 0.

| Primitive | Load | Lockdep passes when `c` or | `rcu_check_sparse()` |
|---|---|---|---|
| `rcu_dereference_check(p, c)` | `READ_ONCE()` | `rcu_read_lock_held()`: `rcu_lock_map` held, so `rcu_read_lock()` only | yes |
| `rcu_dereference_bh_check(p, c)` | `READ_ONCE()` | `rcu_read_lock_bh_held()`: `in_softirq() \|\| irqs_disabled()` | yes |
| `rcu_dereference_sched_check(p, c)` | `READ_ONCE()` | `rcu_read_lock_sched_held()`: `rcu_sched_lock_map` held or `!preemptible()` | yes |
| `rcu_dereference_all_check(p, c)` | `READ_ONCE()` | `rcu_read_lock_any_held()`: any of the three maps held or `!preemptible()` | yes |
| `srcu_dereference_check(p, ssp, c)` | `READ_ONCE()` | `srcu_read_lock_held(ssp)` | yes |
| `rcu_dereference_raw_check(p)` | `READ_ONCE()` | always: the condition is the constant 1 | yes |
| `rcu_dereference_raw(p)` | `READ_ONCE()` | always: no `RCU_LOCKDEP_WARN()` | no |
| `rcu_access_pointer(p)` | `READ_ONCE()` | always: no `RCU_LOCKDEP_WARN()` | yes |
| `rcu_dereference_protected(p, c)` | plain | `c` alone | yes |

- `rcu_dereference()` in a preempt-disabled region or under
  `rcu_read_lock_sched()` alone, or without `CONFIG_PREEMPT_RT` in a
  BH-disabled region or under `rcu_read_lock_bh()` alone: lockdep splat, since
  those do not acquire `rcu_lock_map`. Use `rcu_dereference_all()`,
  `rcu_dereference_bh()` or `rcu_dereference_sched()`.
- `rcu_read_lock_held_common()` in `kernel/rcu/update.c`: runs first in the
  four RCU `_held()` helpers; with lockdep enabled and `!rcu_is_watching()` or
  `!rcu_lockdep_current_cpu_online()` they return false even inside
  `rcu_read_lock()`. `srcu_read_lock_held()` does not call it.
- rcu_dereference_raw_notrace() and rcu_dereference_index_check(): not defined
  here. `rcu_dereference_raw_check()` and `srcu_dereference_notrace()` pass the
  constant 1 as the condition, so they never call a `_held()` helper.
- `rcu_dereference_raw()` with a concurrent writer: the load is `READ_ONCE()`,
  it cannot tear. Only `rcu_dereference_protected()` needs writers excluded.
- `list_for_each_entry_rcu()`: loads through `list_entry_rcu()`, a bare
  `READ_ONCE()`. `hlist_for_each_entry_rcu()` uses `rcu_dereference_raw()`.
- `__list_check_rcu()` in `include/linux/rculist.h`: the only check that
  `list_for_each_entry_rcu()` and `hlist_for_each_entry_rcu()` make; compiled
  in only under `CONFIG_PROVE_RCU_LIST`; passes on `cond` or
  `rcu_read_lock_any_held()`.
- `__rcu_guarded`: `__rcu` plus `__guarded_by(RCU)`, checked at compile time
  under `CONFIG_WARN_CONTEXT_ANALYSIS`, and only for objects whose Makefile
  sets `CONTEXT_ANALYSIS := y` or the per-object form, as
  `CONTEXT_ANALYSIS_kcov.o := y` in `kernel/Makefile`, unless
  `CONFIG_WARN_CONTEXT_ANALYSIS_ALL` is set.
  `rcu_access_pointer()`, `rcu_assign_pointer()`, `RCU_INIT_POINTER()` and
  `unrcu_pointer()` are wrapped in `context_unsafe()`;
  `__rcu_dereference_check()` and `__rcu_dereference_protected()` are not.
- `srcu_dereference_check()`: calls `__srcu_read_lock_must_hold()`, declared
  `__must_hold_shared(ssp)`, whatever `c` is.

**Dependency ordering**

- Bare `READ_ONCE()` of the pointer: same ordering as `rcu_dereference()`;
  `__rcu_dereference_check()` is `READ_ONCE()` plus the lockdep and sparse
  checks, and `list_entry_rcu()` is `READ_ONCE()` alone.
  `Documentation/RCU/rcu_dereference.rst` allows the bare form only where data
  is added and never removed while readers run.
- Integer casts: the value must stay a pointer. The document allows a
  temporary cast to `uintptr_t` for two things only: setting or clearing
  low-order must-be-zero bits of an aligned pointer, and XOR to translate
  pointers. Cast back before any other use.
- Comparison rule below: its six safe cases are those of
  `Documentation/RCU/rcu_dereference.rst`.
- **Potentially unsafe usage**: comparing the returned pointer with a
  non-NULL pointer, then loading through it.
  - Unsafe: the equal branch loads through the pointer, and the object compared
    against was initialised or changed recently. The compiler may load from the
    known address, and that load no longer depends on `rcu_dereference()`.
  - Unsafe: the not-equal branch, when the compiler can see that the pointer
    has only two possible values; not-equal then reveals the value too.
  - Safe: comparison with NULL, as `hlist_for_each_entry_rcu()` does.
  - Safe: the pointer is never dereferenced after the comparison, as in
    `list_empty()`.
  - Safe: only the not-equal branch dereferences and the compiler cannot deduce
    the value, as in `list_first_or_null_rcu()` and the loop test of
    `list_for_each_entry_rcu()`.
  - Safe: the object compared against was initialised long before, for example
    at compile time, at boot, at module init, or under an earlier hold of a
    lock now held.
  - Safe: the other pointer also came from `rcu_dereference()`.
  - Safe: every access after the comparison is a store.

**Publishing a pointer**

- `RCU_INIT_POINTER()`: the comment above it in `include/linux/rcupdate.h`
  gives three cases and no more. A lock held by the writer is not one of them.
- Third case of `RCU_INIT_POINTER()`: the object was already exposed to
  readers, and either nothing reader-visible changed since, or readers may see
  its old state (for example statistical counters).
- `rcu_replace_pointer()`: returns `typeof(ptr)`, the type of the new value,
  not of `rcu_ptr`.
- **Potentially unsafe usage**: `rcu_replace_pointer()` with a constant-true
  `c`.
  - Unsafe: while another task can write the same pointer. The old value is a
    plain load followed by a separate store, so two callers can both get the
    same old pointer and free it twice.
  - Safe: under the lock that serialises the writers, as `tcf_pedit_init()` in
    `net/sched/act_pedit.c` does under `tcf_lock`.
  - Safe: lockless writers use
    `unrcu_pointer(xchg(&p, RCU_INITIALIZER(new)))` instead, as
    `proc_do_cad_pid()` in `kernel/reboot.c` does.

**Removed list entries**

- Backward readers exist: `list_bidir_prev_rcu()` in
  `include/linux/rculist.h` names `prev` for `rcu_dereference()`, as
  `__ns_tree_adjoined_rcu()` in `kernel/nstree.c` uses it.
- A list read with `list_bidir_prev_rcu()`: every removal must be
  `list_bidir_del_rcu()`, which leaves both `next` and `prev`. `list_del_rcu()`
  on such a list hands the backward reader `LIST_POISON2`.
- `next` of a removed entry: safe to follow only for a reader that was inside
  its read-side section when the entry was removed. Nothing updates the removed
  entry's `next` again, so after a later grace period it can point at a freed
  successor.
- `list_for_each_entry_continue_rcu()` and `list_for_each_entry_from_rcu()`
  from an entry kept alive by a reference count: the entry must still be on
  the list when the read-side section begins.
- `hlist_unhashed()` after `hlist_del_init_rcu()`: a plain load, for callers
  that hold the update lock. Without the lock use `hlist_unhashed_lockless()`,
  which pairs with the `WRITE_ONCE()` of `pprev`.
- **Potentially unsafe usage**: adding the removed entry to a list again
  before a grace period.
  - Unsafe: when readers cannot tell that they changed list. The add overwrites
    `next`, a reader standing on the entry continues in the new list, and
    `list_for_each_entry_rcu()` never meets its own `head`.
  - Safe: when readers detect the move and retry. `mnt_change_mountpoint()` in
    `fs/namespace.c` calls `hlist_del_init_rcu()` and then, through
    `attach_mnt()`, `hlist_add_head_rcu()`; its callers hold
    `write_seqlock(&mount_lock)` through `lock_mount_hash()` or
    `guard(mount_writer)`. `lookup_mnt()` rechecks with `read_seqretry()` in
    `__legitimize_mnt()`.

**Ordinary list operations**

- list_empty_rcu() and list_first_entry_rcu(): not defined. Readers call
  `list_empty()`, which is one `READ_ONCE()`.
- **Potentially unsafe usage**: in a reader, `list_empty()` followed by
  `list_first_entry()`.
  - Unsafe: when nothing excludes writers between the two calls;
    `list_first_entry()` loads `next` again and can return the head.
  - Safe: with the update-side lock held across both calls, as
    `mt76_txq_schedule_pending()` in
    `drivers/net/wireless/mediatek/mt76/tx.c` does under `phy->tx_lock`
    although it is inside `rcu_read_lock()`.
  - Safe: `list_first_or_null_rcu()`, one load, NULL when empty.
- `INIT_LIST_HEAD()`: the same two `WRITE_ONCE()` stores as
  `INIT_LIST_HEAD_RCU()` in this tree.
- `list_first_entry_or_null()`: one `READ_ONCE()` of `next`, not two plain
  loads.
- `hlist_del_init()` on a reader-visible node: sets `next` to NULL, so a reader
  standing on the node ends its walk early and silently misses the rest of the
  chain.
- Splice helpers, by which list readers may see:

| Helper | Source list | Destination | Blocks |
|---|---|---|---|
| `list_splice_rcu()` | must not be visible to readers | may be traversed | no |
| `list_splice_init_rcu()` | may be traversed | may be traversed | yes, calls `sync()` |
| `list_splice_tail_init_rcu()` | may be traversed | may be traversed | yes, calls `sync()` |

## Grace periods and callbacks

**Waiting for a grace period:** Rows that differ from the usual picture:

| Primitive | Callable from | Cost, and what is easy to miss |
|---|---|---|
| `get_state_synchronize_rcu_full()` and the other `_full()` calls | as the `unsigned long` forms | cookie is `struct rcu_gp_seq` in `include/linux/rcupdate.h`; there is no rcu_gp_oldstate here |
| `kfree_rcu()`, `kvfree_rcu()` | atomic context | under `CONFIG_KVFREE_RCU_BATCHED`: without `CONFIG_PREEMPT_RT`, tries `kfree_rcu_sheaf()` first: the object waits in a per-CPU sheaf, and a full sheaf goes to plain `call_rcu()`; otherwise batched, with the drain work scheduled `KFREE_DRAIN_JIFFIES` later |
| `kfree_rcu_nolock()` | contexts where no lock may be spun on | uses `local_trylock()` or defers through `defer_kfree_rcu()`; the field must be `struct kvfree_rcu_head`; two-argument form only |
| `synchronize_rcu_tasks_trace()`, `call_rcu_tasks_trace()` | as `synchronize_srcu()`, `call_srcu()` | inline wrappers on `rcu_tasks_trace_srcu_struct`; under `CONFIG_TREE_SRCU` each reader scan in `srcu_readers_active_idx_check()` waits a `synchronize_rcu()` or `synchronize_rcu_expedited()` |
| `synchronize_rcu_tasks_rude()` | sleepable | waits for nothing under `CONFIG_ARCH_WANTS_NO_INSTR` unless `CONFIG_FORCE_TASKS_RUDE_RCU` is set |
| `queue_rcu_work()` | atomic context | a `false` return means the work was already pending: no new grace period is requested for this call |

- `synchronize_rcu()` before the scheduler runs (`rcu_blocking_is_gp()` true):
  does not block and does not call `might_sleep()`, but advances
  `rcu_state.gp_seq_polled` and `rcu_state.gp_seq`, so cookies taken earlier
  read as completed.
- `synchronize_rcu_expedited()` in that state: advances
  `rcu_state.expedited_sequence` and returns.
- `__synchronize_srcu()` in that state: returns at once, so
  `synchronize_rcu_tasks_trace()` does too.
- `synchronize_rcu_tasks_generic()` in that state: WARNs "called too soon"
  and returns without waiting.
- `synchronize_rcu_normal()`: by default queues no callback; the waiter is put
  on `rcu_state.srs_next` and woken at grace-period cleanup
  (`rcu_normal_wake_from_gp` defaults to 1).
- `synchronize_rcu_normal()` fallback: `wait_rcu_gp(call_rcu_hurry)` when the
  parameter is below 1 or while `rcu_sr_normal_latched` is set; the latch is
  set once `RCU_SR_NORMAL_LATCH_THR` waiters are in flight and cleared when
  the count drains to 0.
- Boot-time expediting: `rcu_expedited_nesting` is initialised to 1 in
  `kernel/rcu/update.c`; `rcu_init()` does not call `rcu_expedite_gp()`.
  `rcu_end_inkernel_boot()` drops the count.
- `rcu_normal` set: `synchronize_rcu_expedited()` waits a normal grace period,
  except while `rcu_scheduler_active == RCU_SCHEDULER_INIT`; see
  `rcu_gp_is_normal()`.
- `rcu_expedited` and `rcu_normal` set together: `synchronize_rcu()` enters
  `synchronize_rcu_expedited()`, which then takes the normal path.
- `rcu_expedited`, `rcu_normal`, `rcu_normal_after_boot` as parameters: mode
  0444, so boot command line only (prefix rcupdate.).
- `rcu_normal_after_boot`: registered as a parameter only if
  `CONFIG_PREEMPT_RT` is off or `CONFIG_NO_HZ_FULL` is on.
- Runtime switch: the `rcu_expedited` and `rcu_normal` attributes in
  `kernel/ksysfs.c`; any non-zero integer turns the mode on.
- `CONFIG_TINY_RCU`: neither the parameters nor the sysfs attributes exist;
  `rcu_gp_is_expedited()` is a stub returning false in `kernel/rcu/rcu.h`.
- SRCU follows the same switches: `synchronize_srcu()` expedites when
  `rcu_gp_is_expedited()`, and `synchronize_srcu_expedited()` goes normal
  when `rcu_gp_is_normal()`.

**Matching readers and updaters**

- Tasks Trace readers (`rcu_read_lock_trace()`, `rcu_read_lock_tasks_trace()`,
  `guard(rcu_tasks_trace)`): SRCU-fast readers of
  `rcu_tasks_trace_srcu_struct`, defined in `kernel/rcu/tasks.h`.
- `synchronize_rcu_tasks_trace()` and `call_rcu_tasks_trace()`: inline
  wrappers for `synchronize_srcu()` and `call_srcu()` on that domain; see
  `include/linux/rcupdate_trace.h`.
- There is no rcu_trace_implies_rcu_gp() here. BPF passes the final free
  straight to `call_rcu_tasks_trace()`, for example `bpf_map_put()` in
  `kernel/bpf/syscall.c` and `do_call_rcu_ttrace()` in `kernel/bpf/memalloc.c`.
- What makes that cover plain RCU readers under `CONFIG_TREE_SRCU`:
  `srcu_readers_active_idx_check()` calls `synchronize_rcu()` or
  `synchronize_rcu_expedited()` for a domain with `SRCU_READ_FLAVOR_SLOWGP`.
- The reverse does not hold: `call_rcu()` and `synchronize_rcu()` do not wait
  for `rcu_read_lock_trace()` readers; `__bpf_prog_put_noref()` picks by
  `prog->sleepable`.
- RCU-watching check: `rcu_read_lock()`, `srcu_read_lock_fast()`,
  `srcu_read_lock_fast_updown()` and `srcu_down_read_fast()` have
  `RCU_LOCKDEP_WARN(!rcu_is_watching(), ...)`.
- `rcu_read_lock_trace()` and `rcu_read_unlock_trace()`: each adds an
  `smp_mb()` unless `CONFIG_TASKS_TRACE_RCU_NO_MB`.
- Tracepoint probes: run under `guard(srcu_fast_notrace)(&tracepoint_srcu)`,
  or under `guard(rcu_tasks_trace)()` for faultable (syscall) tracepoints,
  not under `preempt_disable()`; see `include/linux/tracepoint.h`.
- Examples of waiting for every kind of reader that reaches the object:
  - `tracepoint_synchronize_unregister()`: Tasks Trace, then
    `tracepoint_srcu`.
  - `ftrace_shutdown()` in `kernel/trace/ftrace.c`:
    `synchronize_rcu_tasks_rude()`, then `synchronize_rcu_tasks()`.
  - `bpf_tramp_image_put()` in `kernel/bpf/trampoline.c`:
    `call_rcu_tasks_trace()` chained into `call_rcu_tasks()`.

**Callback context**

- Models have the `rcu_do_batch()` contexts, the no-sleep rule and
  re-queueing right; see `rcu_do_batch()` in `kernel/rcu/tree.c` and
  `rcu_torture_fwd_prog_cb()` in `kernel/rcu/rcutorture.c`.
- `rcu_do_batch()` in `rcuc` or `rcuo` context: re-enables BH and calls
  `cond_resched_tasks_rcu_qs()` between two callbacks, so a batch is not one
  atomic region; each callback still runs with BH disabled.
- `call_srcu()` callbacks, which include `call_rcu_tasks_trace()` callbacks:
  invoked from a workqueue by `srcu_invoke_callbacks()` (`srcu_drive_gp()`
  under `CONFIG_TINY_SRCU`), each inside `local_bh_disable()`.
- `call_rcu_tasks()` callbacks: invoked by `rcu_tasks_invoke_cbs()` from the
  Tasks kthread or a workqueue, each inside `local_bh_disable()`.

**Lazy callbacks**

- Names: there is no jiffies_till_flush and no rcu_nocb_all here. The limit is
  `jiffies_lazy_flush` in `kernel/rcu/tree_nocb.h`, changed only by
  `rcu_set_jiffies_lazy_flush()` for tests.
- Offloaded CPUs come from `rcu_nocbs=`, `nohz_full=` or
  `CONFIG_RCU_NOCB_CPU_DEFAULT_ALL`; see `rcu_init_nohz()`.
- Which CPU decides: the CPU that executes `call_rcu()`;
  `__call_rcu_common()` tests `rcu_rdp_is_offloaded()` on
  `this_cpu_ptr(&rcu_data)`.
- Not lazy before `rcu_scheduler_active == RCU_SCHEDULER_RUNNING`:
  `rcu_nocb_try_bypass()` does not use the bypass list until then.
- `enable_rcu_lazy`: mode 0444, so boot command line only; default is
  `!IS_ENABLED(CONFIG_RCU_LAZY_DEFAULT_OFF)`.
- With `CONFIG_RCU_LAZY_DEFAULT_OFF`: laziness is turned on by
  rcutree.enable_rcu_lazy=1; the help text in `kernel/rcu/Kconfig` says =0.
- `kfree_rcu()` is affected by laziness on two of its three paths:
  - sheaf path (`__kfree_rcu_sheaf()` in `mm/slub.c`): a full sheaf is handed
    to plain `call_rcu()`;
  - without `CONFIG_KVFREE_RCU_BATCHED`: `kvfree_call_rcu()` calls plain
    `call_rcu()`;
  - batched path: `kvfree_rcu_queue_batch()` uses `queue_rcu_work()`, which
    calls `call_rcu_hurry()`.
- `synchronize_rcu()`: its default path queues no callback, so laziness does
  not apply; only the `wait_rcu_gp(call_rcu_hurry)` fallback queues one.
- `synchronize_rcu_mult()`: passes the given functions through unchanged, so
  with `call_rcu` the wait is subject to laziness; pass `call_rcu_hurry` to
  avoid the delay.

**Callback barriers**

- `rcu_barrier_tasks_trace()`: inline `srcu_barrier()` on
  `rcu_tasks_trace_srcu_struct`.
- `rcu_barrier_tasks()`: defined only under `CONFIG_TASKS_RCU`, with no macro
  fallback. Without that option `call_rcu_tasks` is `call_rcu`, and
  `rcu_barrier()` is the matching barrier.
- `kvfree_rcu_barrier()` in `mm/slab_common.c`: waits for all pending
  `kfree_rcu()` objects; it also calls `rcu_barrier()`, in both
  `CONFIG_KVFREE_RCU_BATCHED` settings.
- `kvfree_rcu_barrier_on_cache()` under `CONFIG_KVFREE_RCU_BATCHED`: flushes
  only the given cache's sheaves, then calls `rcu_barrier()` and drains the
  batches of every CPU.
- `kmem_cache_destroy()`: calls `kvfree_rcu_barrier_on_cache()` first, so it
  runs `rcu_barrier()` for every non-NULL cache, not only for
  `SLAB_TYPESAFE_BY_RCU` ones.
- What `rcu_barrier()` alone misses of `kfree_rcu()`, for example: objects
  still in a per-CPU `rcu_free` sheaf, and objects in `struct kfree_rcu_cpu`
  batches not yet handed to `queue_rcu_work()`.
- `kfree_rcu_mightsleep()` slow path: runs `synchronize_rcu()` and `kvfree()`
  inline before it returns; no barrier covers a call that has not returned.

## Freeing after a grace period

**Unlink before reclaim**

- **Potentially unsafe usage**: freeing an object with no grace period after
  unlinking it.
  - Unsafe: when the object was ever reachable by an RCU reader and its cache
    is not `SLAB_TYPESAFE_BY_RCU`.
  - Safe: when the object was never made reachable by RCU readers.
    `dentry_free()` in `fs/dcache.c` frees at once only for dentries flagged
    `DCACHE_NORCU`, which `d_alloc_pseudo()` and `d_alloc_cursor()` set at
    allocation; every other dentry goes through `call_rcu()`.
  - Safe: when the cache is `SLAB_TYPESAFE_BY_RCU` and every reader
    revalidates. `__cleanup_sighand()` in `kernel/fork.c` calls
    `kmem_cache_free()` at once; `lock_task_sighand()` rechecks
    `tsk->sighand`.
- **Potentially unsafe usage**: plain `list_del()` on an object that RCU
  readers can reach.
  - Unsafe: on the linkage that readers traverse; it poisons `next`.
  - Safe: on a second linkage that only lock holders walk.
    `audit_del_rule()` in `kernel/auditfilter.c` does `list_del_rcu()` on
    `e->list` and `list_del()` on `e->rule.list`, both under
    `audit_filter_mutex`.
- `audit_del_rule()`: after the unlink it calls `synchronize_rcu()`, tears down
  the rule's watch, tree and mark, and only then `call_rcu()`.
- Polled grace period: a third way to wait. The cookie must be taken after the
  unlink. Under `CONFIG_KVFREE_RCU_BATCHED`, `add_ptr_to_bulk_krc_lock()` in
  `mm/slab_common.c` takes it with `get_state_synchronize_rcu_full()` when the
  pointer is queued; `kvfree_rcu_bulk()` refuses to free, under
  `WARN_ON_ONCE()`, unless `poll_state_synchronize_rcu_full()` says the grace
  period has ended.

**Reference counts after RCU lookup**

- **Potentially unsafe usage**: plain `refcount_inc()` or `atomic_inc()` on an
  object found under `rcu_read_lock()`.
  - Unsafe: when any put can take the count to zero while the object is still
    reachable, as in listing B of `Documentation/RCU/rcuref.rst`.
  - Safe: when the structure's own reference is dropped only from the RCU
    callback that follows the unlink (listing C). `find_get_pid()` in
    `kernel/pid.c` uses `get_pid()`; `free_pid()` does `idr_remove()` and then
    `call_rcu()` with `delayed_put_pid()`, which does the `put_pid()`.
- `get_file_rcu()` in `fs/file.c`: takes the reference with `file_ref_get()` on
  `f_ref`, then reloads the pointer and compares.
- `__fget_files_rcu()` in `fs/file.c`: the fd-table lookup; it does not call
  `get_file_rcu()`.
- `rcuref_t`: a typedef of an anonymous struct in `include/linux/types.h`;
  there is no struct rcuref tag.
- `rcuref_get()`: safe only if the object is freed after a grace period and
  the put cannot be overtaken by one; see "Deconstruction race" in
  `lib/rcuref.c`.
- `rcuref_put()`: disables preemption itself, callable from any context.
- `rcuref_put_rcusafe()`: does not disable preemption; the caller must be
  under `rcu_read_lock()` or non-preemptible, which `__rcuref_put()` checks
  with `RCU_LOCKDEP_WARN()`.

**Type-safe slab caches**

- **Potentially unsafe usage**: taking a lock inside the object under
  `rcu_read_lock()` without first holding a reference.
  - Unsafe: when the lock is initialised on allocation; a stale reader may
    hold or spin on it while it is re-initialised.
  - Safe: when the cache's ctor initialises the lock and nothing
    re-initialises it, and the reader rechecks identity after locking.
    `lock_task_sighand()` in `kernel/signal.c` relies on `sighand_ctor()` in
    `kernel/fork.c` and rechecks `tsk->sighand`.
- **Potentially unsafe usage**: `kmem_cache_zalloc()`, `__GFP_ZERO` or a
  whole-object `memset()` on allocation.
  - Unsafe: when a stale reader operates on a field that the zeroing changes:
    a lock, the `next` pointer of its chain, or a count in which zero is not
    the free value (`FILE_REF_ONEREF` is 0).
  - Safe: when readers only load fields and then revalidate against something
    outside the object. `journal_alloc_journal_head()` in `fs/jbd2/journal.c`
    zeroes; its reader `jbd2_write_access_granted()` rechecks `jh->b_bh`.
  - Safe: zeroing around the field readers follow. `sk_prot_alloc()` in
    `net/core/sock.c` strips `__GFP_ZERO` and calls `sk_prot_clear_nulls()`.
  - Safe: zeroing a count that is already zero on a free object and that
    readers take only with an inc-not-zero form. `vma_init()` in
    `include/linux/mm.h` does `memset()` on the whole object;
    `vma_start_read()` in `mm/mmap_lock.c` takes `vm_refcnt` with
    `__refcount_inc_not_zero_limited_acquire()`.
- `slab_want_init_on_alloc()` and `slab_want_init_on_free()` in `mm/slab.h`:
  `init_on_alloc` and `init_on_free` do not zero objects of these caches or of
  ctor caches; an explicit `__GFP_ZERO` still zeroes an object of a type-safe
  cache that has no ctor.
- Cache with a ctor: `new_slab()` in `mm/slub.c` has
  `WARN_ON_ONCE(s->ctor && (flags & __GFP_ZERO))`; it fires only when a new
  slab page is allocated.
- `refcount_inc_not_zero()`: a relaxed cmpxchg, no ordering against the key
  recheck that follows.
- `refcount_inc_not_zero_acquire()` and `refcount_set_release()` in
  `include/linux/refcount.h`: the pair meant for these caches.
  `vma_mark_attached()` in `include/linux/mmap_lock.h` uses the release form;
  `vma_start_read()` in `mm/mmap_lock.c` uses
  `__refcount_inc_not_zero_limited_acquire()`.
- After the count is set non-zero the object is visible to stale readers even
  before it is linked anywhere, so every field a reader rechecks must be
  written before that store.
- `freeptr_offset` in `struct kmem_cache_args`: the free pointer must not
  overlay a field that guards against recycling (count, key, ctor-set lock).
  `create_cache()` in `mm/slab_common.c` checks only range, alignment and that
  the cache is type-safe or has a ctor.
- `CONFIG_SLUB_RCU_DEBUG`: `slab_free_hook()` in `mm/slub.c` defers the free
  of each object of such a cache through `call_rcu()`, unless its
  `GFP_NOWAIT` allocation fails, so a missing recheck is hidden on such a
  build.

**Forms of kfree_rcu**

| Form | Handed | Context |
|---|---|---|
| `kfree_rcu(ptr, rhf)`, `kvfree_rcu(ptr, rhf)` | object and name of its head field | atomic, irqs off, `raw_spinlock_t` held; not NMI |
| `kfree_rcu_mightsleep(ptr)`, `kvfree_rcu_mightsleep(ptr)` | object only | sleepable only |
| `kfree_rcu_nolock(ptr, kvrhf)` | object and name of its `struct kvfree_rcu_head` field | any, including NMI |

- `kfree_rcu()` and `kvfree_rcu()`: the same macro, `kvfree_rcu_arg_2()`; no
  difference in context or in what may be passed.
- `kfree_rcu_nolock()`: calls `kfree_call_rcu_nolock()` in `mm/slab_common.c`;
  two-argument only; there is no kvfree or headless nolock form.
- `kfree_rcu_nolock()` on a vmalloc, large-kmalloc or remote-node object: not
  queued directly; `defer_kfree_rcu()` hands it to `irq_work`, which calls
  `kvfree_call_rcu()`.
- `struct kvfree_rcu_head` in `include/linux/types.h`: one pointer under
  `CONFIG_KVFREE_RCU_BATCHED`, a wrapped `struct rcu_head` otherwise. There is
  no struct rcu_ptr.
- Field type for `kfree_rcu()` and `kvfree_rcu()`: `struct rcu_head` or
  `struct kvfree_rcu_head`; `kvfree_rcu_arg_2()` casts the field's address, so
  the compiler checks neither.
- Field type for `kfree_rcu_nolock()`: `struct kvfree_rcu_head` only; the
  address is passed uncast.
- Object freed by both `kfree_rcu()` and `kfree_rcu_nolock()`: a union of the
  two head types, as `struct test_kfree_rcu_struct` in
  `lib/tests/slub_kunit.c`.
- Offset limit: `BUILD_BUG_ON(offsetof(typeof(*(ptr)), kvrhf) >= 4096)` in
  `kvfree_rcu_arg_2()` and in `kfree_rcu_nolock()`.
- There is no __is_kvfree_rcu_offset() here, and the offset is not stored in
  the head's `func`.
- Reason for the limit: `kvmalloc_obj_start_addr()` in `mm/slab.h` recovers
  the object start from the head address alone; for vmalloc and large-kmalloc
  objects it subtracts `offset_in_page()`, so the head must lie in the first
  page.

**Locks under kvfree_call_rcu**

- Caller with a head: may hold a `raw_spinlock_t` with irqs off;
  `set_cpus_allowed_force()` in `kernel/sched/core.c` calls `kfree_rcu()` with
  `p->pi_lock` held.
- NMI, or code that may have interrupted the slab allocator or `call_rcu()`:
  not allowed; `krc_this_cpu_lock()` and the barn lock spin unconditionally.
  `kfree_rcu_nolock()` is the form for those.
- Implementation on `CONFIG_PREEMPT_RT`, call with a head: may take
  `raw_spinlock_t` only, because the caller may hold one; the sheaf path is
  skipped and `krcp->lock` is a `raw_spinlock_t`.
- Implementation without `CONFIG_PREEMPT_RT`, under
  `CONFIG_KVFREE_RCU_BATCHED`: before touching `krcp->lock`,
  `kvfree_call_rcu()` calls `kfree_rcu_sheaf()`. That path takes a
  `local_trylock()` and the `spinlock_t` `lock` of `struct node_barn`, may
  allocate with `GFP_NOWAIT`, may `kfree()`, and may `call_rcu()`.
- Sleeping locks such as a mutex: on no path that a call with a head can
  reach.
- Headless call without `CONFIG_PREEMPT_RT`, under
  `CONFIG_KVFREE_RCU_BATCHED`: the sheaf attempt runs first for it too;
  `might_sleep()` is still asserted on entry.
- Page allocation in `add_ptr_to_bulk_krc_lock()`: only for the headless call,
  after `krcp->lock` is dropped, with
  `GFP_KERNEL | __GFP_NORETRY | __GFP_NOMEMALLOC | __GFP_NOWARN`; never
  `GFP_NOWAIT`.
- No free array slot, with a head: the object is chained on `krcp->head`
  through `head->next`; `call_rcu()` is not used.
- Without `CONFIG_KVFREE_RCU_BATCHED`: `kvfree_call_rcu()` is `call_rcu()` with
  `kvfree_rcu_cb()`, or `synchronize_rcu()` then `kvfree()` when headless.
  There is no `krc` and no sheaf path.

**Sheaf path and PREEMPT_RT**

- `kvfree_call_rcu()` on `CONFIG_PREEMPT_RT`: never enters the sheaf path; the
  test is `!IS_ENABLED(CONFIG_PREEMPT_RT)`, not the caller's context.
- `__kfree_rcu_sheaf()` on `CONFIG_PREEMPT_RT`: still reached under
  `CONFIG_KVFREE_RCU_BATCHED`, from `kfree_call_rcu_nolock()` with
  `SLAB_FREE_NOLOCK`. It does not bail out; `VM_WARN_ON_ONCE()` fires only if
  it is entered there with spinning allowed.
- Lockdep map: `kfree_rcu_sheaf_map` in `mm/slub.c`, declared with
  `DEFINE_WAIT_OVERRIDE_MAP()` and `LD_WAIT_CONFIG`.
- Scope of the override: the whole of `__kfree_rcu_sheaf()`;
  `lock_map_acquire_try()` at entry, `lock_map_release()` on the success and
  the fail exit.
- Override on `CONFIG_PREEMPT_RT`: not taken, so lockdep still reports a
  `spinlock_t` taken there under a raw lock, unless it is a trylock;
  `check_wait_context()` skips trylocks.
- **Potentially unsafe usage**: a `spinlock_t` or `local_lock()` taken on the
  `kvfree_call_rcu()` path outside `__kfree_rcu_sheaf()`.
  - Unsafe: when a call with a head can reach it; the caller may hold a
    `raw_spinlock_t`, and nothing there overrides the wait type or keeps
    `CONFIG_PREEMPT_RT` out.
  - Safe: inside `__kfree_rcu_sheaf()`, as a trylock or only when spinning is
    allowed, as `barn_get_empty_sheaf()` does; `kfree_rcu_sheaf_map` covers it
    and `kvfree_call_rcu()` keeps RT out.
  - Safe: on the headless path only, where `might_sleep()` is asserted, as the
    `GFP_KERNEL` page allocation in `add_ptr_to_bulk_krc_lock()` under
    `can_alloc`, after `krcp->lock` is dropped.
- With `SLAB_FREE_DEFAULT`: only the per-CPU lock is a trylock;
  `barn_get_empty_sheaf()` uses `spin_lock_irqsave()`, and the empty sheaf is
  allocated with `GFP_NOWAIT`.
- With `SLAB_FREE_NOLOCK`: `spin_trylock_irqsave()`, allocation with
  `SLAB_ALLOC_NOLOCK`, `kfree_nolock()`; a full sheaf goes to `irq_work`
  instead of `call_rcu()` when `irqs_disabled()`.
- Eligibility in `kfree_rcu_sheaf()`: not a vmalloc address, `virt_to_slab()`
  non-NULL, and under `CONFIG_NUMA` `slab_nid(slab) == numa_mem_id()`.
- `cache_has_sheaves()`: tested inside `__kfree_rcu_sheaf()`, and only when
  `pcs->rcu_free` is NULL.

## SRCU

**SRCU domains**

- Token type: the fast kinds return a `struct srcu_ctr __percpu *`, not an
  `int`; it goes unchanged to the matching unlock.
- `cleanup_srcu_struct()` in `kernel/rcu/srcutree.c` sleeps: it calls
  `flush_delayed_work()`, `flush_work()` and `timer_delete_sync()`, and
  re-enables interrupts.
- `cleanup_srcu_struct()` on a `DEFINE_SRCU()` or `DEFINE_STATIC_SRCU()`
  domain: runs the same checks but, because `sda_is_static` is set (by
  `check_init_srcu_struct()` on the first update-side call), frees only
  `sup->node`; `rcu_verify_early_boot_tests()` in `kernel/rcu/update.c` does
  this.
- Static domains in a module: `srcu_module_going()` in `kernel/rcu/srcutree.c`
  calls `cleanup_srcu_struct()` and then `free_percpu()` on `ssp->sda`; the
  module does not call `cleanup_srcu_struct()` itself.
- Module unload therefore has the same requirements: no reader left and no
  callback queued; `exit_misc_binfmt()` in `fs/binfmt_misc.c` calls
  `srcu_barrier()` in its exit function.

**SRCU reader kinds**

| Kind (flavor bit) | Acquire / release | For | Domain declared with | Release in another context |
|---|---|---|---|---|
| Normal (`SRCU_READ_FLAVOR_NORMAL`) | `srcu_read_lock()` / `srcu_read_unlock()` | default; not for NMI | `DEFINE_SRCU()`, `DEFINE_STATIC_SRCU()`, `init_srcu_struct()` | no, lockdep tracks the holder |
| Normal, semaphore-like (same bit) | `srcu_down_read()` / `srcu_up_read()` | hand-off to another task or irq; not for NMI | same as normal; may share a domain with `srcu_read_lock()` | yes, no lockdep call |
| NMI-safe (`SRCU_READ_FLAVOR_NMI`) | `srcu_read_lock_nmisafe()` / `srcu_read_unlock_nmisafe()` | NMI handlers | same as normal, no special declaration | no, lockdep tracks the holder |
| Fast (`SRCU_READ_FLAVOR_FAST`) | `srcu_read_lock_fast()` / `srcu_read_unlock_fast()` | no `smp_mb()` in the reader; allowed in NMI; RCU must be watching | `DEFINE_SRCU_FAST()`, `DEFINE_STATIC_SRCU_FAST()`, `init_srcu_struct_fast()` | no, lockdep tracks the holder |
| Fast-updown (`SRCU_READ_FLAVOR_FAST_UPDOWN`) | `srcu_read_lock_fast_updown()` / `srcu_read_unlock_fast_updown()`; `srcu_down_read_fast()` / `srcu_up_read_fast()` | fast reader that can be handed off; not for NMI; RCU must be watching | `DEFINE_SRCU_FAST_UPDOWN()`, `DEFINE_STATIC_SRCU_FAST_UPDOWN()`, `init_srcu_struct_fast_updown()` | only the down/up pair |

- There is no lite kind here: no srcu_read_lock_lite() and no
  SRCU_READ_FLAVOR_LITE.
- `srcu_down_read_fast()` and `srcu_up_read_fast()`: pass
  `SRCU_READ_FLAVOR_FAST_UPDOWN`, so they go with
  `srcu_read_lock_fast_updown()` domains and, under `CONFIG_PROVE_RCU`, WARN on
  a `DEFINE_SRCU_FAST()` domain; `uretprobes_srcu` in
  `kernel/events/uprobes.c` is an example.
- `srcu_read_lock_notrace()` and `srcu_read_lock_fast_notrace()`: same flavor
  bits as normal and fast, no lockdep call; the fast one also has no
  `rcu_is_watching()` test.
- `CONFIG_NEED_SRCU_NMI_SAFE`: when set, the NMI-safe and both fast kinds
  count with `atomic_long_inc()` while the normal kind still uses
  `this_cpu_inc()` on the same counters.
- In-NMI WARNs: `srcu_down_read()` and `srcu_up_read()` WARN unconditionally;
  the normal and fast-updown readers WARN only under `CONFIG_PROVE_RCU`.
- `srcu_check_read_flavor()`: does nothing without `CONFIG_PROVE_RCU`, and is
  an empty macro under `CONFIG_TINY_SRCU`; there is no
  srcu_check_read_flavor_force().
- `__srcu_check_read_flavor()` in `kernel/rcu/srcutree.c`: records the flavor
  in the `srcu_reader_flavor` field of the running CPU's `struct srcu_data`,
  and WARNs if that CPU already holds a different one.
- Mixing across CPUs that the declaration checks below do not catch: reported
  only by the grace-period scan, "Mixed reader flavors" in
  `srcu_readers_unlock_idx()` and `srcu_readers_lock_idx()`, also only under
  `CONFIG_PROVE_RCU`.
- Declaration checks in `__srcu_check_read_flavor()`: WARN when the domain was
  declared with a flavor and the reader's differs, and WARN for a
  `SRCU_READ_FLAVOR_FAST` reader on a domain declared with none.
- `SRCU_READ_FLAVOR_FAST_UPDOWN` reader on a domain declared with none:
  `__srcu_check_read_flavor()` has no test for it.
- Without `CONFIG_PROVE_RCU`: the per-CPU `srcu_reader_flavor` is never
  written, so `srcu_readers_active_idx_check()` chooses `synchronize_rcu()` or
  `smp_mb()` from `ssp->srcu_reader_flavor`, the declaration, alone.
- **Unsafe usage**: a fast or fast-updown reader on a domain not declared with
  the matching flavor.
  - Unsafe: without `CONFIG_PROVE_RCU`, on a domain declared with no flavor
    the scan uses `smp_mb()` while the reader has only `barrier()`, and
    nothing reports it.
  - Safe: `tracepoint_srcu` in `kernel/tracepoint.c` is declared with
    `DEFINE_SRCU_FAST()`, which sets `SRCU_READ_FLAVOR_FAST` in
    `ssp->srcu_reader_flavor`, and read with `guard(srcu_fast_notrace)`.
  - Safe: `uretprobes_srcu` is declared with `DEFINE_STATIC_SRCU_FAST_UPDOWN()`
    and read with `srcu_down_read_fast()`.

**SRCU deadlocks and cleanup**

- `cleanup_srcu_struct()` inside a reader of the same domain, Tree SRCU: no
  deadlock; it hits `WARN_ON(srcu_readers_active(ssp))` and returns with
  nothing freed.
- A failed `cleanup_srcu_struct()` in `kernel/rcu/srcutree.c`: leaves
  `ssp->sda`, `ssp->srcu_sup` and any queued work in place; that work reaches
  the domain through `sup->srcu_ssp` and `sdp->ssp`, so the enclosing object
  must not be freed after a WARN.
- **Potentially unsafe usage**: `cleanup_srcu_struct()` with no
  `srcu_barrier()` before it.
  - Unsafe: when a `call_srcu()` callback can still be queued;
    `cleanup_srcu_struct()` in `kernel/rcu/srcutree.c` WARNs on
    `rcu_segcblist_n_cbs()` and returns.
  - Safe: when nothing calls `call_srcu()` on the domain and every
    `synchronize_srcu()` has returned, as `kvm_destroy_vm()` does for
    `kvm->irq_srcu`.
  - Safe: with `srcu_barrier()` after the last `call_srcu()`, as
    `kvm_destroy_vm()` does for `kvm->srcu` and `blk_mq_free_tag_set()` does
    for `set->tags_srcu`.
- `start_poll_synchronize_srcu()`, Tree SRCU: the grace period it requested
  must have ended before `cleanup_srcu_struct()`, which WARNs and returns
  while `srcu_gp_seq` is behind `srcu_gp_seq_needed`; `srcu_barrier()` does
  not wait for it.
- `cleanup_srcu_struct()` from a callback of the same domain: it sleeps, and it
  calls `flush_work()` on the work item that is running the callback.
- Lockdep coverage: only `__synchronize_srcu()`, and `synchronize_srcu()` in
  `kernel/rcu/srcutiny.c`, call `srcu_lock_sync()`; `srcu_barrier()` in
  `kernel/rcu/srcutree.c` and `cleanup_srcu_struct()` have no SRCU annotation.
- `srcu_barrier()` inside a reader of the same domain, Tree SRCU: can deadlock
  when a queued callback still waits for a grace period, and lockdep does not
  report it.
- Configuration: `srcu_lock_sync()` is empty without `CONFIG_DEBUG_LOCK_ALLOC`;
  the `RCU_LOCKDEP_WARN()` for "synchronize_srcu() in same-type SRCU (or in
  RCU) read-side critical section" is empty without `CONFIG_PROVE_RCU`.

## Tasks RCU

**Tasks flavours**

| Flavour | Reader | Update side outside `kernel/rcu/` | In-tree users, for example |
|---|---|---|---|
| Tasks RCU, `CONFIG_TASKS_RCU` | unmarked | `call_rcu_tasks()`, `synchronize_rcu_tasks()`, `rcu_barrier_tasks()` | `kernel/kprobes.c`, `kernel/bpf/trampoline.c` |
| Tasks Rude RCU, `CONFIG_TASKS_RUDE_RCU` | unmarked; any preemption-disabled region on an online CPU, idle CPUs included | `synchronize_rcu_tasks_rude()` only | `kernel/trace/ftrace.c` |
| Tasks Trace RCU, `CONFIG_TASKS_TRACE_RCU` | marked; may sleep | `call_rcu_tasks_trace()`, `synchronize_rcu_tasks_trace()`, `rcu_barrier_tasks_trace()`, `rcu_tasks_trace_expedite_current()` | sleepable BPF, faultable tracepoints, uprobes |

- `call_rcu_tasks_rude()`: `static` in `kernel/rcu/tasks.h`, used only to
  build `synchronize_rcu_tasks_rude()`; there is no rcu_barrier_tasks_rude().
- `synchronize_rcu_tasks_rude()`: returns at once, waiting for nothing, when
  `CONFIG_ARCH_WANTS_NO_INSTR` is set and `CONFIG_FORCE_TASKS_RUDE_RCU` is
  not.
- `CONFIG_TASKS_RCU`: `default NEED_TASKS_RCU && PREEMPTION` in
  `kernel/rcu/Kconfig`; users select `NEED_TASKS_RCU`, so a kernel without
  `PREEMPTION` has Tasks RCU configured out unless `FORCE_TASKS_RCU` is set.
- `CONFIG_TASKS_RCU` off: `call_rcu_tasks` and `synchronize_rcu_tasks` are
  macros for `call_rcu` and `synchronize_rcu` in `include/linux/rcupdate.h`.
- `rcu_barrier_tasks()` with `CONFIG_TASKS_RCU` off: declared, never defined,
  no macro fallback; a caller fails at link time.
- `CONFIG_TASKS_RUDE_RCU` off: `synchronize_rcu_tasks_rude()` has neither
  declaration nor fallback.
- `CONFIG_TASKS_TRACE_RCU` off: `rcu_read_lock_trace()`,
  `rcu_read_unlock_trace()` and `call_rcu_tasks_trace()` are inlines that
  `BUG()`; they are not no-ops and do not fall back to RCU.
- `guard(rcu_tasks_trace)` with `CONFIG_TASKS_TRACE_RCU` off: still defined,
  built from the two `BUG()` stubs.
- `CONFIG_TASKS_TRACE_RCU` off: `synchronize_rcu_tasks_trace()`,
  `rcu_barrier_tasks_trace()`, `rcu_tasks_trace_expedite_current()`,
  `rcu_read_lock_tasks_trace()` and `rcu_read_unlock_tasks_trace()` have no
  definition at all, so a caller does not compile.

**Tasks Trace implementation**

- Tasks Trace RCU: a mapping onto SRCU-fast; there is one
  `struct srcu_struct`, `rcu_tasks_trace_srcu_struct`, defined by
  `DEFINE_SRCU_FAST()` in `kernel/rcu/tasks.h` and exported.
- Reader and update-side functions: all static inlines in
  `include/linux/rcupdate_trace.h`.
- `CONFIG_TASKS_RCU_GENERIC`: is `TASKS_RCU || TASKS_RUDE_RCU`, so a kernel
  with only `CONFIG_TASKS_TRACE_RCU` builds none of the `struct rcu_tasks`
  code and has no Tasks grace-period kthread.
- `rcu_read_lock_trace()`: calls `__srcu_read_lock_fast()` directly, not
  `srcu_read_lock_fast()`, so `srcu_check_read_flavor()` is never run for it.
- `struct task_struct`: still holds `trc_reader_nesting` and
  `trc_reader_scp`; `rcu_read_lock_trace()` uses both.
- End of a Tasks Trace grace period, Tree SRCU: at least one RCU grace period
  has elapsed inside it. See `srcu_readers_active_idx_check()` in
  `kernel/rcu/srcutree.c`; for `SRCU_READ_FLAVOR_SLOWGP` it calls
  `synchronize_rcu()` or `synchronize_rcu_expedited()` on each scan, and
  `srcu_advance_state()` scans twice before `srcu_gp_end()`.
- Some callers rely on the guarantee unconditionally: a
  `call_rcu_tasks_trace()` callback frees memory that plain RCU readers also
  use, with no chained `call_rcu()`. For example
  `__bpf_prog_array_free_sleepable_cb()` in `kernel/bpf/core.c` and
  `bpf_selem_free_trace_rcu()` in `kernel/bpf/bpf_local_storage.c`.
- rcutorture checks the guarantee: `tasks_tracing_torture_read_lock()` in
  `kernel/rcu/rcutorture.c` sometimes protects a reader with
  `rcu_read_lock()` while the updater uses only Tasks Trace.
- Tiny SRCU (`CONFIG_TINY_SRCU`, default with `TINY_RCU`):
  `include/linux/srcutiny.h` maps `DEFINE_SRCU_FAST()` to `DEFINE_SRCU()` and
  `__srcu_read_lock_fast()` to `__srcu_read_lock()`; `srcu_barrier()` is
  `synchronize_srcu()` and `srcu_expedite_current()` is empty.
- Tiny SRCU grace period: `kernel/rcu/srcutiny.c` never calls
  `synchronize_rcu()`; callbacks run from the `srcu_drive_gp()` work item,
  which cannot run inside an RCU reader there: `CONFIG_TINY_RCU` means one
  CPU, and `__rcu_read_lock()` is `preempt_disable()`.

**Tasks Trace reader interfaces**

| Interface | Carried from lock to unlock | Defined in |
|---|---|---|
| `rcu_read_lock_trace()`, `rcu_read_unlock_trace()` | nothing | `include/linux/rcupdate_trace.h` |
| `rcu_read_lock_tasks_trace()`, `rcu_read_unlock_tasks_trace()` | the returned `struct srcu_ctr __percpu *` | `include/linux/rcupdate_trace.h` |
| `guard(rcu_tasks_trace)` | nothing; wraps the `rcu_read_lock_trace()` pair | `DEFINE_LOCK_GUARD_0()` at the end of `include/linux/rcupdate_trace.h` |

- Pointer-carrying pair: there is no guard for it.
- Returned pointer, Tree SRCU: names one of the two `srcu_ctrs[]` elements,
  not a CPU; the unlock increments on whatever CPU it runs on and
  `srcu_readers_unlock_idx()` sums over all CPUs, so a reader may migrate
  between lock and unlock.
- `rcu_read_unlock_tasks_trace()`: calls `srcu_lock_release()` on the calling
  task's lockdep state, so under `CONFIG_DEBUG_LOCK_ALLOC` the lock and the
  unlock still have to run in one task, although the pair uses neither
  `trc_reader_nesting` nor `trc_reader_scp`.
- **Unsafe usage**: closing a `rcu_read_lock_tasks_trace()` reader with
  `rcu_read_unlock_trace()`.
  - Unsafe: `rcu_read_unlock_trace()` computes `trc_reader_nesting - 1`; with
    the count at 0 it stores -1 and skips `__srcu_read_unlock_fast()`, so the
    SRCU lock count is never balanced and no later grace period ends.
  - Safe: keep the returned pointer in a local and pass it to
    `rcu_read_unlock_tasks_trace()`, as `__bpf_trace_run()` in
    `kernel/trace/bpf_trace.c` does; the unlock's `scp` parameter is what
    `__srcu_read_unlock_fast()` increments.

## RCU internals and testing

**Locking the rcu_node tree**

- Release wrappers: `raw_spin_unlock_rcu_node()`,
  `raw_spin_unlock_irq_rcu_node()` and
  `raw_spin_unlock_irqrestore_rcu_node()` in `kernel/rcu/rcu.h` each call
  `lockdep_assert_irqs_disabled()` before unlocking; the acquire wrappers
  contain no assertion.
- `smp_mb__after_unlock_lock()`: `smp_mb()` only under
  `CONFIG_ARCH_WEAK_RELEASE_ACQUIRE`, empty otherwise
  (`include/linux/rcupdate.h`).
- `CONFIG_ARCH_WEAK_RELEASE_ACQUIRE`: selected only in `arch/powerpc/Kconfig`
  and, if `ARCH_USE_QUEUED_SPINLOCKS`, in `arch/riscv/Kconfig`, so on other
  architectures a plain `raw_spin_lock()` on the field behaves the same as
  the wrapper and testing there cannot show a missing barrier.
- The wrappers are macros over any structure with a `__private` field named
  `lock`: `struct rcu_tasks_percpu` in `kernel/rcu/tasks.h` and
  `struct srcu_data`, `struct srcu_node`, `struct srcu_usage` in
  `include/linux/srcutree.h` use them too.
- SRCU: those locks are `raw_spinlock_t`; there is no non-raw
  spin_lock_irqsave_rcu_node() family in this tree.
- Lock order, outermost first: `rcu_state.ofl_lock`,
  `rcu_state.barrier_lock`, `rdp->nocb_lock`, then either
  `rdp->nocb_bypass_lock` or the leaf `->lock`, then one ancestor's `->lock`.
  See `rcutree_report_cpu_starting()` and `rcutree_migrate_callbacks()` in
  `kernel/rcu/tree.c`.
- `rdp->nocb_lock` before `->lock`: blocking in `nocb_gp_wait()`, trylock in
  `nocb_cb_wait()` and `rcu_advance_cbs_nowake()`.
- With `->lock` held and an offloaded `rdp`: `__note_gp_changes()` skips
  `rcu_advance_cbs()` and `rcu_accelerate_cbs()`, and `rcu_report_qs_rdp()`
  skips `rcu_accelerate_cbs()`; both callees assert `nocb_lock` through
  `rcu_lockdep_assert_cblist_protected()`.
- `rdp->nocb_gp_lock`: taken after `nocb_lock` is dropped
  (`__call_rcu_nocb_wake()`), and `__wake_nocb_gp()` drops it before
  `swake_up_one()`.
- **Unsafe usage**: a wakeup, `resched_cpu()` or `task_call_func()` while a
  `struct rcu_node` `->lock` is held.
  - Unsafe: these take `pi_lock` or the rq lock, while
    `__call_rcu_common()` takes the leaf `->lock` in `check_cb_ovld()`
    whatever locks its caller holds.
  - Safe: record the need under the lock and act after the release, as
    `force_qs_rnp()` does with `rsmask`, `rcu_print_task_stall()` with its
    `ts[]` array, `rcu_gp_cleanup()` with `sq`, and the callers of
    `rcu_start_this_gp()` with its return value.
- `rcu_read_unlock_special()` in `kernel/rcu/tree_plugin.h`, entered with
  irqs, preemption or bh disabled: returns without taking any `->lock`; the
  report is made later through `rcu_preempt_deferred_qs_irqrestore()`.
- `rcutorture_one_extend()` in `kernel/rcu/rcutorture.c`: sometimes holds
  `current->pi_lock` across the reader unlock, unless `cur_ops->no_pi_lock`
  is set, so rcutorture can catch a patch that makes the unlock path wake a
  task.
- `call_rcu()` from an irqs-disabled caller on an offloaded CPU:
  `__call_rcu_nocb_wake()` uses `wake_nocb_gp_defer()` (timer) instead of
  `wake_nocb_gp()`.

**Torture tests**

- No mandatory minimum is written in the tree:
  `Documentation/RCU/torture.rst` says not all changes need all scenarios,
  and gives `--configs 'SRCU-N SRCU-P'` for a Tree SRCU change.
- `kvm.sh` with no `--configs`: runs
  `tools/testing/selftests/rcutorture/configs/rcu/CFLIST`; the word `CFLIST`
  inside `--configs` expands to the same list, as in `'5*CFLIST'`.
- `CFLIST` TREE entries: `TREE01` to `TREE05`, `TREE07` and `TREE09` only.
- Scenario files present but not in `CFLIST`, run only when named in
  `--configs`: `TREE06`, `TREE08`, `TREE10`, `NOCB01`, `NOCB02`, `TRIVIAL`,
  `TRIVIAL-PREEMPT`, `BUSTED`, `BUSTED-BOOST`.
- `rcu_nocbs=all`: only in `TREE08.boot`, `NOCB01.boot` and `NOCB02.boot`,
  so a default run never boots with every CPU offloaded.
- `CONFIG_PREEMPT_RT`: set by no file under
  `tools/testing/selftests/rcutorture/configs/rcu/`; `torture.sh` adds it to
  `TREE03` through `--kconfig` (`--do-rt`, on by default).
- `torture.sh` defaults: KASAN pass on, KCSAN pass off; `--do-kcsan` or
  `--do-all` turns KCSAN on.
- Working directory: `kvm.sh` changes to the top of the tree itself;
  `torture.sh` builds its paths from `pwd` and must be started there.
- `kvm.sh` defaults: 30 minutes per scenario; with neither `--cpus` nor
  `--allcpus` each scenario runs in its own batch, one after another.
- Only one `kvm.sh` per source tree: it takes a `flock` on `.kvm.sh.lock`
  and exits if another run holds it; `--kill-previous` kills the holder.
- `tools/testing/selftests/rcutorture/Makefile`: its `all` target runs only
  `kvm.sh --duration 10 --configs TREE01`.
- `kvm.sh` exit status comes from `kvm-recheck.sh`: 1 for `.config` errors,
  2 for build errors, 3 for runtime errors; when several kinds occur the
  highest number wins.
- `.config` errors: `configcheck.sh` reports a scenario when the built
  `.config` lacks a line that the scenario file sets to other than `=n`, or
  sets an option that the file gives as `=n`; `#CHECK#` lines are tested
  too. So a patch that renames or re-gates a `CONFIG_RCU_` option that a
  scenario turns on must update the scenario files.
- Runtime errors: `parse-console.sh` flags console lines matched by
  `console-badness.sh`, whose patterns include `Warn`, `BUG` and `!!!`, so
  a new message under `kernel/rcu/` with such text fails every scenario that
  prints it.

## Model gaps

### Other mistakes models make

- Models take `call_rcu_tasks_rude()` and rcu_barrier_tasks_rude() to be
  callable, because `Documentation/RCU/whatisRCU.rst` lists both. The first is
  `static` in `kernel/rcu/tasks.h` and the second is defined nowhere.
- Models take `CONFIG_PREEMPT_RCU` to follow `CONFIG_PREEMPTION`, and Tiny RCU
  to mean a non-preemptible kernel. rcutorture builds both counter-examples
  with `CONFIG_PREEMPT_LAZY=y` and `CONFIG_PREEMPT_DYNAMIC=n`: `TREE04` checks
  `CONFIG_PREEMPT_RCU=n` and `TINY01` checks `CONFIG_TINY_RCU=y`, both in
  `tools/testing/selftests/rcutorture/configs/rcu/`.
- Models take Tasks Trace RCU to have its own `struct rcu_tasks` instance and
  kthread. `synchronize_rcu_tasks_trace()` is `synchronize_srcu()`, so under
  `CONFIG_TREE_SRCU` and `CONFIG_PROVE_RCU` it gets the `RCU_LOCKDEP_WARN()` of
  `__synchronize_srcu()`, which fires when `rcu_lock_map`, `rcu_bh_lock_map` or
  `rcu_sched_lock_map` is held.
- Models take Tasks Trace readers to be safe wherever RCU is not watching. The
  help text of `CONFIG_TASKS_TRACE_RCU_NO_MB` in `kernel/rcu/Kconfig` makes the
  builder promise that no tracing operation is attached to code that runs
  where `rcu_is_watching()` returns false.
- Models take `list_for_each_entry_rcu()` and `hlist_for_each_entry_rcu()` to
  warn under `CONFIG_PROVE_RCU` when used outside a reader. `__list_check_rcu()`
  in `include/linux/rculist.h` checks only under `CONFIG_PROVE_RCU_LIST`, which
  depends on `RCU_EXPERT`; otherwise the optional condition argument is not
  evaluated.
- Models take `rcu_segcblist_advance()` to take a grace-period number. It takes
  only the list and tests each segment's `struct rcu_gp_seq` with
  `poll_state_synchronize_rcu_full()`; `srcu_segcblist_advance()` is the form
  with a sequence argument.
- Models take `srcu_funnel_gp_start()` to queue the grace-period work itself.
  When it starts a grace period and `srcu_init_done` is set, it calls
  `irq_work_queue()` under the `struct srcu_usage` lock, and `srcu_irq_work()`
  calls `queue_delayed_work()`.
- Models take `WARN_ON_ONCE(!rcu_read_lock_held())`, or `lock_is_held()` on the
  map, as the way to assert a reader. `lockdep_assert_in_rcu_read_lock()`,
  `lockdep_assert_in_rcu_read_lock_bh()`,
  `lockdep_assert_in_rcu_read_lock_sched()` and
  `lockdep_assert_in_rcu_reader()` go through `lockdep_assert_rcu_helper()`, so
  under `CONFIG_PROVE_RCU` they also fire when `rcu_is_watching()` or
  `rcu_lockdep_current_cpu_online()` is false.
- Models take the reader primitives to carry sparse `__acquire()` annotations.
  They carry `__acquires_shared(RCU)` and related attributes from
  `include/linux/compiler-context-analysis.h`, which are empty under sparse and
  active only with `CONFIG_WARN_CONTEXT_ANALYSIS` (`lib/Kconfig.debug`), and
  only for objects whose Makefile sets `CONTEXT_ANALYSIS := y` or the
  per-object form, as `CONTEXT_ANALYSIS_kcov.o := y` in `kernel/Makefile`,
  unless `CONFIG_WARN_CONTEXT_ANALYSIS_ALL` is set.
