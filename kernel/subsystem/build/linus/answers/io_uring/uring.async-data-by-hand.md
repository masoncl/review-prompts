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
