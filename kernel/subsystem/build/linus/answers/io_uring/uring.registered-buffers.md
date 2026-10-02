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
