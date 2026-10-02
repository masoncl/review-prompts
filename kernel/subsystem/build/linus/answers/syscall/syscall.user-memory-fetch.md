- `copy_clone_args_from_user()` in `kernel/fork.c`: copies into a local
  `struct clone_args`, tests that copy, and only then fills
  `struct kernel_clone_args`; the unknown-flag test comes later, in
  `clone3_args_valid()`.
- `sched_copy_attr()` in `kernel/sched/syscalls.c`: never writes `attr->size`
  after the copy; it differs from `perf_copy_attr()` in that.
- **Unsafe usage**: reading a size field with `get_user()`, checking it,
  copying the whole structure, then using the size field of the copy;
  `copy_struct_from_user()` copies from offset 0 of `src`, so it fetches the
  field a second time and the copied value was never checked.
  - Safe: store the checked value over the copied field, as `perf_copy_attr()`
    in `kernel/events/core.c` and `user_reg_get()` in
    `kernel/trace/trace_events_user.c` do.
  - Safe: never read the copied field and keep using the checked local, as
    `sched_copy_attr()` does for its `SCHED_ATTR_SIZE_VER1` test.
