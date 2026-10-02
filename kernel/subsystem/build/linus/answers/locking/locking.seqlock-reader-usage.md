- Sleeping in a lockless section: allowed, the reader holds no lock and does
  not disable preemption; `__alloc_pages_slowpath()` in `mm/page_alloc.c`
  keeps a `read_mems_allowed_begin()` cookie across direct reclaim.
- Body shared with a locked pass (`read_seqbegin_or_lock()`,
  `scoped_seqlock_read()` with `ss_lock`): runs under a `spinlock_t` on the
  second pass, so it must not sleep.
- KCSAN: plain loads in the section are treated as atomic, up to
  `KCSAN_SEQLOCK_REGION_MAX` accesses; begin calls
  `kcsan_atomic_next(KCSAN_SEQLOCK_REGION_MAX)` and retry calls
  `kcsan_atomic_next(0)`, for `read_seqbegin()` as well.
- `ktime_get()` in `kernel/time/timekeeping.c` reads with plain loads.
- **Potentially unsafe usage**: leaving the section, or acting on what it
  read, without the retry check.
  - Unsafe: when the result needs two or more loads to come from the same
    write generation; a writer can change one between them.
  - Safe: when one load alone proves the result, as `hrtimer_active()` in
    `kernel/time/hrtimer.c` returns true on either flag; `base->seq` is
    there only to rule out a false negative.
  - Safe: when the object was validated under its own lock and pinned, as
    `d_lookup()` in `fs/dcache.c` leaves on a hit; `__d_lookup()` compares
    under `d_lock` and takes the reference.
- `get_fs_root()` and `get_fs_pwd()` in `include/linux/fs_struct.h`: locking
  readers with `read_seqlock_excl()`, not retry loops.
