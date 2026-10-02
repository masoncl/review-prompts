- Map reference: none is held by any of the three kinds; `cb->map` in
  `struct bpf_async_cb` and `ctx->map` in `struct bpf_task_work_ctx` are plain
  pointers.
- Program reference for `BPF_TIMER` and `BPF_WORKQUEUE`: taken by
  `bpf_async_update_prog_callback()` at set_callback time, not at start.
- `bpf_timer_start()` and `bpf_wq_start()`: take a temporary reference on
  `cb->refcnt` and drop it once the start was issued; they return `-ENOENT`
  once `refcnt` has reached zero.
- `bpf_timer_cancel_and_free()` and `bpf_wq_cancel_and_free()`: both are
  `bpf_async_cancel_and_free()`; it does not read `hrtimer_running` and does
  not queue the cancel to a workqueue.
- `bpf_async_cancel_and_free()`: calls `hrtimer_try_to_cancel()` or
  `cancel_work()` inline, or queues `BPF_ASYNC_CANCEL` with
  `bpf_async_schedule_op()` when `defer_timer_wq_op()` is true; neither waits
  for a running callback.
- `bpf_async_schedule_op()` failing in `kmalloc_nolock()`: the cancel is
  skipped and the last reference dropped; `bpf_async_cb_rcu_tasks_trace_free()`
  cancels later.
- `bpf_async_cb_rcu_tasks_trace_free()`: runs after an RCU tasks trace grace
  period, cancels again, and requeues itself for another grace period while
  the callback is still running; only then is the `struct bpf_async_cb` freed.
- `bpf_task_work_cancel_and_free()`: does not wait; it queues
  `task_work_cancel()` to irq_work only if the state was `BPF_TW_SCHEDULED`; a
  callback that later sees `BPF_TW_FREED` returns without calling the program.
- Last user reference: `bpf_map_put_uref()` calls `map_release_uref`, which
  for the map types that can hold these fields is
  `array_map_free_internal_structs()`, `htab_map_free_internal_structs()` or
  `rhtab_map_free_internal_structs()`; there is no
  htab_map_free_timers_and_wq, htab_free_malloced_timers_and_wq or
  array_map_free_timers_wq.
- `bpf_map_free_internal_structs()`: what each of them calls per element; it
  covers `BPF_TASK_WORK` as well as timer and wq.
- `htab_free_malloced_internal_structs()`: walks only elements linked in a
  bucket; `htab_free_prealloced_internal_structs()` walks every preallocated
  element, the extra ones included.
- `bpf_task_work_acquire_ctx()` after `usercnt` is 0: returns `-EBUSY` and
  calls `bpf_task_work_cancel_and_free()` on the field.
