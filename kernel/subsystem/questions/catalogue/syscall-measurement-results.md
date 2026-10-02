# What the syscall measurement found

Three models were asked the 32 questions in `syscall-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; reader
B is the oldest and assumed a kernel several releases behind the other two.
Which models they were does not matter here. The hand-written guide is 146
words and was never checked against current sources, so the built guide aims
for 600 words, the least a built guide is given, and differences between the
two are expected and are noted below.

## What all three readers got wrong

- **Where the tables end.** All three named `file_setattr` (469) or `listns`
  (470) as the newest call. `scripts/syscall.tbl` and every architecture's
  table go on to 471 `rseq_slice_yield` and 472 `fchroot`, and the next free
  number is 473. A reader that reasons from "the last call I know" picks a
  number that is taken.
- **Same number everywhere, with exceptions nobody listed correctly.** alpha's
  table is offset by 110 (`fchroot` is 582). The three mips tables hold the
  plain number and `arch/mips/kernel/syscalls/Makefile` adds 4000, 5000 or
  6000 through `--offset`; two readers gave 5469-style numbers as table
  contents. In `arch/x86/entry/syscalls/syscall_64.tbl` the x32 rows 512 to
  547 are closed and the comment says 548 and above are not for x32-specific
  calls; reader A said a new x32 row goes above 547. The shared numbering
  starts at 424, not 403, because 403 to 423 are `32`-only time64 rows.
- **The document against the code.** `Documentation/process/adding-syscalls.rst`
  writes the x86 compat column as `__ia32_compat_sys_xyzzy` and the x32 row as
  `__x32_compat_sys_xyzzy`. The tables name plain `compat_sys_*`;
  `arch/x86/entry/syscall_32.c` and `arch/x86/entry/syscall_64.c` add the
  `__ia32_` and `__x64_` prefixes, and no x32 prefix exists
  (`__x64_compat_sys_*()` is the x32 stub). The document's x32 example row 555
  is outside the permitted range. Its section on calls that return elsewhere
  describes `stub_` entry points that no file under `arch/x86/entry/` has; the
  tables carry a `noreturn` column instead. No reader found all of these and
  reader B found none.
- **The generic number header.** `include/uapi/asm-generic/unistd.h` is still
  extended by hand for every new call (`__NR_fchroot` 472, `__NR_syscalls`
  473) but nothing under `arch/` includes it; tables are sized by the
  `__NR_syscalls` in the generated headers. Reader B thought it was the shared
  table arm64 and riscv build from. The copies under `tools/` (the header,
  `tools/scripts/syscall.tbl`, the perf tables) are left to the perf
  maintainers by `tools/include/uapi/README`; of the last three calls only the
  `fchroot` commit touched them itself.
- **64-bit arguments by value.** Reader A did not recognise `SC_ARG64` and
  `SC_VAL64`; reader B listed the wrong users; reader C thought
  `CONFIG_ARCH_SPLIT_ARG64` gates the macros. They are unconditional in
  `include/linux/syscalls.h`, ordered by `__LITTLE_ENDIAN`, used by
  `fanotify_mark` (through `SYSCALL32_DEFINE6`), `arch/hexagon/kernel/syscalltab.c`
  and `arch/sh/kernel/sys_sh32.c`; the option, selected by X86_32, PPC32 and
  32-bit parisc, only picks the split form of `fanotify_mark`. The compat
  halves are `compat_arg_u64()`, `compat_arg_u64_dual()` and
  `compat_arg_u64_glue()` in `include/asm-generic/compat.h`, ordered by
  `CONFIG_CPU_BIG_ENDIAN`, and riscv is the only architecture that asks for
  all eight generic compat versions.
- **What a new call's patches contain.** Each reader needed five or six
  corrections. Each of the last three calls was wired into all sixteen
  architecture tables, `scripts/syscall.tbl` and the generic header in one
  commit (for example "arch: hookup fchroot() system call"), not x86 first. The
  table list is more than `arch/*/kernel/syscalls/`: arm and arm64 compat live
  under `arch/*/tools/`, x86 under `arch/x86/entry/syscalls/`.
  `arch/arm64/tools/syscall_64.tbl` is the shared table again, not one to
  edit. `fchroot()` has neither a configuration option nor a `COND_SYSCALL()`
  line; `rseq_slice_yield` has both. The document asks for linux-api only.
- **Return values in the error range.** `force_successful_syscall_return()`
  does something only on alpha, powerpc, sparc and nios2; elsewhere it is
  empty and a value in the last 4095 is still read as an error. `mmap()` does
  not use it; `shmat()`, `times()` and `F_GETOWN` do.
- **Out-of-range numbers on x86-64.** All said `__x64_sys_ni_syscall()`
  answers them. It is only the `default:` of the switch in `x64_sys_call()`;
  a number outside both ranges calls nothing and `regs->ax` keeps the
  `-ENOSYS` the entry code stored.

## What only some readers got wrong

- **s390 has no compat support in this tree.** Readers A and B invented
  `__s390_compat_sys_` entries and an s390 override of `compat_ptr()` or
  `__SC_DELOUSE`; no architecture overrides either. Reader A also invented
  `__powerpc_sys_` names: powerpc's wrapper emits an unprefixed `sys_<name>()`
  taking `const struct pt_regs *`, and is selected only without compat. On
  x86, arm64, riscv and s390 no `sys_<name>` symbol exists at all, which
  readers A and B both had wrong when explaining why kernel code must not call
  one.
- **Arguments a flag gives meaning to** (the hand-written guide's subject).
  Readers A and C had the rule right and the code half right. `mremap()` copies
  `new_addr` into `struct vma_remap_struct` unconditionally, the gated readers
  are `check_mremap_params()` and `vrm_set_new_addr()`, and `check_prep_vma()`
  then overwrites `vrm->new_addr` with `addr` when `vrm_implies_new_addr()` is
  false, after which `do_mremap()` uses it ungated. `futex()` always passes
  the `utime` register on as `val2`; only reading it as a timeout is gated by
  `futex_cmd_has_timeout()`. Reader B placed both gates in the wrong function
  and called the `val2` use unsafe.
- **Reader B on fundamentals.** It put the body of a call in `sys_name()`
  (it is in `__do_sys_name()`), said `__SC_TEST` refuses `u64` (it exempts
  `long long`), said x86-64 dispatches through `sys_call_table[]` (a switch;
  the array is kept for `kernel/trace/trace_syscalls.c`), named a
  scripts/Makefile.syscalls that does not exist (`scripts/Makefile.asm-headers`),
  said x86 shares `scripts/syscall.tbl`, said an added argument needs a new
  call number, described the last argument of `copy_struct_to_user()` as a
  padding bitmap (`bool *ignored_trailing`), said architectures outside x86 get
  new calls later, and said seccomp and tracing keep no lists
  (`mode1_syscalls`, `check_faultable_syscall()`).
- **`copy_struct_to_user()`** (readers A and C). Reader A suggested `-E2BIG`
  for lost data where the kerneldoc suggests `-EMSGSIZE`, and invented a
  sched_attr_copy_to_user(); every in-tree caller passes NULL for
  `ignored_trailing`.
- **Compat details** (readers A and C). The generic `COMPAT_SYSCALL_DEFINEx`
  does run `__SC_TEST`; what it leaves out is `__PROTECT()` and the metadata.
  `in_compat_syscall()` is `is_compat_task()` only by default; x86 and sparc
  override it. riscv and loongarch do not list `time32` in their
  `Makefile.syscalls`.
- **The missing-call check** (readers A and B). `scripts/checksyscalls.sh`
  compares against `arch/x86/entry/syscalls/syscall_32.tbl`, not the shared
  table or the generic header, and runs from `prepare` in the top-level
  `Kbuild`.
- **Audit and tracing lists** (readers B and C). `audit_classify_syscall()`
  has copies on alpha, parisc, s390, sparc and x86 beside `lib/audit.c`; new
  calls do join the class lists in `include/asm-generic/audit_*.h`.

## What the readers already knew

Readers A and C needed no correction or one on: how `copy_struct_from_user()`
treats the three size cases, its errors and the `PAGE_SIZE` and first-version
checks its callers make; rejecting unknown flag bits with `-EINVAL`; how
`membarrier()` gained `cpu_id`; which argument types need a compat entry point;
the six-argument limit, the widening in `__se_sys_name()` and the build-time
type test; what `COND_SYSCALL()` expands to and when a line is needed; copying
a structure once and validating the copy. Reader B knew the outline of most of
these and got a detail wrong in each.

## Where the hand-written guide is stale

- "Adding additional arguments to a syscall does not break ABI as long as the
  existing arguments are not changed" is stated without its precondition. Old
  callers leave whatever was in the register, so it is safe only when the new
  argument is read under a flag or command the old interface rejected.
  `membarrier()` refused any non-zero `flags` before `MEMBARRIER_CMD_FLAG_CPU`
  existed and forces `cpu_id` to -1 when the flag is clear.
- The paragraph on flag-gated parameters is right in substance and `mm/mremap.c`
  is where it came from, but it is an absolute that the same file contradicts:
  once `check_prep_vma()` has replaced `vrm->new_addr`, ungated use is correct.
- "REPORT as bugs" tells a reviewer what to report. A built guide says which
  usage is unsafe and which similar usage is correct.
- It has no map: nothing on the tables, the stubs, compat, 64-bit arguments or
  the extensible-structure helpers, which is most of what a syscall patch
  touches.

## What was left out of the build set, and why

The build set is sized to 600 words, the least a built guide is given, and no
answer is budgeted under 40: nine questions and 510 words of budget, which with
titles and headings comes to about 610. It keeps the seven it had at 300
words, now with room for whole sentences: the file map, number allocation, the
document's stale parts, 64-bit arguments, the two subjects of the hand-written
guide, and the checklist for a new call. Two came back, chosen by what a
reviewer of a syscall patch most needs among the things readers got wrong:
`arch-wrappers`, because readers A and B invented entry symbols and compat
support that this tree does not have, and `uapi-unistd`, because all three
were weak on it and every patch that adds a call has to decide what to do
about that header and the copies under `tools/`.

- `extensible-struct`, `flags-validation`, `compat-when`, `arg-type-limits`,
  `ni-stubs`, `user-memory-fetch`: two of three readers already answer them
  correctly and the kerneldoc or the document says the rest.
- `generic-table`, `arch-tables`, `compat-table-wiring`: weak, but the
  checklist, the documentation question and the generic header question carry
  the parts that decide a review (which tables, the header, the `tools/`
  copies, how the compat column is spelled). `generic-table` is the first to
  bring back if the guide is given more room: no answer lists the ABI keywords
  of the shared table.
- `in-kernel-calls`, `define-expansion`, `metadata`, `dispatch`,
  `table-generation`, `missing-check`: about the machinery, which a patch
  adding or changing a call rarely touches.
- `struct-to-user`, `struct-layout`, `compat-define`, `compat-arg64`,
  `time-types`, `other-consumers`, `return-values`,
  `fd-and-path-conventions`: real, but each matters to a minority of patches.
  `return-values` is the one among them that all three readers got wrong.

Four questions were reworded when the build set was resized, in both files,
without changing what they ask. `arg64-native` asks whether the tree has macros
for the two halves instead of presupposing them. `new-call-checklist` asks when
a configuration option and a stub are needed instead of listing them as parts
of every series, and asks for macro names in full. `arch-wrappers` asks for the
entry symbol of a call named foo, because the real symbols are pasted together
by the macros and appear nowhere in the tree as text, and `doc-accuracy` asks
for parts of the document by subject because two of its headings are kernel
versions.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader A           68        36%      4     15   6.12 to 6.17
reader B           77        78%      0     31   6.10 to 6.12
reader C           55        25%     10      8   6.12 to 6.19

question                             reader A      reader B      reader C   verdict
syscall.core-files                   14% ( 3)      19% ( 6)       6% ( 2)   middling
syscall.doc-accuracy                 56% ( 4)      90% ( 3)      49% ( 3)   all weak
syscall.define-expansion             30% ( 1)      88% ( 3)      13% ( 1)   weak: reader B
syscall.arch-wrappers                51% ( 5)      90% ( 1)       0% ( 0)   weak: reader A, reader B
syscall.arg-type-limits               0% ( 0)      88% ( 1)      19% ( 1)   weak: reader B
syscall.metadata                     64% ( 1)      83% ( 1)      29% ( 2)   weak: reader A, reader B
syscall.in-kernel-calls              46% ( 1)      74% ( 1)      39% ( 2)   weak: reader A, reader B
syscall.generic-table                36% ( 5)      84% ( 4)      68% ( 2)   weak: reader B, reader C
syscall.arch-tables                  16% ( 3)      86% ( 3)      31% ( 2)   weak: reader B
syscall.number-allocation            55% ( 3)      86% ( 4)      43% ( 2)   all weak
syscall.uapi-unistd                  51% ( 1)      82% ( 3)      55% ( 2)   all weak
syscall.table-generation             52% ( 1)      60% ( 4)       1% ( 1)   weak: reader A, reader B
syscall.dispatch                     45% ( 1)      85% ( 1)      33% ( 2)   weak: reader A, reader B
syscall.ni-stubs                     18% ( 1)      75% ( 1)      12% ( 1)   weak: reader B
syscall.missing-check                41% ( 1)      90% ( 1)      31% ( 1)   weak: reader A, reader B
syscall.flags-validation             16% ( 1)      70% ( 3)       3% ( 1)   weak: reader B
syscall.extensible-struct             0% ( 0)      68% ( 1)       0% ( 0)   weak: reader B
syscall.struct-to-user               31% ( 2)      68% ( 1)      18% ( 2)   weak: reader B
syscall.struct-layout                33% ( 2)      79% ( 1)      18% ( 2)   weak: reader B
syscall.flag-gated-args              28% ( 1)      80% ( 3)      20% ( 3)   weak: reader B
syscall.adding-arguments              7% ( 1)      91% ( 1)       0% ( 0)   weak: reader B
syscall.fd-and-path-conventions      59% ( 1)      91% ( 1)       7% ( 1)   weak: reader A, reader B
syscall.arg64-native                 82% ( 6)      86% ( 4)      49% ( 3)   all weak
syscall.compat-when                  23% ( 2)      77% ( 3)       5% ( 1)   weak: reader B
syscall.compat-define                20% ( 2)      83% ( 3)      16% ( 2)   weak: reader B
syscall.compat-arg64                 72% ( 4)      85% ( 3)      39% ( 1)   weak: reader A, reader B
syscall.compat-table-wiring          49% ( 2)      82% ( 4)      26% ( 2)   weak: reader A, reader B
syscall.time-types                   38% ( 3)      79% ( 1)      26% ( 1)   weak: reader B
syscall.new-call-checklist           46% ( 6)      75% ( 5)      41% ( 6)   all weak
syscall.other-consumers              25% ( 1)      92% ( 4)      42% ( 3)   weak: reader B, reader C
syscall.return-values                62% ( 2)      75% ( 1)      42% ( 2)   all weak
syscall.user-memory-fetch            17% ( 1)      52% ( 1)      21% ( 1)   weak: reader B
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `syscall.in-kernel-calls`, `syscall.generic-table`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `syscall.define-expansion`, `syscall.arg-type-limits`, `syscall.arch-tables`, `syscall.ni-stubs`, `syscall.flags-validation`, `syscall.extensible-struct`, `syscall.struct-layout`, `syscall.compat-when`, `syscall.compat-define`, `syscall.compat-table-wiring`, `syscall.user-memory-fetch`.

## Questions reorganised

Grouped by subject: defining an entry point, numbers and tables, arguments and structures, word size.
24 questions became 23.
Merged: `syscall.generic-table` and `syscall.arch-tables` into `syscall.table-lines` (what one line of
the shared table reaches, where the tables it does not reach live); whether a call is wired into
every table at once went to `syscall.new-call-checklist`.
`syscall.arch-wrappers`, `syscall.number-allocation` and `syscall.arg64-native` ask for the rule and
where a reader who extends it goes wrong, not for a list of architectures. `syscall.ni-stubs` and
`syscall.compat-define` were cut to three things each. Nothing was dropped.
