- Barrier: `__schedule()` calls `rq_lock()` then `smp_mb__after_spinlock()`;
  there is no smp_mb__before_spinlock() in this tree.
- `smp_mb__after_spinlock()`: orders the caller's state store, which may be a
  plain `__set_current_state()`, before the `signal_pending_state()` load in
  `try_to_block_task()`.
- `TASK_RUNNING` store on a still-queued task, for `p != current`: made by
  `ttwu_runnable()` under the same rq lock, so the lock itself orders it
  against the `prev_state` read.
- `hrtick_schedule_enter()` (`CONFIG_SCHED_HRTICK`): runs right after the
  barrier; while `rq->hrtick_sched` is set, `hrtick_start()` called during the
  pick only records the delay, and `hrtick_schedule_exit()` arms the timer.
- `rq->clock_update_flags = RQCF_UPDATED`: stored directly after
  `update_rq_clock()`, before `try_to_block_task()` and the pick, so
  `RQCF_ACT_SKIP` covers only that one `update_rq_clock()` call.
- `block_task()` flags: `DEQUEUE_SLEEP | DEQUEUE_NOCLOCK`, plus
  `DEQUEUE_SPECIAL` when `is_special_task_state()` matches `prev_state`.
- `should_block`: `__schedule()` passes `!task_is_blocked(prev)`; it is false
  only when `sched_proxy_exec()` is true and `prev->blocked_on` is set, and
  then `prev` stays queued.
- Signal branch of `try_to_block_task()`: besides storing `TASK_RUNNING` it
  writes `*task_state_p`, so `trace_sched_switch()` reports a running `prev`,
  and calls `clear_task_blocked_on()`; `p->is_blocked` stays 0.
- `switch_count = &prev->nvcsw`: assigned after `try_to_block_task()`
  whatever it returned, so a sleep cancelled by a signal that still switches
  counts as voluntary.
- `preempt` has two meanings: `sched_mode > SM_NONE` for `schedule_debug()`
  and `rcu_note_context_switch()`; `sched_mode == SM_PREEMPT` from the
  `prev_state` read onwards.
- `SM_RTLOCK_WAIT`: preemption only in the first meaning; `prev` blocks on its
  state like `SM_NONE`.
- `SM_RTLOCK_WAIT` and `saved_state`: `__schedule()` never touches it;
  `current_save_and_set_rtlock_wait_state()` in the caller does.
- `SM_RTLOCK_WAIT` and signals: `signal_pending_state()` still runs and
  returns 0, because `TASK_RTLOCK_WAIT` has neither `TASK_INTERRUPTIBLE` nor
  `TASK_WAKEKILL`.
- `SM_IDLE`: is -1, so preemption in neither meaning; `try_to_block_task()`
  is never called; a switch is still counted, in `prev->nivcsw`.
- `SM_IDLE` shortcut: with `rq->nr_running` 0 and `scx_enabled()` false it
  sets `next = prev` and `rq->next_class = &idle_sched_class` by hand and
  jumps past the pick.
