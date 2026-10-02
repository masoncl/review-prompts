- `fuse_direct_io()` before a read or a write on a `FOPEN_DIRECT_IO` file:
  calls `filemap_write_and_wait_range()` on the range and returns its error
  before any request is sent.
- `fuse_direct_io()` before a `FOPEN_DIRECT_IO` write: calls
  `invalidate_inode_pages2_range()` and returns its error.
- `fc->direct_io_allow_mmap`: tested by neither step above, nor by
  `fuse_dio_wr_exclusive_lock()`; within `fs/fuse` it is read only in
  `fuse_file_mmap()`.
- `fuse_sync_writes()`: runs for reads and writes alike, when the call is not
  `FUSE_DIO_CUSE` and `filemap_range_has_writeback()` is true.
- Invalidation after a write: done by `fuse_direct_write_iter()`, not by
  `fuse_direct_io()`; only when `res > 0 && mapping->nrpages`; the result is
  ignored.
- Async write that is not blocking, with `res > 0` and `mapping->nrpages`:
  `fuse_aio_complete()` queues `fuse_aio_invalidate_worker()` on
  `s_dio_done_wq`, which invalidates and then calls `ki_complete`.
- `cuse_write_iter()` and `fuse_dax_direct_write()` call `fuse_direct_io()`
  themselves and do no invalidation after the write.
- `fuse_dio_lock()` returns holding `inode_lock_shared()` only when all of
  these hold:
  - `ff->open_flags` has `FOPEN_PARALLEL_DIRECT_WRITES`
  - `IOCB_APPEND` is clear
  - `FUSE_I_CACHE_IO_MODE` is clear in `fi->state`
  - `fuse_io_past_eof()` is false, both before and after taking the lock
  - `fuse_inode_uncached_io_start(fi, NULL)` returns 0 under the shared lock
- `O_DIRECT` without `FOPEN_DIRECT_IO`, on a file that is neither DAX nor
  passthrough: the write goes through `fuse_cache_write_iter()` under
  `inode_lock()`, never the shared lock; `fuse_file_io_open()` clears
  `FOPEN_PARALLEL_DIRECT_WRITES` for such a file.
- Async kiocb with `fc->async_dio`, write within EOF: `fuse_direct_IO()`
  returns `-EIOCBQUEUED` and `fuse_dio_unlock()` runs without waiting for the
  replies, so the inode lock and the uncached-io count cover submission only.
