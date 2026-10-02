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
