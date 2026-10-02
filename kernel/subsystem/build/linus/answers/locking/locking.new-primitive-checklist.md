- Lockdep entry point: `_mutex_lock_killable(lock, subclass, nest_lock)`. Under
  `CONFIG_DEBUG_LOCK_ALLOC`, `mutex_lock_killable()`,
  `mutex_lock_killable_nested()` and `mutex_lock_killable_nest_lock()` are all
  macros over it in `include/linux/mutex.h`; no function is named
  `mutex_lock_killable_nested()`.
- Definitions: four. `mutex_lock_killable()` and `_mutex_lock_killable()` each
  exist in `kernel/locking/mutex.c` and again in
  `kernel/locking/rtmutex_api.c` under `CONFIG_PREEMPT_RT`.
- `__mutex_lock_common()` in `kernel/locking/rtmutex_api.c`: a separate static
  function with the same name as the one in `kernel/locking/mutex.c`, taking
  five arguments and calling `__rt_mutex_lock()`.
- `__cond_acquires(0, lock)` on both prototypes: checked by Clang context
  analysis under `CONFIG_WARN_CONTEXT_ANALYSIS`. `kernel/locking/Makefile`
  turns it on per object, for example `CONTEXT_ANALYSIS_mutex.o := y`.
- Guard class: three lines in `include/linux/mutex.h`, needed by
  `scoped_cond_guard()` and `ACQUIRE()` users and by context analysis:
  `DEFINE_LOCK_GUARD_1_COND(mutex, _kill, ...)`,
  `DECLARE_LOCK_GUARD_1_ATTRS(mutex_kill, ...)` and
  `class_mutex_kill_constructor()`.
- Rust: `mutex_lock_killable()` is a macro under `CONFIG_DEBUG_LOCK_ALLOC`, so
  a Rust caller would need a wrapper; `rust/helpers/mutex.c` wraps
  `mutex_lock()` and `mutex_trylock()` and has none for it.
- `lib/locking-selftest.c`: `ww_test_normal()` calls `mutex_lock_killable()`
  through `ww_mutex_base_lock_killable()`; with `CONFIG_PREEMPT_RT` that macro
  is `rt_mutex_lock_killable()` instead.
- `lib/test_context-analysis.c` (`CONFIG_CONTEXT_ANALYSIS_TEST`): compile-only;
  `test_mutex_trylock()` covers `mutex_lock_killable()`, and nothing there uses
  the `mutex_kill` guard.
- `kernel/locking/locktorture.c` and `kernel/locking/test-ww_mutex.c`: do not
  call `mutex_lock_killable()`; the mutex torture type takes `mutex_lock()`.
