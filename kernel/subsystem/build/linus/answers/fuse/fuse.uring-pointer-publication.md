| Object | Store | Loads |
|---|---|---|
| `fch->ring` | `smp_store_release()` under `fch->lock` | `smp_load_acquire()` in the three setup handlers; `READ_ONCE()` in `fuse_uring_ready()`; plain elsewhere |
| `ring->queues[qid]` | `smp_store_release()` under `fch->lock` | `smp_load_acquire()` in `fuse_uring_add_bufpool()`; plain in `fuse_uring_create_queue()`; `READ_ONCE()` elsewhere |
| `ring->ready` | `smp_store_release()` after `WRITE_ONCE()` of `fiq->ops` | `smp_load_acquire()` in `fuse_uring_ready()` |

- `fuse_uring_create()`: has no test for an existing ring; it runs once, from
  `fuse_uring_conn_init()`, before `fch->initialized` is stored with release.
- `fuse_uring_create_queue()` when the slot is taken: frees its queue; returns
  the existing one for REGISTER and `-EEXIST` for
  `FUSE_IO_URING_CMD_ADD_QUEUE`.
- Lifetime: pointers stay until `fuse_uring_destruct()`, which
  `delayed_release()` runs after the last `fuse_conn_put()`; a reader needs
  the `struct fuse_conn` behind `fch->conn` kept alive for the whole use.
- **Unsafe usage**: using `ring->queues[qid]` without a NULL test.
  - Safe: test `qid < ring->nr_queues`, load once, test for NULL, as
    `fuse_uring_commit_fetch()` does; a slot stays NULL until its queue is
    created.
  - Safe: after `fuse_uring_ready()`, `fuse_uring_task_to_queue()` still tests
    and its callers handle NULL.
- **Potentially unsafe usage**: plain load of `fch->ring`.
  - Unsafe: when nothing orders the load after `fuse_uring_create()`; the
    reader may see the pointer before `nr_queues` and `queues`.
  - Safe: after `smp_load_acquire()` of `fch->initialized`, as
    `fuse_uring_commit_fetch()` is reached through `fuse_uring_cmd()`.
  - Safe: after taking and dropping `fch->lock` with `connected` cleared, as
    `fuse_uring_abort()` is reached from `fuse_chan_abort()`;
    `fuse_uring_create()` tests `connected` under that lock.
- **Potentially unsafe usage**: touching the lists or `stopped` of a queue
  without `queue->lock`.
  - Unsafe: while a command, a request or teardown can still reach the queue;
    every list move runs under `queue->lock`, see the assert in
    `fuse_uring_add_req_to_ring_ent()`.
  - Safe: take `queue->lock` first, then test `queue->stopped`, as
    `fuse_uring_queue_fuse_req()` does.
  - Safe: in `fuse_uring_destruct()`, which runs from `delayed_release()`
    after the last `fuse_conn_put()`; each installed device and a pending
    `async_teardown_work` hold a connection reference.
