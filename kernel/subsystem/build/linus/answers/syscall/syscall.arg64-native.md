- `SC_ARG64(name)` and `SC_VAL64(type, name)`: defined unconditionally in
  `include/linux/syscalls.h`; `SC_ARG64` always expands to two `u32` type/name
  pairs, on 64-bit kernels too.
- `compat_arg_u64_dual(name)`: always two `u32` type/name pairs; defined in
  `include/asm-generic/compat.h` inside `#ifndef compat_arg_u64`, and no
  architecture supplies its own.
- `compat_arg_u64(name)`: the same two halves written as parameter
  declarations, for prototypes; `compat_arg_u64_glue(name)` rebuilds the
  value.
- Half order: `SC_ARG64` tests `__LITTLE_ENDIAN`; `compat_arg_u64_dual()` tests
  `CONFIG_CPU_BIG_ENDIAN`.
- `loff_t` declared in `SYSCALL_DEFINEx` on a 32-bit kernel: arrives whole
  only where the C calling convention is kept; `__SC_LONG` then declares the
  parameter as `long long`.
- x86-32 and PPC32 pt_regs stubs: hand one register to each declared
  argument (`SC_IA32_REGS_TO_ARGS`, `SC_POWERPC_REGS_TO_ARGS`), so a 64-bit
  argument must be declared as two halves, as in `arch/x86/kernel/sys_ia32.c`
  and `arch/powerpc/kernel/sys_ppc32.c`.
- riscv32: `__SYSCALL_SE_DEFINEx` in
  `arch/riscv/include/asm/syscall_wrapper.h` aliases the wrapper to a
  seven-`ulong` function so that wider arguments still follow the C
  convention.
- `CONFIG_ARCH_SPLIT_ARG64`: selected by `X86_32`, PPC32 and 32-bit parisc; its
  only users are the `fanotify_mark` definition in
  `fs/notify/fanotify/fanotify_user.c` and its prototype in
  `include/linux/syscalls.h`.
- `SYSCALL32_DEFINE6(fanotify_mark, ...)`: emits `compat_sys_fanotify_mark`
  under `CONFIG_COMPAT` and the split `sys_fanotify_mark` otherwise; the
  unsplit `SYSCALL_DEFINE5` is compiled only without
  `CONFIG_ARCH_SPLIT_ARG64`.
- Generic users of `compat_arg_u64_dual()`: each is compiled only if the
  architecture defines the matching macro, for example
  `__ARCH_WANT_COMPAT_PREAD64`; riscv defines all eight, powerpc only
  `__ARCH_WANT_COMPAT_FALLOCATE`, arm64 none.
- **Unsafe usage**: `SC_ARG64()` or `compat_arg_u64_dual()` at parameter 2 or
  4 for an ABI that aligns a 64-bit argument to a register pair.
  - Unsafe: the macros add no padding, so both halves are read one register
    before the ones userspace filled.
  - Safe: at parameter 1, 3 or 5, as `compat_sys_fallocate` in `fs/open.c`,
    the one generic entry powerpc opts into; the rule is stated in
    `Documentation/process/adding-syscalls.rst`.
  - Safe: an architecture entry with an explicit pad argument before the
    halves, as `ppc_pread64` in `arch/powerpc/kernel/sys_ppc32.c` and
    `compat_sys_aarch32_pread64` in `arch/arm64/kernel/sys32.c`.
