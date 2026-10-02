- Where stated: `Documentation/process/adding-syscalls.rst`, section "Do not
  call System Calls in the Kernel"; two comments in
  `include/linux/syscalls.h` (above the sys_ prototypes, above the `ksys_`
  block); one comment in `include/linux/compat.h` above the compat_sys_
  prototypes.
- `ksys_` helpers: the documentation does not restrict them to legacy or
  early-boot users; it names a helper as the way to share the work between
  the syscall, its compat variant and other kernel code.
- **Potentially unsafe usage**: calling a sys_ or compat_sys_ entry point
  that a definition macro emits from kernel code.
  - Unsafe: by the plain sys_ or compat_sys_ name with C arguments, from code
    that is built on an architecture selecting `ARCH_HAS_SYSCALL_WRAPPER`,
    which includes generic code outside `arch/`; the generic prototypes are
    compiled out and the entry takes a register frame.
  - Safe: from `arch/` code of an architecture that does not select
    `ARCH_HAS_SYSCALL_WRAPPER`, passing on the arguments userspace gave, as
    `parisc_madvise()` does with `sys_madvise()`; the prototypes under
    `#ifndef CONFIG_ARCH_HAS_SYSCALL_WRAPPER` and the exception for `arch/` in
    `Documentation/process/adding-syscalls.rst` define this.
  - Safe: from `arch/` code that calls the prefixed entry with a
    `struct pt_regs` of the user task, as `__emulate_vsyscall()` does with
    `__x64_sys_gettimeofday()`; `arch/x86/include/asm/syscall_wrapper.h`
    declares `__x64_sys_getcpu()`, `__x64_sys_gettimeofday()` and
    `__x64_sys_time()` for it.
- **Unsafe usage**: passing a kernel buffer to a `__user` parameter of a
  `ksys_` helper; `ksys_read()` reaches `vfs_read()`, which tests the buffer
  with `access_ok()` and returns `-EFAULT` when that fails.
  - Safe: `kernel_read()` in `fs/read_write.c`, which takes `void *` and
    builds a kvec iterator in `__kernel_read()`.
- do_mkdirat() and do_unlinkat(): not in this tree; `filename_mkdirat()` and
  `filename_unlinkat()` in `fs/namei.c` do that, declared in `fs/internal.h`
  only.
- `ksys_lseek()`: `static` in `fs/read_write.c`, not callable from elsewhere.
- ksys_dup(): not in this tree.
- `ksys_truncate()`: defined out of line in `fs/open.c`; the static inline
  helpers are in `include/linux/syscalls.h` after the comment "just wrappers
  to fs-internal functions".
- `init_mount()` and the other helpers in `include/linux/init_syscalls.h`:
  take kernel pointers and are `__init`, so only boot-time code can call them.
