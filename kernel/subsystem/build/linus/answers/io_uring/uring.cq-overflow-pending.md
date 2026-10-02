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
