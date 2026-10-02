Rows that differ from the usual picture:

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
