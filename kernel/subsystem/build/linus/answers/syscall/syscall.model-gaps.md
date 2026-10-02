- Models name secure_computing() as the seccomp entry hook. It is defined
  nowhere here; `seccomp_permit_syscall()` in `include/linux/seccomp.h` is the
  hook.
- Models know the generic `syscall_trace_enter()` from other trees. In
  `include/linux/entry-common.h` it takes `(regs, work, syscall)`, in that
  order.
- Models know `futex_cmd_has_timeout()` as the only argument gate in the
  `futex` entry point. `FUTEX_ROBUST_UNLOCK` in the `op` word gives `uaddr2` a
  meaning for `FUTEX_WAKE`, `FUTEX_WAKE_BITSET` and `FUTEX_UNLOCK_PI`;
  `do_futex()` returns `-ENOSYS` for the flag with any other command.
- Models know the helpers behind `mkdirat` and `unlinkat` under other names.
  `filename_mkdirat()` and `filename_unlinkat()` in `fs/namei.c` take a
  `struct filename *` and leave dropping it to the caller.
- Models take `ksys_ftruncate()` to take two arguments. It takes a third
  `flags` argument, `FTRUNCATE_LFS` in `include/linux/syscalls.h`.
- Models take `scripts/syscall.tbl` to have a newstat tag. The tag beside `64`
  on numbers 79 and 80 is `stat64`, on `fstatat64` and `fstat64`.
