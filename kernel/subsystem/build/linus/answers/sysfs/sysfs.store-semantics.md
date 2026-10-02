- Longest write passed in one call: `PAGE_SIZE` bytes, with the NUL at
  `buf[PAGE_SIZE]`.
- No table in `fs/sysfs/file.c` sets `atomic_write_len`, so
  `kernfs_fop_write_iter()` clamps a longer write to `PAGE_SIZE`; it does not
  return `-E2BIG`.
- A longer write: store sees only the first `PAGE_SIZE` bytes, and write(2)
  returns what store returns.
- Zero-length write: reaches `sysfs_kf_write()`, which returns 0 without
  calling store.
