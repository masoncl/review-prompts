# What the build measurement found

Three models were asked the 39 questions in `build-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader A said it assumed kernels 6.10
to 6.17 and reader C 6.12 to 7.0; both describe Kbuild's structure correctly
(the goal variables, how flags are combined, `if_changed`, fixdep, the module
stages), and reader C needed the fewest corrections. Reader B said 6.10 to
6.12 but answered from a much older picture: helpers, variables and files
that are gone, and rules stated backwards. The hand-written guide was never
checked against current sources, so differences between it and the built guide
are expected and are noted near the end.

Kbuild is old and its outline is well known. What the readers got wrong is
what the last few releases renamed or split (the warning makefile, the steps
between the archives and vmlinux, the dialect variable), numbers that move
every few releases (tool versions), and corners nobody reads: what a probe
does with a warning-disabling option, which modpost messages are fatal, what
the UAPI header test compiles with.

## What all three readers got wrong

- **The warning makefile.** Every reader named scripts/Makefile.extrawarn
  somewhere. The file is `scripts/Makefile.warn`; it holds the default
  warnings, the `W=` groups and the `W=e`/`CONFIG_WERROR` handling, which also
  reaches host programs, userspace programs, Rust, the assembler and the
  linker.
- **From archives to vmlinux.** Readers A and C had the top-level `Makefile`
  building `vmlinux.a`, and reader B did not know the file. The `Makefile`
  runs `scripts/Makefile.vmlinux_a`, which makes
  `built-in-fixup.a` and then `vmlinux.a`; `scripts/Makefile.vmlinux_o` links
  `vmlinux.o` and runs objtool on it; `scripts/link-vmlinux.sh` produces
  `vmlinux.unstripped`, and `scripts/Makefile.vmlinux` strips that into
  `vmlinux`. BTF comes from `scripts/gen-btf.sh`.
- **The dialect variable.** `-std=gnu11` is not added to `KBUILD_CFLAGS`
  directly. It is in the exported `CC_FLAGS_DIALECT` together with
  `CONFIG_CC_MS_EXTENSIONS` (`-fms-anonymous-structs` where the compiler has
  it, else `-fms-extensions`). Readers A and C said in so many words that they
  knew of no shared variable; reader A was unsure the Microsoft extensions are
  global, reader B did not mention them. The decompressors, the x86 real-mode
  code and EFI stub, the arm64 compat and loongarch vDSOs and the s390
  purgatory all add `CC_FLAGS_DIALECT`; what they do not get is
  `-funsigned-char`, which outside `tools/` appears only in the top-level
  `Makefile`.
- **The tools directory.** All three said no tool gets `-fno-strict-aliasing`
  or `-funsigned-char`. `tools/perf/Makefile.config` adds both, and
  `-std=gnu11`; several selftests add `-fno-strict-aliasing` too. The
  `-Wstrict-aliasing=3` in `tools/scripts/Makefile.include` is for compilers
  that are not Clang.
- **Tool versions.** Readers A and C gave Clang 15.0.0, Rust 1.78.0 and
  bindgen 0.65.1, and pahole 1.16 or 1.22. The tree says Clang 17.0.1 (18.0.0
  for loongarch), Rust 1.85.0 (higher for s390 and powerpc), bindgen 0.71.1,
  pahole 1.26. Reader B gave GCC 5.1, binutils 2.25 and Make 3.82 and said
  none of them is enforced; they are 8.1, 2.30 and 4.0, and the compiler,
  assembler and linker checks run from `scripts/Kconfig.include`.
- **Probing a warning-disabling option.** Every reader said `cc-option` must
  not be given a `-Wno-` option. `__cc-option` rewrites `-Wno-x` to `-Wx` for
  the test, `cc-disable-warning` is only `cc-option` on the `-Wno-` form, and
  `scripts/Makefile.warn` uses `cc-option` that way throughout. Readers also
  put `CLANG_FLAGS` in `KBUILD_CFLAGS` (it goes into `KBUILD_CPPFLAGS`) and
  two said `ccflags-y += $(call cc-option,...)` probes once per file (the
  variable is simply expanded, so once per directory).
- **The UAPI header test.** Readers A and C made it depend on `CC_CAN_LINK`;
  it depends only on `HEADERS_INSTALL`. None knew the flags: `-std=c90
  -Werror -nostdinc`, each header included twice, a second pass as C++98, then
  `usr/include/headers_check.pl`, with `no-header-test`,
  `no-header-test-cxx` and `uses-libc` as the exception lists. Reader B
  described a generated `.c` file per header compiled as gnu11.
- **Exported header install.** Readers A and C remembered a list of headers
  allowed to leak `CONFIG_` names. There is none: any `CONFIG_` outside a
  comment fails `scripts/headers_install.sh`, as does a GPL SPDX tag without
  the syscall note. None mentioned that `__ASSEMBLY__` is rewritten to
  `__ASSEMBLER__`. Reader B offered header-y.
- **The post-link hook.** Readers A and C said an architecture's
  `Makefile.postlink` also runs for every module. Only
  `scripts/Makefile.vmlinux` calls it, on `vmlinux.unstripped`. They took it
  from `Documentation/kbuild/makefiles.rst`, which is out of date here.
- **Delayed objtool and LTO.** `delay-objtool` is set by `CONFIG_LTO_CLANG`,
  `CONFIG_X86_KERNEL_IBT` or `CONFIG_KLP_BUILD`; only the first makes the
  objects bitcode. No reader was sure the distributed ThinLTO mode
  (`CONFIG_LTO_CLANG_THIN_DIST`, `scripts/Makefile.thinlto`) exists. For
  modules the conversion and objtool happen in `cmd_ld_multi_m`, not in
  `scripts/Makefile.modfinal`.
- **Userspace programs.** Readers A and C named CC_CAN_LINK_STATIC, which
  this tree does not have, and had `-m32`/`-m64` always copied from the kernel
  flags; that happens only when `CONFIG_ARCH_USERFLAGS` is unset. Reader B
  took the target from the cross-compile prefix and gave the command-line
  variables as the flags.

## What only some readers got wrong

- **Reader B on fundamentals.** cc-ifversion, KBUILD_SRC, hostcxxprogs,
  header-y, scripts/Makefile.asm-generic and a subdir-ccflags-remove-y were
  all offered and none exists. `ld-option` runs the compiler (it runs
  `$(LD) -v`); the tree has no Rust option probe (it has `rustc-option`); the
  saved command is cmd_target (it is `savedcmd_$@`); a target missing from
  `targets` goes stale (it is rebuilt every time); `targets += $@` is the
  correct form (entries are written without `$(obj)/`); a missing
  `MODULE_LICENSE()` and a missing namespace import are warnings (both are
  errors); a default namespace is an unquoted token (it is a quoted C string);
  `extra-y` is built on every visit (only under `KBUILD_BUILTIN`, and no
  makefile uses it any more); a duplicate `obj-y` entry links twice; `$(src)`
  is relative to `$(srctree)`; a script is run correctly by its path.
- **Descending the wrong way** (readers A and B). Objects in `obj-y` of a
  directory entered through `obj-m` or `subdir-y` are not "built but not
  linked": without `need-builtin` nothing depends on them and they are never
  compiled. Both also missed the two `$(warning ...)` lines printed when
  `subdir-y` reaches a makefile that lists modules.
- **modpost severities** (readers A and C). The missing
  `MODULE_DESCRIPTION()` warning is unconditional, not a `W=1` extra.
  `KBUILD_MODPOST_WARN` downgrades only undefined symbols; reader C thought
  `-w` was added by itself when `Module.symvers` is missing.
- **modpost -W** (readers A and C). `scripts/Makefile.modpost` passes it
  for `W=1`, and modpost ignores it: the variable it sets is never read.
- **`if_changed`** (reader A). A space after the comma makes the command
  name empty so nothing runs; the overwrite problem belongs to calling
  `if_changed` twice for one target. A `rule_` used with `if_changed_rule`
  must itself save the command.
- **The shell** (reader A). `CONFIG_SHELL` is `sh`; scripts that need bash
  are run through `$(BASH)`.
- **`always-m` and `lib.a`** (reader C). `always-m` is built on every visit
  like `always-y`; members of a `libs-y` directory's `lib.a` are all linked,
  because `vmlinux.a` is linked whole.
- **Host programs** (readers A and B). hostprogs-y is not read; Rust needs
  `foo-rust := y`; there is no per-program HOSTLDFLAGS.

## What the readers already knew

Readers A and C: the goal variables and that `extra-y` is deprecated, what
happens to an entry listed twice, link order, the source and object path
variables and that `$(src)` already contains the source root, how `_c_flags`
is assembled and which per-file variable survives a removal, `filechk`, what
fixdep does and that a generated header needs an explicit prerequisite, the
module stages, the quoting of a default namespace and the `module:`
namespaces, external modules with `M=` and `MO=`, the `generic-y` lists
(reader C). All three knew which documents are the authority on what.

## Where the hand-written guide is stale or thin

- It says the dialect is `gnu11` and stops. The tree adds the Microsoft
  anonymous-struct extension on top through `CC_FLAGS_DIALECT`, and code built
  with its own flags gets the dialect but not `-funsigned-char`.
- It states as a rule that files under `tools/` assume strict aliasing and
  that type punning there should be warned about. perf and several selftests
  are built with `-fno-strict-aliasing`; the flags are per tool.
- It points at `Documentation/process/changes.rst` for tool versions without
  a number. Every reader's numbers were stale, and the numbers the build
  enforces are in `scripts/min-tool-version.sh`. Python 3.9 is the documented
  minimum.
- Its points about Python 3, `-funsigned-char` and `-fno-strict-aliasing` are
  still true.
- It has nothing on Kbuild itself: no file names, no probes, no `if_changed`,
  no modpost, no exported headers.
- It was never onboarded to the drift checker.

## What was left out of the build set and why

The hand-written guide is 247 words, so the built guide aims at 600, the floor
for a short guide, and no answer is budgeted under 40 words: at 300 words and
15 to 30 an answer the bullets came out as fragments that needed the question
beside them. Ten questions were kept, 480 words of budget: the five about
language and toolchain, which every review needs and every reader got partly
wrong, then the file map, the option probes, `if_changed` and the modpost
severities. The tenth is `build.uapi-header-test`, brought back when the size
was raised: every reader had it wrong, and it says which C an exported header
may use, so it sits with the dialect questions. The rest of the room went to
the two tables and the list of tool versions, 55 to 75 words each. A first
build at 520 words of budget put one builder's guide over the upper limit,
mostly in the cell separators of its tables, so the budgets above 40 were
trimmed; `build.if-changed` got its 50 back when one builder's answer came
out clipped again at 40.

Four of the kept questions were reworded, in both sets, so that they do not
presuppose their answer: `build.c-dialect` no longer calls every option in its
list always-on, `build.separate-flag-sets` asks whether that code gets the
dialect and whether any file is compiled both ways, and
`build.uapi-header-test` asks whether the test exists before asking how it
works. `build.c-dialect`, `build.uapi-header-test` and `build.modpost-checks`
now ask for names in full.

- Dropped because readers A and C answer them and the kept questions carry
  part of what reader B lacks: `build.goal-variables`,
  `build.composite-objects`, `build.builtin-and-module`, `build.link-order`,
  `build.flag-variables`, `build.include-paths`, `build.filechk`,
  `build.dependency-tracking`, `build.module-stages`,
  `build.symbol-namespaces`, `build.external-modules`, `build.docs`.
- Dropped for room, although at least two readers needed real corrections on
  each: `build.uapi-export`, `build.lto-and-objtool`, `build.vmlinux-stages`,
  `build.user-programs`, `build.probing-usage`, `build.descending`,
  `build.kbuild-change-checklist`. They are the first to bring back if the
  size limit is raised again, `build.uapi-export` before the rest. At 40
  words each there was no room for another without taking the words back out
  of the answers that had been clipped.
- Dropped as narrower: `build.arch-makefile`, `build.output-directory`,
  `build.instrumentation-opt-out`, `build.module-vs-builtin-flags`,
  `build.warning-levels`, `build.clean`, `build.host-programs`,
  `build.section-mismatch`, `build.symbol-versions`,
  `build.asm-generic-wrappers`.
- Folded into a kept question: the renamed warning makefile and the split
  vmlinux makefiles are asked for by `build.core-files`.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A:  86 corrections, 30% rewritten on average
reader B: 122 corrections, 77% rewritten on average
reader C:  74 corrections, 20% rewritten on average

question                        reader A      reader B      reader C
build.core-files                3% ( 3)       81% ( 2)      4% ( 3)
build.docs                      0% ( 0)       0% ( 0)       11% ( 1)
build.vmlinux-stages            55% ( 4)      87% ( 2)      19% ( 4)
build.arch-makefile             44% ( 2)      81% ( 1)      14% ( 2)
build.output-directory          42% ( 3)      76% ( 1)      13% ( 1)
build.goal-variables            5% ( 2)       57% ( 4)      11% ( 3)
build.composite-objects         13% ( 1)      84% ( 2)      21% ( 2)
build.builtin-and-module        0% ( 0)       80% ( 1)      0% ( 0)
build.descending                43% ( 2)      83% ( 3)      10% ( 1)
build.link-order                11% ( 1)      78% ( 1)      22% ( 0)
build.flag-variables            22% ( 2)      84% ( 5)      19% ( 2)
build.include-paths             7% ( 2)       88% ( 2)      5% ( 1)
build.instrumentation-opt-out   15% ( 2)      73% ( 4)      44% ( 3)
build.module-vs-builtin-flags   35% ( 2)      88% ( 3)      24% ( 1)
build.c-dialect                 51% ( 1)      93% ( 3)      13% ( 2)
build.separate-flag-sets        73% ( 1)      85% ( 1)      43% ( 2)
build.tools-tree                35% ( 1)      80% ( 1)      24% ( 1)
build.tool-versions             51% ( 1)      92% ( 1)      13% ( 2)
build.script-languages          46% ( 2)      81% ( 1)      24% ( 1)
build.option-probing            16% ( 4)      91% ( 7)      43% ( 3)
build.probing-usage             55% ( 3)      92% ( 3)      32% ( 4)
build.warning-levels            18% ( 5)      94% ( 4)      25% ( 2)
build.if-changed                47% ( 4)      77% ( 5)      14% ( 1)
build.filechk                   0% ( 0)       69% ( 1)      0% ( 0)
build.dependency-tracking       11% ( 1)      75% ( 5)      0% ( 0)
build.clean                     14% ( 1)      82% ( 5)      43% ( 2)
build.host-programs             40% ( 5)      83% ( 8)      2% ( 1)
build.user-programs             68% ( 3)      77% ( 3)      43% ( 2)
build.module-stages             13% ( 1)      73% ( 4)      8% ( 2)
build.modpost-checks            25% ( 3)      44% ( 6)      24% ( 1)
build.section-mismatch          13% ( 1)      76% ( 2)      27% ( 1)
build.symbol-versions           24% ( 1)      81% ( 3)      26% ( 1)
build.symbol-namespaces         1% ( 1)       78% ( 3)      12% ( 1)
build.external-modules          14% ( 4)      78% ( 4)      25% ( 1)
build.uapi-export               28% ( 3)      72% ( 3)      13% ( 5)
build.uapi-header-test          80% ( 4)      83% ( 3)      51% ( 6)
build.asm-generic-wrappers      51% ( 2)      69% ( 4)      8% ( 0)
build.lto-and-objtool           68% ( 5)      85% ( 7)      54% ( 7)
build.kbuild-change-checklist   53% ( 3)      71% ( 4)      19% ( 2)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `build.probing-usage`, `build.kbuild-change-checklist`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `build.goal-variables`, `build.composite-objects`, `build.descending`, `build.flag-variables`, `build.include-paths`, `build.instrumentation-opt-out`, `build.dependency-tracking`, `build.host-programs`, `build.module-stages`, `build.symbol-namespaces`, `build.external-modules`, `build.uapi-export`.

## Questions reorganised

The build set is now grouped by subject, each under one `- section:` so that one builder answers
it: language and toolchain (what every review needs, put first), exported headers, probing the
toolchain, saying what to build, flags and paths, custom rules, modules and modpost, the shared
makefiles. Each question is a hazard, a contract or orientation and asks two or three things; the
tables left are of variants a makefile chooses among or of values that change what a patch must do.
Merged: `build.goal-variables` and `build.composite-objects` into `build.goals`, without the list
of suffixes. Dropped: `build.module-stages`, an inventory of stages and intermediate files that
would not change a review; `build.core-files` keeps a row for the module stages. 26 became 24.

## No longer loaded on every review

`review-core.md` used to load this guide before anything else, because the
hand-written one was 250 words of baseline for reading any C in the tree: GNU C11,
unsigned `char`, no strict aliasing, Python 3, where the tool minimums are. Built
as the difference from what models believe, the guide says little of that, since
the models know it, and says instead where it does not hold (code built with its
own flags, `tools/`) and how Kbuild works: 4,200 words that a patch to a driver or
to `mm/` does not need. The baseline was also instruction to the reviewer ("do not
report"), which a built guide never carries. So the two are separate now. The
baseline is hand-written in `kernel/technical-patterns.md`, "Language and
Toolchain Baseline", which every review loads, and points here for the exceptions.
This guide loads like any other, from its row in `subsystem.md`, which also names
the directories that build with their own flags.
