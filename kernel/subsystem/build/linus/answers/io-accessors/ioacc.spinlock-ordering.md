- `ARCH_HAS_MMIOWB`: selected only by `arch/powerpc/Kconfig` (if `PPC64`) and
  `arch/riscv/Kconfig`.
- `CONFIG_MMIOWB`: the symbol `include/asm-generic/mmiowb.h` tests; in
  `kernel/Kconfig.locks` it is `ARCH_HAS_MMIOWB` and depends on `SMP`.
  Without it `mmiowb_set_pending()`, `mmiowb_spin_lock()` and
  `mmiowb_spin_unlock()` are empty macros.
- mips and sh: do not select `ARCH_HAS_MMIOWB`; they call `mmiowb()` on every
  unlock, in `queued_spin_release()` in `arch/mips/include/asm/spinlock.h`
  and `arch_spin_unlock()` in `arch/sh/include/asm/spinlock-llsc.h` (used
  under `CONFIG_CPU_SH4A`; `arch/sh/include/asm/spinlock-cas.h` has no such
  call).
- loongarch: `__io_aw()` in `arch/loongarch/include/asm/io.h` is `mmiowb()`,
  so the barrier follows every non-relaxed write, not the unlock.
- ia64: there is no such directory under `arch/` in this tree.
- `mmiowb()`: has no generic definition; only some arch headers define it, so
  code that builds on every architecture cannot call it.
- `Documentation/driver-api/io_ordering.rst`: contains no `mmiowb()`; its fix
  is `(void)readl(safe_register)` before the unlock, and it calls that the
  driver's responsibility.
- `Documentation/driver-api/device-io.rst`: says posted writes are not
  strictly ordered against a spinlock; this and `io_ordering.rst` contradict
  guarantee 2 in `Documentation/memory-barriers.txt`.
- The code implements guarantee 2 with a barrier, not a read: the accessors
  and unlock paths above issue it where `spin_lock()` reaches
  `do_raw_spin_lock()` (not `CONFIG_PREEMPT_RT`, where `spin_lock()` is
  `rt_spin_lock()`), so `writel()` under `spin_lock()` without a read-back
  is not a missing barrier.
- `rwlock_t`: not covered; the hooks are only in `do_raw_spin_lock()`,
  `do_raw_spin_trylock()` and `do_raw_spin_unlock()`; `do_raw_write_lock()`
  and `do_raw_write_unlock()` in `include/linux/rwlock.h` have none.
