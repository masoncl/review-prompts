# Timer Subsystem Delta

## Timer Patterns [TIMER]

#### TIMER-001: Use-after-free on timer expiry

**Risk**: Use-after-free / system crash

**Details**: Structure containing a timer freed without canceling the timer first.
A pending timer holds an implicit reference to its containing structure. Before
freeing, the timer must be canceled with a _sync variant to guarantee the
callback is not running on another CPU.

#### TIMER-002: Deadlock from sync cancel in callback

**Risk**: Deadlock

**Details**: `del_timer_sync()` / `timer_delete_sync()` / `timer_shutdown_sync()`
spin-wait for the callback to finish. Calling any of these from within the
timer's own callback deadlocks. Use the non-sync `del_timer()` /
`timer_delete()` from the callback, or simply don't re-arm (return
HRTIMER_NORESTART for hrtimers).

#### TIMER-003: Lock ordering with sync cancel

**Risk**: Deadlock

**Details**: `del_timer_sync()` waits for the callback to complete. If the
caller holds a lock that the callback also acquires, the callback will block
on that lock while `del_timer_sync()` waits for the callback, causing deadlock.
The lock must be released before calling any sync cancel, or the callback must
not take that lock.

#### TIMER-004: Re-arm after shutdown

**Risk**: Silent timer loss / use-after-free

**Details**: `timer_shutdown()` / `timer_shutdown_sync()` permanently prevent
the timer from being re-armed. Any subsequent `mod_timer()` or `add_timer()`
silently does nothing. Code that expects to reuse a timer after shutdown will
have silent failures. These APIs are for teardown paths only.

#### TIMER-005: Non-sync cancel races

**Risk**: Use-after-free

**Details**: `del_timer()` / `timer_delete()` only dequeues the timer. The
callback may still be running on another CPU. Code that frees the containing
structure after a non-sync cancel has a use-after-free if the callback is
mid-execution. Always use a sync variant before freeing, or use
`timer_shutdown_sync()` in teardown paths.

#### TIMER-006: timer_pending() is not synchronization

**Risk**: Race condition

**Details**: `timer_pending()` returns whether the timer is enqueued, but
it can change immediately after the check. It must not be used as a
synchronization mechanism or as proof that the callback is not running.
A timer that is not pending may still have its callback executing.

#### TIMER-007: hrtimer callback context violations

**Risk**: System crash / undefined behavior

**Details**: hrtimer callbacks execute in hardirq context by default. They
must not sleep, acquire mutexes, allocate with GFP_KERNEL, or call any
function that might sleep. Use HRTIMER_MODE_SOFT to run the callback in
softirq context instead, which still prohibits sleeping but allows
operations that are safe in BH context.

#### TIMER-008: hrtimer cancel from callback

**Risk**: Deadlock

**Details**: `hrtimer_cancel()` waits for the callback to finish and cannot
be called from within the callback. To stop an hrtimer from its own callback,
return HRTIMER_NORESTART. To reschedule, use `hrtimer_forward()` or
`hrtimer_forward_now()` and return HRTIMER_RESTART.

## Timer Types

### timer_list (low-resolution timers)
- Resolution: jiffies (1-10ms depending on HZ)
- Callback context: **softirq** (timer softirq, `TIMER_SOFTIRQ`)
- Cannot sleep in callback — no mutexes, no GFP_KERNEL allocations
- Can use spinlocks, RCU read-side, atomic operations
- Setup: `timer_setup(timer, callback, flags)` or `DEFINE_TIMER(name, callback)`
- Arm: `mod_timer(timer, expires)` or `add_timer(timer)`
- Cancel: `timer_delete()` / `timer_delete_sync()` (preferred over del_timer variants)
- Teardown: `timer_shutdown_sync()` — cancels and prevents re-arming
- Re-arm from callback: call `mod_timer()` inside the callback
- `mod_timer()` works whether or not the timer is currently pending

### hrtimer (high-resolution timers)
- Resolution: nanoseconds (ktime_t)
- Callback context: **hardirq** by default, **softirq** with HRTIMER_MODE_SOFT
- Return value from callback: `HRTIMER_NORESTART` (stop) or `HRTIMER_RESTART` (continue)
- To reschedule from callback: call `hrtimer_forward_now()` then return HRTIMER_RESTART
- Setup: `hrtimer_init(timer, clock_id, mode)`
- Arm: `hrtimer_start(timer, time, mode)` or `hrtimer_start_range_ns()`
- Cancel: `hrtimer_cancel()` (sync) or `hrtimer_try_to_cancel()` (may fail if running)
- `hrtimer_try_to_cancel()` returns -1 if callback is currently executing
- Pinned mode (`HRTIMER_MODE_*_PINNED`): timer fires on the CPU where it was armed

### delayed_work (workqueue-based timers)
- Callback context: **process context** (can sleep)
- Setup: `INIT_DELAYED_WORK(dwork, callback)`
- Arm: `schedule_delayed_work(dwork, delay)` or `queue_delayed_work(wq, dwork, delay)`
- Cancel: `cancel_delayed_work_sync()` — waits for callback completion
- When sleeping is needed in the callback, use delayed_work instead of timer_list

## Execution Context Constraints

What each timer callback context prohibits:

| Operation | timer_list (softirq) | hrtimer default (hardirq) | hrtimer SOFT (softirq) | delayed_work (process) |
|-----------|---------------------|--------------------------|----------------------|----------------------|
| Sleep/schedule | prohibited | prohibited | prohibited | allowed |
| mutex_lock | prohibited | prohibited | prohibited | allowed |
| GFP_KERNEL alloc | prohibited | prohibited | prohibited | allowed |
| spin_lock | allowed | allowed | allowed | allowed |
| spin_lock_bh | prohibited (already in BH) | allowed | prohibited (already in BH) | allowed |
| spin_lock_irqsave | allowed | allowed | allowed | allowed |
| RCU read-side | allowed (implicit) | allowed (implicit) | allowed (implicit) | needs rcu_read_lock() |
| mod_timer | allowed | n/a | n/a | allowed |
| hrtimer_forward | n/a | allowed | allowed | n/a |
| del_timer_sync | depends (see TIMER-003) | prohibited if same timer | depends (see TIMER-003) | allowed |

## Unsafe Calling Contexts

### Functions that must NOT be called from timer callbacks (softirq/hardirq)
- `msleep()`, `ssleep()`, `usleep_range()` — sleep functions
- `wait_for_completion()`, `wait_event()` — blocking waits
- `mutex_lock()`, `down()` — sleeping locks
- `kmalloc(..., GFP_KERNEL)` — use `GFP_ATOMIC` instead
- `copy_to_user()`, `copy_from_user()` — user memory access may fault
- `request_firmware()` — may sleep waiting for userspace
- `vfree()` — may sleep, use `vfree_atomic()` from atomic context
- `synchronize_rcu()` — blocks waiting for grace period; use `call_rcu()` instead
- `flush_work()`, `flush_workqueue()` — may sleep waiting for work completion
- `dev_close()`, `unregister_netdev()` — networking teardown sleeps

### Functions that must NOT be called from hrtimer callbacks (hardirq) but are safe in softirq
- `spin_lock_bh()` — already below BH, will warn or deadlock
- `local_bh_disable()` — meaningless/dangerous in hardirq context
- `napi_schedule()` — safe but check context requirements of specific drivers
- Other softirq-only primitives

### Sync cancel restrictions
- `del_timer_sync()` / `timer_delete_sync()` / `timer_shutdown_sync()`: must NOT be called from the timer's own callback, and must NOT hold any lock that the callback also takes
- `hrtimer_cancel()`: must NOT be called from the hrtimer's own callback
- `cancel_delayed_work_sync()`: must NOT be called from the work's own callback

## Common Teardown Patterns

### Correct: sync cancel before free
```
timer_shutdown_sync(&obj->timer);
kfree(obj);
```

### Correct: flag + non-sync cancel from callback
```
/* In teardown path: */
obj->shutting_down = true;
timer_shutdown_sync(&obj->timer);
kfree(obj);

/* In callback: */
void callback(struct timer_list *t) {
    struct obj *o = from_timer(o, t, timer);
    if (o->shutting_down)
        return;  /* don't re-arm */
    /* ... do work ... */
    mod_timer(&o->timer, jiffies + interval);
}
```

### Wrong: non-sync cancel before free
```
del_timer(&obj->timer);  /* callback may still be running! */
kfree(obj);              /* use-after-free */
```

### Wrong: sync cancel while holding callback's lock
```
spin_lock(&obj->lock);
del_timer_sync(&obj->timer);  /* DEADLOCK if callback takes obj->lock */
spin_unlock(&obj->lock);
```

## Modern API Preference

The kernel is migrating to clearer timer API names:
- `del_timer()` → `timer_delete()` — preferred in new code
- `del_timer_sync()` → `timer_delete_sync()` — preferred in new code
- `timer_shutdown_sync()` — use for teardown paths (prevents re-arm)
- `setup_timer()` — removed, use `timer_setup()` instead

New code should use the modern names. Don't flag old names as regressions in
existing code, but do flag use of the removed `setup_timer()` or the ancient
`init_timer()`.

## Quick Checks
- Timer freed without sync cancel → use-after-free (TIMER-001)
- Sync cancel called from own callback → deadlock (TIMER-002, TIMER-008)
- Lock held across sync cancel that callback also takes → deadlock (TIMER-003)
- `timer_pending()` used for synchronization → race condition (TIMER-006)
- Sleep-capable function called from timer/hrtimer callback → crash (TIMER-007)
- `del_timer()` (non-sync) followed by free → use-after-free (TIMER-005)
- hrtimer callback not returning HRTIMER_RESTART or HRTIMER_NORESTART → undefined
- `mod_timer()` called after `timer_shutdown_sync()` → silent no-op (TIMER-004)
