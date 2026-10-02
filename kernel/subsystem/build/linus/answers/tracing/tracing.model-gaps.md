- Models take comments near this code as proof that a tracepoint disables
  preemption. The comment in `trace_event_buffer_reserve()` says the tracepoint
  itself disables preemption, and the one above `event_triggers_call()` says
  `rcu_read_lock_sched()` is held; `__DECLARE_TRACE()` in
  `include/linux/tracepoint.h` does neither.
- Models take `tracing_mark_write()` to copy user memory between reserve and
  commit with a nofault copy. `trace_user_fault_read()`, which does its copy,
  must be entered with preemption disabled, enables preemption while it
  copies, and its buffer is valid only while preemption stays off.
  `ftrace_syscall_enter()` in `kernel/trace/trace_syscalls.c` also reaches it,
  through `syscall_get_data()`, before its reserve.
- Models take `event_mutex` to be the only lock on `ftrace_events`.
  `__register_event()` and the removal paths also hold `trace_event_sem`
  (`kernel/trace/trace_output.c`) for write; it nests inside `event_mutex` and
  `trace_types_lock`, see `trace_remove_event_call()`.
- Models take an fprobe handler to get a `struct pt_regs *`. Both
  `entry_handler` and `exit_handler` of `struct fprobe` get a
  `struct ftrace_regs *`; see `include/linux/fprobe.h`.
- Models take trigger data to be freed in place after a grace period.
  `trigger_data_free()` in `kernel/trace/trace_events_trigger.c` queues it on
  `trigger_data_free_list`; a kthread, or the caller through
  `trigger_data_free_queued_locked()` when no kthread could be created, calls
  `tracepoint_synchronize_unregister()` before the free.
- Models take trace option masks to be named constants. `trace_flags` is a
  `u64` tested with `TRACE_ITER()` (`kernel/trace/trace.h`); apart from
  `TRACE_ITER_SYM_MASK` only the bit numbers have names.
