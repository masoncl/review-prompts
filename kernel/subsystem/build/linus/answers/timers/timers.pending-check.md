- True result: no caller lock keeps it true; `expire_timers()` detaches the
  timer under `base->lock` alone, at any moment.
- False result: stays false only while every arming path, the callback's own
  re-arm included, runs under a lock the caller holds.
- **Potentially unsafe usage**: deciding from `timer_pending()` what the timer
  core will do next, such as whether a reference owned by the queued timer must
  be dropped or taken.
  - Unsafe: when expiry or another CPU can change the queue state between the
    test and the action, the action does not test again under `base->lock`,
    and no lock held across the test is also taken by the callback and by
    every arming path; the test and the action then disagree.
  - Safe: act on a 1 from `timer_delete()` or a 0 from `mod_timer()`, each
    decided under `base->lock`, on a timer that is never shut down, as
    `sk_stop_timer()` and `sk_reset_timer()` in `net/core/sock.c` do.
  - Safe: as a shortcut in front of a call that tests again under `base->lock`,
    as `__timer_delete()` and `__mod_timer()` do themselves.
  - Safe: when the test runs under a lock that the callback and every arming
    path also take, as `__vector_schedule_cleanup()` in
    `arch/x86/kernel/apic/vector.c` does under `vector_lock`;
    `expire_timers()` detaches the timer before the callback, so a callback
    that makes a true result stale still takes the lock after the caller.
