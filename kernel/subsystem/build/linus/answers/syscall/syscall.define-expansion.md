- `SYSCALL_METADATA()`: emitted by `SYSCALL_DEFINEx()`, before and outside
  `__SYSCALL_DEFINEx()`.
- `sys##name`: declared with
  `__attribute__((alias(__stringify(__se_sys##name))))`; there is no SyS_
  symbol here, and `__SYSCALL_DEFINEx()` does not use `SYSCALL_ALIAS()` from
  `include/linux/linkage.h`.
- `sys##name` and `__se_sys##name`: one function under two symbols that differ
  only in declared parameter types, so the body in `__do_sys##name` sits
  behind one wrapper, not two.
- `ALLOW_ERROR_INJECTION(sys##name, ERRNO)`: always part of the expansion;
  expands to nothing without `CONFIG_FUNCTION_ERROR_INJECTION`.
- `__PROTECT()`: expands to `asmlinkage_protect()`, which is
  `do { } while (0)` from `include/linux/linkage.h` unless the architecture
  defines it; only `arch/m68k/include/asm/linkage.h` does.
