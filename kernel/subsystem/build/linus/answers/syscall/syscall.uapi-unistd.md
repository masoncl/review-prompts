- `include/uapi/asm-generic/unistd.h`: hand-written and current; it holds
  `__NR_fchroot` 472 and `__NR_syscalls` 473, matching `scripts/syscall.tbl`.
- Nothing in the build compares the header with `scripts/syscall.tbl`; outside
  `tools/` and `Documentation/` nothing includes it and only comments name its
  path.
- `tools/include/uapi/README`: speaks of kernel headers in general and names
  neither this header nor the tables; it says not to touch the copies when
  changing the originals.
- `tools/perf/check-headers.sh`: this is what names
  `include/uapi/asm-generic/unistd.h`, `scripts/syscall.tbl` and the per-arch
  tables; a difference only prints a warning.
- Copies under `tools/` may lag: for example
  `tools/perf/arch/parisc/entry/syscalls/syscall.tbl` ends at 462 `mseal`
  while `arch/parisc/kernel/syscalls/syscall.tbl` ends at 472.
