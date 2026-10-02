- s390: has no compat support in this tree; `compat_ptr()` has one
  definition, in `include/linux/compat.h`, a widening cast with no masking.
- Pointer argument without a compat entry, x86: the ia32 stub that
  `__IA32_SYS_STUBx()` emits for a native definition reads the 32-bit
  registers through `__SC_COMPAT_CAST()` in
  `arch/x86/include/asm/syscall_wrapper.h`, so the pointer arrives
  zero-extended.
- Pointer argument without a compat entry, arm64: the stub from the native
  `__SYSCALL_DEFINEx()` serves both tables and passes `regs->orig_x0` and
  `regs->regs[1]` to `regs->regs[5]` whole; `kernel_entry` in
  `arch/arm64/kernel/entry.S` zero-extends `x0` only.
- `long`-typed argument on x86: `__SC_COMPAT_CAST()` casts to `int` when
  `__TYPE_IS_L(t)`, so `long`, `off_t` and `ssize_t` are sign-extended in the
  ia32 stub of a native definition; every other type is zero-extended.
- Signed `long`-sized argument elsewhere: needs a compat entry declared with
  a 32-bit signed type where the stub passes registers whole;
  `compat_sys_lseek` in `fs/read_write.c` takes `compat_off_t` for this.
- Pointer to a struct that holds a pointer: needs no separate entry when the
  shared code picks the layout itself; `readv` and `writev` are wired to
  `sys_readv` and `sys_writev` for 32-bit callers and `import_iovec()` in
  `lib/iov_iter.c` tests `in_compat_syscall()`.
- 32-bit time type as the only difference: handled by native
  `SYSCALL_DEFINEx` entries such as `sys_clock_gettime32`, named in the native
  column of the 32-bit tables, not by a compat entry.
- Compat column of a table row: may name a native function, for example
  `sys_ni_syscall` for `vm86` in `arch/x86/entry/syscalls/syscall_32.tbl`; a
  name there does not prove a `COMPAT_SYSCALL_DEFINEx` exists.
