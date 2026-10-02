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
