| State | Fields | Protection in this tree |
|---|---|---|
| Task work list | `work_list` (`struct mpscq`), cursor `work_head` | push: no lock; pop: `uring_lock` |
| Timeout lists | `timeout_list`, `ltimeout_list`, `cq_last_tm_flush` | `timeout_lock`, both lists |
| Buffer rings | `io_bl_xa` | lookup: `uring_lock`; store, erase: `uring_lock` and `mmap_lock`; mmap lookup: `mmap_lock` |
| Mapped regions | `ring_region`, `sq_region`, `param_region` | `mmap_lock` while the ring file exists |

- `mpscq_push()` on `work_list`: any context, inside the RCU section of
  `io_req_local_work_add()`.
- `mpscq_pop()` on `work_list`: one consumer at a time, serialised by
  `uring_lock`, not by task identity.
- `io_cancel_local_task_work()`: pops under `uring_lock` without testing
  `submitter_task`; `io_ring_exit_work()` calls it from a kworker.
- `io_lockdep_assert_cq_locked()` in `io_uring/io_uring.h`: states the CQE
  cache rule per ring type; see "CQ locking".
- There is no io_create_region_mmap_safe() here; `io_region_publish()` in
  `io_uring/memmap.h` copies a finished region into the ctx under `mmap_lock`.
- `io_region_validate_mmap()` and `io_pbuf_get_region()`: assert `mmap_lock`.
- No lock taken, regions: `io_allocate_scq_urings()` fills `ring_region` and
  `sq_region` before the ring file exists; `io_rings_free()` runs from
  `io_ring_ctx_free()`.
