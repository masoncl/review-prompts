- Compiler: Clang 23 or later; `CONFIG_WARN_CONTEXT_ANALYSIS` in
  `lib/Kconfig.debug` has `depends on CC_IS_CLANG && CLANG_VERSION >= 230000`.
- `CONFIG_WARN_CONTEXT_ANALYSIS`: `default y`, and also depends on
  `!TRACE_BRANCH_PROFILING`.
- Opt-in: `CONTEXT_ANALYSIS := y` in the Makefile of a directory, or per
  object, for example `CONTEXT_ANALYSIS_mutex.o := y` in
  `kernel/locking/Makefile`; search Makefiles for `CONTEXT_ANALYSIS` to see
  what is opted in.
- File not opted in: `WARN_CONTEXT_ANALYSIS` is not defined, so every
  annotation in `include/linux/compiler-context-analysis.h` expands to
  nothing; no attribute reaches the compiler.
- File opted in: gets `CFLAGS_CONTEXT_ANALYSIS` from
  `scripts/Makefile.context-analysis`, which defines `WARN_CONTEXT_ANALYSIS`
  and enables `-Wthread-safety`, `-Wthread-safety-pointer` and
  `-Wthread-safety-beta`.
- Headers in an opted-in file: warnings located in `include/linux/`,
  `include/net/`, `include/acpi/`, `include/asm-generic/` and arch include
  directories are suppressed by `scripts/context-analysis-suppression.txt`,
  except the headers that file lists with `=emit`.
- Opt-out: a value of the same Makefile variables starting with `n` works;
  see the `patsubst` in `scripts/Makefile.lib`. Per-file `n` overrides
  directory `y`; per-file `y` overrides directory `n`; directory `n`
  overrides `CONFIG_WARN_CONTEXT_ANALYSIS_ALL`.
- `CONFIG_WARN_CONTEXT_ANALYSIS_ALL`: depends on `EXPERT && !COMPILE_TEST`,
  applies only where `is-kernel-object` is set, and drops the suppression
  file.
