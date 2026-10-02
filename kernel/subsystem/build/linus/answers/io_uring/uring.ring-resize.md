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
