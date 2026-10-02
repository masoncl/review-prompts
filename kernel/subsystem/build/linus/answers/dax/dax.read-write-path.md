- `IOCB_ATOMIC` in `iocb->ki_flags`: `dax_iomap_rw()` hits `WARN_ON_ONCE()` and
  returns `-EIO`; this is its first test, ahead of the zero-length return.
- Lock assertions: `lockdep_assert_held_write()` for a write and
  `lockdep_assert_held()` for a read, on `inode->i_rwsem`; there is no
  `WARN_ON_ONCE()` on `inode_is_locked()`, and without `CONFIG_LOCKDEP` nothing
  is tested.
- Read on a read-only superblock: `sb_rdonly()` true skips the read assertion;
  `erofs_file_read_iter()` in `fs/erofs/data.c` calls with no `i_rwsem` held.
- `IOCB_NOWAIT`: `dax_iomap_rw()` turns it into `IOMAP_NOWAIT` itself.
- Type test in `dax_iomap_iter()`: passes `IOMAP_MAPPED`, and any type whose
  `iomap->flags` has `IOMAP_F_SHARED`; everything else is `WARN_ON_ONCE()` and
  `-EIO`.
- `IOMAP_UNWRITTEN` without `IOMAP_F_SHARED`: rejected for a write.
- The type test is not limited to writes: a read of a type other than
  `IOMAP_HOLE`, `IOMAP_UNWRITTEN` or `IOMAP_MAPPED` reaches it too.
- `DAX_RECOVERY_WRITE`: no iocb or iomap flag selects it (there is no
  IOMAP_DAX_RECOVERY here); it is used only for the second
  `dax_direct_access()` call, made when the first returned `-EHWPOISON` and the
  iter is a write.
- Recovery copy: `dax_recovery_write()` replaces `dax_copy_from_iter()` only
  when that second call returned a positive count; a negative result goes
  through `dax_mem2blk_err()` like any other.
- Recovery write that copies nothing: the loop ends with `-EFAULT`, not `-EIO`.
  `dax_recovery_write()` returns 0 when the driver has no `recovery_write` op;
  `pmem_recovery_write()` returns 0 for a poisoned range that is not
  page-aligned.
- Width of the poison test: the request passed to `dax_direct_access()` is the
  rest of the I/O inside this iomap, `ALIGN(length + offset, PAGE_SIZE)`, and
  `__pmem_direct_access()` in `drivers/nvdimm/pmem.c` returns `-EHWPOISON` under
  `DAX_ACCESS` when any bad block lies in it, so a read fails with `-EIO` even
  when the page at `pos` is good.
