- `scripts/syscallhdr.sh` with `--emit-nr`: writes the number on the last
  selected line plus one; it neither sorts nor takes a maximum.
- Order is enforced elsewhere: `scripts/syscalltbl.sh` fails the build on a
  table that is out of order.
- `scripts/Makefile.asm-headers`: sets `syshdr-args := --emit-nr`, so every
  user of the shared table gets a generated `__NR_syscalls`.
- mips: passes no `--emit-nr`; `arch/mips/kernel/syscalls/syscallnr.sh` writes
  `__NR_64_Linux_syscalls`, `__NR_N32_Linux_syscalls` and
  `__NR_O32_Linux_syscalls`, and `NR_syscalls` in
  `arch/mips/include/asm/unistd.h` adds the base.
