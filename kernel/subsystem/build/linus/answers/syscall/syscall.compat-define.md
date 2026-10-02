- `__SC_DELOUSE`: used by the compat macro only; the native macro uses
  `__SC_CAST`.
- `__SC_DELOUSE` and `compat_ptr()`: one definition each, both in
  `include/linux/compat.h`; no architecture overrides either.
- `__SC_DELOUSE(t, v)`: casts through `unsigned long` to the declared type and
  masks nothing; the macro narrows or sign-extends an argument only if it is
  declared with a 32-bit type such as `compat_long_t` or `compat_off_t`.
- Pointer arguments of a compat definition: declared as `__user` pointers, to
  the compat struct where the layout differs, and used without
  `compat_ptr()`.
- `compat_uptr_t` by value as an argument type: only the `msgsnd`, `msgrcv`,
  `shmat` and `ipc` compat definitions under `ipc/` take it, and they call
  `compat_ptr()` on it.
- Generic `COMPAT_SYSCALL_DEFINEx`: emits `ALLOW_ERROR_INJECTION()`, the
  `__se_compat_sys##name` wrapper and `__SC_TEST`; it leaves out
  `SYSCALL_METADATA()` and `__PROTECT()`.
- x86, arm64 and riscv `COMPAT_SYSCALL_DEFINEx` in their
  `asm/syscall_wrapper.h`: also leave out `__SC_TEST`, which their native
  `__SYSCALL_DEFINEx` keeps.
- `arch_trace_is_compat_syscall()`: makes syscall tracing skip 32-bit calls
  only where `ARCH_TRACE_IGNORE_COMPAT_SYSCALLS` is defined, which x86 (only
  under `CONFIG_IA32_EMULATION`), arm64 and riscv do.
- x86 `in_compat_syscall()` in `arch/x86/include/asm/compat.h`: returns
  `in_32bit_syscall()`, which is `in_ia32_syscall() || in_x32_syscall()`.
- `in_compat_syscall()` on x86: true inside a native handler too when the
  call came by a 32-bit ABI; under `CONFIG_IA32_EMULATION`
  `syscall_32_enter()` in `arch/x86/entry/syscall_32.c` sets `TS_COMPAT` for
  every 32-bit call, and `in_x32_syscall()` tests `__X32_SYSCALL_BIT` in
  `orig_ax`.
- `CONFIG_X86_32`: `in_ia32_syscall()` and `in_32bit_syscall()` are constant
  true while `in_compat_syscall()` is false, since `CONFIG_COMPAT` is off.
- sparc: the second override; `in_compat_syscall()` in
  `arch/sparc/include/asm/compat.h` tests the trap type, while
  `is_compat_task()` there tests `TIF_32BIT`.
- **Unsafe usage**: `is_compat_task()` in shared code to pick the user-memory
  layout of the current call.
  - Unsafe: x86 defines no `is_compat_task()` when `CONFIG_COMPAT` is set, and
    on x86 and sparc the ABI belongs to the call, not the task.
  - Safe: `in_compat_syscall()`, as `import_iovec()` in `lib/iov_iter.c` does.
  - Safe: `is_compat_task()` for a property of the task's address space, as
    `arch_mmap_rnd()` in `mm/util.c` does; that code is built only under
    `CONFIG_ARCH_WANT_DEFAULT_TOPDOWN_MMAP_LAYOUT`, which x86 does not
    select.
