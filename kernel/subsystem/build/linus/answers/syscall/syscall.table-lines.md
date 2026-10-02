- Tags in `scripts/syscall.tbl`: `common`, `32`, `64`, `time32`, `stat64`,
  `renameat`, `rlimit`, `memfd_secret`, and the architecture tags `arc`, `csky`,
  `nios2`, `or1k`, `riscv`.
- newstat: no such tag here; `newfstatat` (79) and `fstat` (80) are tagged `64`.
- `nospu`, `spu`, `x32`, `i386`, `oabi`, `eabi`, `n32`, `n64`, `o32`: tags of
  the powerpc, x86, arm and mips tables, not of the shared one.
- `hexagon`: requested in `arch/hexagon/kernel/Makefile.syscalls`, but no line
  carries it.
- Where an architecture chooses: `arch/<arch>/kernel/Makefile.syscalls`, which
  `scripts/Makefile.asm-headers` includes; it appends to `syscall_abis_32` and
  `syscall_abis_64`. There is no `arch/<arch>/kernel/syscalls/Makefile` on
  these architectures.
- 32 or 64 list: picked by the stem of each header named in `syscall-y` in
  `arch/<arch>/include/asm/Kbuild` and `arch/<arch>/include/uapi/asm/Kbuild`.
- Users of the shared table: the architectures that have
  `arch/*/kernel/Makefile.syscalls` (eight files).
- Lines that share a number (244 under `arc`, `csky`, `nios2`, `or1k`):
  selecting two tags that hold the same number makes `scripts/syscalltbl.sh`
  fail with "not sorted or duplicates the same syscall number".
- arm64: `arch/arm64/kernel/Makefile.syscalls` sets `syscalltbl` to
  `arch/arm64/tools/syscall_%.tbl`. `arch/arm64/tools/syscall_32.tbl` is its
  own compat table. `arch/arm64/tools/syscall_64.tbl` reads line for line as
  `scripts/syscall.tbl`; file searches over `arch/` do not list it.
- Own tables: `arch/<arch>/kernel/syscalls/` (alpha, m68k, microblaze, mips,
  parisc, powerpc, s390, sh, sparc, xtensa), `arch/x86/entry/syscalls/`, and
  `arch/arm/tools/` for arm.
