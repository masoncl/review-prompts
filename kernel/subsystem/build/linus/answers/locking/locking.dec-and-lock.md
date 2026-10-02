- `refcount_dec_and_lock()` returning false: the count was not always
  decremented. `refcount_dec_not_one()` in `lib/refcount.c` leaves a count of
  `REFCOUNT_SATURATED` or 0 unchanged and the helper returns false.
- False from the slow path: the count was 1 when sampled, the lock was taken,
  the decrement did not reach zero, and the lock was dropped again. The
  caller sees no difference from the fast path.
- `atomic_dec_and_lock()`: a function in `lib/dec_and_lock.c`, not a macro.
  Only `atomic_dec_and_lock_irqsave()` and `atomic_dec_and_raw_lock_irqsave()`
  are macros, in `include/linux/spinlock.h`.
- **Potentially unsafe usage**: a lookup under the lock passed to
  `refcount_dec_and_lock()` that takes a plain `refcount_inc()` on what it
  finds.
  - Unsafe: when the releaser unlocks before it unlinks the object; the
    lookup then finds a zero count, and `refcount_inc()` warns and saturates.
  - Safe: when the releaser unlinks before it unlocks, as `free_uid()` does
    through `free_user()` in `kernel/user.c` (with
    `refcount_dec_and_lock_irqsave()`), with `uid_hash_find()` as the lookup.
    The helper only promises that the 1 to 0 transition happens with the lock
    held; `kref_put_lock()` in `include/linux/kref.h` calls `release` with
    the lock held.
