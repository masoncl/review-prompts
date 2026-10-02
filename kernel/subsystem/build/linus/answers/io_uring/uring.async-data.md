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
