- `delay-objtool` in `scripts/Makefile.lib`: set by `CONFIG_LTO_CLANG`,
  `CONFIG_X86_KERNEL_IBT` or `CONFIG_KLP_BUILD`.
- `cmd_objtool`, `cmd_cc_o_c` and `cmd_as_o_S`: defined in
  `scripts/Makefile.lib`, not `scripts/Makefile.build`.
- `scripts/Makefile.build`: holds `is-standard-object`, the target-specific
  `objtool-enabled` settings, `cmd_ld_multi_m` and `cmd_rustc_o_rs`.
- Run points with `delay-objtool` set:

| Object | Where objtool runs |
|---|---|
| Built-in code | once on `vmlinux.o`, `scripts/Makefile.vmlinux_o` |
| Multi-object module | on the linked module `.o`, `$(multi-obj-m)` rule in `scripts/Makefile.build` |
| Single-object module | at compile time, through `is-single-obj-m` |

- `scripts/Makefile.modfinal`: has no module-wide objtool run and does not
  use `vmlinux-objtool-args-y`; nothing named prelink exists in `scripts/`.
- `objtool-enabled := y` in `scripts/Makefile.lib` is the default for
  makefiles that do not override it: `scripts/Makefile.modfinal` runs objtool
  on each `%.mod.o` and on `.module-common.o` (with `--module`),
  `scripts/Makefile.vmlinux` on, for example, `.vmlinux.export.o`.
- Rust objects: `cmd_rustc_o_rs` in `scripts/Makefile.build` and
  `cmd_rustc_library` in `rust/Makefile` end with `$(cmd_objtool)`.
- `arch/x86/boot/startup/Makefile`: sets `objtool-enabled` and
  `objtool-args` itself for `$(pi-objs)`; they run per object with `--noabs`
  even under `delay-objtool`, then with `--dry-run` in place of
  `objtool-args-y`.
- **Potentially unsafe usage**: `OBJECT_FILES_NON_STANDARD` to keep objtool
  off an object.
  - Unsafe: with `delay-objtool` set, for an object that is linked into
    `vmlinux.o` or into a multi-object module; the `vmlinux.o` and
    `$(multi-obj-m)` runs do not consult `is-standard-object`, so the code is
    still processed.
  - Safe: for an object that is linked into neither `vmlinux` nor a module,
    as the `lib-y` objects in `arch/x86/boot/startup/Makefile`, whose `lib.a`
    is in neither `KBUILD_VMLINUX_OBJS` nor `KBUILD_VMLINUX_LIBS` (top-level
    `Makefile`); the only run left is the per-object one, which
    `is-standard-object` in `scripts/Makefile.build` gates.
- `--prefix=`: gated by `CONFIG_CALL_PADDING`, value
  `CONFIG_FUNCTION_PADDING_BYTES`; there is no PREFIX_SYMBOLS Kconfig symbol.
- `--noinstr` and `--unret`: added only in `scripts/Makefile.vmlinux_o`,
  never in `objtool-args-y`; objtool rejects both without `--link`
  (`opts_valid()`).
- Without `delay-objtool`, the `vmlinux.o` run gets only `--werror`,
  `--noinstr`, `--unret`, `--klp-symids` and `--link`; `objtool-args-y` is
  not passed.
- objtool has no --vmlinux option; the linked-object mode is `--link`.
- `objtool-args-` block in `scripts/Makefile.lib`: also has `--cfi` and
  `--fineibt` (inside `ifdef CONFIG_CALL_PADDING`), `--hacks=skylake`, and
  `--no-unreachable` for `CONFIG_GCOV_KERNEL` or `CONFIG_KCOV`.
- `--klp-symids`: added in `scripts/Makefile.vmlinux_o` from the make
  variable `KLP_SYMIDS`, which `scripts/livepatch/klp-build` passes; no
  Kconfig symbol.
- `--backtrace`: passed by no kbuild file; extra options reach objtool
  through the `OBJTOOL_ARGS` environment variable, read by
  `cmd_parse_options()` in `tools/objtool/builtin-check.c`.
