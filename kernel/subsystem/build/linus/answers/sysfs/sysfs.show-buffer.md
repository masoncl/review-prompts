- Normal path zeroing: `sysfs_kf_seq_show()` does `memset(buf, 0, PAGE_SIZE)`
  before every call; the seq_file buffer itself comes from `kvmalloc()` in
  `seq_buf_alloc()`, with no `__GFP_ZERO`.
- Prealloc buffer: `kmalloc(PAGE_SIZE + 1)` in `kernfs_fop_open()`, never
  zeroed by kernfs or sysfs, reused by every read and write on that open
  file.
- `sysfs_emit()` and `sysfs_emit_at()`: WARN and return 0 when
  `offset_in_page(buf)` is non-zero, so they must be given the pointer show
  received, with any offset passed as `at`.
- Normal path, read at an offset that differs from `m->read_pos` (pread, or
  after lseek): `seq_read_iter()` calls `traverse()`, which runs show again
  from the start; nothing cached is used.
- Normal path, count of `PAGE_SIZE` or more: `sysfs_kf_seq_show()` does
  `WARN(1, "OOB write or bad count ...")` on every such call, then uses
  `PAGE_SIZE - 1`.
- Prealloc path, count of `PAGE_SIZE` or more: `sysfs_kf_read()` does a plain
  printk "fill_read_buffer: %pS returned bad count", no WARN, then uses
  `PAGE_SIZE - 1`.
