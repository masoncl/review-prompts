- **Potentially unsafe usage**: plain `refcount_inc()` or `atomic_inc()` on an
  object found under `rcu_read_lock()`.
  - Unsafe: when any put can take the count to zero while the object is still
    reachable, as in listing B of `Documentation/RCU/rcuref.rst`.
  - Safe: when the structure's own reference is dropped only from the RCU
    callback that follows the unlink (listing C). `find_get_pid()` in
    `kernel/pid.c` uses `get_pid()`; `free_pid()` does `idr_remove()` and then
    `call_rcu()` with `delayed_put_pid()`, which does the `put_pid()`.
- `get_file_rcu()` in `fs/file.c`: takes the reference with `file_ref_get()` on
  `f_ref`, then reloads the pointer and compares.
- `__fget_files_rcu()` in `fs/file.c`: the fd-table lookup; it does not call
  `get_file_rcu()`.
- `rcuref_t`: a typedef of an anonymous struct in `include/linux/types.h`;
  there is no struct rcuref tag.
- `rcuref_get()`: safe only if the object is freed after a grace period and
  the put cannot be overtaken by one; see "Deconstruction race" in
  `lib/rcuref.c`.
- `rcuref_put()`: disables preemption itself, callable from any context.
- `rcuref_put_rcusafe()`: does not disable preemption; the caller must be
  under `rcu_read_lock()` or non-preemptible, which `__rcuref_put()` checks
  with `RCU_LOCKDEP_WARN()`.
