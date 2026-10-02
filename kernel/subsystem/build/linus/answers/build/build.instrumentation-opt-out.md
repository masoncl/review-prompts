- `lib-y` objects: kernel objects; `part-of-builtin` in
  `scripts/Makefile.lib` matches `$(real-obj-y) $(lib-y)`.
- Kernel object or not: decided by the list the object is in, not by the
  image it ends up in.
- gcov and KCOV: on for a kernel object only with `CONFIG_GCOV_PROFILE_ALL`
  or `CONFIG_KCOV_INSTRUMENT_ALL`; otherwise only where a switch says `y`.
- Other switches of the same form: `CONTEXT_ANALYSIS` (opt-in unless
  `CONFIG_WARN_CONTEXT_ANALYSIS_ALL`), `UBSAN_INTEGER_WRAP` (falls back to
  `UBSAN_SANITIZE`), `AUTOFDO_PROFILE`; search `scripts/Makefile.lib` for
  `$(target-stem).o)` to list them.
- Propeller: `scripts/Makefile.lib` reads `PROPELLER_PROFILE` for the
  directory but no per-file variable with that prefix.
- Directory switches: exported nowhere in the tree, so each subdirectory
  makefile sets its own.
- Assembler objects: `_a_flags` gets no sanitizer or coverage flags.
- Rust objects: `_rust_flags` gets only the KASAN, KCOV and AutoFDO flags.
- objtool: runs from `cmd_cc_o_c`, `cmd_as_o_S` and `cmd_rustc_o_rs` on every
  `$(obj)/%.o` for which `is-standard-object` in `scripts/Makefile.build` is
  set, under `CONFIG_OBJTOOL` and with `delay-objtool` empty.
- `OBJECT_FILES_NON_STANDARD_$(target-stem).o := n`: overrides a directory
  `OBJECT_FILES_NON_STANDARD := y`.
- `delay-objtool` (`CONFIG_LTO_CLANG`, `CONFIG_X86_KERNEL_IBT` or
  `CONFIG_KLP_BUILD`): per-object objtool runs only for single-object
  modules; multi-part modules get it at `cmd_ld_multi_m`, built-in code in
  `scripts/Makefile.vmlinux_o`.
- `scripts/Makefile.vmlinux_o`: does not read `OBJECT_FILES_NON_STANDARD`; it
  also runs objtool on `vmlinux.o` under `CONFIG_NOINSTR_VALIDATION` without
  `delay-objtool`, so the switch does not exempt built-in code from noinstr
  validation.
- Set of kinds to turn off: not fixed by the build; `kernel/entry/Makefile`
  and `mm/kasan/Makefile` set only `KASAN_SANITIZE`, `UBSAN_SANITIZE` and
  `KCOV_INSTRUMENT` to `n`.
- `__noinstr_section()` in `include/linux/compiler_types.h`: carries the
  per-function attributes for KCSAN, KASAN, KMSAN, coverage and profiling;
  some expand to nothing, for example `__no_sanitize_coverage` when the
  compiler lacks the attribute; it has no UBSAN attribute.
- `drivers/firmware/efi/libstub/Makefile` and the x86 vDSO
  (`arch/x86/entry/vdso/common/Makefile.include`): set no switch at all;
  the objects compiled from the stub sources and the vDSO objects
  (`vobjs-y`) are in `targets` only.
- **Potentially unsafe usage**: listing an object of code that must not be
  instrumented in `obj-y`, `obj-m` or `lib-y`.
  - Unsafe: when the makefile sets no switch for a kind that must be off and
    that the configuration enables; `is-kernel-object` is `y`, so
    `scripts/Makefile.lib` adds that kind's flags and objtool runs.
  - Safe: the compiled object is only in `targets` and a renamed copy goes in
    the list, as `drivers/firmware/efi/libstub/Makefile` does with
    `targets := $(lib-y)` and the `.stub.o` copies; `is-kernel-object` is
    empty for the compiled object.
  - Safe: a switch set to `n` for each kind that must be off, as
    `kernel/entry/Makefile` does for KASAN, UBSAN and KCOV on its `obj-y`
    objects; the `patsubst n%` tests in `scripts/Makefile.lib` read the
    switch before `is-kernel-object`.
