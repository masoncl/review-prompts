- Tables: 470 `listns`, 471 `rseq_slice_yield` and 472 `fchroot` each have a
  line in `scripts/syscall.tbl` and in all 16 table files under `arch/`; none
  of those is fed from another. `arch/arm64/tools/syscall_64.tbl` is not a
  17th; it reads as `scripts/syscall.tbl`.
- ABI word on the new line differs per table: `common` in most, `i386` in
  `arch/x86/entry/syscalls/syscall_32.tbl`, `n32`, `n64` and `o32` in the mips
  tables; powerpc uses `common` or `nospu` (`rseq_slice_yield` is `nospu`).
- Calls needing architecture support still take a number in every table:
  `map_shadow_stack` has a line at 453 (563 on alpha) in every table; 447
  (557 on alpha) `memfd_secret` is a line or a "reserved" comment everywhere.
- One table only: `uretprobe` 335 and `uprobe` 336, in
  `arch/x86/entry/syscalls/syscall_64.tbl` alone, below the common sequence.
- Option and stub, calls 463–472: none has an option of its own, and nine of
  the ten have no line in `kernel/sys_ni.c`, because their files are always
  built.
- `rseq_slice_yield`: defined inside `#ifdef CONFIG_RSEQ_SLICE_EXTENSION` in
  `kernel/rseq.c`, an option for the feature, with
  `COND_SYSCALL(rseq_slice_yield)`.
- `mseal`: no option; `mm/Makefile` builds `mm/mseal.c` only with
  `CONFIG_64BIT` and `CONFIG_MMU`, so it has `COND_SYSCALL(mseal)`.
- `Documentation/process/adding-syscalls.rst` says a new call should normally
  have its own option and lists wiring up one particular architecture, usually
  x86, as a separate commit; calls 463–472 are in every table, and only
  `rseq_slice_yield` sits under an option.
