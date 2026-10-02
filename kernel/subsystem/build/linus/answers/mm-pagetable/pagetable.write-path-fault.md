- No prefault up front: `generic_perform_write()` in `mm/filemap.c` goes
  straight to `write_begin` and `copy_folio_from_iter_atomic()`.
- Fault-in: the only `fault_in_iov_iter_readable()` call is after
  `write_end` returned 0 with `copied == 0`, when the folio is unlocked
  again.
- -EFAULT: set by `generic_perform_write()` itself only when that call
  returns `bytes`, meaning nothing could be faulted in.
- `write_end` returned 0: `chunk` is halved if above `PAGE_SIZE`; with
  `copied` non-zero the pass is retried with `bytes = copied`. There is no
  cap to a single iovec segment.
- `iomap_write_iter()` in `fs/iomap/buffered-io.c` differs: it calls
  `fault_in_iov_iter_readable()` before `iomap_write_begin()` on every pass
  and has no fault-in after a failed copy.
