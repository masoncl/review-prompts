| Job | File | Easy to miss |
|---|---|---|
| Compat definition macros | `include/linux/compat.h` | `COMPAT_SYSCALL_DEFINEx()` is not in `include/linux/syscalls.h` |
| Entry point that is compat only when `CONFIG_COMPAT` | `include/linux/syscalls.h` | `SYSCALL32_DEFINE0()` to `SYSCALL32_DEFINE6()`; for example `fanotify_mark` in `fs/notify/fanotify/fanotify_user.c` |
| Table shared by several architectures | `scripts/syscall.tbl` | default `syscalltbl` in `scripts/Makefile.asm-headers`; used by each arch that has `arch/<arch>/kernel/Makefile.syscalls`, arm64 through the link `arch/arm64/tools/syscall_64.tbl` |
| ABI tags an arch selects from the shared table | `arch/<arch>/kernel/Makefile.syscalls` | sets only `syscall_abis_32`, `syscall_abis_64`, `syscalltbl`; holds no rules; absent on the arches that run the scripts from their own table `Makefile` |
| Older generic list | `include/uapi/asm-generic/unistd.h` | no `#include` of it outside `tools/`; a call added only here reaches no kernel table |
| Documentation | `Documentation/process/adding-syscalls.rst` | its first generic section still says to edit `include/uapi/asm-generic/unistd.h`; the "Since 6.11" section names `scripts/syscall.tbl` instead |
| Tables of one architecture | `arch/<arch>/kernel/syscalls/`, `arch/x86/entry/syscalls/`, `arch/arm/tools/`, `arch/arm64/tools/` | all but arm64 have a `Makefile` beside the table that runs the scripts, run from `archheaders` in `arch/<arch>/Makefile` (arm: table and count from `archprepare`); `arch/arm64/tools/Makefile` has no rule for the tables, `scripts/Makefile.asm-headers` builds them |
| arm64 tables | `arch/arm64/tools/syscall_32.tbl`, `arch/arm64/tools/syscall_64.tbl` | `syscall_64.tbl` is a symbolic link to `scripts/syscall.tbl`, so searches skip it; compat needs its own row in `syscall_32.tbl` |
| Table to headers | `scripts/syscallhdr.sh`, `scripts/syscalltbl.sh` | run by every per-arch table `Makefile`, s390 included, and by `scripts/Makefile.asm-headers` |
| Table to count of calls, arm and mips | `arch/arm/tools/syscallnr.sh`, `arch/mips/kernel/syscalls/syscallnr.sh` | `scripts/syscallnr.sh` exists but no Makefile names it |
| Size-supplied struct copy | `include/linux/uaccess.h` | besides `copy_struct_from_user()`: `copy_struct_to_user()`, `copy_struct_from_bounce_buffer()`, `copy_struct_to_bounce_buffer()` |
| Same copy through a `sockptr_t` | `include/linux/sockptr.h` | `copy_struct_from_sockptr()`, `copy_struct_to_sockptr()`; a kernel pointer takes the bounce-buffer form |
