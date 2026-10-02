- Debug `do_raw_spin_lock()`: in `kernel/locking/spinlock_debug.c`; there is no
  spinlock_debug.c under `lib/`.
- `include/linux/spinlock_api_up.h`: used only when `CONFIG_SMP` and
  `CONFIG_DEBUG_SPINLOCK` are both off.
- UP with lockdep: `CONFIG_DEBUG_LOCK_ALLOC` and `CONFIG_PROVE_LOCKING` select
  `CONFIG_DEBUG_SPINLOCK`, so the call goes through `__raw_spin_lock()` in
  `include/linux/spinlock_api_smp.h` and does call `spin_acquire()`;
  `arch_spin_lock()` still comes from `include/linux/spinlock_up.h`.
- `CONFIG_GENERIC_LOCKBREAK` without `CONFIG_DEBUG_LOCK_ALLOC`: replaces the
  `__raw_spin_lock()` layer. The header version is compiled out and
  `BUILD_LOCK_OPS()` in `kernel/locking/spinlock.c` generates a loop of
  `preempt_disable()`, `do_raw_spin_trylock()`, `preempt_enable()`,
  `arch_spin_relax()`; it does not call `spin_acquire()` or `LOCK_CONTENDED()`.
- `CONFIG_GENERIC_LOCKBREAK` is live: several arch Kconfig files define it for
  `SMP && PREEMPTION`, for example `arch/powerpc/Kconfig` when
  `PPC_QUEUED_SPINLOCKS` is off.
- `CONFIG_INLINE_SPIN_LOCK`: cannot be set with `CONFIG_DEBUG_SPINLOCK` or
  `CONFIG_GENERIC_LOCKBREAK` (`kernel/Kconfig.locks`), so every lockdep kernel
  keeps the out-of-line `_raw_spin_lock()` in `kernel/locking/spinlock.c`.
