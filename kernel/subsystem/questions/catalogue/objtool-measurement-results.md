# What the objtool measurement found

Three models were asked the 37 questions in `objtool-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Readers A and C said they assumed
kernels 6.12 to 6.19, know how objtool works and get most names right; reader
C needed the fewest corrections. Reader B said 6.10 to 6.12 and was wrong
about fundamentals: which architectures have a decoder, which way round the
two trap types fail, whether the tool has livepatch subcommands, a trace
option or Rust handling at all. The hand-written guide was never checked
against current sources, so differences between it and the built guide are
expected and are noted near the end.

How objtool works is well known: the branch walk, the unwind hint types, what
stack validation enforces, what the noinstr and uaccess checks allow. What the
readers got wrong is what moved: every annotation now goes through one section
and one header and the functions that used to read each annotation are gone
(only reader C knew either), the build glue gained a third reason to run at
link time, and the tool grew livepatch subcommands, a disassembler and a
tracer. After that come a score of facts that would change a verdict: where
the reachable annotation goes, which warning a missing list entry really
produces, that a per-file exception does nothing for the link-time run, and
which architecture can enable which check.

The wording of `objtool.compiler-traps` was tightened after the measurement
(it asked for the flags passed "when objtool is enabled", which presupposed a
condition the tree does not have). `objtool.core-files`,
`objtool.dead-end-detection` and `objtool.warnings-vs-errors` were reworded
when the build set was resized, so that none takes for granted the livepatch
subcommands, separate handling of Rust functions or an option that upgrades
warnings. The numbers are for the earlier wordings.

## What all three readers got wrong, or two with the third unsure

- **Where the annotation macros are.** Readers A and B put the `ANNOTATE_`
  macros in `include/linux/objtool.h`; reader C named the right file but
  marked it unsure in three answers. They and `ASM_ANNOTATE()` are in
  `include/linux/annotate.h`; the type numbers are in
  `include/linux/objtool_types.h`; `include/linux/objtool.h` keeps
  `UNWIND_HINT()` and `STACK_FRAME_NON_STANDARD()`. All instruction
  annotations share `.discard.annotate_insn`, and a second section,
  `.discard.annotate_data`, holds `ANNOTATE_DATA_SPECIAL` entries that only
  `tools/objtool/klp-diff.c` reads (readers A and B left it out). Reader B
  named a struct annotate_insn that does not exist; an entry is two 32-bit
  words, a PC-relative offset and the type, read by `annotype()`.
- **How annotations are read.** Readers A and B listed per-annotation readers
  (read_retpoline_hints(), read_instr_hints(), read_intra_function_calls(),
  add_dead_ends()) that are not in the tree, and readers A and C said
  `decode_file()` does not exist and called it decode_sections(). It exists
  and calls `read_annotate()` three times, with `__annotate_early()`,
  `__annotate_ifc()` and `__annotate_late()`; `read_unwind_hints()` comes
  before the late pass, and the code states its ordering constraints as
  comments, which no reader listed in full.
- **The leftover reachability macro.** `ASM_REACHABLE` in
  `include/linux/objtool.h` still writes `.discard.reachable`, which nothing
  under `tools/objtool` reads and nothing in the tree uses. Reader A said no
  such macro was left, reader B was unsure and reader C named the wrong one.
  `unreachable()` emits nothing for objtool.
- **`WARN()` on x86-64.** None knew that a `WARN()` with a format goes through
  `__WARN_printf()` to a static call to `__WARN_trap()` in
  `arch/x86/entry/entry.S`, which executes an annotated `ud1`, not an inline
  `ud2`.
- **Every function that tests the two trap types.** All three left out
  `validate_retpoline()`: with `--cfi` it requires the instruction before a
  retpoline thunk call to be `INSN_BUG` and otherwise warns "no-cfi indirect
  call!". All three also left `INSN_LEA_RIP` out of the instruction types.
- **Link-time objtool.** `delay-objtool` in `scripts/Makefile.lib` is set by
  `CONFIG_LTO_CLANG`, `CONFIG_X86_KERNEL_IBT` or `CONFIG_KLP_BUILD`; reader A
  left out the third, reader B had the list wrong and reader C hedged.
  `OBJECT_FILES_NON_STANDARD` is handled by `is-standard-object` in
  `scripts/Makefile.build` and does nothing for the run on `vmlinux.o` or on
  a multi-object module. Reader A offered an OBJTOOL_FLAGS variable that is
  nowhere in the tree.
- **Options and their configuration symbols.** `--uaccess` is passed for
  `CONFIG_HAVE_UACCESS_VALIDATION` (readers A and B said CONFIG_X86_SMAP),
  `--prefix` for `CONFIG_CALL_PADDING` (reader A said CONFIG_CALL_THUNKS,
  reader C CONFIG_PREFIX_SYMBOLS), `--cfi` for `CONFIG_CFI` and `--fineibt`
  for `CONFIG_FINEIBT`, both in the options group and not the actions group.
  `--noinstr` and `--unret` are passed only from `scripts/Makefile.vmlinux_o`.
  Readers A and C invented a `--checksum` action and a link_opts_valid()
  function; checksums come from the `objtool klp checksum` subcommand and the
  check is `opts_valid()`. Readers A and B spelled the upgrade option
  --Werror; it is `--werror`.
- **What happens on failure.** `objtool_run()` returns before `elf_write()`
  and the object is removed by `.DELETE_ON_ERROR` in `scripts/Kbuild.include`.
  `--backup` copies the object on any warning, not only on failure, and no
  Makefile passes it.
- **Which architecture can enable what.** `CONFIG_STACK_VALIDATION` depends on
  `UNWINDER_FRAME_POINTER`, which LoongArch does not have, so stack
  validation cannot be enabled there although `HAVE_STACK_VALIDATION` is
  selected. powerpc selects `HAVE_STATIC_CALL_INLINE` on 32-bit as well as
  `HAVE_OBJTOOL_MCOUNT`. x86 has `HAVE_OBJTOOL` only on 64-bit.
- **Compiler flags.** `-mno-check-zero-division` and
  `-fno-isolate-erroneous-paths-dereference` are added to `cflags-y` in
  `arch/loongarch/Makefile` unconditionally, after the `CONFIG_OBJTOOL` block
  closes; reader A said under `CONFIG_OBJTOOL`, reader C hedged and reader B
  offered -fno-reorder-blocks-and-partition, which no architecture Makefile
  passes. `arch/x86/Makefile` passes no flag of this kind.
- **Warning texts and what they mean.** "unreachable instruction" means no
  path reaches the instruction; code after a call objtool already treats as a
  dead end gets "missing __noreturn in .c/.h or NORETURN() in noreturns.h"
  instead (readers A and C had these the wrong way round). The retpoline text
  says "MITIGATION_RETPOLINE build". "unannotated intra-function call" and
  "UNWIND_HINT_IRET_REGS without ENDBR" are errors that stop the run, not
  warnings, which no reader said. The return-thunk check is inside
  `validate_retpoline()` and so needs `--retpoline` as well (readers A and
  C).
- **Adding an annotation or hint type, and the header copies.** All three
  were more than half rewritten. An unknown annotation type is a fatal
  `ERROR_INSN()` in `__annotate_late()`; an unknown hint type is accepted by
  `read_unwind_hints()` and fails only in `init_orc_entry()`, so only with
  `--orc`. `tools/objtool/sync-check.sh` checks `include/linux/objtool_types.h`
  on every architecture and everything else only on x86, and on a mismatch
  prints a warning and a `diff -u` command without failing the build.
- **The livepatch subcommands.** `objtool klp` has `checksum`, `diff` and
  `post-link`, built only on x86 and only with libxxhash; without them the
  weak `cmd_klp()` in `tools/objtool/weak.c` answers. Reader B said there were
  none, readers A and C left out `checksum`.

## What only some readers got wrong

- **Reader B on fundamentals.** It listed an arm64 decoder and no LoongArch
  one (the decoders are x86, loongarch and powerpc); named include/linux/frame.h;
  had the consequences of swapping the two trap types the wrong way round;
  listed INSN_CONTEXT_SWITCH, which is now `INSN_SYSCALL` and `INSN_SYSRET`;
  called `tools/objtool/noreturns.h` a generated list and said there was no
  Rust handling (`is_rust_noreturn()`); knew five of the nine annotation
  types; said there was no `--trace`, `--backup` or `--disas`; said inline asm
  with a call needs ANNOTATE_INTRA_FUNCTION_CALL (it needs
  `ASM_CALL_CONSTRAINT`); said safe-list functions are exempt from the uaccess
  checks (they start with user access enabled and must return that way); and
  said `validate_retpoline()` accepts an lfence and that objtool rewrites
  returns.
- **Where the reachable annotation goes** (readers A and B).
  `ANNOTATE_REACHABLE` marks the dead-end instruction itself, the `ud2` or
  `break`, and `__annotate_late()` clears that instruction's `dead_end`. Both
  said it goes on the instruction after.
- **LoongArch encodings** (reader A). `break 0x0` is `INSN_TRAP`, `break 0x1`
  and `amswap.w $zero, $ra, $zero` are `INSN_BUG`, other break codes are
  ordinary instructions. Readers A and B did not know x86 types `udb` as
  `INSN_BUG`; reader C was right on every row.
- **How a function is found not to return** (readers A and B). The scan of the
  function body for a return applies to any non-weak function defined in the
  object, global ones included, follows a sibling call up to five deep, and
  does not look at ordinary calls. A global function missing from the list
  gives the fall-through warning, not the missing `__noreturn` one. The Rust
  match is on mangled `_R` names and never on rust_panic.
- **An example that is gone** (reader A). `___bpf_prog_run()` no longer carries
  `STACK_FRAME_NON_STANDARD`; it relies on `__annotate_jump_table`.
- **Alternatives** (readers A and B). The recursion into `insn->alts` is in
  `validate_insn()`; there is no skip_orig; `ANNOTATE_IGNORE_ALTERNATIVE`
  stops the walk in whichever group carries it; the CLAC and STAC special
  case in `skip_alt_group()` runs on every walk, not only with `--uaccess`
  (reader C).
- **Return untraining** (reader A). ANNOTATE_UNRET_END does not exist; the end
  marker is `VALIDATE_UNRET_END`, a retpoline-safe NOP, and
  `ANNOTATE_UNRET_SAFE` does not exempt a return from `validate_unret()`.
- **Uaccess details** (readers A and B). The save and restore of the flags
  register is tracked only inside an alternative group; the documentation
  asks of a new safe-list function only that it is notrace and obviously never
  calls `schedule()`.

## What the readers already knew

Readers A and C: the unwind hint types and the per-architecture hint macros
(one correction each), callable against non-callable assembly, the generic
treatment of the two trap types apart from the kCFI test, the noinstr rules
and why `instrumentation_end()` is an instruction, the uaccess state machine,
the sections objtool writes and who reads them. Reader C also had the
per-architecture trap table and the dead-end rules nearly right. All three
knew the stack validation rules in outline and what `STACK_FRAME_NON_STANDARD`
does to a function's ORC data.

## Where the hand-written guide is stale

Less than most: its subject is narrow and the code it names is unchanged.
`decode_instructions()` does set `dead_end` for `INSN_BUG`,
`validate_retpoline()`, `ignore_unreachable_insn()` and `validate_sls()` do
test the types as it says, its x86 and LoongArch table is right, and
`arch/loongarch/Makefile` does pass the two flags it names.

- Its summary of what goes wrong is loose. A BUG typed as a trap lets the walk
  run past it, so the usual result is a fall-through or end-of-section
  warning, and an unreached one is silently ignored. A trap typed as BUG stops
  the walk, so what follows is reported unreachable and the straight-line
  speculation check fails; nothing is hidden.
- It does not say that a `WARN()` trap is the same instruction as `BUG()` and
  is kept reachable by an annotation on the instruction itself, which is the
  case a decoder change is most likely to break.
- It leaves out powerpc, whose decoder uses neither type.
- It does not say the LoongArch flags are unconditional, or that x86 passes
  none and relies on `ignore_unreachable_insn()`.
- It has no map of the tool and nothing on annotations, which is where every
  reader was out of date.

## What was left out of the build set and why

The build set has 10 of the 37 questions and 500 words of budget. The
hand-written guide is 312 words, under the 600-word floor for a built guide, so
the set is sized to 600 words (480 to 720) with no question budgeted under 40.
The first cut, 7 questions and 230 words held to the 312, left 25 to 45 words
an answer, and the answers came out as fragments that needed the question
beside them. The set is weighted towards what loads the guide: a change under
`tools/objtool/`, above all to a decoder. Kept from the first cut: where the
code and the kernel-side macros are, how annotations reach the tool (two
readers were wrong and the third hedged), the two trap types, the
per-architecture table, how calls that do not return are found (additions to
`tools/objtool/noreturns.h` are the commonest objtool patch, and two readers
had the rule wrong), and the two things a decoder has to agree with outside
objtool. Added with the larger size:

- `objtool.reachability-annotations`: which instruction the reachable
  annotation goes on decides whether a `WARN()` trap ends the path, two readers
  put it on the wrong one, and no reader knew of the leftover macro.
- `objtool.warnings-vs-errors`: it decides whether a new finding breaks the
  build, and no reader said which findings stop the run.
- `objtool.new-annotation-checklist`: every reader had more than half of this
  answer rewritten, and the number is shared between the kernel and the tool.

Left out:

- `objtool.decoder-change-checklist`, because the three decoder questions
  that are kept already say what to check and where.
- What readers A and C answer and only the oldest reader does not: the unwind
  hints, callable and non-callable assembly, the stack rules, the noinstr and
  uaccess checks, the instruction types, the generated sections.
- What all got partly wrong but few patches under this guide's trigger turn
  on: the build glue and option table, which architecture enables what, the
  order of `decode_file()`, the debugging options, the mitigation and IBT
  checks, the warning texts, the annotation types and skipping validation,
  the header copies and the livepatch subcommands. They stay in the
  measurement set. A guide loaded for users of the annotations (entry code,
  `noinstr`, `user_access_begin()`) would want the annotation types, skipping
  validation and the warning table first.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader A          125        39%      2     18   6.12 to 6.19
reader B          131        80%      0     37   6.10 to 6.12
reader C          106        30%      9     11   6.12 to 6.19

question                              reader A      reader B      reader C   verdict
objtool.core-files                    16% ( 6)      44% ( 7)      15% ( 6)   weak: reader B
objtool.build-integration             62% ( 3)      83% ( 1)      44% ( 3)   all weak
objtool.actions-and-config            22% ( 3)      69% ( 2)      35% ( 6)   weak: reader B
objtool.arch-support                  35% ( 2)      76% ( 1)      34% ( 2)   weak: reader B
objtool.decode-order                  57% ( 6)      90% ( 1)      41% ( 4)   all weak
objtool.validation-passes             40% ( 3)      83% ( 5)      24% ( 1)   weak: reader A, reader B
objtool.warnings-vs-errors            42% ( 6)      92% ( 1)      39% ( 3)   weak: reader A, reader B
objtool.debugging-aids                45% ( 5)      80% ( 3)      35% ( 1)   weak: reader A, reader B
objtool.insn-types                    21% ( 3)      79% ( 6)      24% ( 5)   weak: reader B
objtool.bug-vs-trap                   27% ( 2)      92% ( 2)      13% ( 1)   weak: reader B
objtool.arch-bug-trap-map             43% ( 3)      68% ( 1)       4% ( 1)   weak: reader A, reader B
objtool.runtime-trap-match            34% ( 2)      91% ( 2)      47% ( 3)   weak: reader B, reader C
objtool.compiler-traps                52% ( 3)      92% ( 4)      46% ( 2)   all weak
objtool.dead-end-detection            69% ( 4)      86% ( 5)      13% ( 2)   weak: reader A, reader B
objtool.jump-tables                   46% ( 3)      86% ( 4)      29% ( 3)   weak: reader A, reader B
objtool.annotation-mechanism          48% ( 6)      85% ( 8)      41% ( 3)   all weak
objtool.annotation-types              29% ( 2)      73% ( 4)      23% ( 4)   weak: reader B
objtool.reachability-annotations      43% ( 2)      88% ( 2)      22% ( 1)   weak: reader A, reader B
objtool.func-vs-code                  24% ( 1)      76% ( 1)      11% ( 1)   weak: reader B
objtool.non-standard-usage            35% ( 3)      65% ( 1)      47% ( 1)   weak: reader B, reader C
objtool.unwind-hint-types              6% ( 1)      64% ( 6)      11% ( 2)   weak: reader B
objtool.unwind-hint-macros             8% ( 1)      87% ( 4)      24% ( 2)   weak: reader B
objtool.stack-rules                   37% ( 4)      80% ( 7)      12% ( 3)   weak: reader B
objtool.alternatives                  48% ( 4)      80% ( 4)      20% ( 2)   weak: reader A, reader B
objtool.noinstr-validation            41% ( 2)      92% ( 6)      17% ( 3)   weak: reader A, reader B
objtool.noinstr-usage                 34% ( 1)      75% ( 4)       3% ( 1)   weak: reader B
objtool.uaccess-validation            37% ( 3)      87% ( 3)      11% ( 1)   weak: reader B
objtool.uaccess-usage                 59% ( 2)      69% ( 3)      25% ( 2)   weak: reader A, reader B
objtool.mitigation-checks             33% ( 7)      80% ( 8)      26% ( 5)   weak: reader B
objtool.ibt-validation                37% ( 4)      79% ( 3)      30% ( 3)   weak: reader B
objtool.generated-sections            24% ( 5)      61% ( 5)      21% ( 7)   weak: reader B
objtool.warning-meanings              29% ( 9)      80% ( 8)      66% ( 6)   weak: reader B, reader C
objtool.documentation                 70% ( 2)      88% ( 2)      47% ( 3)   all weak
objtool.decoder-change-checklist      16% ( 4)      82% ( 4)      39% ( 1)   weak: reader B
objtool.new-annotation-checklist      63% ( 3)      93% ( 1)      81% ( 4)   all weak
objtool.tools-header-sync             66% ( 3)      75% ( 1)      47% ( 3)   all weak
objtool.klp-subcommands               59% ( 2)      93% ( 1)      52% ( 5)   all weak
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `objtool.build-integration`, `objtool.non-standard-usage`, `objtool.uaccess-usage`, `objtool.warning-meanings`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `objtool.annotation-types`, `objtool.func-vs-code`, `objtool.unwind-hint-types`, `objtool.stack-rules`, `objtool.alternatives`, `objtool.noinstr-validation`, `objtool.noinstr-usage`, `objtool.uaccess-validation`, `objtool.decoder-change-checklist`.

## Questions reorganised

Subjects now, after the file map and the build glue: annotations, trap instructions and dead ends,
reading a run, noinstr and uaccess, stack validation and unwind hints. Nothing merged. Dropped:
`objtool.decoder-change-checklist`, which restated `objtool.bug-vs-trap`, `objtool.compiler-traps`
and `objtool.runtime-trap-match` now that one builder answers them together. Reworded so as not to
ask for an inventory: `objtool.bug-vs-trap` asks which checks act on either type, not for every
function; `objtool.new-annotation-checklist` asks what an unknown type does and what checks the
header copies; `objtool.annotation-mechanism` and `objtool.unwind-hint-types` no longer ask for an
entry's layout or a structure's fields. 25 became 24.
