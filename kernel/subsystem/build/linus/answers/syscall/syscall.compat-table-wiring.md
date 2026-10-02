- `scripts/syscalltbl.sh`: generates the x86 `syscalls_32.h`, `syscalls_64.h`
  and `syscalls_x32.h` too, run from `arch/x86/entry/syscalls/Makefile`; there
  is no script under `arch/x86/entry/syscalls/`.
- `__SYSCALL_WITH_COMPAT` in `arch/x86/entry/syscall_32.c`: picks the compat
  name under `CONFIG_IA32_EMULATION` and the native name otherwise; `__SYSCALL`
  then pastes `__ia32_` on whichever was picked.
- Compat column `-`: `scripts/syscalltbl.sh` treats it as empty; x86 rows use
  it to reach the sixth column, `noreturn`.
- `arch/arm64/tools/syscall_32.tbl`: every row has abi `common`.
- x32 rows of `arch/x86/entry/syscalls/syscall_64.tbl`: the entry point is in
  the fourth column, whether it is a compat name such as `compat_sys_execve`
  or a native one such as `sys_readv`; no row of that file names an entry in
  the compat column.
- `arch/x86/entry/syscall_64.c`: defines no `__SYSCALL_WITH_COMPAT`, so a
  compat column in `syscall_64.tbl` has nothing to expand it.
- `syscalls_x32.h`: built from the `common` and `x32` rows; `x32_sys_call()`
  pastes `__x64_`, so an x32 row naming `compat_sys_execve` calls
  __x64_compat_sys_execve.
- Rows in `syscall_64.tbl` numbered 329 and above, outside 512-547: all are
  `common`.
- `common` call entered from x32: runs the native x64 stub with
  `in_compat_syscall()` true, so shared code that tests it parses user memory
  in the 32-bit layout.
