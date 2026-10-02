- `btrfs_release_path` in `fs/btrfs/ctree.h`: a `DEFINE_FREE()` whose type is
  `struct btrfs_path`, not a pointer; used through
  `BTRFS_PATH_AUTO_RELEASE()`.
- `_T` for a struct type: a copy of the whole struct; `btrfs_release_path(&_T)`
  is given the address of the copy, not of the variable.
- `include/linux/file.h`: the `int` and `struct fd` cases are `DEFINE_CLASS()`
  (`get_unused_fd`, `fd`), not `DEFINE_FREE()`; the only `DEFINE_FREE()` there
  is `fput`.
- `__free_path_put` in `include/linux/path.h`: written by hand as
  `#define __free_path_put path_put`, so `path_put()` gets the address of the
  variable, with no copy and no test.
- `struct path` under `__free(path_put)`: must be initialised, as in
  `struct path path __free(path_put) = {};`.
