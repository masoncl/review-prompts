- `--werror`: the option is spelled in lower case; it sets `opts.werror`, see
  `check_options[]` in `tools/objtool/builtin-check.c`.
- `CONFIG_OBJTOOL_WERROR`: adds `--werror` through
  `objtool-args-$(CONFIG_OBJTOOL_WERROR)` in `scripts/Makefile.lib`.
- `scripts/Makefile.vmlinux_o`: adds `--werror` itself, also for
  `CONFIG_OBJTOOL_WERROR`, only in the `else` branch of
  `ifeq ($(delay-objtool),y)`; with `delay-objtool` it inherits
  `objtool-args-y`.
- `CONFIG_OBJTOOL_WERROR` in `lib/Kconfig.debug`: `depends on OBJTOOL &&
  !COMPILE_TEST` and has no `default`, so a config with `CONFIG_COMPILE_TEST`
  set cannot enable it.
- Warning count: the macros in `tools/objtool/include/objtool/warn.h` keep no
  count; `check()` adds up the return values of the validators in a local
  `warnings`. There is no global counter.
- `WARN()` in a function that returns 0: printed, not counted, does not fail the
  build under `--werror`; for example "file already has .ibt_endbr_seal,
  skipping" in `create_ibt_endbr_seal_sections()`.
- Warning-severity macros: `WARN()`, `WARN_FUNC()`, `WARN_INSN()`. The ELF and
  libc forms exist only as `ERROR_ELF()` and `ERROR_GLIBC()`.
- `WARN_STR`: is "error" when `opts.werror` is set, so under
  `CONFIG_OBJTOOL_WERROR` a warning line reads `error: objtool:` like a fatal
  one.
- `ERROR_INSN()`: plain `ERROR_FUNC()`; it does not test or set `sym->warned`
  and does not call `BT_INSN()`. Only `WARN_INSN()` prints once per symbol.
- `BT_INSN()`: prints when `opts.verbose || opts.backtrace`.
- After a counted warning: `do_validate_branch()` stops for that function; the
  rest of its path is not validated, the next function is.
- Warnings without `--werror`: `check()` returns `ret`, still 0, so
  `objtool_run()` goes on to `elf_write()`.
- End of `check()` with `opts.verbose`: prints "%d warning(s) upgraded to
  errors" (only with `opts.werror`) and calls `disas_warned_funcs()`; it does
  not print the command line.
- `disas_warned_funcs()`: empty stub in `tools/objtool/include/objtool/disas.h`
  when `DISAS` is not defined.
- `.orig` copy: made by `make_backup()` only with `--backup` (`opts.backup`),
  whenever `ret || warnings`, so also for warnings that are not upgraded.
- `make_backup()`: also prints the original command line itself, with the
  object replaced by `<obj>.orig -o <obj>` when `opts.output` is not set; there
  is no `print_args()` under `tools/objtool`.
- `--backup`: nothing in this tree passes it; `cmd_parse_options()` reads extra
  options from the `OBJTOOL_ARGS` environment variable.
- `.DELETE_ON_ERROR`: defined in `scripts/Kbuild.include`, which
  `scripts/Makefile.build` and `scripts/Makefile.vmlinux_o` include.
