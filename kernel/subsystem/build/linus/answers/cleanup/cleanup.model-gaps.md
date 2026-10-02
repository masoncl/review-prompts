- Models take `mutex` and `rwsem_read` to be `DEFINE_GUARD()` classes. Here
  the variants of `mutex`, `rwsem_read` and `rwsem_write` are added with
  `DEFINE_LOCK_GUARD_1_COND()`; see `include/linux/mutex.h` and
  `include/linux/rwsem.h`.
- Models take `scoped_seqlock_read()` to be a one-pass scope. Its body runs
  again when `read_seqretry()` returns non-zero after the lockless pass; see
  `__scoped_seqlock_next()` in `include/linux/seqlock.h`.
- Models take a `goto` label next to a cleanup scope as a breach of the
  header's rule. `__scoped_user_access_begin()` in `include/linux/uaccess.h`,
  behind `scoped_user_read_access()` and its siblings, does `goto elbl` before
  the `__cleanup()` variable is declared.
