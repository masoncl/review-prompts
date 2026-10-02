- `kernel/locking/rtmutex.c`: never an object of its own; `kernel/locking/Makefile`
  has no entry for it, and every copy comes from `#include "rtmutex.c"`.
- Includers: four, found by searching for `#include "rtmutex.c"`.

| Includer | Built when | Defines before the include |
|---|---|---|
| `kernel/locking/rtmutex_api.c` | `CONFIG_RT_MUTEXES` | `RT_MUTEX_BUILD_MUTEX` |
| `kernel/locking/ww_rt_mutex.c` | `CONFIG_PREEMPT_RT` | `RT_MUTEX_BUILD_MUTEX`, `WW_RT` |
| `kernel/locking/spinlock_rt.c` | `CONFIG_PREEMPT_RT` | `RT_MUTEX_BUILD_SPINLOCKS` |
| `kernel/locking/rwsem.c` | `CONFIG_PREEMPT_RT` branch only | `RT_MUTEX_BUILD_MUTEX` |

- Copies per kernel: none without `CONFIG_RT_MUTEXES`, one on a non-RT kernel
  with it, four with `CONFIG_PREEMPT_RT`.
- `RT_MUTEX_BUILD_SPINLOCKS`: the macro name ends in S; `rt_spin_lock()` is in
  `kernel/locking/spinlock_rt.c`, not in `kernel/locking/rtmutex_api.c`.
- `RT_MUTEX_BUILD_SPINLOCKS` also changes shared code: only in that build does
  `rt_mutex_steal()` let a waiter of equal priority steal the lock, and only
  when the waiter is not RT or deadline priority.
- `kernel/locking/ww_mutex.h`: built once per kernel. There are two include
  sites and they exclude each other: `kernel/locking/mutex.c` inside
  `#ifndef CONFIG_PREEMPT_RT`, and `kernel/locking/rtmutex.c` under `WW_RT`,
  reached only through `kernel/locking/ww_rt_mutex.c`.
- Without `WW_RT`, the ww hooks at the top of `kernel/locking/rtmutex.c`
  return 0 or are empty; they do not call `BUG()`.
- `WW_RT` in `kernel/locking/rtmutex.c`: search for `build_ww_mutex()`. The
  part that is easy to miss is `task_blocks_on_rt_mutex()`: a waiter with a
  `ww_ctx` skips the early `-EDEADLK` return for `owner == task`.
- `WW_RT` in `__waiter_less()`: equal-priority waiters are ordered by ww stamp,
  and a waiter with a `ww_ctx` sorts before one without.
- `__ww_waiter_add()` under `WW_RT`: empty. `task_blocks_on_rt_mutex()` has
  already enqueued the waiter, and dequeues it if `__ww_mutex_add_waiter()`
  fails.
- `__ww_ctx_less()` under `WW_RT`: compares RT and deadline priority before
  the stamp; the non-RT build compares the stamp only.
