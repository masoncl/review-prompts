| Pointer | Use it when |
|---|---|
| `rings` | `uring_lock` or `completion_lock` is held, or the ring lacks `IORING_SETUP_DEFER_TASKRUN` |
| `rings_rcu` through `io_get_rings()` | inside an RCU read section, or with `uring_lock` or `completion_lock` held |
| `rings_rcu` through `rcu_dereference()` | the caller is always inside an RCU read section |

- `io_get_rings()` in `io_uring/io_uring.h`: always dereferences `rings_rcu`,
  with lockdep conditions for the two locks; it never returns `rings`.
- `rcu_dereference()` on `rings_rcu` directly: `io_eventfd_signal()` and
  `io_ctx_mark_taskrun()`.
- `io_eventfd_signal()`: tests the result for NULL; `io_rings_free()` clears
  `rings_rcu`.
- `rings` during a resize: NULL from the start of the copy until the swap;
  `rings_rcu` keeps the old rings until the new ones are assigned.
- `__io_sqring_full()`, `__io_sqring_entries()`, `__io_cqring_events()`,
  `__io_cqring_events_user()`: call `io_get_rings()` and do not enter RCU; the
  caller enters RCU, as `io_uring_poll()` does, or holds `uring_lock`, as
  `io_submit_sqes()` and `__io_cqring_overflow_flush()` do.
- `io_sqring_full()` and `io_sqring_entries()`: enter RCU themselves.
- `io_cqring_wait()`: sets its local pointer to NULL after
  `rcu_read_unlock()` and fetches again later.
- `sq.head` with `IORING_SETUP_SQ_REWIND`: `io_commit_sqring()` does not
  publish it and resets `cached_sq_head` to 0.
- **Potentially unsafe usage**: dereferencing `rings` with neither
  `uring_lock` nor `completion_lock` held.
  - Unsafe: on a ring with `IORING_SETUP_DEFER_TASKRUN`;
    `io_register_resize_rings()` sets it to NULL and later frees the old
    rings.
  - Safe: on a ring that cannot have `IORING_SETUP_DEFER_TASKRUN`, as in
    `io_req_normal_work_add()` and `io_sq_thread()`;
    `io_register_resize_rings()` rejects such rings.
  - Safe: under `completion_lock` alone, as `io_cqring_add_overflow()` does;
    resize holds `completion_lock` over the swap.
