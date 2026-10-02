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
