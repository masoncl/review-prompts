- `add_ignores()`: sets `ignore` on the function's `struct symbol` and on its
  `cfunc`; `struct instruction` has no ignore flag.
- Skipped for an ignored function: everything that runs through
  `validate_branch()` (stack and CFI rules, uaccess, noinstr), the
  "unannotated intra-function call" and "unsupported call to non-function"
  errors, and "unreachable instruction".
- Not skipped: `validate_retpoline()`, `validate_ibt()`, `validate_sls()`,
  `validate_unrets()` and the site sections that `check()` creates; none of
  them tests `ignore`.
- Relocation against a section symbol: `add_ignores()` uses
  `find_func_by_offset()`, and skips the entry without a message when no
  function starts there.
- **Unsafe usage**: `STACK_FRAME_NON_STANDARD` on a symbol that is not
  `STT_FUNC`, such as code closed with `SYM_CODE_END`.
  - Unsafe: `add_ignores()` fails with "unexpected relocation symbol type" for
    any symbol type other than `STT_FUNC` and `STT_SECTION`.
  - Safe: on a symbol closed with `SYM_FUNC_END`, as `clear_bhb_loop` in
    `arch/x86/entry/entry_64.S`.
- Asm `STACK_FRAME_NON_STANDARD_FP`: defined only under `CONFIG_OBJTOOL`; the
  other branch of `include/linux/objtool.h` gives empty asm macros for
  `UNWIND_HINT` and `STACK_FRAME_NON_STANDARD` only.
- `is-standard-object`: defined in `scripts/Makefile.build`; a per-file value
  of `n` overrides a directory value of `y`.
- `is-kernel-object` in `scripts/Makefile.lib`: also required by
  `is-standard-object`, so an object outside `real-obj-y`, `lib-y` and
  `real-obj-m` gets no per-object objtool run whatever the variable says,
  unless its Makefile sets `objtool-enabled` itself, as
  `arch/x86/boot/startup/Makefile` does.
- With `delay-objtool`: `OBJECT_FILES_NON_STANDARD` is still honoured for a
  single-object module (`is-single-obj-m`); it is not consulted for
  `vmlinux.o` or for `$(multi-obj-m)`, so built-in code is validated anyway.
- Without `delay-objtool` but with `CONFIG_NOINSTR_VALIDATION`:
  `scripts/Makefile.vmlinux_o` still runs objtool on `vmlinux.o` with
  `--noinstr`, and that run does not consult `OBJECT_FILES_NON_STANDARD`.
- `OBJECT_FILES_NON_STANDARD` users: a search finds a handful of Makefiles,
  for example `arch/x86/platform/pvh/Makefile`, which sets it for `head.o`,
  a built-in object, and so is not an example of safe use (see "Build
  integration"); no Makefile for purgatory, realmode or vDSO code sets it.
