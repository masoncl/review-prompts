- Both queues are a `struct mpscq` (defined in `include/linux/io_uring_types.h`,
  operations in `io_uring/mpscq.h`), not a `struct llist_head` and not a
  `struct io_wq_work_list`.
- Both queues are FIFO: the runners in `io_uring/tw.c` do not call
  `llist_reverse_order()`.
- Consumer cursor: kept outside the queue, and every `mpscq_pop()` needs it.

| Queue | Producer side | Consumer cursor | Runners |
|---|---|---|---|
| per task | `task_list` of `struct io_uring_task` | `task_head` of `struct io_uring_task` | `tctx_task_work_run()` |
| per ring | `work_list` of `struct io_ring_ctx` | `work_head` of `struct io_ring_ctx` | `__io_run_local_work()`; `io_cancel_local_task_work()` |

- There is no work_llist, retry_llist or io_handle_tw_list() in this tree.
- `__io_run_local_work_loop()` hitting `max_events`: the remaining entries
  stay on `work_list`; nothing is moved to a second list.
- `tctx_task_work_run()`: takes `max_entries` and `count`, pops and calls the
  handlers itself; entries past `max_entries` stay on `task_list`.
