- Newest calls in this tree that show the zero-flags form: the `fchroot` entry
  point in `fs/open.c` and the `listns` entry point in `kernel/nstree.c`; both
  open with `if (flags) return -EINVAL;`.
- `mseal` in `mm/mseal.c`: tests `flags` before anything else.
- `cachestat` in `mm/filemap.c`: tests `flags` only after the fd lookup, the
  `copy_from_user()` of the range, `is_file_hugepages()` and
  `can_do_cachestat()`, so `-EBADF`, `-EFAULT`, `-EOPNOTSUPP` or `-EPERM` can
  be returned for a call that also has an unknown flag.
- `openat2`: `build_open_flags()` in `fs/open.c` tests `how->flags` against
  `VALID_OPENAT2_FLAGS`, not `VALID_OPEN_FLAGS`; both are in
  `include/linux/fcntl.h`.
- `VALID_OPENAT2_FLAGS`: adds `OPENAT2_REGULAR`, which is bit 32, so a
  `how->flags` value that does not fit an `int` can pass.
- `build_open_flags()`: has no separate test that `how->flags` fits an `int`;
  it swaps `OPENAT2_REGULAR` for the internal `__O_REGULAR` before it assigns
  `op->open_flag`.
