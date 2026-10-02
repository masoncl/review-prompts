- `copy_struct_from_user()` first test: `WARN_ON_ONCE(ksize >
  __builtin_object_size(dst, 1))` returns `-E2BIG` before any user access.
- `usize` below the first published size, including 0, when the caller makes
  no minimum check: the helper zero-fills `dst` from `usize` on, copies
  `usize` bytes and returns 0, so the caller sees a valid structure of
  defaults.
- `build_open_how()` in `fs/open.c`: reads no user memory; it builds a
  `struct open_how` from `int` flags and a mode, as `do_sys_open()` does for
  `open` and `openat`. The `openat2` copy and both size checks are in the
  `openat2` entry point.
- Field appended later and selected by a flag, where 0 is a valid value of
  the field: the caller also tests that `usize` covers the field, because
  after the copy a zero that userspace wrote looks the same as a zero the
  helper filled in.
  - `copy_clone_args_from_user()` in `kernel/fork.c`: `CLONE_INTO_CGROUP` with
    `usize < CLONE_ARGS_SIZE_VER2` returns `-EINVAL`.
  - `sched_copy_attr()` in `kernel/sched/syscalls.c`: `SCHED_FLAG_UTIL_CLAMP`
    with `size < SCHED_ATTR_SIZE_VER1` returns `-EINVAL`.
