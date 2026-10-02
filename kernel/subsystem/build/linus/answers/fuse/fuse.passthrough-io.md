- `FOPEN_PASSTHROUGH` with `FOPEN_DIRECT_IO`: allowed by
  `FOPEN_PASSTHROUGH_MASK` in `fs/fuse/iomode.c`; the flag is not cleared.
- With both flags, `fuse_file_read_iter()`, `fuse_file_write_iter()`,
  `fuse_splice_read()` and `fuse_splice_write()` skip the backing file;
  `fuse_file_mmap()` tests `fuse_file_passthrough()` before
  `FOPEN_DIRECT_IO` and still maps the backing file.
- DAX inode: `fuse_file_io_open()` returns 0 before it looks at
  `FOPEN_PASSTHROUGH`, so `ff->passthrough` stays NULL and nothing is passed
  through.
- `backing_file_open()`: its first argument is the FUSE `struct file *`, not
  a path; `fuse_passthrough_open()` passes `file`.
- Credential switch: the helpers in `fs/backing-file.c` use
  `scoped_with_creds(ctx->cred)`; they contain no direct `override_creds()`
  call.
- `file_remove_privs(iocb->ki_filp)`: `backing_file_write_iter()` and
  `backing_file_splice_write()` call it on the FUSE file before the switch,
  so it runs with the credentials of the task doing the write.
- Attributes: nothing is copied from the backing inode.
- After a write, `fuse_passthrough_end_write()` calls
  `fuse_write_update_attr()`: `i_size` is raised to `iocb->ki_pos` when the
  write went past it, and `FUSE_STATX_MODSIZE` is invalidated.
- After a read, splice read or mmap, `fuse_file_accessed()` calls
  `fuse_invalidate_atime()`: it invalidates `STATX_ATIME` unless the inode is
  `IS_RDONLY()`; it does not call `touch_atime()`.
- Invalidated attributes are refetched from the server, so the FUSE inode
  shows the size and times that the server reports.
- Async write that returns `-EIOCBQUEUED`: `end_write` runs later from
  `backing_aio_complete_work()` on the `s_dio_done_wq` of the FUSE
  superblock, outside the `inode_lock()` that
  `fuse_passthrough_write_iter()` took.
- `fuse_passthrough_mmap()`: its ctx has no `end_write`, and
  `backing_file_mmap()` replaces `vma->vm_file` with the backing file, so
  stores through a shared mapping neither update nor invalidate the FUSE
  inode's cached size or times.
