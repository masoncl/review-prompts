- x32 entry of a compat definition: __x64_compat_sys_foo;
  `__X32_COMPAT_SYS_STUBx()` passes `x64` to `__SYS_STUBx()`.
- __x32_ prefix: emitted by no code; it appears only in
  `Documentation/process/adding-syscalls.rst` and its translations.
- x86 `.tbl` files: hold unprefixed names (sys_foo, compat_sys_foo);
  `__SYSCALL()` in `arch/x86/entry/syscall_64.c` and
  `arch/x86/entry/syscall_32.c` pastes `__x64_` or `__ia32_` in front.
- s390: only the `__s390x_` prefix exists;
  `arch/s390/include/asm/syscall_wrapper.h` defines no compat macros and
  `__S390_SYS_STUBx()` is empty.
- powerpc: the entry symbol is sys_foo with no prefix, taking
  `const struct pt_regs *`; see `__SYSCALL_DEFINEx()` in
  `arch/powerpc/include/asm/syscall_wrapper.h`.
- powerpc selects `ARCH_HAS_SYSCALL_WRAPPER` only `if !SPU_BASE && !COMPAT`;
  otherwise it uses the generic macros and sys_foo takes the C arguments.
- x86, arm64, riscv, s390: no symbol named sys_foo is emitted; `__se_sys##name`
  and `__do_sys##name` are `static`.
- Generic prototypes: compiled out under the wrapper; the sys_ block in
  `include/linux/syscalls.h` and the compat_sys_ block in
  `include/linux/compat.h` are both inside
  `#ifndef CONFIG_ARCH_HAS_SYSCALL_WRAPPER`.
- Argument type: `const struct pt_regs *` on x86, arm64, riscv and powerpc;
  `struct pt_regs *` without `const` on s390.
- `COND_SYSCALL()`: there is no SYS_NI macro here; the x86, arm64, riscv and
  powerpc overrides emit a `__weak` function under the entry name that
  returns `sys_ni_syscall()`; s390 applies `cond_syscall()` to the prefixed
  name.
