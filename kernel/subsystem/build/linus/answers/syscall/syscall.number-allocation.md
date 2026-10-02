- From 424 on, a call has the same number in every table except alpha, where
  it is that number plus 110.
- Last three calls in every table: 470 `listns`, 471 `rseq_slice_yield`,
  472 `fchroot` (alpha 580, 581, 582). Next free: 473 (alpha 583).

| Table | Last common line | Userspace passes |
|---|---|---|
| `scripts/syscall.tbl` | 472 | the table number |
| `arch/alpha/kernel/syscalls/syscall.tbl` | 582 | the table number |
| `arch/mips/kernel/syscalls/syscall_n64.tbl` | 472 | `__NR_Linux` + 472 |
| `arch/x86/entry/syscalls/syscall_64.tbl` | 472 | 472; x32 adds `__X32_SYSCALL_BIT` |

- `__NR_Linux`: 4000 for o32, 5000 for n64, 6000 for n32, in
  `arch/mips/include/uapi/asm/unistd.h`.
- `arch/x86/entry/syscalls/syscall_64.tbl`: the file's last entry is 547 `x32`;
  a new call goes after the last `common` line, as the comment above 424 says.
