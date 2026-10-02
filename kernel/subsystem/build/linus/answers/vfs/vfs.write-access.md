- `mnt_want_write()` (`fs/namespace.c`): `sb_start_write()`, then
  `mnt_get_write_access()`; on failure it has already called `sb_end_write()`,
  so the caller calls `mnt_drop_write()` only after success.
- `guard(super_write)(sb)` and `scoped_guard(super_write, sb)`: an
  `sb_start_write()` and `sb_end_write()` pair, from `DEFINE_GUARD()` in
  `include/linux/fs/super.h`; `do_ftruncate()` in `fs/open.c` uses it.
- `mnt_want_write_file()`: skips the writer count only if the file has
  `FMODE_WRITER`, and then still fails with `-EROFS` if `__mnt_is_readonly()`.
- `FMODE_WRITER`: `do_dentry_open()` sets it for a file opened for write
  unless `special_file()` is true; a special file opened for write holds no
  mount write access.
- Freeze levels: `freeze_super()` blocks `SB_FREEZE_WRITE` first, then
  `SB_FREEZE_PAGEFAULT`, then `SB_FREEZE_FS`.
- A task inside `sb_start_pagefault()` or `sb_start_intwrite()` must not then
  call `sb_start_write()`; it would block on the first level while
  `freeze_super()` waits for it on a later one.
- There is no do_unlinkat() here; `filename_unlinkat()` in `fs/namei.c` shows
  `mnt_want_write()` taken before the directory lock.
