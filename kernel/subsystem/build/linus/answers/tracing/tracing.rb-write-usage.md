- `cpu_buffer->nest`: not changed by a reserve; only
  `ring_buffer_nest_start()` and `ring_buffer_nest_end()` change it.
- Length limit: `rb_subbuf_max_data_size()`. `struct trace_buffer` has no
  `max_data_size` field and there is no BUF_MAX_DATA_SIZE; the only disable
  tests in `ring_buffer_lock_reserve()` are the two `record_disabled`
  counters.
- Second reserve in the same context without `ring_buffer_nest_start()`:
  `trace_recursive_lock()` lets the first one through on
  `RB_CTX_TRANSITION`; NULL comes only when that bit is already set.
- Nested reserve inside an open reserve of the same context: bracket it with
  `ring_buffer_nest_start()` and `ring_buffer_nest_end()`, as
  `__synth_event_trace_start()` and `__synth_event_trace_end()` in
  `kernel/trace/trace_events_synth.c` do.
- `ring_buffer_lock_reserve()` also returns NULL:
  - in NMI without `CONFIG_ARCH_HAVE_NMI_SAFE_CMPXCHG` or with
    `CONFIG_GENERIC_ATOMIC64`;
  - with absolute timestamps, when the event length (header included) plus
    `RB_LEN_TIME_EXTEND` exceeds `rb_subbuf_max_data_size()`;
  - on a remote buffer, every time.
- Swapped-buffer test in `rb_reserve_next_event()`: compiled only under
  `CONFIG_RING_BUFFER_ALLOW_SWAP`.
- Retry limit in `rb_reserve_next_event()`: 1000 loops, then `RB_WARN_ON()`
  leaves `buffer->record_disabled` raised.
- `ring_buffer_event_time_stamp()`: valid only between reserve and commit, in
  the context that reserved; it indexes `event_stamp[]` by the nesting level
  in `committing`.
- **Unsafe usage**: enabling preemption or sleeping between
  `ring_buffer_lock_reserve()` and `ring_buffer_unlock_commit()`, a page
  fault that sleeps included.
  - Unsafe: when the code between them can schedule;
    `ring_buffer_unlock_commit()` finds the CPU buffer with
    `raw_smp_processor_id()`; `reset_disabled_cpu_buffer()` and
    `ring_buffer_subbuf_order_set()` rely on `synchronize_rcu()` to have
    waited for every open commit.
  - Safe: copy user data before the reserve, as `tracing_mark_write()` does
    with `trace_user_fault_read()`; `write_marker_to_buffer()` then copies
    from that kernel buffer between reserve and commit.
  - Safe: a user copy that cannot sleep, under `pagefault_disable()`, as
    `copy_nofault()` in `user_event_ftrace()` in
    `kernel/trace/trace_events_user.c`; a failed copy discards the event.
