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
