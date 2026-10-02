# io_uring Subsystem

## Main structures

### Objects and how they relate

- Where the core lives: task_work is in `io_uring/tw.c` and `io_uring/tw.h`,
  `io_cqring_wait()` in `io_uring/wait.c`, `io_uring_try_cancel_requests()`
  and `io_uring_cancel_generic()` in `io_uring/cancel.c`; `io_uring/io_uring.c`
  keeps setup, submit, issue and CQ posting.
- `struct mpscq`: the type of both task_work queues; code under `io_uring/`
  does not call `llist_add()`.
- `struct io_tw_req`: what a task_work callback (`io_req_tw_func_t`) receives,
  by value, with an `io_tw_token_t`; the request is `tw_req.req`.
- `flags` in `struct io_ring_ctx`: holds only the `IORING_SETUP_*` flags;
  internal ring state is in `int_flags`.
- CQ locking is decided per ring. `io_uring_create()` sets
  `IO_RING_F_LOCKLESS_CQ` for `IORING_SETUP_DEFER_TASKRUN` or
  `IORING_SETUP_IOPOLL`; `IORING_SETUP_SINGLE_ISSUER` alone does not set it.
  - With `IO_RING_F_LOCKLESS_CQ`: `uring_lock` serialises the CQ.
  - Without it: `__io_submit_flush_completions()` takes `completion_lock`
    even though it holds `uring_lock`.
  - `cq_overflow_list`: under `completion_lock` on every ring;
    `io_cqring_add_overflow()` asserts it.
- Entry size is not fixed per ring:
  - `IORING_SETUP_CQE_MIXED`: a CQE with `IORING_CQE_F_32` takes two CQ slots;
    `io_fill_nop_cqe()` posts an `IORING_CQE_F_SKIP` filler when one would
    straddle the ring end.
- `struct io_kiocb` is not always built from an SQE. For example
  `io_msg_data_remote()` in `io_uring/msg_ring.c` allocates one from
  `req_cachep` only to carry a CQE to another ring by task_work.
  - Such a request takes its own `ctx->refs` reference, in
    `io_msg_remote_post()`.
- `struct io_rsrc_node`: unregistering does not wait for requests.
  `io_rsrc_data_free()` drops the table's reference on each slot and frees
  the table; the node lives until the last request puts it.
  - `refs` is a plain `int`; `io_put_rsrc_node()` asserts `uring_lock`.
- `struct io_mapped_ubuf`: has its own `refcount_t` `refs`, because
  `io_register_clone_buffers()` makes nodes in two rings point at one buffer.
- `struct io_br_sel`: the result of a provided-buffer selection.
  - `buf_list` in it is NULL after a selection made with
    `IO_URING_F_UNLOCKED`; the list can go away once `uring_lock` is dropped.
- `struct io_restriction` also hangs off the task, as `io_uring_restrict` in
  `struct task_struct`. It is set by `io_uring_register()` with fd -1.
  - `__io_uring_fork()` copies it to the child; `io_uring_create()` copies it
    into every ring the task creates (`io_ctx_restriction_clone()`).
- `struct io_bpf_filters`: per-opcode classic BPF filters inside a
  `struct io_restriction`; refcounted and shared copy-on-write between task
  and rings. `io_submit_sqe()` runs them after prep; a deny fails the request
  with `-EACCES`.
- `struct io_uring_bpf_ops` (`io_uring/bpf-ops.h`): a BPF struct_ops attached
  to one ring. While `loop_step` is set in the ctx, `io_uring_enter()` does
  nothing but `io_run_loop()`.
  - `struct iou_ctx`: an empty type; the `struct io_ring_ctx` pointer is cast
    to it for the BPF program.
- `struct io_zcrx_ifq` (`io_uring/zcrx.h`): one zero-copy receive queue. A
  ring holds it in the `zcrx_ctxs` xarray, but does not own it alone.
  - Another ring can import it (`ZCRX_REG_IMPORT`), so it has its own `refs`
    and `user_refs`.
  - `master_ctx`: the one ring that receives its notification CQEs.
  - Registering needs `IORING_SETUP_DEFER_TASKRUN` and one of
    `IORING_SETUP_CQE32` or `IORING_SETUP_CQE_MIXED`.

## Where to look

### Source files

- Files not in the table: `io_uring/Makefile` gives the option of each; those
  on its `obj-$(CONFIG_IO_URING)` line need no other option.
- `Kbuild` enters `io_uring/` only under `CONFIG_IO_URING`, so every option
  in the table is in addition to that one.

| Job | File | Built only under | Easy to miss |
|---|---|---|---|
| Task work | `io_uring/tw.c` | — | `tctx_task_work()` is here, not in `io_uring/io_uring.c`; `io_req_task_work_add()` is an inline in `io_uring/tw.h` |
| Waiting for completions | `io_uring/wait.c` | — | `io_cqring_wait()` is here, not in `io_uring/io_uring.c` |
| Registered resources | `io_uring/rsrc.c` | — | `io_fixed_fd_install()` and `io_fixed_fd_remove()` are in `io_uring/filetable.c` |
| Worker pool | `io_uring/io-wq.c` | `CONFIG_IO_WQ` | promptless `bool` in `fs/Kconfig`; `config IO_URING` in `init/Kconfig` selects it, so it is built whenever io_uring is |
| Zero-copy send notifications | `io_uring/notif.c` | — | not gated on `CONFIG_NET`; the only caller of `io_alloc_notif()` is in `io_uring/net.c`, which is built under `CONFIG_NET` |
| Zero-copy receive | `io_uring/zcrx.c` | `CONFIG_IO_URING_ZCRX` | `def_bool y` with no prompt in `io_uring/Kconfig`; its `depends on` lines decide it, for example `NET_RX_BUSY_POLL` |
| Passthrough commands | `io_uring/uring_cmd.c` | — | socket commands (`io_uring_cmd_sock()`) are in `io_uring/cmd_net.c`, built under `CONFIG_NET` |
| BPF hooks: per-opcode filters | `io_uring/bpf_filter.c` | `CONFIG_IO_URING_BPF` | classic BPF programs, run from `io_submit_sqe()` in `io_uring/io_uring.c`; `def_bool y` in `io_uring/Kconfig`, depends on `BPF` and `NET` |
| BPF hooks: struct_ops | `io_uring/bpf-ops.c` | `CONFIG_IO_URING_BPF_OPS` | `def_bool y` in `io_uring/Kconfig`, depends for example on `DEBUG_INFO_BTF`; there is no bpf.c under `io_uring/` |
| BPF hooks: the loop that calls `loop_step` | `io_uring/loop.c` | — | built without `CONFIG_IO_URING_BPF_OPS`, but only `io_uring/bpf-ops.c` sets `ctx->loop_step` |
| Test-only file | `io_uring/mock_file.c` | `CONFIG_IO_URING_MOCK_FILE` | `tristate` in `init/Kconfig`, so it can be a module; registers a misc device |

## The ring context and its locks

**Internal ring state flags**

- `int_flags`: one `unsigned int` in the first, read-mostly group of
  `struct io_ring_ctx`, next to `flags`.
- Bit names: the `IO_RING_F_` enum just above the struct in
  `include/linux/io_uring_types.h`. Tests read
  `ctx->int_flags & IO_RING_F_TASK_COMPLETE`.
- No 1-bit bitfields remain; a patch that uses ctx->task_complete or
  ctx->lockless_cq does not build here.
- The former single restricted bit is two: `IO_RING_F_OP_RESTRICTED` (SQE
  checks, `io_check_restriction()`) and `IO_RING_F_REG_RESTRICTED` (register
  opcodes, `__io_uring_register()`).
- Written only in `io_uring_create()`: `IO_RING_F_TASK_COMPLETE`,
  `IO_RING_F_LOCKLESS_CQ`, `IO_RING_F_SYSCALL_IOPOLL`, `IO_RING_F_COMPAT`.
- `IO_RING_F_TASK_COMPLETE`: needs `IORING_SETUP_DEFER_TASKRUN` set and
  `IORING_SETUP_IOPOLL` clear.
- `IO_RING_F_LOCKLESS_CQ`: `IO_RING_F_TASK_COMPLETE` or `IORING_SETUP_IOPOLL`.
- A ring with both `IORING_SETUP_DEFER_TASKRUN` and `IORING_SETUP_IOPOLL` has
  `IO_RING_F_LOCKLESS_CQ` without `IO_RING_F_TASK_COMPLETE`.
- Restricted bits: set at creation from `op_registered` and `reg_registered`
  of `current->io_uring_restrict` (`io_ctx_restriction_clone()`), or later by
  `io_register_restrictions()`; nothing clears them.
- `IO_RING_F_POLL_ACTIVATED`: set at creation only when
  `IO_RING_F_TASK_COMPLETE` is clear; otherwise by `io_activate_pollwq_cb()`.
- Bits that are cleared at run time: `IO_RING_F_HAS_EVFD`,
  `IO_RING_F_DRAIN_ACTIVE`, `IO_RING_F_DRAIN_NEXT`.
- Writes after creation: plain `|=` and `&=` on the shared word, under
  `uring_lock`; `io_activate_pollwq_cb()` takes the mutex only for that.
- Reads without `uring_lock`: for example `io_commit_cqring_flush()` and
  `io_uring_poll()` wrap them in `data_race()`.

**Ring context field locks**

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

**Lock order**

- Order, outermost first: `lock` of `struct io_sq_data`, `uring_lock`,
  `mmap_lock`, `completion_lock`, `timeout_lock`.
- `uring_lock`, `mmap_lock`, `completion_lock` in that order: see the swap in
  `io_register_resize_rings()`.
- `completion_lock` outside `timeout_lock`: see `io_kill_timeouts()` and
  `io_disarm_next()`.
- `tctx_lock`: a mutex of `struct io_ring_ctx` that protects `tctx_list`;
  `uring_lock` alone does not.
- `tctx_lock` inside `uring_lock`: for example `__io_async_cancel()` and
  `io_ring_exit_work()`.
- `tctx_lock` alone: `io_tctx_install_node()` and `io_uring_del_tctx_node()`.
- Interrupt context: only `timeout_lock`.
- `completion_lock`: every acquisition is a plain `spin_lock()`, process
  context only; `io_lockdep_assert_cq_locked()` asserts `in_task()`.
- **Potentially unsafe usage**: blocking on a second ring's `uring_lock` while
  holding the first ring's.
  - Unsafe: when the first lock is the one the submission path already holds,
    so the pair is not in address order; two rings messaging each other
    deadlock.
  - Safe: `mutex_trylock()` and return `-EAGAIN` when `issue_flags` lacks
    `IO_URING_F_UNLOCKED`, as `io_lock_external_ctx()` in
    `io_uring/msg_ring.c` does; `io_msg_ring()` passes `-EAGAIN` up unchanged.
  - Safe: with `IO_URING_F_UNLOCKED` no ring lock is held, so
    `io_lock_external_ctx()` uses `mutex_lock()`.
  - Safe: drop the first lock, then take both by address, the second with
    `mutex_lock_nested()` and `SINGLE_DEPTH_NESTING`, as `lock_two_rings()`
    in `io_uring/rsrc.c` does.
- `io_register_clone_buffers()`: does the drop and `lock_two_rings()`;
  `io_clone_buffers()` only asserts both locks.
- After the drop: state tested earlier is tested again; `io_clone_buffers()`
  re-tests `buf_table.nr`.
- Same ring as source and target: `io_register_clone_buffers()` skips the
  drop and relock; `lock_two_rings()` requires two different rings.

**Timeout lock**

- `io_disarm_next()` and `io_timeout_cancel()`: entered with `completion_lock`
  held, take `timeout_lock` inside.
- `io_kill_timeout()`: takes no lock and posts nothing; it cancels the timer,
  bumps `cq_timeouts` and moves the entry to the caller's local list.
- `io_flush_killed_timeouts()`: queues the completions with
  `io_req_queue_tw_complete()`, after `timeout_lock` is dropped.
- Sections under `timeout_lock`: none posts a CQE or queues task work;
  `io_timeout_fn()` and `io_link_timeout_fn()` unlock before
  `io_req_task_work_add()`.
- `hrtimer_try_to_cancel()` returning -1: the callback owns the request.
  `io_kill_timeout()` leaves it on `timeout_list`; `io_timeout_extract()`
  returns `-EALREADY`.
- Link chains: walking `link` of a request with `REQ_F_LINK_TIMEOUT` needs
  `timeout_lock`, because `io_link_timeout_fn()` edits the chain; see
  `io_match_task_safe()` and `io_prep_async_link()`.
- **Unsafe usage**: taking `completion_lock`, any other `spinlock_t` or a
  mutex while holding `timeout_lock`, a `raw_spinlock_t` taken with
  interrupts off.
  - Safe: take `completion_lock` first, as `io_kill_timeouts()` does.
  - Safe: collect under `timeout_lock`, act after unlock, as
    `io_flush_timeouts()` does.
- **Unsafe usage**: `hrtimer_cancel()` on a timeout timer while holding
  `timeout_lock`; `io_timeout_fn()` and `io_link_timeout_fn()` take the lock.
  - Safe: `hrtimer_try_to_cancel()` and handle -1, as `io_kill_timeout()`
    does.

**Shared ring memory**

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

**Ring resize**

- Required setup flag: only `IORING_SETUP_DEFER_TASKRUN`.
  `IORING_SETUP_NO_MMAP` is not required.
- Flags in the argument: only `RESIZE_FLAGS`, else `-EINVAL`.
- Inherited from the ring: `COPY_FLAGS` in `io_uring/register.c`, six flags,
  including `IORING_SETUP_CQE_MIXED` and `IORING_SETUP_SQE_MIXED`.
- SQPOLL: the function does not reject it; `io_uring_sanitise_params()`
  rejects `IORING_SETUP_SQPOLL` with `IORING_SETUP_DEFER_TASKRUN` at setup.
- `uring_lock`: held by the caller, `__io_uring_register()`; the function
  takes `mmap_lock`, then `completion_lock`.
- Grace period: `synchronize_rcu_expedited()`, after `completion_lock` and
  `mmap_lock` are dropped and before `io_register_free_rings()` frees the old
  regions.
- `-EOVERFLOW` path: no grace period; the new regions were never published,
  and `rings` and `sq_sqes` are put back.
- `cqe_cached` and `cqe_sentinel`: reset to NULL in the swap, since they
  point into the old ring.
- Readers kept safe: those that use `rings_rcu` inside an RCU read section;
  see "Shared ring memory" for the rest.

## Request state

**Request structure unions**

- Unions in `struct io_kiocb` (`include/linux/io_uring_types.h`); every other
  member, including `file_node`, `creds`, `apoll`, `async_data`, `link`, `cqe`
  and `big_cqe`, has its own storage:

| Union | Live member is chosen by |
|---|---|
| `file` / `cmd` | both; `file` is the first word of `cmd` |
| `kbuf` / `buf_node` | `REQ_F_BUFFER_SELECTED` / `REQ_F_BUF_NODE` |
| `comp_list` / `apoll_events` | on `free_list` or `compl_reqs` / poll armed |
| `io_task_work` / `iopoll_start` | task work queued / hybrid IOPOLL timing |
| `hash_node` / `iopoll_node` / `rcu_head` | see below |
| `cqe.fd` / `cqe.flags` | before / after `io_assign_file()` |

- `REQ_F_BUFFER_RING`: marks no union member; there is no `buf_list` pointer in
  the request, the list travels in `struct io_br_sel`.
- `kbuf` with `buf_node`: neither `io_find_buf_node()` nor
  `io_provided_buffer_select()` tests the other flag; prep must reject the
  combination, for example `io_sendmsg_prep()` and `io_recvmsg_prep()`.
- `iopoll_node`: live when `REQ_F_IOPOLL` is set, which happens at issue in
  `io_rw_init_file()` and `io_uring_cmd()`; `ctx->iopoll_list` links through
  it, not through `comp_list`.
- `hash_node`: used by poll, futex, waitid and cancelable uring_cmd lists.
- `hash_node` with `iopoll_node`: `io_init_req()` fails opcodes without
  `iopoll` in `struct io_issue_def` on an `IORING_SETUP_IOPOLL` ring, and
  `io_uring_cmd_mark_cancelable()` returns early on `REQ_F_IOPOLL`.
- `rcu_head`: only for requests allocated by `io_msg_data_remote()` and freed
  by `io_msg_tw_complete()`.
- `iopoll_start`: written at issue under `IORING_SETUP_HYBRID_IOPOLL`.
- `cqe.fd`: `io_assign_file()` also runs from `io_wq_submit_work()`, so
  `cqe.flags` must not be written before the file is assigned, except on a
  request that is failed without being issued, as `io_submit_fail_init()` does
  through `io_req_set_res()`.
- `struct io_cmd_data`: `file` plus `data[56]`, 64 bytes on 64-bit; the opcode
  struct's own leading file pointer counts toward that size.
- `struct io_rw`: starts with `struct kiocb`, not `struct file *`; it relies on
  `ki_filp` being the first member.

**Request reference counts**

- `REQ_F_REFCOUNT` is enabled at three places only, none in `io_uring/poll.c`
  (poll uses `poll_refs`):

| Where | Request | Initial value |
|---|---|---|
| `io_wq_submit_work()` | the request | 2, or `req_ref_get()` if enabled |
| `__io_prep_linked_timeout()` | head (`io_req_set_refcount()`) | 1 |
| `__io_prep_linked_timeout()` | `req->link`, the timeout | 2 |

- `__io_req_set_refcount()`: tests the flag; on a request whose count is
  enabled it changes nothing, so the count passed is dropped.
- There is no req_set_refcount() here; the helper is `io_req_set_refcount()`.
- `req_ref_put_and_test_atomic()` on a request without the flag: warns, then
  decrements; `io_wq_free_work()` is its caller.

**Reading SQE fields**

- SQE pointer lifetime: `io_commit_sqring()` publishes the SQ head at the end
  of `io_submit_sqes()`, so the slot stays unreused through prep and through an
  issue that carries `IO_URING_F_INLINE`, and no longer.
- `sqe_copy` in `struct io_cold_def`: only `IORING_OP_URING_CMD` and
  `IORING_OP_URING_CMD128` have one; no other opcode's SQE is copied.
- `io_uring_cmd_prep()`: stores the ring pointer in `ioucmd->sqe`;
  `io_uring_cmd_sqe_copy()` later copies into `sqes` of `struct io_async_cmd`
  and re-points it.
- Inline issue that returns `-EIOCBQUEUED`: no copy is made; `ioucmd->sqe`
  still points into the ring after `io_submit_sqes()` returns.
- **Potentially unsafe usage**: a prep or issue handler reading an SQE field
  with a plain load.
  - Unsafe: when the SQE is in the ring and the value is stored or used after
    the load; `io_get_sqe()` returns a pointer into `ctx->sq_sqes`, which
    userspace can rewrite between the check and the use.
  - Safe: when the load only rejects a field and the value is never used
    again, as `io_fsync_prep()` does with `sqe->addr` and
    `__io_timeout_prep()` with `sqe->len`.
  - Safe: when the SQE is a kernel copy, as in `io_uring_sync_msg_ring()`;
    `io_uring_register_send_msg_ring()` fills it with `copy_from_user()`.
- **Potentially unsafe usage**: keeping the `sqe` pointer in the request.
  - Unsafe: when the opcode has no `sqe_copy` handler, or the pointer is read
    after an inline issue returned `-EIOCBQUEUED`.
  - Safe: read during an issue that no inline `-EIOCBQUEUED` preceded, with an
    `sqe_copy` handler installed, as `blkdev_uring_cmd()` does on its first
    issue; `io_req_sqe_copy()` returns `-EFAULT` if a copy is needed without
    `IO_URING_F_INLINE`.
- Request fields: zero only in a fresh slab object (`__GFP_ZERO` in
  `__io_alloc_req_refill()`); `io_req_add_to_cache()` recycles without
  clearing.
- `io_init_fail_req()`: zeroes `req->cmd.data` when `io_init_req()` fails
  before prep, because `io_req_defer_failed()` still calls the `fail` handler,
  for example `io_sendrecv_fail()` reading `done_io`.
- `io_req_add_to_cache()`: calls `io_poison_cached_req()` under `CONFIG_KASAN`
  only; it poisons `ctx`, `tctx`, `file`, `creds`, `apoll` and the task-work
  function, not the rest of `cmd`.
- There is no io_rw_prep() or io_prep_rw_setup() here; see `io_prep_rw()` and
  `__io_prep_rw()` in `io_uring/rw.c`.
- Prep setting what it later reads: `io_sendmsg_prep()` (`done_io`),
  `io_connect_prep()` (`in_progress`), `__io_splice_prep()` (`rsrc_node`).

**Opcode cleanup flag**

- `io_clean_op()`: runs the cleanup handler before it `kfree()`s `async_data`,
  so the handler may dereference it.
- `io_clean_op()` calls the cleanup handler with `uring_lock` held, from
  `io_free_batch_list()`; `io_readv_writev_cleanup()` asserts it.
- Path names: this tree holds them in `struct delayed_filename`, filled by
  `delayed_getname()`, consumed by `complete_getname()` and released by
  `dismiss_delayed_filename()`; io_uring prep handlers do not call `getname()`.
- **Unsafe usage**: setting `REQ_F_NEED_CLEANUP` while a field the cleanup
  handler reads still holds data of the previous request.
  - Safe: initialise first, as `__io_getxattr_prep()` does with
    `INIT_DELAYED_FILENAME()` and `kvalue`, because `io_getxattr_prep()` can
    still fail in `delayed_getname()` after the flag is set.
  - Safe: set the flag early and make the handler test state, as
    `io_send_zc_prep()` does before async data exists; `io_send_zc_cleanup()`
    tests `req_has_async_data()`.
  - Safe: flag set at issue, field cleared in prep, as `__io_splice_prep()`
    does with `rsrc_node` for `io_splice_get_file()`.
- **Potentially unsafe usage**: failing prep with a resource held and the flag
  clear.
  - Unsafe: when only the cleanup handler releases the resource;
    `io_clean_op()` calls the handler only under `REQ_F_NEED_CLEANUP`.
  - Safe: release it in prep, as `io_renameat_prep()` does for `oldpath` when
    the second `delayed_getname()` fails.
  - Safe: fail after the flag is set and leave it to `io_clean_op()`, as
    `__io_openat_prep()` does on its `-EINVAL` return for `file_slot` with
    `O_CLOEXEC`.
  - Safe: when the resource is `async_data` with `REQ_F_ASYNC_DATA` set;
    `io_clean_op()` `kfree()`s it, as after a failed `move_addr_to_kernel()`
    in `io_connect_prep()`.
- **Potentially unsafe usage**: issue releasing the resource and leaving
  `REQ_F_NEED_CLEANUP` set.
  - Unsafe: when the handler would release it again, as `io_xattr_cleanup()`
    would for `kname`; `io_xattr_finish()` therefore clears the flag.
  - Safe: when consuming empties the holder, as in `io_statx()`:
    `complete_getname()` NULLs it and `putname()` ignores NULL.
- `io_openat2()` on `-EAGAIN`: puts the name back with `putname_to_delayed()`
  and returns with the flag still set.

**Async data**

- `io_clean_op()`: frees with plain `kfree()`, whatever the opcode;
  `async_size` is in `struct io_issue_def` and is used only to allocate.
- `io_uring_alloc_async_data()`: every call is on a prep path; search for it.
- There is no io_uring_cmd_prep_setup() here; `io_uring_cmd_prep()` allocates.
- `io_futex_prep()` allocates nothing.
- `io_connect_prep()` and `io_bind_prep()`: pass a NULL cache and get a
  `kmalloc()`ed `struct sockaddr_storage`; they do not use `netmsg_cache`.
- NULL-cache allocations are not zeroed; cached ones only in the first
  `init_clear` bytes, on fresh allocation, and on reuse only under
  `CONFIG_KASAN`.
- Returned to a cache by `io_rw_recycle()`, `io_netmsg_recycle()`,
  `io_req_uring_cleanup()` and `io_futex_complete()`.
- Freed early by `io_req_async_data_free()` callers, for example
  `io_waitid_free()` and `io_futexv_complete()`.
- Anything else, for example timeout and connect data, is left to
  `io_clean_op()`.
- `io_uring_cmd_cleanup()` is the cleanup handler; the recycler is
  `io_req_uring_cleanup()`.
- **Unsafe usage**: clearing `REQ_F_ASYNC_DATA` and leaving `async_data`
  non-NULL.
  - Safe: `io_req_async_data_clear()`, which NULLs it;
    `io_req_async_data_free()` frees the pointer without testing the flag, and
    `io_futex_wait()` calls it on a request that never had data.
- **Potentially unsafe usage**: detaching `async_data` while
  `REQ_F_NEED_CLEANUP` stays set and the cleanup handler dereferences
  `async_data`.
  - Unsafe: when the detach is outside the cleanup handler, so `io_clean_op()`
    still calls the handler afterwards; `io_sendmsg_recvmsg_cleanup()`
    dereferences without a test.
  - Safe: pass the flag to `io_req_async_data_clear()`, as
    `io_netmsg_recycle()` does.
  - Safe: clear the flag first, as `io_req_rw_cleanup()` does before
    `io_rw_recycle()`.
  - Safe: inside the cleanup handler itself, after its last use, as
    `io_readv_writev_cleanup()` does through `io_rw_recycle()`;
    `io_clean_op()` then clears `IO_REQ_CLEAN_FLAGS`.

**Async data set by hand**

- Three in-tree users set the flag by hand: `io_futex_wait()`,
  `io_futexv_prep()` and the `IORING_OP_POLL_ADD` double-poll entry.
- Timeout is not one; `__io_timeout_prep()` uses
  `io_uring_alloc_async_data()`.
- `io_futexv_prep()`: allocates one `struct io_futexv_data` with
  `kzalloc_flex()`, and on a parse error frees it before the flag is set.
- `IORING_OP_POLL_ADD`: `io_poll_double_prepare()` sets `REQ_F_ASYNC_DATA`,
  then `__io_queue_proc()` stores a `kmalloc_obj()`ed `struct io_poll` through
  `&req->async_data`; `io_clean_op()` frees it.
- **Potentially unsafe usage**: setting `REQ_F_ASYNC_DATA` before the pointer.
  - Unsafe: when `async_data` may hold a stale pointer, since `io_clean_op()`
    frees whatever is there.
  - Safe: on a request that went through `io_init_req()`, which NULLs
    `async_data`, as `io_poll_double_prepare()` relies on.

**Async data recycling from io-wq**

- Detection: all three test `issue_flags & IO_URING_F_UNLOCKED`; none tests
  `IO_URING_F_IOWQ` or `PF_IO_WORKER`.
- `IO_URING_F_UNLOCKED` also comes from non-worker callers, for example the
  `io_uring_cmd_done()` call in `fuse_uring_entry_teardown()` in
  `fs/fuse/dev_uring.c`.

| Function | With `IO_URING_F_UNLOCKED` | Left on the request |
|---|---|---|
| `io_netmsg_recycle()` | frees the iovec, returns | `async_data`, `REQ_F_ASYNC_DATA` and `REQ_F_NEED_CLEANUP` unchanged |
| `io_rw_recycle()` | returns false, frees nothing | everything |
| `io_req_uring_cleanup()` | returns at once | everything |

- There is no io_rw_iovec_free() here; `io_req_rw_cleanup()` calls
  `io_vec_free()` when `io_rw_recycle()` returns false, including cache-full.
- rw in io-wq: `io_req_rw_cleanup()` does nothing while `REQ_F_REFCOUNT` or
  `REQ_F_REISSUE` is set, and `io_wq_submit_work()` always sets
  `REQ_F_REFCOUNT`; this also holds for the later task-work completion.
- What is left is released by `io_clean_op()`:

| Opcode | Cleanup handler, if `REQ_F_NEED_CLEANUP` | `async_data` ends |
|---|---|---|
| rw | `io_readv_writev_cleanup()`: frees iovec, then recycles | in `rw_cache` |
| net | `io_sendmsg_recvmsg_cleanup()`: frees iovec only | `kfree()`d |
| uring_cmd | `io_uring_cmd_cleanup()`: recycles with the vec | in `cmd_cache` |

- Without `REQ_F_NEED_CLEANUP` (no iovec was allocated): no handler runs and
  `io_clean_op()` `kfree()`s `async_data`.
- Cache full in the table above: `io_clean_op()` `kfree()`s `async_data`.
- `io_sendmsg_zc()` with `IO_URING_F_UNLOCKED`: skips the recycle call
  entirely and leaves the notif flush to `io_send_zc_cleanup()`; there is no
  io_send_zc() here.

**Freeing a completed request**

- No slow flag set: only `io_put_file()`, `io_req_put_rsrc_nodes()` and
  `io_put_task()` run, then `io_req_add_to_cache()`; these four run for every
  freed request.
- `REQ_F_POLLED`: is in `IO_REQ_CLEAN_SLOW_FLAGS` directly, not in
  `IO_REQ_CLEAN_FLAGS`; `io_clean_op()` does not touch `apoll`.
- Slow block, in order:
  1. `REQ_F_REISSUE`: clear it, `io_queue_iowq()`, skip the rest; the request
     is not freed.
  2. `REQ_F_REFCOUNT`: `req_ref_put_and_test()`; skip the request unless last.
  3. `REQ_F_POLLED` and `apoll` non-NULL: `kfree()` `double_poll`,
     `io_cache_free()` to `apoll_cache`.
  4. `IO_REQ_LINK_FLAGS`: `io_queue_next()`.
  5. `IO_REQ_CLEAN_FLAGS`: `io_clean_op()`.
- `io_req_put_rsrc_nodes()`: tests `file_node` by pointer and NULLs it; tests
  `buf_node` by `REQ_F_BUF_NODE` and leaves both as they are.
- There is no req_caches or io_free_req_to_cache() here, and io_uring does not
  call `kmem_cache_free_bulk()`.
- Slab free of a request in the ctx cache: only `__io_req_caches_free()`,
  reached from `io_req_caches_free()` and from `io_queue_deferred()` on the
  drain path.

## Submission and issue

**Opcode tables**

- `struct io_issue_def` has no iopoll_queue member; whether a request goes on
  the iopoll list is the request flag `REQ_F_IOPOLL`, set by the handler at
  issue (`io_rw_init_file()` in `io_uring/rw.c`, `io_uring_cmd()`).
- `struct io_issue_def` also holds `is_128`, `filter_pdu_size` and
  `filter_populate`; `io_init_req()` reads `is_128`, and
  `io_uring_populate_bpf_ctx()` in `io_uring/bpf_filter.c` reads the other two.
- `struct io_cold_def` has exactly `name`, `sqe_copy`, `cleanup`, `fail`.
- `io_uring_optable_init()` build checks: each array is compared to
  `IORING_OP_LAST` separately, not to the other array.
- `io_uring_optable_init()` boot checks: `BUG_ON()` for a NULL `prep`, and for
  a NULL `issue` unless `prep` is `io_eopnotsupp_prep()`; `WARN_ON_ONCE()`
  only for a NULL `name`.
- `io_uring_optable_init()` checks no other member: flag bits, `async_size`,
  `filter_pdu_size` and the cold callbacks are unchecked.
- **Unsafe usage**: an `io_issue_defs[]` entry with `filter_pdu_size` set and
  no `filter_populate`.
  - Unsafe: with a BPF filter registered for the opcode,
    `io_uring_populate_bpf_ctx()` calls `filter_populate` with no NULL test.
  - Safe: set both together, as the `IORING_OP_OPENAT` entry does.

**Opcode callback contexts**

- `io_tw_lock()` in `io_uring/tw.h`: only `lockdep_assert_held()`; it takes
  nothing.
- Task work: the runner takes `uring_lock` before calling the handler; see
  `tctx_task_work_run()`, `io_run_local_work()` and
  `io_cancel_local_task_work()` in `io_uring/tw.c`.
- `issue` from poll: `io_poll_issue()` calls `__io_issue_sqe()` directly, so
  there is no `io_assign_file()` and no completion on `IOU_COMPLETE`;
  `io_poll_check_events()` acts on the return value.
- `filter_populate`: called from `io_submit_sqe()` after `prep` returned 0,
  under `uring_lock` and inside `guard(rcu)`, only when the ring has a filter
  for that opcode.
- `sqe_copy`: called through `io_req_sqe_copy()` under `uring_lock`, at most
  once per request (`REQ_F_SQE_COPIED`), from three places: `io_submit_sqe()`
  when the request is appended behind a link head, `io_queue_sqe_fallback()`,
  and `io_queue_async()`.
- `sqe_copy` from `io_queue_async()` without `IO_URING_F_INLINE`, for a
  request not yet copied whose opcode has `sqe_copy`: `io_req_sqe_copy()`
  warns and the request fails with `-EFAULT`.
- `cleanup`: `io_clean_op()` has one caller, `io_free_batch_list()`, reached
  only from `__io_submit_flush_completions()`; so `uring_lock` is held, the
  CQE is already filled, and the last reference is gone.
- `cleanup` relies on that lock: `io_uring_cmd_cleanup()` puts into
  `ctx->cmd_cache` with issue flags 0.
- `cleanup` also runs for a request whose `prep` failed after setting
  `REQ_F_NEED_CLEANUP`.
- `fail`: `io_req_defer_failed()` calls it after `req_set_fail()` and
  `io_req_set_res()`, before `io_req_complete_defer()`.
- `fail` on an unprepared request: `io_submit_fail_init()` leads to
  `io_req_defer_failed()` for an unlinked request or a link head whose `prep`
  failed or never ran; `io_init_fail_req()` zeroes `req->cmd.data` only for
  failures before `prep`.
- `fail` is not called for link members cancelled behind a failed head:
  `io_req_tw_fail_links()` in `io_uring/timeout.c` completes them with
  `io_req_task_complete()`.

**Submission path**

- `req->file` is NULL in `prep`: `io_init_req()` only stores `req->cqe.fd`
  when `needs_file` is set; `io_assign_file()` runs at issue.
- No file-table or fixed-file lookup precedes `prep`.
- Checks in `io_init_req()` before `prep`, besides opcode and SQE flags:
  `ioprio`, `iopoll` on an `IORING_SETUP_IOPOLL` ring, `buffer_select`,
  `io_check_restriction()`, personality.
- `is_128` opcodes: on a ring without `IORING_SETUP_SQE128`, `io_init_req()`
  requires `IORING_SETUP_SQE_MIXED` and a second contiguous entry, and consumes
  it before `prep`; otherwise `-EINVAL`.
- `req->cmd.data` is not cleared before a successful `prep`; `prep` must set
  every field that `issue`, `fail` or `cleanup` reads.
- `io_init_req()` sets `req->tctx` to `current->io_uring` and
  `req->async_data` to NULL.
- BPF filters run after `prep`, in `io_submit_sqe()`; a denial goes to
  `io_submit_fail_init()` with `-EACCES` on an already prepared request.
- Lock: every step in `io_submit_sqes()` is under `uring_lock`
  (`__must_hold`), but the first issue is not always one of those steps.

| Request | First issue | `uring_lock` | `IO_URING_F_INLINE` |
|---|---|---|---|
| plain, or link head once the link is complete | `io_queue_sqe()` in `io_submit_sqe()` | held | set |
| `REQ_F_FORCE_ASYNC`, no drain | `io_wq_submit_work()` | not held | not set |
| later link member | `io_req_task_submit()`, or io-wq via `io_wq_free_work()` | held / not held | not set |
| drained (carries `REQ_F_FORCE_ASYNC`) | `io_wq_submit_work()`, after `io_req_task_submit()` from `io_queue_deferred()` calls `io_queue_iowq()` | not held | not set |

- Init failure in a link: only the failing request and the head get
  `REQ_F_FAIL`; the other members get no flag and complete with `-ECANCELED`
  in `io_req_tw_fail_links()`.
- Init failure in a link: no member is issued, the head included.
- Members after the failed one are still prepared, so their `prep` may
  allocate; they are then cancelled.
- `io_submit_fail_init()` returns 0 when the failing request has
  `IO_REQ_LINK_FLAGS`; the batch continues whatever
  `IORING_SETUP_SUBMIT_ALL` says.
- `io_submit_fail_init()` returns the error when the failing request is
  unlinked or ends the link; `io_submit_sqes()` then stops, unless
  `IORING_SETUP_SUBMIT_ALL` is set.

**Issue flags**

- `IO_URING_CMD_TASK_WORK_ISSUE_FLAGS` in `include/linux/io_uring/cmd.h` is
  `IO_URING_F_COMPLETE_DEFER`; uring_cmd task-work callbacks pass it on.

| Flag | Tells the handler | Set by |
|---|---|---|
| `IO_URING_F_NONBLOCK` | must not block | `io_queue_sqe()`; `io_poll_issue()`; `io_wq_submit_work()` only for `REQ_F_FORCE_ASYNC` with `pollin` or `pollout` and `io_file_can_poll()`, cleared after one poll attempt |
| `IO_URING_F_COMPLETE_DEFER` | `uring_lock` held, `io_req_complete_defer()` allowed | `io_queue_sqe()`; `io_poll_issue()`; `io_uring_try_cancel_uring_cmd()` |
| `IO_URING_F_UNLOCKED` | `uring_lock` not held; `io_ring_submit_lock()` takes it | `io_wq_submit_work()` |
| `IO_URING_F_IOWQ` | called from io-wq | `io_wq_submit_work()` |
| `IO_URING_F_INLINE` | called from `io_submit_sqes()`, SQE still readable | `io_submit_sqe()` only; `io_req_task_submit()` passes 0 |
| `IO_URING_F_MULTISHOT` | called from `io_poll_issue()`; may return `IOU_REQUEUE`; must not return `IOU_ISSUE_SKIP_COMPLETE` | `io_poll_issue()` only |
| `IO_URING_F_SQE128` | command has a 128-byte SQE | `io_uring_cmd()`: `IORING_SETUP_SQE128` or opcode `IORING_OP_URING_CMD128` |
| `IO_URING_F_CQE32` | 32-byte CQE may be posted | `io_uring_cmd()`: `IORING_SETUP_CQE32` or `IORING_SETUP_CQE_MIXED` |
| `IO_URING_F_IOPOLL` | command is polled to completion | `io_uring_cmd()`: `IORING_SETUP_IOPOLL` and the file has `uring_cmd_iopoll` |
| `IO_URING_F_CANCEL` | `->uring_cmd()` is asked to cancel an issued command | `io_uring_try_cancel_uring_cmd()` |
| `IO_URING_F_COMPAT` | compat layout | `io_uring_cmd()`: `io_is_compat()` |

- `IO_URING_F_SQE128`, `IO_URING_F_CQE32`, `IO_URING_F_IOPOLL`,
  `IO_URING_F_COMPAT`: only `f_op->uring_cmd` implementations see them; no
  other issue handler does.
- `IO_URING_F_INLINE` is tested in one place, `io_req_sqe_copy()`.
- `IO_URING_F_IOWQ`: `io_req_complete_post()` warns and drops the completion
  without it, so a caller of `io_issue_sqe()` passes either
  `IO_URING_F_COMPLETE_DEFER` or `IO_URING_F_IOWQ`.

**Issue return codes**

- `IOU_RETRY` is `-EAGAIN`; the core cannot tell them apart.
- `IOU_ISSUE_SKIP_COMPLETE`: `io_issue_sqe()` returns 0 for it, and calls
  `io_iopoll_req_issued()` when the request has `REQ_F_IOPOLL`.
- Other non-zero return, inline: `io_queue_async()` calls
  `io_req_defer_failed()` with that value.
- Other non-zero return, io-wq: `io_wq_submit_work()` calls
  `io_req_task_queue_fail()`.
- `-EAGAIN` in io-wq: retried in a loop only when the request has
  `REQ_F_IOPOLL` and `io_wq_worker_stopped()` is false; retried once blocking
  after a poll attempt for `REQ_F_FORCE_ASYNC` that did not arm; otherwise the
  request fails with `-EAGAIN`.
- **Unsafe usage**: returning `IOU_REQUEUE` without `IO_URING_F_MULTISHOT`.
  - Unsafe: inline or in io-wq the value is treated as an error and the CQE
    carries `-3072`.
  - Safe: test `IO_URING_F_MULTISHOT` first and fall back to `IOU_RETRY`, as
    `io_recv_finish()` in `io_uring/net.c` and `io_zcrx_tcp_recvmsg()` in
    `io_uring/zcrx.c` do.
- **Unsafe usage**: returning `IOU_ISSUE_SKIP_COMPLETE` under
  `IO_URING_F_MULTISHOT`.
  - Unsafe: `io_poll_issue()` warns, and `io_poll_check_events()` returns it
    as an error, so the request fails with `-EIOCBQUEUED`.
  - Safe: return `IOU_RETRY` to stay armed, as `io_read_mshot()` does.
- Handler return under `io_poll_issue()`, as mapped by
  `io_poll_check_events()`:

| Handler returns | `io_poll_check_events()` |
|---|---|
| `IOU_COMPLETE` | returns `IOU_POLL_REMOVE_POLL_USE_RES` |
| `IOU_REQUEUE` | returns `IOU_POLL_REQUEUE` |
| `IOU_RETRY` | drops its references and returns `IOU_POLL_NO_ACTION`, or loops if a wakeup came in meanwhile; poll stays armed |
| other negative | returns it |

- `io_poll_check_events()` results, as handled by `io_poll_task_func()`:

| Result | `IORING_OP_POLL_ADD` | Any other opcode |
|---|---|---|
| `IOU_POLL_NO_ACTION` | nothing | nothing |
| `IOU_POLL_REQUEUE` | `__io_poll_execute()` again, entries stay armed | same |
| `IOU_POLL_DONE` | complete with the mask | `io_req_task_submit()` |
| `IOU_POLL_REISSUE` | `io_req_task_submit()` | `io_req_task_submit()` |
| `IOU_POLL_REMOVE_POLL_USE_RES` | complete with `req->cqe.res` | `io_req_task_complete()` |
| negative | `req_set_fail()`, complete with it | `io_req_defer_failed()` |

- `tw.cancel` set: `io_poll_check_events()` returns `-ECANCELED` before
  looking at events, and `io_req_task_submit()` fails the request with
  `-EFAULT` instead of reissuing.

**Punt to poll or io-wq**

- `io_queue_async()` order: fail unless the return is `-EAGAIN` and
  `REQ_F_NOWAIT` is clear; `io_req_sqe_copy()`; `io_arm_poll_handler()`; act
  on its result.
- `io_req_sqe_copy()` runs before `io_arm_poll_handler()`, so it covers all
  three results, not only the io-wq one.
- `IO_APOLL_READY`: `io_req_task_queue()`, so the retry runs from task work,
  not in `io_queue_async()`.
- Linked timeout: `__io_issue_sqe()` calls `__io_prep_linked_timeout()` before
  the handler and `io_queue_linked_timeout()` after it, whatever the handler
  returned; `io_queue_async()` does not touch the timeout.
- `io_arm_poll_handler()` and `io_arm_apoll()` return `IO_APOLL_ABORTED` when:
  - the opcode has neither `pollin` nor `pollout` (`io_arm_poll_handler()`
    only)
  - `io_file_can_poll()` is false
  - `io_req_alloc_apoll()` returns NULL: allocation failed, or the
    `APOLL_MAX_RETRY` budget of this request is used up
  - `__io_arm_poll_handler()` returns negative: `vfs_poll()` queued no wait
    entry or set an error, and reported no event
- `REQ_F_POLLED`: does not refuse poll; it means `req->apoll` exists and is
  reused.
- `REQ_F_NOWAIT` and `IORING_SETUP_IOPOLL`: not tested in
  `io_arm_poll_handler()`; `REQ_F_NOWAIT` is tested earlier in
  `io_queue_async()`.
- `io_queue_iowq()`: fails the request with `-ECANCELED` through
  `io_req_task_queue_fail()` when `current` is `PF_KTHREAD` or the task has no
  `tctx->io_wq`.
- `io_prep_async_work()`: `unbound_nonreg_file` does not apply to block
  devices; they stay on bounded workers.
- `io_prep_async_work()`: hashing applies to regular files with
  `hash_reg_file`, except `O_DIRECT` files with `FOP_DIO_PARALLEL_WRITE`, and
  to any regular file request with `REQ_F_IOPOLL`.
- io-wq poll attempt after `-EAGAIN`: `IO_APOLL_READY` and `IO_APOLL_ABORTED`
  both lead to a blocking retry in the worker.

## Posting completions

**Completion paths**

- `io_req_complete_defer()`: the only requirement checked is
  `lockdep_assert_held(&req->ctx->uring_lock)`; the caller need not be a
  submission path, and must be the submitter task only where "CQ locking"
  asks that of the flush.
  - For example `io_uring_try_cancel_uring_cmd()` in `io_uring/uring_cmd.c`
    passes `IO_URING_F_CANCEL | IO_URING_F_COMPLETE_DEFER` and flushes itself.
  - Task work reaches it from a kworker through `io_tctx_fallback_work()`, and
    from `io_cancel_local_task_work()` in `io_ring_exit_work()`.
- `io_req_task_complete()`: calls `io_req_complete_defer()` and nothing else.
- Flush after `io_req_complete_defer()`: must run before `uring_lock` is
  dropped; search callers of `io_submit_flush_completions()` for the places
  that do it.
- Request after `io_req_complete_defer()`: may be recycled before the caller's
  own flush, because `io_req_post_cqe()` calls
  `__io_submit_flush_completions()` when `compl_reqs` is not empty.
- `__io_uring_cmd_done()` on a request without `REQ_F_IOPOLL`:
  `WARN_ON_ONCE()` and return when `IO_URING_F_COMPLETE_DEFER` comes with
  `IO_URING_F_UNLOCKED`.
- `io_req_complete_post()`: static in `io_uring/io_uring.c`, called only by
  `io_issue_sqe()` when `IO_URING_F_COMPLETE_DEFER` is not set.
  - Without `IO_URING_F_IOWQ` it does `WARN_ON_ONCE()` and returns; the
    request is not completed.
  - It never posts on a ring with `IO_RING_F_LOCKLESS_CQ` in `ctx->int_flags`
    (there is no lockless_cq field); it queues `io_req_task_complete()`.
  - It never frees; `req_ref_put()` relies on the extra reference that
    `io_wq_submit_work()` takes.
  - An opcode handler reaches it by `io_req_set_res()` and returning
    `IOU_COMPLETE`; other code cannot call it.
- `io_req_queue_tw_complete()`: overwrites `req->cqe.flags` with 0. A
  completion that carries cflags calls `io_req_set_res()`, sets
  `io_task_work.func` to `io_req_task_complete()` and calls
  `io_req_task_work_add()`, as `io_nop()` does.
- `io_req_queue_tw_complete()` queue: `ctx->work_list` on
  `IORING_SETUP_DEFER_TASKRUN` rings, else `req->tctx->task_list`; see
  `__io_req_task_work_add()` in `io_uring/tw.h`.

**CQ locking**

- `io_lockdep_assert_cq_locked()`: body compiled only under
  `CONFIG_PROVE_LOCKING`; first asserts `in_task()` for every ring.

| `IORING_SETUP_DEFER_TASKRUN` | `IORING_SETUP_IOPOLL` | Required |
|---|---|---|
| no | no | `completion_lock` held |
| no | yes | `uring_lock` held |
| yes | no | `uring_lock` held and `current == ctx->submitter_task` |
| yes | yes | `uring_lock` held only |

- Submitter test: skipped when `ctx->submitter_task` is NULL or `ctx->refs` is
  dying.
- Flags read by the assert: `ctx->flags` for the two setup flags, and
  `IO_RING_F_TASK_COMPLETE` in `ctx->int_flags`.
- `IO_RING_F_LOCKLESS_CQ`: not read by the assert. Posting code reads it to
  skip `completion_lock`, for example `__io_cq_lock()` and
  `io_req_post_cqe()`.
- `IO_RING_F_SYSCALL_IOPOLL`: not read by the assert; it suppresses the
  wakeup in `__io_cq_unlock_post()` and makes `io_uring_enter()` call
  `io_iopoll_check()`.
- `io_cq_lock()`: always takes `completion_lock`; `__io_cq_lock()` is the
  conditional one.

**CQE posting helpers**

| Helper | Context and locks | Overflow | Flush |
|---|---|---|---|
| `io_post_aux_cqe()` | process context; takes `completion_lock` on every ring; caller meets the rest of "CQ locking" | yes, `GFP_NOWAIT`; false if dropped | itself |
| `io_add_aux_cqe()` | `uring_lock` held; asserts `IO_RING_F_LOCKLESS_CQ` | yes, `GFP_KERNEL`; returns void | later, via `cq_flush` |
| `io_req_post_cqe()` | `uring_lock` held; asserts not an io-wq worker | no; returns false | later, via `cq_flush` |
| `io_req_post_cqe32()` | as `io_req_post_cqe()` | no; returns false | later, via `cq_flush` |
| `io_defer_get_uncommited_cqe()` | caller meets "CQ locking"; takes no lock | no; returns false | later, via `cq_flush` |

- `io_post_aux_cqe()` on an `IORING_SETUP_IOPOLL` or
  `IORING_SETUP_DEFER_TASKRUN` ring: the caller holds `uring_lock` itself;
  `__io_msg_ring_data()` takes it for `IORING_SETUP_IOPOLL` targets.
- `io_post_aux_cqe()` lock: plain `spin_lock()`, and `io_get_cqe_overflow()`
  asserts `in_task()`.
- `io_add_aux_cqe()`: does not take or need `completion_lock` to fill;
  `io_cqe_overflow()` takes it only to queue an overflow entry.
- `submit_state.cq_flush`: makes `io_submit_flush_completions()` commit the
  tail even with empty `compl_reqs`; the caller's path must reach it before
  dropping `uring_lock`.
- `io_req_post_cqe32()`: `io_fill_cqe_aux32()` does `WARN_ON_ONCE()` and
  returns false on a ring with neither `IORING_SETUP_CQE32` nor
  `IORING_SETUP_CQE_MIXED`; it overwrites `cqe[0].user_data` in the caller's
  array.
- `io_defer_get_uncommited_cqe()`: defined in `io_uring/io_uring.h`; the
  caller writes the slot, as `io_zcrx_queue_cqe()` does.

**32-byte CQEs**

- `cqe32` on an `IORING_SETUP_CQE32` ring: must be false; the ring flag alone
  makes `io_get_cqe_overflow()` advance `cqe_cached` by two.
- **Unsafe usage**: `cqe32` true on an `IORING_SETUP_CQE32` ring.
  `io_cqe_cache_refill()` then applies the wrap test and the two-slot minimum
  to 32-byte slots, and `io_fill_nop_cqe()` writes the filler at the
  unshifted index.
  - Safe: `__io_cqring_overflow_flush()` forces `is_cqe32` to false when the
    ring has `IORING_SETUP_CQE32`.
  - Safe: `io_defer_get_uncommited_cqe()` passes
    `ctx->flags & IORING_SETUP_CQE_MIXED`.
  - Safe: `io_req_set_res32()` sets `IORING_CQE_F_32` only through
    `ctx_cqe32_flags()`, which returns 0 unless the ring has
    `IORING_SETUP_CQE_MIXED`.
- There is no REQ_F_CQE32_INIT in this tree; `io_fill_cqe_req()` derives
  `cqe32` from `IORING_CQE_F_32` in `req->cqe.flags`.
- `IORING_SETUP_CQE_MIXED` size of an entry: taken from `IORING_CQE_F_32` in
  the CQE's own flags by `io_alloc_ocqe()` and `__io_cqring_overflow_flush()`,
  so a CQE without the flag is stored and flushed as 16 bytes.
- `io_defer_get_uncommited_cqe()` on an `IORING_SETUP_CQE_MIXED` ring: always
  reserves 32 bytes; the caller sets `IORING_CQE_F_32` itself, as
  `io_zcrx_queue_cqe()` does.
- `IORING_SETUP_CQE_MIXED` with `cq_entries` below 2: `rings_size()` returns
  `-EOVERFLOW`.

**CQ overflow**

- Allocation: `io_alloc_ocqe()` adds `__GFP_ACCOUNT`; `io_cqe_overflow()`
  passes `GFP_KERNEL` before taking `completion_lock`;
  `io_cqe_overflow_locked()` passes `GFP_NOWAIT`. Neither uses `GFP_ATOMIC`.
- `io_cqe_overflow()`: used on `IO_RING_F_LOCKLESS_CQ` rings by
  `__io_submit_flush_completions()` and by `io_add_aux_cqe()`; it can sleep.
- CQEs that can be dropped: any that reach `io_cqring_add_overflow()` with a
  NULL entry, which is final CQEs, `io_post_aux_cqe()` and `io_add_aux_cqe()`.
- `io_req_post_cqe()`, `io_req_post_cqe32()` and
  `io_defer_get_uncommited_cqe()`: for the CQE they post, never queue an
  overflow entry and never touch `rings->cq_overflow` or
  `IO_CHECK_CQ_DROPPED_BIT`; they return false.
- `__io_cqring_overflow_flush()` with `dying` true: frees entries without
  posting and without counting them in `rings->cq_overflow`.
- `-EBADR`: returned by `io_cqring_wait()` in `io_uring/wait.c` and by
  `io_iopoll_check()`.
- `io_uring_enter`: returns `-EBADR` and clears `IO_CHECK_CQ_DROPPED_BIT`
  only when the submit part of the same call returned 0; otherwise the
  submit count is returned and the bit stays set.
- There is no cq_extra field and no IORING_SETUP_CQ_NODROP in this tree;
  `IORING_FEAT_NODROP` is the feature bit.

**Pending overflow entries**

- `IO_CHECK_CQ_OVERFLOW_BIT` test that refuses a slot: in
  `io_cqe_cache_refill()` only. `io_get_cqe_overflow()` hands out slots still
  in the cached range without it.
- `__io_cqring_overflow_flush()` on `need_resched()`: writes only
  `ctx->cqe_sentinel = ctx->cqe_cached`; `cqe_cached` keeps its value.
- Reset path in `__io_cqring_overflow_flush()`: only inside the loop when
  `need_resched()` is true, before `io_cq_unlock_post()` and `mutex_unlock()`
  of `uring_lock`.
- Final `io_cq_unlock_post()` at the end of `__io_cqring_overflow_flush()`:
  does not reset `cqe_sentinel`.
- **Unsafe usage**: dropping `completion_lock` or `uring_lock` while overflow
  entries are pending and the cached range is not empty; another poster gets
  a slot ahead of the pending entries.
  - Safe: set `cqe_sentinel` to `cqe_cached` first, as the `need_resched()`
    path of `__io_cqring_overflow_flush()` does.

**Messages between rings**

- Choice of path: `io_msg_need_remote()` tests only `IO_RING_F_TASK_COMPLETE`
  in the target's `int_flags`; no trylock result and no source flag is
  involved.
- Target with `IORING_SETUP_R_DISABLED`: `-EBADFD`, for both
  `IORING_MSG_DATA` and `IORING_MSG_SEND_FD`; nothing is queued.
- Target with `IORING_SETUP_DEFER_TASKRUN` and `IORING_SETUP_IOPOLL`:
  `IO_RING_F_TASK_COMPLETE` is not set, so the CQE is posted directly under
  the target's `uring_lock`.
- `IORING_MSG_SEND_FD` remote path: `io_msg_fd_remote()` uses
  `task_work_add()` with `TWA_SIGNAL` on the target's `submitter_task`, and
  returns `-EOWNERDEAD` if that fails. No private request is allocated.
  - `io_msg_tw_fd_complete()` then runs in the target task, posts with
    `io_post_aux_cqe()`, and completes the source request with
    `io_req_queue_tw_complete()`.
- `IORING_MSG_SEND_FD` direct path: `io_msg_install_complete()` always takes
  the target's `uring_lock`; `__io_msg_ring_data()` takes it only for
  `IORING_SETUP_IOPOLL` targets.
- There is no io_double_lock_ctx() here; `io_lock_external_ctx()` in
  `io_uring/msg_ring.c` does that.
- `IO_URING_F_UNLOCKED` callers of `io_lock_external_ctx()`: io-wq,
  `io_msg_tw_fd_complete()`, and `io_uring_sync_msg_ring()`, which has no
  source ring. All get the blocking `mutex_lock()`.
- `io_msg_remote_post()`: returns void, sets `req->tctx = NULL`, and has no
  test of `submitter_task`. The data path has no `-EOWNERDEAD`.
- `submitter_task` of the target: valid because the `smp_load_acquire()` test
  of `IORING_SETUP_R_DISABLED` pairs with the `smp_store_release()` in
  `io_register_enable_rings()`.
- Remote data path result: `io_msg_data_remote()` returns 0 once queued; an
  overflow or drop on the target is not reported to the sender.
- Private request and ring type: `io_req_task_work_add_remote()` does
  `WARN_ON_ONCE()` and returns on a ring without `IORING_SETUP_DEFER_TASKRUN`;
  `io_req_normal_work_add()` would dereference `req->tctx`.
- Freeing: `io_msg_tw_complete()` uses `kfree_rcu(req, rcu_head)`, then
  `percpu_ref_put()` on the target's `refs`.
- `kfree_rcu()` and the queueing code: `io_req_local_work_add()` does not
  touch the request after `mpscq_push()`; `zcrx_notif_tw()` in
  `io_uring/zcrx.c` frees the same kind of request with `kmem_cache_free()`.
- **Unsafe usage**: completing the private request through
  `io_req_task_complete()` or `io_req_complete_defer()`.
  `io_free_batch_list()` calls `io_put_task()`, which dereferences
  `req->tctx`, and puts the request in the target's cache.
  - Safe: a task work callback of its own that posts the CQE and frees the
    request, as `io_msg_tw_complete()` does.

## Task work

**Task work queues**

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

**mpscq producers and consumers**

- `mpscq_push()`: usable from task, softirq and hardirq context; it is one
  `xchg()` on `tail` plus one `WRITE_ONCE()`, takes no lock and never retries.
- `mpscq_push()` return value: `true` when the queue was empty before the
  push; `io_req_normal_work_add()` notifies the task only then;
  `io_req_local_work_add()` sets `IORING_SQ_TASKRUN` and signals the eventfd
  only then, but decides the wake from `cq_wait_nr` on every add.
- Consumers: one at a time, serialised by the caller; `mpscq_pop()` and
  `mpscq_pop_emptied()` have no protection of their own.
- `task_list` consumers: no lock; `tctx_task_work_run()` is called by the
  task that owns the tctx, or by `io_tctx_fallback_work()`, which
  `io_fallback_tw()` queues only after `task_work_add()` failed.
- `mpscq_pop()` returning NULL: either the queue is empty, or a producer has
  swapped `tail` and not yet linked its node; `mpscq_empty()` is false in the
  second case.
- **Potentially unsafe usage**: treating NULL from `mpscq_pop()` as "queue
  empty".
  - Unsafe: when the consumer then sleeps or tears down without testing
    `mpscq_empty()`; an entry already pushed is left unrun.
  - Safe: test `mpscq_empty()` after NULL and retry while it is false, as
    `tctx_task_work_run()` does.
  - Safe: stop on NULL and let the caller re-test `io_local_work_pending()`,
    as `__io_run_local_work_loop()` and `io_run_local_work_continue()` do.
- **Potentially unsafe usage**: retrying `mpscq_pop()` in a loop after NULL.
  - Unsafe: when the loop cannot be preempted or holds something the
    producer needs; the producer may have been preempted between its two
    stores and the loop never ends.
  - Safe: `cond_resched()` between attempts in process context, as
    `io_cancel_local_task_work()` and `__io_run_local_work()` do;
    `tctx_task_work_run()` also drops `ctx->uring_lock` first through
    `ctx_flush_and_put()`.
- `tctx_task_work_run()`: stops after a pop for which `mpscq_pop_emptied()`
  is true; the next `mpscq_push()` returns `true` and
  `io_req_normal_work_add()` calls `task_work_add()` again.

**Deferred task running**

- There is no io_ring_submitter_task() here; the tests are
  `io_allowed_run_tw()` and `io_allowed_defer_tw_run()` in `io_uring/tw.h`.
- `io_req_local_work_add()`: there is no nr_tw field, no IO_CQ_WAKE_FORCE
  and no `try_cmpxchg()` loop; it pushes with `mpscq_push()` and then counts
  `cq_wait_nr` down.
- `IO_CQ_WAKE_INIT`: defined as `(-1)` in `io_uring/wait.h`; `cq_wait_nr` is
  compared as a signed `int`.
- `cq_wait_nr` values:

| Value | Meaning |
|---|---|
| `IO_CQ_WAKE_INIT` | no waiter, or a forced add has claimed the wake |
| 0 | the lazy countdown reached zero and the wake was issued |
| above 0 | number of lazy adds still needed before the wake |

- Wake decision in `io_req_local_work_add()`, in order:
  1. `cq_wait_nr <= 0`: return, no wake.
  2. Add with `IOU_F_TWQ_LAZY_WAKE` (cleared first for a request with
     `IO_REQ_LINK_FLAGS`): `atomic_dec_and_test()`; wake only when it
     reaches zero.
  3. Add without it: `atomic_xchg()` to `IO_CQ_WAKE_INIT`; wake only when
     the old value was above 0.
- One wake per arming: after the wake `cq_wait_nr` is 0 or below, so later
  adds do not wake until the waiter arms it again.
- Early wake: a producer delayed between its push and the countdown can
  count down a later wait cycle; the waiter must recheck, as the loop in
  `io_cqring_wait()` does.
- Arming `cq_wait_nr`: `io_cqring_wait()` in `io_uring/wait.c` and
  `io_loop_wait_start()` in `io_uring/loop.c` store the count before
  `set_current_state()`; `io_cqring_min_timer_wakeup()` and
  `io_uring_try_cancel_requests()` store 1 followed by `smp_mb()`.

**Task work token**

- Guarantee: `ctx->uring_lock` of `req->ctx` is held, and the runner calls
  `io_submit_flush_completions()` after the handler returns.
- Not guaranteed: that `current` is the task that submitted the request; the
  runner can be a kworker (`io_tctx_fallback_work()`, `io_ring_exit_work()`),
  and then `tw.cancel` is true.
- Creators: a local `struct io_tw_state`, instantiated only in
  `io_uring/tw.c`, by `tctx_task_work_run()`, `io_run_local_work()`,
  `io_run_local_work_locked()` and `io_cancel_local_task_work()`; there is no
  macro for it.
- There is no io_fallback_req_func() here; `ctx_flush_and_put()` receives a
  token and does not create one.
- Code that is not task work: set the result, set `req->io_task_work.func`,
  call `io_req_task_work_add()`; `io_req_queue_tw_complete()` in
  `io_uring/io_uring.h` and `io_req_task_queue_fail()` do all three.
- **Potentially unsafe usage**: calling `io_req_complete_defer()`,
  `io_req_task_complete()` or `io_req_defer_failed()` outside a task work
  handler.
  - Unsafe: when `ctx->uring_lock` is not held or nothing flushes
    `submit_state.compl_reqs` afterwards; `io_req_complete_defer()` has
    `lockdep_assert_held()` and only appends to that list.
  - Safe: on the issue path with `IO_URING_F_COMPLETE_DEFER`, as
    `io_issue_sqe()` does; `io_submit_sqes()` runs under `uring_lock` and
    flushes in `io_submit_state_end()`.
  - Safe: under the lock with an explicit flush, as
    `io_uring_try_cancel_uring_cmd()` does.
- **Unsafe usage**: passing `IO_URING_CMD_TASK_WORK_ISSUE_FLAGS` to
  `io_uring_cmd_done()` outside a task work callback;
  `__io_uring_cmd_done()` then calls `io_req_complete_defer()`.
  - Safe: inside the callback given to `io_uring_cmd_complete_in_task()`, as
    `fuse_uring_send_in_task()` does.
  - Safe: inside `->uring_cmd()`, pass on the `issue_flags` it received, as
    `fuse_uring_cancel()` does; `io_uring_try_cancel_uring_cmd()` holds
    `uring_lock` and flushes after the call.

**Task work at exit**

- `io_should_terminate_tw()`: true for `PF_EXITING` or `PF_KTHREAD` in
  `current->flags`, or `percpu_ref_is_dying(&ctx->refs)`; it does not test
  for a pending signal.
- Handlers do not call `io_should_terminate_tw()`; only the runners in
  `io_uring/tw.c` do, and they store the result in `cancel` of
  `struct io_tw_state`. Handlers test `tw.cancel`.
- `tctx_task_work_run()`: recomputes `ts.cancel` each time it locks a ctx,
  that is when `req->ctx` is not the ctx it holds; not for every entry.
- `__io_run_local_work()`: recomputes `tw.cancel` on every pass of its
  `again` loop.
- `io_cancel_local_task_work()`: sets `cancel` to true without calling
  `io_should_terminate_tw()`.
- Result code on cancel is per handler: for example `io_req_task_submit()`
  fails the request with `-EFAULT`, `io_poll_check_events()` returns
  `-ECANCELED`.
- Per-task queue: there is no fallback_llist, no `fallback_work` in
  `struct io_ring_ctx` and no io_fallback_req_func(); entries are never moved
  off `task_list`.
- `io_fallback_tw()`: takes one argument; it takes a task reference and
  queues `fallback_work` of `struct io_uring_task`, a `struct work_struct`,
  on `system_dfl_wq`.
- `io_tctx_fallback_work()`: calls `tctx_task_work_run()` on the same
  `task_list` from a kworker, so `PF_KTHREAD` makes every handler see
  `tw.cancel`.
- `tctx_task_work_run()` in a task with `PF_EXITING`: does not punt; it runs
  the handlers in that task with `tw.cancel` true.
- Per-ring queue: there is no io_move_task_work_from_local();
  `io_cancel_local_task_work()` pops `work_list` under `ctx->uring_lock` and
  calls each handler in the calling task.
- `io_cancel_local_task_work()` callers: `io_ring_exit_work()` and
  `io_iopoll_try_reap_events()`.

**Ring exit cancel loop**

- `io_ring_exit_work()`: calls `io_cancel_local_task_work()` on every pass
  of its inner loop when `IORING_SETUP_DEFER_TASKRUN` is set; the handlers
  run in the exit kworker itself, not in a second work item.
- Loop shape: inner `do { io_cancel_local_task_work(); cond_resched(); }
  while (io_uring_try_cancel_requests(ctx, NULL, true, false))`; outer loop
  ends on `wait_for_completion_interruptible_timeout()` of `ctx->ref_comp`.
- `io_uring_try_cancel_requests()` with a NULL `tctx`: does not call
  `flush_delayed_work()` or `io_run_task_work()`, and skips
  `io_run_local_work()` in the kworker because `io_allowed_defer_tw_run()`
  is false.
- `io_cancel_local_task_work()`: returns `void`, so work it ran does not
  count as progress for the inner loop; the timed outer wait calls it again.
- **Unsafe usage**: a loop run by a task other than `submitter_task` that
  waits for the ring's requests to drain without calling
  `io_cancel_local_task_work()` on each pass.
  - Unsafe: `__io_run_local_work()` returns `-EEXIST` for that task, entries
    stay on `work_list`, and their requests keep `ctx->refs` from reaching
    zero.
  - Safe: `io_ring_exit_work()` calls it before every
    `io_uring_try_cancel_requests()`.
  - Safe: in `submitter_task`, `io_uring_try_cancel_requests()` runs the
    queue with `io_run_local_work()`, as under `io_uring_cancel_generic()`.
- **Unsafe usage**: taking `work_list` as empty after one call of
  `io_cancel_local_task_work()`.
  - Unsafe: when the cancelled requests have links; the final
    `io_submit_flush_completions()` reaches `io_queue_next()`, which queues
    the next request on `work_list` after the drain loop has ended.
  - Safe: call it again until `ctx->ref_comp` completes, as
    `io_ring_exit_work()` does.
- **Unsafe usage**: calling `io_cancel_local_task_work()` or
  `io_uring_try_cancel_requests()` with `ctx->uring_lock` held; both take it.
  - Safe: drop the lock first, as `io_iopoll_try_reap_events()` does before
    `io_cancel_local_task_work()`.
- **Potentially unsafe usage**: sleeping without a timeout after a pass that
  cancelled nothing.
  - Unsafe: when `cq_wait_nr` was not armed for this pass, or work queued
    before the sleep is not rechecked; `io_req_local_work_add()` wakes once
    per arming.
  - Safe: `io_uring_cancel_generic()` relies on
    `io_uring_try_cancel_requests()` storing 1 in `cq_wait_nr` each pass,
    and after `prepare_to_wait()` it tests `io_local_work_pending()` and
    `tctx_inflight()` before `schedule()`.
  - Safe: the cancel loop of `io_ring_exit_work()` waits for requests only
    in `wait_for_completion_interruptible_timeout()`.

## Multishot and poll

**Poll ownership**

- `io_poll_get_ownership()` slow-path test: compares the whole `poll_refs`
  value, cast to unsigned and not masked, with `IO_POLL_REF_BIAS`; while
  `IO_POLL_CANCEL_FLAG` or `IO_POLL_RETRY_FLAG` is set, every attempt takes
  `io_poll_get_ownership_slowpath()`.
- `io_poll_get_ownership_slowpath()`: ORs in `IO_POLL_RETRY_FLAG`; it
  increments, and can win ownership, only if the reference bits were zero.
  It does not set the count to `IO_POLL_REF_BIAS`.
- `__io_arm_poll_handler()`: starts `poll_refs` at 1 only with
  `IO_URING_F_UNLOCKED`; without it it starts at 0 and the arming code is not
  the owner.
- Arming without ownership: must call `io_poll_can_finish_inline()` before it
  completes inline or calls `__io_poll_execute()`; when that fails it calls
  `io_poll_mark_cancelled()` (arming error) or leaves the request hashed, and
  returns 0.
- `io_poll_check_events()`: releases ownership only at the loop exit that
  returns `IOU_POLL_NO_ACTION`; every other return keeps the references, so
  no later wakeup can queue task_work.
- `IOU_POLL_REQUEUE`: `io_poll_task_func()` requeues with
  `__io_poll_execute()`, not `io_poll_execute()`, because it still owns the
  request.
- There is no io_poll_remove_one() here; cancel is `io_poll_cancel_req()`
  (mark, then `io_poll_execute()`), and `IORING_OP_POLL_REMOVE` uses
  `io_poll_disarm()`, which returns `-EALREADY` without ownership.
- **Potentially unsafe usage**: writing `req->flags` or unlinking a wait
  entry without ownership.
  - Unsafe: from a wakeup after `io_poll_get_ownership()` returned false,
    when it writes `req->flags`, or touches the request after `poll->head` is
    stored NULL; `io_poll_task_func()` may be completing the request at the
    same time.
  - Safe: `io_pollfree_wake()` on `POLLFREE`: marks cancelled, calls
    `io_poll_execute()`, then only unlinks with `io_poll_remove_waitq()`,
    whose `smp_store_release()` of `poll->head` must come last because
    `io_poll_remove_entry()` skips the waitqueue lock once it reads NULL.
  - Safe: `io_poll_double_prepare()` sets `REQ_F_DOUBLE_POLL` under the first
    entry's `head->lock`, which `io_poll_wake()` runs under
    (`__wake_up_common()` asserts it).
  - Safe: `__io_queue_proc()` sets `REQ_F_SINGLE_POLL` before the first
    `add_wait_queue()`, when no entry can fire.

**Multishot flags**

- `REQ_F_MULTISHOT`: set only by `io_sendmsg_prep()` for
  `IORING_RECVSEND_BUNDLE`; tested only by `io_wq_submit_work()`. No handler
  reads it.
- `REQ_F_APOLL_MULTISHOT`: set by opcode prep, for example
  `io_recvmsg_prep()`, `io_accept_prep()`, `io_read_mshot_prep()` and
  `io_recvzc_prep()`; `io_arm_poll_handler()` does not set it.
- `io_cmd_poll_multishot()` in `io_uring/uring_cmd.c`: the one place that
  sets `REQ_F_APOLL_MULTISHOT` at issue time, just before `io_arm_apoll()`.
- `REQ_F_APOLL_MULTISHOT` readers in `io_uring/poll.c`: `io_arm_apoll()`
  leaves out `EPOLLONESHOT`; `io_poll_check_events()` calls `io_poll_issue()`
  instead of posting the poll mask itself.
- `IORING_POLL_ADD_MULTI` and `IORING_TIMEOUT_MULTISHOT` requests: carry
  neither request flag; the state is the missing `EPOLLONESHOT` in
  `poll->events` and the flag in `struct io_timeout_data`.
- Staying armed: a handler tests `req->flags & REQ_F_APOLL_MULTISHOT`, as
  `io_accept()`, `io_recv_finish()` and `io_read_mshot()` do.
- First inline issue: has no `IO_URING_F_MULTISHOT`, yet these handlers post
  with `IORING_CQE_F_MORE` and return `IOU_RETRY`; `io_queue_async()` then
  arms poll.
- `IO_URING_F_MULTISHOT` in a handler: gates what the poll loop alone
  understands, for example `IOU_REQUEUE` and `io_poll_multishot_retry()`; see
  "Multishot handler results".
- `io_uring_cmd_post_mshot_cqe32()`: the exception, it refuses to post
  without `IO_URING_F_MULTISHOT`.
- Clearing: only `io_wq_submit_work()` clears `REQ_F_APOLL_MULTISHOT`; a
  handler that ends multishot leaves it set and returns `IOU_COMPLETE`.

**Multishot handler results**

- Finish: `io_req_set_res()` then `IOU_COMPLETE`; a positive return is not a
  completion, `io_poll_check_events()` carries on as for `IOU_RETRY`.
- Run again, three forms:

  | Form | Effect | Used by |
  |---|---|---|
  | loop inside the handler | no return to the core | `io_recv_finish()` returning false, `io_accept()` |
  | `io_poll_multishot_retry()` then `IOU_RETRY` | `io_poll_check_events()` loops, calls `vfs_poll()`, reissues only if it reports events | `io_read_mshot()` |
  | `IOU_REQUEUE` | new task_work through `__io_poll_execute()`, ownership kept | `io_recv_finish()`, `io_zcrx_tcp_recvmsg()` |

- After a posted CQE with input possibly left, under `IO_URING_F_MULTISHOT`:
  a plain `IOU_RETRY` waits for a new wakeup that may never come; the handler
  must use one of the three forms.
- `io_read_mshot()`: calls `io_poll_multishot_retry()` only under
  `IO_URING_F_MULTISHOT`, and returns `IOU_RETRY` either way.
- Final CQE after `IOU_COMPLETE`: `__io_submit_flush_completions()` falls
  back to `io_cqe_overflow()` or `io_cqe_overflow_locked()`, so finishing is
  what keeps the result.
- **Potentially unsafe usage**: `IOU_RETRY` after `io_req_post_cqe()` or
  `io_req_post_cqe32()` returned false.
  - Unsafe: when the result is already consumed, such as a buffer committed
    by `io_put_kbuf()` or an installed fd; nothing posts it later.
  - Safe: `io_uring_cmd_timestamp()` splices the unposted skbs back onto
    `sk_error_queue` before it returns `-EAGAIN`.
- File would block: the handler posts nothing, calls `io_kbuf_recycle()` and
  returns `IOU_RETRY`, as `io_recv()` and `io_read_mshot()` do; they do not
  arm poll themselves.
- `io_read_mshot()` on an unpollable file: `-EBADFD`, before any read.

**Multishot requests in io-wq**

- The test: `req->flags & (REQ_F_MULTISHOT|REQ_F_APOLL_MULTISHOT)`; either
  flag is enough, and no prep function sets both.
- Order of the branches in `io_wq_submit_work()`:

  | Step | Condition | Result |
  |---|---|---|
  | 1 | `io_file_can_poll()` false | fail, `-EBADFD` |
  | 2 | `O_NONBLOCK` or `FMODE_NOWAIT` | `io_arm_poll_handler()`; anything but `IO_APOLL_OK` fails with `-ECANCELED`; the handler is not called |
  | 3 | otherwise | clear both flags, then the normal issue loop, as a single-shot request |

- Reason in the code: with `IORING_SETUP_DEFER_TASKRUN` only the submitter
  task may post CQEs, and auxiliary CQEs are not rerouted the way final
  completions are.
- Flag timing: the check sees only flags set before the worker runs;
  `io_cmd_poll_multishot()` sets `REQ_F_APOLL_MULTISHOT` at issue and is not
  caught on its first issue.
- After step 3 the cleared request flag is what a handler sees:
  `io_read_mshot()` takes its `!(req->flags & REQ_F_APOLL_MULTISHOT)` branch
  and completes once.
- **Potentially unsafe usage**: a request that posts more than one CQE and
  has neither flag set at prep.
  - Unsafe: when the issue handler itself calls `io_req_post_cqe()` and can
    run in a worker (`REQ_F_FORCE_ASYNC`, or a punt by `io_queue_async()`).
  - Safe: posting only from task_work, as `io_timeout_complete()` does, and
    `io_poll_check_events()` for `IORING_OP_POLL_ADD`.
  - Safe: posting only under `IO_URING_F_MULTISHOT`, which a worker never
    passes, as `io_uring_cmd_post_mshot_cqe32()` enforces.
  - Safe: a handler that tests a private flag, when prep also set
    `REQ_F_MULTISHOT`, as `io_sendmsg_prep()` does for
    `IORING_RECVSEND_BUNDLE` and `io_send_finish()`; a socket file always
    has `FMODE_NOWAIT` (`sock_alloc_file()`), so a worker takes step 2 and
    never calls `io_send()`.

## Provided buffers

**Provided buffer kinds**

- `req->buf_index` after selection: the buffer id for both kinds
  (`io_provided_buffer_select()` and `io_ring_buffer_select()` both store the
  bid).
- `req->buf_index` before selection: the group id, set by `io_init_req()`;
  prep copies it to `io->buf_group` (`io_uring/rw.c`) or `sr->buf_group`
  (`io_uring/net.c`).
- Legacy recycle: takes the group from `req->kbuf->bgid`, not from
  `req->buf_index`.
- Ring flag states:

| Flags on the request | Meaning |
|---|---|
| `REQ_F_BUFFER_RING` and `REQ_F_BUFFERS_COMMIT` | ring buffer picked, `bl->head` not yet moved |
| `REQ_F_BUFFER_RING` alone | ring buffer picked and already committed; the request keeps it across retries |

- `io_do_buffer_select()`: false while `REQ_F_BUFFER_RING` or
  `REQ_F_BUFFER_SELECTED` is set, so a retry reuses the buffer it holds.
- `io_ring_buffers_peek()`: sets `REQ_F_BUFFER_RING` and not
  `REQ_F_BUFFERS_COMMIT`; its callers `io_buffers_select()` and
  `io_buffers_peek()` add `REQ_F_BUFFERS_COMMIT`.
- `IO_REQ_CLEAN_FLAGS` in `io_uring/io_uring.c`: contains
  `REQ_F_BUFFER_SELECTED` but not `REQ_F_BUFFER_RING`; `io_clean_op()` frees a
  legacy buffer the handler never put, a ring buffer has no such fallback.

**Buffer ring memory access**

- `IOBL_INC` progress: kept only in the shared entry; `io_kbuf_inc_commit()`
  writes the advanced `addr` and reduced `len` back, and the next selection
  reads them again from shared memory.
- No kernel-private offset exists, so every selection must treat `addr` and
  `len` of the head entry as new untrusted input, including on a partly
  consumed buffer.
- `access_ok()`: both `io_ring_buffer_select()` and `io_ring_buffers_peek()`
  call it on the local copies of `addr` and `len`.
- Callers rely on that check: `io_recvmsg()` builds its iterator with
  `iov_iter_ubuf()` and `io_recv_buf_select()` for a bundle with
  `iov_iter_init()`, neither of which checks the range.
- Failed `access_ok()`: `io_ring_buffer_select()` returns a NULL `addr` with
  neither `REQ_F_BUFFER_RING` nor `REQ_F_BUFFERS_COMMIT` set;
  `io_ring_buffers_peek()` returns `-EFAULT`.
- `bl->min_left_sub_one`: `io_kbuf_inc_commit()` treats an incremental buffer
  as used up when the remainder is not above it, then writes `len` 0 and moves
  `bl->head`; it comes from `min_left` of `struct io_uring_buf_reg`.
- `io_kbuf_inc_commit()` with `len` 0, or on an entry whose `len` reads 0:
  returns false and does not move `bl->head`.
- `ctx->uring_lock`: must be held; `io_buffer_get_list()` and
  `io_buffers_peek()` assert it, `io_kbuf_commit()` has no assertion of its
  own and updates `bl->head` with plain stores.
- `bl->head`: kernel-private but not hidden; `io_register_pbuf_status()`
  copies it to userspace.
- **Potentially unsafe usage**: reading one field of a `struct io_uring_buf`
  more than once.
  - Unsafe: when the check (clamp, `access_ok()`, zero test) is applied to one
    read and a different read supplies the length or address of the transfer.
  - Safe: when each read is used on its own, as in `io_ring_buffers_peek()`:
    the first read of `len` only tests for zero and limits how many entries
    are walked, and each iovec takes one `READ_ONCE()` local that feeds both
    `access_ok()` and `iov_len`.

**Buffer commit**

- `io_should_commit()`: true for `IO_URING_F_UNLOCKED`, or for a file that
  cannot poll unless `io_is_uring_cmd()`; it does not test
  `REQ_F_APOLL_MULTISHOT`.
- `io_is_uring_cmd()`: matches `IORING_OP_URING_CMD` and
  `IORING_OP_URING_CMD128`.
- `io_should_commit()` has one caller, `io_ring_buffer_select()`; the
  multi-buffer paths decide differently:

| Selector (ring list) | Flags it leaves set | Commit at selection |
|---|---|---|
| `io_ring_buffer_select()` | `REQ_F_BUFFER_RING`; also `REQ_F_BUFFERS_COMMIT` unless it committed | when `io_should_commit()` is true |
| `io_buffers_select()` | `REQ_F_BUFFER_RING`, `REQ_F_BL_NO_RECYCLE` | always |
| `io_buffers_peek()` | `REQ_F_BUFFER_RING`, `REQ_F_BUFFERS_COMMIT` | never |

- uring_cmd, locked issue: `io_uring_cmd_buffer_select()` selects through
  `io_buffer_select()` without a commit; the commit is in
  `io_uring_mshot_cmd_post_cqe()`, through `io_put_kbuf()` with
  `sel->buf_list`.
- uring_cmd under `IO_URING_F_UNLOCKED`: committed at selection like any other
  opcode.
- `io_kbuf_commit()`: clears `REQ_F_BUFFERS_COMMIT` itself; with the flag
  clear it returns true and does not touch the list.
- `io_kbuf_commit()` with `len < 0`: clears the flag and returns true without
  moving `bl->head`, so the buffer stays in the ring.
- `io_kbuf_commit()` arguments: a plain ring moves `bl->head` by `nr` and
  ignores a non-negative `len`; an `IOBL_INC` ring uses only `len`.
- `REQ_F_BUF_MORE`: set when a select-time commit returns false; the later
  put commits nothing, `__io_put_kbufs()` reports `IORING_CQE_F_BUF_MORE` for
  the flag and `__io_put_kbuf_ring()` clears it.
- Byte count: pass the bytes placed in the buffer, not the raw return value;
  `io_recv()` and `io_recvmsg()` clamp `consumed` to the selected length
  because `MSG_TRUNC` returns the full packet size.
- Bundle count: `io_bundle_nbufs()` returns 0 for `ret <= 0`, so the put of a
  failed bundle moves the head by nothing.
- **Unsafe usage**: returning from the issue handler with
  `REQ_F_BUFFERS_COMMIT` still set.
  - Unsafe: the next issue skips selection (`io_do_buffer_select()` is false)
    and puts with a NULL list, so `bl->head` never moves and another request
    is handed the same buffer.
  - Safe: recycle before returning, as `io_recv()` does on `-EAGAIN` and
    `io_read()` does when `__io_read()` fails while the flag is set.
  - Safe: commit before returning, as `io_net_kbuf_recyle()` does.
- **Potentially unsafe usage**: `io_put_kbuf()` or `io_put_kbufs()` with a NULL
  list.
  - Unsafe: while `REQ_F_BUFFERS_COMMIT` is set; `__io_put_kbuf_ring()` skips
    `io_kbuf_commit()`, the CQE reports the bid and `bl->head` stays.
  - Safe: when `REQ_F_BUFFERS_COMMIT` is clear, as in `io_req_rw_complete()`:
    `io_should_commit()` committed at selection for `IO_URING_F_UNLOCKED` and
    for a file that cannot poll, and `io_read()` recycles on a negative return
    while the flag is set.

**Buffer recycle and put**

- Wait for poll with nothing transferred: `io_kbuf_recycle()`, called by the
  handler; its only callers are in `io_uring/rw.c`, `io_uring/net.c` and
  `io_uring/uring_cmd.c`, no core path does it.
- Retry after a partial transfer: neither helper; `io_net_kbuf_recyle()` in
  `io_uring/net.c` (spelled so) sets `REQ_F_BL_NO_RECYCLE` and calls
  `io_kbuf_commit()` with the bytes done, building no cflags.
- After `io_net_kbuf_recyle()`: `REQ_F_BUFFER_RING` stays set, so the retry
  does no selection and continues in the same buffer with the iterator left
  in `kmsg->msg.msg_iter`.
- Final put after such a retry: gets a NULL list and builds cflags from
  `req->buf_index`.
- `io_kbuf_recycle()` on a ring buffer with a NULL list: returns false and
  leaves `REQ_F_BUFFER_RING` set; the buffer was already committed and stays
  with the request.
- `io_kbuf_recycle()` on a legacy buffer: ignores the list argument;
  `io_kbuf_recycle_legacy()` calls `io_ring_submit_lock()`, which takes
  `ctx->uring_lock` for `IO_URING_F_UNLOCKED`, and looks the list up again.
- `io_read()`: recycles only when `REQ_F_BUFFERS_COMMIT` is set, so a legacy
  buffer or an already committed ring buffer stays with the request on
  error.
- `io_put_kbufs()` on a legacy buffer: frees the `struct io_buffer` through
  `io_kbuf_drop_legacy()`; it does not return to the list.
- `io_put_kbuf()` and `io_put_kbufs()` with neither selected flag set: return
  0, so calling them after a recycle is harmless.

**Buffer list lifetime**

- `IORING_OP_REMOVE_BUFFERS`: does not free the list;
  `io_remove_buffers_legacy()` frees only `struct io_buffer` entries and an
  emptied legacy list stays in `ctx->io_bl_xa`.
- A list that was stored in `ctx->io_bl_xa` is freed only in `io_put_bl()`,
  reached from:
  - `io_unregister_pbuf_ring()`, ring lists only (`-EINVAL` for legacy);
  - `io_register_pbuf_ring()`, which replaces an empty legacy list of the
    same group through `io_destroy_bl()`;
  - `io_destroy_buffers()` at ring teardown.
- A group can change kind while a request owns a legacy buffer;
  `io_kbuf_recycle_legacy()` frees the buffer when the list is gone or is now
  a ring.
- `buf_list` after `io_ring_buffer_select()`: NULL whenever the buffer was
  committed at selection, locked or not; non-NULL means the commit is
  pending.
- `buf_list` after `io_buffers_select()`: when the group exists, NULL only for
  `IO_URING_F_UNLOCKED`; in the locked case it stays set, also for a legacy
  list and although the commit is done.
- `buf_list` after `io_buffers_peek()`: the ring list, or NULL for a legacy
  list.
- `addr` and `val` of `struct io_br_sel`: one union; storing the result in
  `val` destroys `addr`, so handlers consume `addr` first, as
  `__ublk_batch_dispatch()` does.
- Reset per pass: `io_recv()`, `io_recvmsg()` and `io_send()` set
  `sel.buf_list = NULL` at the top of each retry pass, since a pass where
  `io_do_buffer_select()` is false does no selection.
- The put and recycle helpers dereference the list only in
  `io_kbuf_commit()`, and only while `REQ_F_BUFFERS_COMMIT` is set;
  `io_kbuf_recycle_ring()` tests it for NULL only.
- uring_cmd: `io_uring_mshot_cmd_post_cqe()` must get the `struct io_br_sel`
  from `io_uring_cmd_buffer_select()` within the same issue call.
- **Unsafe usage**: calling `io_kbuf_commit()` directly with a NULL list while
  `REQ_F_BUFFERS_COMMIT` is set.
  - Unsafe: it reads `bl->flags` with no NULL test.
  - Safe: go through `io_put_kbuf()` or `io_put_kbufs()`, which test the list
    in `__io_put_kbuf_ring()`.
  - Safe: call it with the list just returned by a locked selection, as
    `io_net_kbuf_recyle()` does behind its test of `REQ_F_BUFFERS_COMMIT`.

## Registered buffers and resource nodes

**Resource nodes**

- There is no io_req_assign_rsrc_node() in this tree: `io_file_get_fixed()` in
  `io_uring/io_uring.c` and `io_find_buf_node()` in `io_uring/rsrc.c` do
  `node->refs++` themselves, inside `io_ring_submit_lock()`.
- `io_rsrc_node_lookup()` in `io_uring/rsrc.h`: bounds check only, takes no
  reference and asserts no lock.
- `io_file_get_fixed()`: does not set `REQ_F_FIXED_FILE`; the flag is set
  before the call, by the SQE flags copied in `io_init_req()` or by the
  opcode, as `io_nop_prep()` does. It ORs in `io_slot_flags()`.
- `io_req_put_rsrc_nodes()`: has one caller, `io_free_batch_list()`.
  `io_clean_op()` touches neither `req->file_node` nor `req->buf_node`.
- Splice and tee with `SPLICE_F_FD_IN_FIXED`: `io_splice_get_file()` in
  `io_uring/splice.c` takes its own reference on the input file's node,
  stores it in `rsrc_node` of `struct io_splice` and sets
  `REQ_F_NEED_CLEANUP`.
- `io_splice_cleanup()`: puts that reference; it is reached through
  `io_clean_op()` from `io_free_batch_list()`, so under `uring_lock`.
- Fixed-file lookup without a node reference: `io_msg_grab_file()` in
  `io_uring/msg_ring.c` takes `get_file()` on the file before it unlocks,
  and leaves `node->refs` alone.
- `io_clone_buffers()`: does `node->refs++` for each destination node it
  carries into the new table; the old table's reference goes in
  `io_rsrc_data_free()`.
- `io_clone_buffers()`: a cloned source buffer gets a new node from
  `io_rsrc_node_alloc()` in the destination ring; the node is not shared
  between rings, only its `struct io_mapped_ubuf` is.
- `io_free_rsrc_node()`: when `node->tag` is non-zero it first posts a CQE
  with `io_post_aux_cqe(ctx, node->tag, 0, 0)`, then releases by type.
- Failed registration: `io_sqe_files_register()` and
  `io_sqe_buffers_register()` call `io_clear_table_tags()` before they free
  the table, so no tag CQE is posted for those nodes.

**Importing a registered buffer**

- Request passed in: need not be the request being issued;
  `io_send_zc_import()` in `io_uring/net.c` passes `sr->notif` to
  `io_import_reg_buf()` and to `io_import_reg_vec()`.
- **Potentially unsafe usage**: passing the issuing request as `req`.
  - Unsafe: when the pages can still be in use after that request is freed;
    `io_req_put_rsrc_nodes()` then drops the node and the last put runs
    `io_buffer_unmap()`.
  - Safe: when the request is freed only after the I/O on the iterator has
    ended, as in `io_init_rw_fixed()` in `io_uring/rw.c`.
  - Safe: pass a request that lives as long as the pages are used, as
    `io_send_zc_import()` does with the notif.
- **Unsafe usage**: importing on a request whose prep did not store
  `req->buf_index`; `io_init_req()` writes it only for
  `IOSQE_BUFFER_SELECT`, and requests are recycled.
  - Safe: prep reads `sqe->buf_index` under the same flag that later
    triggers the import, as `io_sendmsg_prep()` does for
    `IORING_RECVSEND_FIXED_BUF`.
  - Safe: `io_uring_cmd_import_fixed()` and
    `io_uring_cmd_import_fixed_vec()` return `-EINVAL` when the command lacks
    `IORING_URING_CMD_FIXED`, the flag under which `io_uring_cmd_prep()`
    stores the index.
  - Safe: copy the index to the request that is passed, as
    `io_send_zc_import()` does with `notif->buf_index`.
- **Unsafe usage**: importing on a request that also selects a provided
  buffer; `buf_node` and `kbuf` are one union in `struct io_kiocb`, and
  `req->buf_index` doubles as the buffer group or buffer id.
  - Safe: prep rejects the combination with `REQ_F_BUFFER_SELECT`, as
    `io_sendmsg_prep()` and `io_recvmsg_prep()` do.
  - Safe: `io_uring_cmd_prep()` allows `REQ_F_BUFFER_SELECT` only with
    `IORING_URING_CMD_MULTISHOT`, which it rejects together with
    `IORING_URING_CMD_FIXED`.
- `io_find_buf_node()` with `REQ_F_BUF_NODE` already set: returns
  `req->buf_node` with no lock, lookup or new reference; a changed
  `req->buf_index` is ignored.
- **Potentially unsafe usage**: passing to `io_import_reg_vec()` a request
  other than the one whose async data holds `vec`; on reallocation the
  function sets `REQ_F_NEED_CLEANUP` on the request passed in.
  - Unsafe: when the owner of `vec` does not already have
    `REQ_F_NEED_CLEANUP`; `io_clean_op()` calls the opcode's `cleanup` only
    under that flag.
  - Safe: the owner sets the flag in prep, as `io_send_zc_prep()` does.
- Direction constants: there is no IO_IMU_DEST or IO_IMU_SOURCE; the bits in
  `imu->dir` are `IO_BUF_DEST` and `IO_BUF_SOURCE` in
  `include/linux/io_uring_types.h`.
- Kernel buffer direction: `io_buffer_register_request()` stores one bit,
  `1 << rq_data_dir(rq)`; `io_buffer_register_bvec()` stores the caller's
  mask, which may hold both bits.
- `io_import_reg_vec()`: tests the direction once, before it looks at any
  iovec.
- Per-segment range in `io_import_reg_vec()`: `validate_fixed_range()` runs in
  `io_vec_fill_bvec()` for a user buffer and in `iov_kern_bvec_size()` for a
  kernel buffer.
- `io_vec_fill_kern_bvec()`: has no range check of its own; it relies on
  `io_kern_bvec_size()` having run first.
- `validate_fixed_range()`: also returns `-EFAULT` when `len` is above
  `MAX_RW_COUNT`, for the single buffer and for each iovec.
- Kernel buffer addresses: `imu->ubuf` is 0, so `buf_addr` and `iov_base` are
  byte offsets into the buffer, not user addresses.
- Zero length: `io_import_reg_buf()` accepts `len == 0` after the range and
  direction checks and returns an empty iterator; `io_import_reg_vec()`
  rejects a zero-length iovec with `-EFAULT`.
- Summed length in `io_import_reg_vec()`: overflow gives `-EOVERFLOW`; a total
  above `MAX_RW_COUNT` gives `-EINVAL`.

**Registered buffer layout**

- `struct io_mapped_ubuf` has no is_kbuf field; a kernel-registered buffer is
  `imu->flags & IO_REGBUF_F_KBUF`, defined in `io_uring/rsrc.h`.
- Start offset in the first entry: use `imu->bvec[0].bv_offset` or
  `imu->bvec[0].bv_len`; neither `io_vec_fill_bvec()` nor
  `io_import_fixed()` derives it from `imu->ubuf`.
- Two equivalent forms exist: `io_vec_fill_bvec()` adds
  `imu->bvec[0].bv_offset` and indexes with `offset >> imu->folio_shift`;
  `io_import_fixed()` subtracts `bvec[0].bv_len` when the offset reaches it
  and skips `1 + (offset >> imu->folio_shift)` entries.
- **Unsafe usage**: shift arithmetic on `imu->bvec` of a buffer with
  `IO_REGBUF_F_KBUF`; its entries have arbitrary lengths and
  `imu->folio_shift` is `PAGE_SHIFT` whatever they are
  (`io_kernel_buffer_init()`).
  - Safe: test the flag first and walk the entries, as `io_import_fixed()`
    does through `io_import_kbuf()`.
  - Safe: `io_import_reg_vec()` calls `io_vec_fill_bvec()` only when the
    flag is clear, and `io_vec_fill_kern_bvec()` when it is set.
- `imu->len`: `size_t`; `io_kernel_buffer_init()` takes the total as
  `unsigned int`.
- Kernel registration has two entry points: `io_buffer_register_request()`
  copies the bvecs of a `struct request` and stores the request as
  `imu->priv`; `io_buffer_register_bvec()` copies a caller array and stores
  the caller's `priv`.
- ublk calls `io_buffer_register_request()` with `ublk_io_release()`;
  `io_buffer_register_bvec()` is used by `fs/fuse/dev_uring.c`.
- `io_kernel_buffer_init()`: `-EBUSY` when the slot holds a node, `-EINVAL`
  when the index is out of range; it never replaces a buffer.
- There is no io_buffer_unregister_bvec(); `io_buffer_unregister()` serves
  both entry points.
- `io_buffer_unregister()`: `-EINVAL` for an empty or out-of-range slot,
  `-EBUSY` for a slot that holds a user buffer; it drops only the table's
  node reference.
- User buffer pages: released by `io_release_ubuf()`, installed as
  `imu->release` with `imu->priv = imu`; it calls
  `unpin_user_folio(folio, 1)` once per bvec, not `unpin_user_page()`.
- One pin per bvec: `io_coalesce_buffer()` drops all but one pin of each
  folio at registration.
- Kernel buffer pages: released by the `release` callback given at
  registration; io_uring holds no pin on them.
- `io_buffer_unmap()`: calls `imu->release(imu->priv)` for both kinds, with
  no `IO_REGBUF_F_KBUF` test; only `io_buffer_unaccount_pages()` skips kernel
  buffers.
- `imu->release`: runs when the last `imu->refs` goes, which can be after
  `io_buffer_unregister()` has returned, and with `uring_lock` held of the
  ring that drops it.
- Userspace can empty a kernel buffer's slot: `__io_sqe_buffers_update()` and
  `io_sqe_buffers_unregister()` put any node, with no `IO_REGBUF_F_KBUF`
  test, so `release` can run without the driver calling
  `io_buffer_unregister()`.
- Accounting: `struct io_mapped_ubuf` has no field named `acct_pages`;
  `io_buffer_unmap()` computes the count with `io_buffer_unaccount_pages()`,
  which uses `ctx->hpage_acct` for compound pages, on every call, before it
  tests `imu->refs`.
- `io_unaccount_mem()`: called from `io_buffer_unmap()` on the last
  `imu->refs` only, not from `io_release_ubuf()`.

## Zero-copy send

**Notification and buffer lifetime**

- There is no io_send_zc() and no io_sendmsg_zc_prep() in this tree.
- `io_sendmsg_zc()` in `io_uring/net.c`: the issue function for both
  `IORING_OP_SEND_ZC` and `IORING_OP_SENDMSG_ZC`; see `io_issue_defs[]` in
  `io_uring/opdef.c`.
- `io_sendmsg_zc()` tells the two opcodes apart by `req->opcode`:
  `sock_sendmsg()` for `IORING_OP_SEND_ZC`, `__sys_sendmsg_sock()` otherwise.
- `io_send_zc_prep()`: the prep function for both opcodes; it also branches on
  `req->opcode`, to `io_send_setup()` or `io_sendmsg_setup()`.
- `io_send_zc_import()`: the one place that imports a registered buffer for a
  zero-copy send, with `sr->notif` as owner, through `io_import_reg_buf()` or
  `io_import_reg_vec()`.
- `io_send_zc_import()` runs at issue, from `io_sendmsg_zc()`, only while
  `REQ_F_IMPORT_BUFFER` is set on the send request; it clears the flag on
  success, so a retry does not import again.
- `notif->buf_index`: `io_send_zc_import()` copies it from `req->buf_index`
  before the import, because `io_find_buf_node()` looks up `buf_index` of the
  request it is passed and stores the node in that request's `buf_node`.
- Notification `user_data`: `sqe->addr3` when it is non-zero, otherwise the
  send request's `user_data`; see `io_send_zc_prep()`.
- `io_alloc_notif()` call in `io_send_zc_prep()`: comes after the
  `sqe->__pad2[0]` and `REQ_F_CQE_SKIP` checks, and before the flags are read.
- Prep failure before the allocation: no notification exists and
  `REQ_F_NEED_CLEANUP` is not set.
- Prep failure after the allocation (for example a flag outside
  `IO_ZC_FLAGS_VALID`, or a failed `io_msg_alloc_async()`):
  `REQ_F_NEED_CLEANUP` is already set, so `io_clean_op()` calls
  `io_send_zc_cleanup()`, and a notification CQE is still posted.
- Flag validation in `io_send_zc_prep()`: the only test that rejects is
  against `IO_ZC_FLAGS_VALID`; no combination of valid flags is rejected
  there.

**Notification flush**

- `io_notif_flush()` has two callers, `io_sendmsg_zc()` and
  `io_send_zc_cleanup()`, both in `io_uring/net.c`.
- `io_tx_ubuf_complete()` at the last reference: queues
  `io_notif_tw_complete()` with `__io_req_task_work_add()`, also when the
  flush itself drops the last reference with `ctx->uring_lock` held; a
  notification linked by `io_link_skb()` instead passes the drop to the chain
  head.
- `io_tx_ubuf_complete()`: never puts the notification on the completion list
  directly and does not call `io_req_complete_post()`.
- `IORING_NOTIF_USAGE_ZC_COPIED`: `io_notif_tw_complete()` ORs it into
  `notif->cqe.res`, not into the CQE flags.
- Lock requirement of `io_notif_flush()`: stated only by its
  `__must_hold(&notif->ctx->uring_lock)` annotation; neither it nor
  `io_tx_ubuf_complete()` has a `lockdep_assert_held()`.
- `io_notif_tw_complete()`: this is where `lockdep_assert_held()` on
  `ctx->uring_lock` is.
- Where the flush is done:

  | Case | Flush done in |
  |---|---|
  | issue returns `IOU_COMPLETE`, no `IO_URING_F_UNLOCKED` | `io_sendmsg_zc()` |
  | issue returns `IOU_COMPLETE` with `IO_URING_F_UNLOCKED` (io-wq) | `io_send_zc_cleanup()` |
  | issue returns `-ENOTSOCK`, `-EOPNOTSUPP` or an import error, in any context | `io_send_zc_cleanup()` |
  | issue returns `-EAGAIN` | nowhere yet; the notification is kept for the retry |
  | request fails or is cancelled before issue | `io_send_zc_cleanup()` |

- `io_send_zc_cleanup()`: reached only through `io_clean_op()`, which
  `io_free_batch_list()` calls with `ctx->uring_lock` held, and only while
  `REQ_F_NEED_CLEANUP` is set on the send request.
- io-wq order: after `io_sendmsg_zc()` returns, `io_req_complete_post()`
  posts the send CQE, or queues `io_req_task_complete()` on a ring with
  `IO_RING_F_LOCKLESS_CQ`; the cleanup flush runs later, when the request is
  freed, so the notification CQE cannot be queued ahead of the send CQE.
- `io_sendrecv_fail()`: writes only the send request's CQE; for the two
  zero-copy opcodes it sets `IORING_CQE_F_MORE` while `REQ_F_NEED_CLEANUP` is
  still set, and it copies `sr->done_io` into `cqe.res` if non-zero. It does
  not touch the notification.
- **Unsafe usage**: calling `io_req_msg_cleanup()` on a zero-copy send, without
  `IO_URING_F_UNLOCKED`, while `sr->notif` is still set.
  - Unsafe: `io_netmsg_recycle()` clears `REQ_F_NEED_CLEANUP` when it puts the
    header in `netmsg_cache`, so `io_clean_op()` never calls
    `io_send_zc_cleanup()` and the notification is never flushed.
  - Safe: flush, set `sr->notif = NULL`, then call `io_req_msg_cleanup()`, as
    `io_sendmsg_zc()` does.

## Passthrough commands

**Passthrough command SQE**

- Copy storage: `sqes[2]` in `struct io_async_cmd` (`io_uring/uring_cmd.h`),
  allocated as `req->async_data` by `io_uring_cmd_prep()`; there is no
  io_uring_cmd_data structure in this tree.
- `io_uring_cmd_sqe_copy()`: core-only. It is declared in
  `io_uring/uring_cmd.h`, not exported, and reached only through the
  `sqe_copy` member of `io_cold_defs[]` from `io_req_sqe_copy()` in
  `io_uring/io_uring.c`. A driver cannot request the copy.
- `uring_sqe_size()`: takes the request; gives the copy length, 128 bytes for
  `IORING_SETUP_SQE128` rings or opcode `IORING_OP_URING_CMD128`, else 64.
  A plain `IORING_OP_URING_CMD` on an `IORING_SETUP_SQE_MIXED` ring gets 64.
- `io_req_sqe_copy()` callers: `io_queue_async()` after `-EAGAIN`,
  `io_queue_sqe_fallback()` (forced async, drain), and `io_submit_sqe()` for
  every request added behind a link head. In the last two the first
  `->uring_cmd()` call already sees the copy.
- `cmd->sqe` in a call whose `issue_flags` carry `IO_URING_F_INLINE`: the SQ
  ring slot. `io_submit_sqe()` passes that flag only for requests it has not
  copied.
- `io_req_uring_cleanup()`: on completion without `IO_URING_F_UNLOCKED` it
  puts the async data into `ctx->cmd_cache` and, when the cache takes it,
  sets `ioucmd->sqe` to NULL; `cmd->sqe` is dead after `io_uring_cmd_done()`
  or a final return value.
- Payload size: `io_uring_sqe_cmd()` bounds the type to a 64-byte SQE,
  `io_uring_sqe128_cmd()` to 128 bytes, both at build time only. A driver
  using the 128-byte form must reject calls without `IO_URING_F_SQE128`, as
  `fuse_uring_cmd()` and `ublk_ctrl_uring_cmd()` do; otherwise it reads past
  the slot or past the 64 copied bytes.
- **Potentially unsafe usage**: reading `cmd->sqe` after the issue call
  returned `-EIOCBQUEUED` (task-work callback, completion handler).
  - Unsafe: when that issue call had `IO_URING_F_INLINE`; nothing copies the
    SQE afterwards and userspace may rewrite the slot.
  - Safe: when that issue call had `IO_URING_F_UNLOCKED` and the driver never
    calls `io_uring_cmd_issue_blocking()`; `io_queue_async()` and
    `io_queue_sqe_fallback()` run `io_req_sqe_copy()` before
    `io_queue_iowq()`. `ublk_ch_uring_cmd()` defers such calls to
    `ublk_ch_uring_cmd_cb()`, which then reads the SQE.
- **Unsafe usage**: reading `cmd->sqe` in a reissue the driver requested with
  `io_uring_cmd_issue_blocking()` after an inline `-EIOCBQUEUED`;
  `io_queue_iowq()` copies nothing and `IORING_URING_CMD_REISSUE` is set only
  by `io_uring_cmd()` on a `-EAGAIN` return.
  - Safe: a reissue after `-EAGAIN` from the inline issue;
    `io_queue_async()` copied the SQE before it, so
    `btrfs_uring_encoded_read()` reads `cmd->sqe->addr` again from the copy.

**Passthrough driver interface**

- `io_uring_cmd_done(cmd, ret, issue_flags)`: no `res2` argument.
  `io_uring_cmd_done32(cmd, ret, res2, issue_flags)` stores `res2` in
  `req->big_cqe.extra1` and, on `IORING_SETUP_CQE_MIXED` rings, sets
  `IORING_CQE_F_32`.
- Task-work callback type: `io_req_tw_func_t`, arguments
  `struct io_tw_req` and `io_tw_token_t`. There is no io_uring_cmd_tw_t and
  the callback receives no issue_flags.
- Inside the callback: get the command with `io_uring_cmd_from_tw()`, pass
  `IO_URING_CMD_TASK_WORK_ISSUE_FLAGS` to `io_uring_cmd_done()`;
  `uring_lock` is held.
- `tw.cancel`: true when the task is exiting, runs as a kthread, or the ring
  is dying (`io_should_terminate_tw()` in `io_uring/tw.h`). There is no
  IO_URING_F_TASK_DEAD flag. The callback must still complete the command,
  as `ublk_ch_uring_cmd_cb()` and `fuse_uring_send_in_task()` do.
- `io_uring_cmd_do_in_task_lazy()`: the lazy form; there is no
  io_uring_cmd_complete_in_task_lazy. `IOU_F_TWQ_LAZY_WAKE` is for commands
  that post one CQE and is ignored without `IORING_SETUP_DEFER_TASKRUN`.
- `io_uring_cmd_issue_blocking()`: not exported, so built-in callers only.
- `IORING_SETUP_IOPOLL` ring, file without `->uring_cmd_iopoll`:
  `io_uring_cmd()` does not fail; it leaves `REQ_F_IOPOLL` and
  `IO_URING_F_IOPOLL` clear and issues the command as non-polled.
- `IORING_URING_CMD_MULTISHOT`: `io_uring_cmd()` has no special case. Any
  return other than `-EAGAIN` and `-EIOCBQUEUED` ends the request.
- `-EAGAIN` from an `io_queue_sqe()` issue (`IO_URING_F_NONBLOCK`):
  `io_queue_async()` sends the request to io-wq; `io_arm_poll_handler()`
  returns `IO_APOLL_ABORTED` because the two opcodes set neither `pollin`
  nor `pollout` in `io_issue_defs[]`.
- `-EAGAIN` from the io-wq issue (`IO_URING_F_UNLOCKED | IO_URING_F_IOWQ`):
  `io_wq_submit_work()` fails the request with `-EAGAIN`, unless
  `REQ_F_IOPOLL` is set, in which case it loops and reissues.
- Completing inside the issue call: after `io_uring_cmd_done()` the issue
  call must return `-EIOCBQUEUED`, as `fuse_uring_cmd()` does; any other
  value makes `io_uring_cmd()` complete the request a second time or, for
  `-EAGAIN`, reissue it.
- `issue_flags` given to `io_uring_cmd_done()` must match the caller's lock
  state; they need not come from the core:

| Caller | `issue_flags` |
|---|---|
| issue or cancel call | the argument received |
| task-work callback | `IO_URING_CMD_TASK_WORK_ISSUE_FLAGS` |
| sleepable context without `uring_lock` | `IO_URING_F_UNLOCKED`, as `fuse_uring_entry_teardown()` |

- `IO_URING_F_UNLOCKED` on a cancelable command: `io_uring_cmd_del_cancelable()`
  takes the `uring_lock` mutex, so the caller must be able to sleep and must
  not hold that lock.

**Cancelable commands**

- `io_uring_cmd_mark_cancelable()`: sets only `IORING_URING_CMD_CANCELABLE`
  in `cmd->flags`; it sets no `REQ_F_` flag.
- Lock: taken by `io_ring_submit_lock()` from `issue_flags`. A call with
  `IO_URING_F_UNLOCKED` (io-wq issue) is valid and takes `uring_lock` itself.
- No effect when `req->flags` has `REQ_F_IOPOLL`. `io_uring_cmd()` sets that
  only if the ring is `IORING_SETUP_IOPOLL` and the file has
  `->uring_cmd_iopoll`; on an IOPOLL ring with a file lacking it the mark
  takes effect.
- `REQ_F_IOPOLL` command: never gets an `IO_URING_F_CANCEL` call, so teardown
  cannot depend on one.
- `IORING_OP_ASYNC_CANCEL`: `io_try_cancel()` in `io_uring/cancel.c` does not
  visit `ctx->cancelable_uring_cmd`. The only sender of `IO_URING_F_CANCEL`
  is `io_uring_try_cancel_uring_cmd()`, from
  `io_uring_try_cancel_requests()`.
- Cancel call `issue_flags`: exactly `IO_URING_F_CANCEL |
  IO_URING_F_COMPLETE_DEFER`. `IO_URING_F_SQE128` and `IO_URING_F_CQE32` are
  absent, so `IO_URING_F_CANCEL` must be tested before those, as
  `fuse_uring_cmd()` does.
- Cancel call result: the return value is ignored and the handler may leave
  the command pending. `ublk_cancel_cmd()` skips a started request and
  `fuse_uring_cancel()` acts only in state `FRRS_AVAILABLE`.
- Repetition: `io_uring_try_cancel_uring_cmd()` returns true whenever it
  called a handler, and `io_uring_cancel_generic()` and `io_ring_exit_work()`
  loop on that with only `cond_resched()` between passes.
  `io_ring_exit_work()` calls the handler again until the command is
  completed.
- Sleeping: the handler runs in process context under the `uring_lock` mutex
  and may sleep; `ublk_start_cancel()` takes `ub->cancel_mutex` and quiesces
  the queue.
- pdu: state the handler reaches through the pdu must be written before the
  mark and stay valid until `io_uring_cmd_done()`; see `ublk_prep_cancel()`
  and `fuse_uring_prepare_cancel()`.
- **Unsafe usage**: returning a final value (neither `-EIOCBQUEUED` nor
  `-EAGAIN`) from the issue call after marking, without
  `io_uring_cmd_done()`. `io_uring_cmd()` completes the request without
  `io_uring_cmd_del_cancelable()`, leaving a freed request on
  `ctx->cancelable_uring_cmd`.
  - Safe: return `-EIOCBQUEUED` on every path after the mark, as
    `fuse_uring_cmd()` does once `fuse_uring_do_register()` has marked.
- **Unsafe usage**: marking a command that another context may already
  complete. `io_uring_cmd_del_cancelable()` tests the flag before taking the
  lock; a completion that runs first skips the unlink and the mark then links
  a finished request.
  - Safe: mark before the command is published to completers, as
    `fuse_uring_do_register()` does before it sets `ent->cmd`.
- **Unsafe usage**: in the `IO_URING_F_CANCEL` call, calling
  `io_uring_cmd_done()` with `IO_URING_F_UNLOCKED`, or on a marked command
  other than the one passed. The first relocks the held `uring_lock`; the
  second can unlink the entry that `hlist_for_each_entry_safe()` already
  saved as next.
  - Safe: complete only the passed command with the passed `issue_flags`, as
    `fuse_uring_cancel()` does.

## SQPOLL and IOPOLL rings

**SQPOLL thread pointer**

- `thread` writers: `io_sq_offload_create()` stores the task and
  `io_sq_thread()` stores NULL at its two exits, all under `sqd->lock`;
  nothing else writes it.
- `io_sq_thread_stop()`, `io_put_sq_data()`, `io_sq_thread_finish()`: do not
  clear `thread`; `io_sq_thread_stop()` sets `IO_SQ_THREAD_SHOULD_STOP`,
  wakes the thread and waits on `exited`, and the other two reach it only
  when the last `refs` of the `struct io_sq_data` is dropped.
- Task reference: taken by `get_task_struct(tsk)` in
  `io_sq_offload_create()`, after `thread` is published and before
  `wake_up_new_task()`.
- `create_io_thread()` in `kernel/fork.c`: only returns what
  `copy_process()` returns.
- Reference drop: `put_task_struct(current)` in `io_sq_thread()`, under
  `sqd->lock`, directly after the NULL store, so a non-NULL result of
  `sqpoll_task_locked()` stays valid until `sqd->lock` is released.
- Lock order: `sqd->lock` is taken outside `ctx->uring_lock`;
  `io_sq_thread()` holds `sqd->lock` while `__io_sq_thread()` takes
  `uring_lock`.
- Code holding `uring_lock`: drops it before `io_sq_thread_park()` or
  `mutex_lock(&sqd->lock)`, as `io_register_iowq_max_workers()` and
  `__io_register_iowq_aff()` in `io_uring/register.c` do.
- `tsk->io_uring` of the returned task: can be NULL while `thread` is not.
  `io_sq_offload_create()` assigns it after publishing `thread`, outside
  `sqd->lock`, and leaves it NULL when `io_uring_alloc_task_context()`
  fails.
- `io_uring_alloc_task_context()`: returns the `struct io_uring_task *`; the
  caller stores it in `tsk->io_uring`.
- Readers of `tsk->io_uring`: test it for NULL, for example
  `io_ring_exit_work()` and `io_wq_cpu_affinity()`.
- **Potentially unsafe usage**: a plain load of `thread`, without
  `sqpoll_task_locked()` or `rcu_dereference()`.
  - Unsafe: when the loaded pointer is dereferenced or handed to another
    function; `io_sq_thread()` can clear it and drop the reference at any
    time.
  - Safe: when the value is only compared with NULL, as `io_uring_enter()`
    does to return `-EOWNERDEAD` and `io_sq_offload_create()` does to return
    `-ENXIO` on attach.
- Task signalled for task work on an `IORING_SETUP_SQPOLL` ring:
  `req->tctx->task`, by `__set_notify_signal()` in
  `io_req_normal_work_add()` in `io_uring/tw.c`; the function returns
  without `task_work_add()` and reads neither `sq_data` nor `thread`.
- `req->tctx`: set to `current->io_uring` in `io_init_req()`. On an SQPOLL
  ring `io_submit_sqes()` is reached only from `__io_sq_thread()`, so the
  task is the SQPOLL thread.
- `IORING_SETUP_DEFER_TASKRUN` with `IORING_SETUP_SQPOLL`: rejected by
  `io_uring_sanitise_params()`, so `io_req_local_work_add()` is never the
  path on an SQPOLL ring.
- `-EPERM` from `io_attach_sq_data()` (other `task_tgid`): not returned to
  user space; `io_get_sq_data()` falls through and allocates a new
  `struct io_sq_data` with its own thread.

**IOPOLL completion**

- `iopoll_list`: a `struct list_head`; requests are linked through
  `iopoll_node`.
- `comp_list`: not the link while a request is on `iopoll_list`;
  `io_do_iopoll()` uses it only after `list_del()`, to queue the request on
  `submit_state.compl_reqs`.
- Membership test: `io_issue_sqe()` calls `io_iopoll_req_issued()` when the
  request has `REQ_F_IOPOLL` and the handler returned
  `IOU_ISSUE_SKIP_COMPLETE`; there is no iopoll_queue bit in
  `struct io_issue_def`.
- `__io_uring_cmd_done()`: chooses the release store to `iopoll_completed`
  by `REQ_F_IOPOLL`, not by `IORING_SETUP_IOPOLL`.
- Reap loop in `io_do_iopoll()`: skips a request that is not completed and
  goes on, so requests leave the list out of order; pairing is
  `smp_store_release()` in the callback with `smp_load_acquire()` here.
- Lockless `list_empty(&ctx->iopoll_list)`: used as a hint without
  `uring_lock` in `__io_sq_thread()`, `io_sq_thread()` and
  `io_uring_try_cancel_requests()`; every walk, add and delete is under
  `uring_lock`.
- Release store to `iopoll_completed`: must be the callback's last access
  to the request; a poller holding `uring_lock` can then recycle it through
  `io_free_batch_list()`.
- Task work on a `REQ_F_IOPOLL` uring_cmd: allowed when the task-work
  callback finishes through `__io_uring_cmd_done()`, which for
  `REQ_F_IOPOLL` stores `iopoll_completed` instead of completing the
  request; `io_do_iopoll()` still posts the CQE.
- `iopoll_start`: shares storage with `io_task_work`, so queueing task work
  overwrites it.
- `poll_ctx` of `struct io_comp_batch`: set to the ring by `io_do_iopoll()`;
  a driver compares it with `io_uring_cmd_ctx_handle()` to learn whether
  the completion runs under that ring's `uring_lock`.
- **Potentially unsafe usage**: completing a polled uring_cmd with
  `io_uring_cmd_done32()` and `issue_flags` 0.
  - Unsafe: when the completion does not run inside `io_do_iopoll()` of the
    request's own ring; `io_req_uring_cleanup()` then puts into
    `ctx->cmd_cache` without `uring_lock`.
  - Safe: when `iob->poll_ctx` equals the request's ring, as
    `nvme_uring_cmd_end_io()` tests; `io_req_uring_cleanup()` treats every
    call without `IO_URING_F_UNLOCKED` as locked.
  - Safe: otherwise punt with `io_uring_cmd_do_in_task_lazy()` and complete
    with `IO_URING_CMD_TASK_WORK_ISSUE_FLAGS`, as `nvme_uring_task_cb()`
    does; `tctx_task_work_run()` holds `uring_lock` around the callback.

**Reissued requests**

- Marking condition in `io_complete_rw_iopoll()`: `res == -EAGAIN` and
  `io_rw_should_reissue()` returns true; it is tested before any comparison
  with `req->cqe.res`.
- When `io_complete_rw_iopoll()` does not mark the request: `req->cqe.res`
  is set to the result of `io_fixup_rw_res()` when that differs from it.
- `-EOPNOTSUPP`: leads to reissue only in `__io_complete_rw_common()`, the
  non-IOPOLL path.
- `io_rw_should_reissue()` returns false when any of these holds, and makes
  no other test:
  - the file is neither a block device nor a regular file;
  - `REQ_F_NOWAIT` is set;
  - the caller is an io-wq worker and the request lacks `REQ_F_IOPOLL`;
  - `percpu_ref_is_dying(&ctx->refs)`;
  - `CONFIG_BLOCK` is off.
- Iterator restore: done inside `io_rw_should_reissue()` at marking time
  (`io_meta_restore()`, `iov_iter_restore()`), in the completion callback's
  context, not later in the retry.
- CQE skip: `__io_submit_flush_completions()` posts nothing for a request
  with `REQ_F_REISSUE`.
- `io_free_batch_list()`: clears `REQ_F_REISSUE` and calls `io_queue_iowq()`
  directly, with no task work in between; the request is not put or
  returned to the cache. There is no io_req_task_queue_reissue() here.
- Thread-group test: lives in `io_queue_iowq()`, not in
  `io_rw_should_reissue()`; when `current` is not in the thread group of
  `req->tctx->task` it warns and sets `IO_WQ_WORK_CANCEL`, so
  `io_wq_submit_work()` fails the request with `-ECANCELED`.
- `io_req_complete_post()`: sends a request with `REQ_F_REISSUE` through
  `io_req_task_complete()` task work instead of posting a CQE, so it reaches
  `io_free_batch_list()` too.

## Cancellation and teardown

**Async cancel search and matching**

- `io_try_cancel()`, io-wq step: returns at once only when
  `io_async_cancel_one()` gives 0; `-EALREADY` (work running) continues to
  `io_poll_cancel()` like `-ENOENT` does.
- `io_try_cancel()` after an io-wq `-EALREADY`: returns what the later steps
  return, so with `CONFIG_FUTEX` the caller can see `-ENOENT` for a request
  that is running in io-wq.
- `__io_async_cancel()` slow path: runs whenever `io_try_cancel()` returns
  `-ENOENT`, with or without `IORING_ASYNC_CANCEL_ALL`; it searches only the
  io-wq of each task on `ctx->tctx_list`, under `uring_lock` and
  `ctx->tctx_lock`.
- `io_cancel_req_match()`: `user_data` is compared when
  `IORING_ASYNC_CANCEL_USERDATA` is set, or when neither
  `IORING_ASYNC_CANCEL_FD` nor `IORING_ASYNC_CANCEL_OP` is set; with
  `IORING_ASYNC_CANCEL_ANY` it is not compared at all.
- `io_cancel_req_match()` with `IORING_ASYNC_CANCEL_FD`: compares `req->file`
  with `cd->file` only; `REQ_F_FIXED_FILE` is used in `io_async_cancel()` to
  resolve `cd->file`, not in the match.
- Sequence mark: there is no REQ_F_CANCEL_SEQ flag; the mark is
  `cancel_seq_set` in `struct io_kiocb` plus `cancel_seq` in
  `struct io_wq_work`, both written by `io_cancel_match_sequence()` in
  `io_uring/cancel.h`.
- Sequence test: runs only with `IORING_ASYNC_CANCEL_ALL` or
  `IORING_ASYNC_CANCEL_ANY`; a keyed single cancel can match the same request
  on every call.
- `io_cancel_match_sequence()`: stamps the request as a side effect of the
  match, whether or not the cancel then succeeds.
- `io_poll_find()` in `io_uring/poll.c`: does not call
  `io_cancel_req_match()`; it compares `user_data` in one hash bucket and
  calls `io_cancel_match_sequence()` itself, only for
  `IORING_ASYNC_CANCEL_ALL`. `io_poll_file_find()` is the one that calls
  `io_cancel_req_match()`.
- Count returned with `IORING_ASYNC_CANCEL_ALL` or `IORING_ASYNC_CANCEL_ANY`:
  `nr` in `__io_async_cancel()` goes up once per `io_try_cancel()` call that
  returned anything but `-ENOENT`, and once per task on `ctx->tctx_list` whose
  io-wq had a match in the slow path; `io_cancel_remove()` with
  `IORING_ASYNC_CANCEL_ALL` cancels every match on its list in one call.
- `io_sync_cancel()`: entered with `uring_lock` held (from
  `io_uring_register()`); it runs the same `__io_async_cancel()` search and
  retries only on `-EALREADY`, never on `-ENOENT`.
- `io_sync_cancel()` retry: takes a new `cd.seq` from `ctx->cancel_seq` on
  every pass.
- `__io_sync_cancel()`: looks the fixed file up again on every pass, because
  `uring_lock` was dropped in between.
- `io_sync_cancel()` result from the wait loop: `-ENOENT` and positive counts
  are turned into 0.

**Inflight tracking**

- Tracked kinds, two in this tree:

  | Kind | Where tracked | Condition |
  |---|---|---|
  | io_uring file used as a normal file | `io_file_get_normal()` | `io_is_uring_fops()` true |
  | futex wait | `io_futex_wait_prep()`, `io_futexv_prep()` | a futex without `FLAGS_SHARED` |

- Linked timeouts and io-wq work in general are not tracked; `REQ_F_INFLIGHT`
  is set nowhere but in `io_req_track_inflight()`.
- `io_req_track_inflight()`: sets the flag and increments
  `inflight_tracked`; nothing else.
- Futex tracking: done at prep, not in `io_futex_wait()` or
  `io_futexv_wait()`; for `io_futexv_prep()` one private futex in the vector
  is enough.
- Fixed files: never tracked because the file tables reject io_uring files;
  see the `io_is_uring_fops()` tests in `io_uring/rsrc.c` and
  `io_uring/filetable.c`.
- File tracking point: `io_assign_file()`, or an issue handler's own call of
  `io_file_get_normal()`, for example `io_splice_get_file()`.
  `io_assign_file()` runs at inline issue in `io_issue_sqe()`, or in
  `io_wq_submit_work()` for a request that `io_queue_sqe_fallback()` queued
  to io-wq unissued, so such a request waits on the io-wq list untracked.
- `io_put_task()` on the owning task: only does `cached_refs++`; `inflight`
  does not move and `tctx->wait` is not woken.
- `io_put_task()` from another task: subtracts from `inflight` and wakes
  `tctx->wait` when `in_cancel` is set.
- `inflight` during cancel: drops for the task's own completions only at
  `io_uring_drop_tctx_refs()`; `tctx_task_work_run()` calls it when
  `in_cancel` is set and `current->io_uring` is that tctx.
- `io_match_task()` in `io_uring/timeout.c`: a second copy of the
  `REQ_F_INFLIGHT` link walk, used by `io_kill_timeouts()` with
  `ctx->timeout_lock` already held; `io_match_task_safe()` must not be
  called with that lock held.

**Task exit and exec**

- Mapping:

  | Path | Entry | `cancel_all` | Count tested for zero |
  |---|---|---|---|
  | exit, `do_exit()` | `io_uring_files_cancel()` | false | `inflight_tracked` |
  | exec, `begin_new_exec()` | `io_uring_task_cancel()` | true | `inflight` sum |

- Second break in `io_uring_cancel_generic()`: the loop also ends when the
  `inflight` sum reads zero, whatever `cancel_all` is.
- Sleep test: the value saved before cancelling is always the `inflight` sum;
  `schedule()` runs only if it equals `tctx_inflight(tctx, !cancel_all)`,
  which on exit is `inflight_tracked`.
- `io_uring_clean_tctx()`: runs after the loop on exit and on exec.
- With `cancel_all`: `in_cancel` is decremented and the tctx is freed with
  `io_uring_free_tctx()` in `io_uring/tctx.c`, not `__io_uring_free()`.
  `__io_uring_free()` is the task-free path and also frees
  `io_uring_restrict`.
- `io_uring_try_cancel_requests()` under `uring_lock`, in order:
  `io_cancel_defer_files()`, `io_poll_remove_all()`,
  `io_waitid_remove_all()`, `io_futex_remove_all()`,
  `io_uring_try_cancel_uring_cmd()`, `io_kill_timeouts()`.
- `io_uring_try_cancel_requests()` last step: `io_run_task_work()` when
  `tctx` is set; nothing when it is NULL. There is no per-ring fallback work
  in this tree; `fallback_work` is in `struct io_uring_task` and is run by
  `io_tctx_fallback_work()` in `io_uring/tw.c`.
- `io_uring_try_cancel_uring_cmd()`: does not test `REQ_F_INFLIGHT`. With
  `cancel_all` false it cancels every cancelable command of the task; with
  `cancel_all` true it does not compare `req->tctx` at all.
- io-wq step with a `tctx`: `io_cancel_task_cb()` does not compare the ring,
  so one call cancels the task's matching io-wq work on all its rings.
- Local task work step: runs only when `io_allowed_defer_tw_run()` is true,
  that is when `ctx->submitter_task` is `current`.
- SQPOLL thread: `io_sq_thread()` drains pending task work with `io_sq_tw()`
  first, then calls `io_uring_cancel_generic(true, sqd)` with `sqd->lock`
  held; the call passes the thread's own tctx, not `sqd`, as the match.
- SQPOLL thread after the call: its tctx is already freed (`cancel_all` is
  true), so `io_uring_files_cancel()` in its `do_exit()` does nothing.

**Ring teardown**

- `io_ring_ctx_wait_and_kill()`: under `uring_lock` kills `ctx->refs` and
  unregisters personalities, then queues `ctx->exit_work` on `iou_wq`. It
  frees no other registered resource and flushes no fallback work.
- `io_ring_exit_work()` first step: `io_terminate_zcrx()` under
  `uring_lock`, before the cancel loop.
- `io_req_caches_free()` in the loop: each cached request holds one
  `ctx->refs` reference (taken in `__io_alloc_req_refill()`), so
  `ctx->ref_comp` cannot complete until this call has emptied the cache.
- Timeout: after `IO_URING_EXIT_WAIT_MAX` the loop warns once and the wait
  interval goes from `HZ / 20` to `HZ * 60`.
- tctx-list walk: holds `uring_lock` and `ctx->tctx_lock`; both are dropped
  while waiting for the callback.
- `task_work_add()` failure in the walk: warns and retries with the next
  node; the walk does not remove the failed node.
- `io_tctx_exit_cb()`: skips the removal when `current->io_uring` is NULL or
  `in_cancel` is set, and still completes.
- Before the free: one lock and unlock of `ctx->completion_lock`, then
  `synchronize_rcu()` for `IORING_SETUP_DEFER_TASKRUN` only.
- `io_ring_ctx_free()` first call: `io_unregister_bpf_ops()`, then
  `io_sq_thread_finish()`.
- `io_ring_ctx_free()` steps that rely on an earlier step:

  | Step | Relies on |
  |---|---|
  | `io_unregister_zcrx()` | `io_terminate_zcrx()` in `io_ring_exit_work()` marked every entry; it warns and stops otherwise |
  | `io_rings_free()` and `kfree(ctx)` | `io_sq_thread_finish()` took the ring off `sqd->ctx_list`; `io_sq_thread()` dereferences `ctx->rings` of every ring on that list |
  | `mmdrop(ctx->mm_account)` | `io_sqe_buffers_unregister()` ran; `io_buffer_unmap()` unaccounts against `ctx->mm_account` |
  | `io_rings_free()` | `io_cqring_overflow_kill()` ran; it dereferences `ctx->rings` |
  | `free_uid(ctx->user)` | buffer unregister, `io_destroy_buffers()`, the `param_region` free and `io_rings_free()` ran; all unaccount against `ctx->user` |
  | `percpu_ref_exit(&ctx->refs)` | `ctx->ref_comp` completed |
  | `io_req_caches_free()` | request cache already empty; it runs after `percpu_ref_exit()` |
  | `xa_destroy(&ctx->hpage_acct)` | buffer unregister ran; `io_buffer_unaccount_pages()` uses it |

- `io_rings_free()` after `mmdrop()`: safe because `io_free_region()`
  unaccounts against the `struct user_struct` only.
- `WARN_ON_ONCE(ctx->nr_req_allocated)`: checks that the last
  `io_req_caches_free()` left no request allocated.

## ABI and tests

**UAPI layout checks and compat**

- `BUILD_BUG_SQE_ELEM()` lines in `io_uring_init()`: do not cover every member
  of `struct io_uring_sqe`; for example `optval`, `optlen`, `level`,
  `uring_cmd_flags` and `zcrx_ifq_idx` have no line.
- SQE member without a line: only the 64-byte size check and the offsets of
  the listed members after it constrain it; nothing forces a line for a new
  union member.
- `struct io_uring_cqe`, `struct io_uring_params`, `struct io_sqring_offsets`,
  `struct io_cqring_offsets`: `io_uring_init()` has no size or offset check
  for them; review their layout by hand.
- `struct io_uring_cqe`: the one `BUILD_BUG_ON()` under `io_uring/` that names
  it is in `io_process_timestamp_skb()` in `io_uring/cmd_net.c`; it requires
  the same size as `struct io_timespec`.
- Headers under `include/uapi/linux/io_uring/`: no layout check in
  `io_uring_init()`.
- `struct io_uring_rsrc_update` against `struct io_uring_rsrc_update2`: the
  check compares `sizeof` only (first not larger than second); field overlap
  is not checked.
- `IORING_OP_LAST`: no build-time check that it fits in a `u8`.
- Per-opcode command struct size: checked by `io_kiocb_cmd_sz_check()` in
  `include/linux/io_uring_types.h`, at each `io_kiocb_to_cmd()` use, not in
  `io_uring_init()`.
- `IORING_URING_CMD_MASK`: `io_uring_init()` requires its top 8 bits clear;
  kernel-internal `IORING_URING_CMD_CANCELABLE` and `IORING_URING_CMD_REISSUE`
  in `include/linux/io_uring/cmd.h` use that range.
- `tools/testing/selftests/`: has no io_uring directory.
- In-tree tests that use io_uring: in the directories of other subsystems;
  search `tools/testing` for `io_uring`; for example
  `tools/testing/selftests/net/io_uring_zerocopy_tx.c`,
  `tools/testing/selftests/drivers/net/hw/iou-zcrx.c` and
  `tools/testing/vsock/vsock_uring_test.c`.
- `io_uring/mock_file.c`, built with `CONFIG_IO_URING_MOCK_FILE` from
  `init/Kconfig`: test-only misc device `io_uring_mock`;
  `io_create_mock_file()` sets `TAINT_TEST`; nothing under `tools/` uses it.
- `tools/include/uapi/linux/io_uring.h`: not identical to
  `include/uapi/linux/io_uring.h`; for example it has no `IORING_OP_PIPE`.

**Compat tasks**

- `io_is_compat()`: tests `IO_RING_F_COMPAT` in `ctx->int_flags`; `struct
  io_ring_ctx` has no field named compat; `io_uring_create()` sets the bit.
- Message header: there is no io_compat_msg_copy_hdr() or
  io_sendmsg_copy_hdr(); `io_msg_copy_hdr()` in `io_uring/net.c` reads both
  layouts, called from `io_sendmsg_setup()` and `io_recvmsg_copy_hdr()`.
- Iovec for read/write: there is no io_compat_import() or
  io_iov_compat_buffer_select_prep(); see `io_import_vec()` and
  `io_iov_buffer_select_prep()` in `io_uring/rw.c`.
- `__import_iovec()` and `iovec_from_user()`: take the layout as an explicit
  `bool compat` argument; they do not call `in_compat_syscall()`.
- Negative compat iovec length: rejected with `-EINVAL` inside
  `copy_compat_iovec_from_user()` in `lib/iov_iter.c`; a handler that reads
  through `iovec_from_user()` or `__import_iovec()` needs no check of its own.
- Socket opcodes: prep also sets `MSG_CMSG_COMPAT` in the message flags on a
  compat ring; see `io_sendmsg_prep()` and `io_recvmsg_prep()`.
- `->uring_cmd()` handlers: `io_uring_cmd()` passes the ring state as
  `IO_URING_F_COMPAT` in `issue_flags`; `io_uring_cmd_getsockopt()` in
  `io_uring/cmd_net.c` hands it to `do_sock_getsockopt()`.
- Provided buffers in `io_uring/kbuf.c` and `io_get_ext_arg()` in
  `io_uring/io_uring.c`: no compat test; their structures have one layout.
- `io_epoll_ctl_prep()`: plain `copy_from_user()` of `struct epoll_event`, no
  compat branch.
- Register opcodes: none under `io_uring/` rejects a compat ring.
- **Potentially unsafe usage**: choosing the layout with `in_compat_syscall()`,
  directly or through a helper that hides it such as `import_iovec()`.
  - Unsafe: in a prep, issue or `->uring_cmd()` handler; `io_submit_sqes()` is
    also called from `__io_sq_thread()`, so the result describes the running
    thread, not the ring whose user wrote the structure.
  - Safe: pass `io_is_compat(req->ctx)` to `__import_iovec()` or
    `iovec_from_user()`, as `io_net_import_vec()` and `io_prep_reg_iovec()` do.
  - Safe: in code that runs only inside the caller's syscall and reads the
    caller's own argument, as `io_cqring_wait()` does for the signal mask and
    `io_register_iowq_aff()` for the CPU mask.

## Model gaps

### Other mistakes models make

- Models do not know `IOU_F_TWQ_IN_WAKE`. Wake handlers pass it, for example
  `io_futex_wake_fn()` and `io_waitid_wait()` to `__io_req_task_work_add()`
  and `io_poll_wake()` through `__io_poll_execute()`;
  `io_req_local_work_add()` then passes it to `io_eventfd_signal()` as
  `defer`, so the eventfd is signalled through `call_rcu_hurry()`, not inline.
- Models take `io_submit_sqes()` to always read `sq.tail`. With
  `IORING_SETUP_SQ_REWIND` it does not read it; it takes `ctx->sq_entries` as
  the number of entries available.
- Models take `ctx->flags` to be fixed after creation.
  `io_register_enable_rings()` clears `IORING_SETUP_R_DISABLED` with
  `smp_store_release()` after it sets `submitter_task` (on
  `IORING_SETUP_SINGLE_ISSUER` rings); `io_uring_enter()` pairs with
  `smp_load_acquire()`.
- Models take a registered-buffer send to import with the notification.
  That holds for zero-copy only; `IORING_OP_SEND` and `IORING_OP_RECV` accept
  `IORING_RECVSEND_FIXED_BUF`, and `io_send()` and `io_recv()` import with the
  request itself.
- Models take buffer cloning to need only the two ring locks.
  `io_register_clone_buffers()` returns `-EEXIST` if a different source ring
  has a `submitter_task` that is not `current`; `io_clone_buffers()` needs
  equal `user` and `mm_account`.
