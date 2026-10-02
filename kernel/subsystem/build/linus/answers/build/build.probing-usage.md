- `$(call cc-option,-Wno-foo)` and `$(call cc-disable-warning,foo)`: the same
  test; `scripts/Makefile.warn` uses the first form.
- **Unsafe usage**: testing a `-Wno-` option with a probe that does not go
  through `__cc-option`: a bare `try-run`, or `cc-option` in
  `scripts/Kconfig.include`.
  - Safe: `cc-option`, `cc-option-yn` or `cc-disable-warning` from
    `scripts/Makefile.compiler`; `__cc-option` tests the `-W` form, as
    `arch/x86/boot/compressed/Makefile` relies on.
- `:=` is not required: a per-object `+=` of a probe is routine, for example
  `CFLAGS_debug_info.o += $(call cc-option, ...)` in `lib/Makefile`.
- `CFLAGS_$(target-stem).o`: not initialised by `scripts/Makefile.build`, so
  `+=` leaves it recursive and the probe runs each time `c_flags` is expanded
  for that object; the cost is forks, the result is the same.
- `ccflags-y`, `asflags-y`, `ldflags-y`, `rustflags-y`: initialised with `:=`
  in `scripts/Makefile.build`, so `+=` onto them runs the probe once.
- Top `Makefile`: includes `scripts/Makefile.compiler` before
  `include/config/auto.conf`, and only under `need-compiler`.
- `need-compiler` empty (every goal is in `no-sync-config-targets`, such as
  `clean`): the arch `Makefile` is still included, and every probe call in it
  expands to empty; `cc-option-yn` is then neither `y` nor `n`, and no
  fallback is returned.
- Flags the object gets and the probe does not: see `c_flags` in
  `scripts/Makefile.lib`; for example `ccflags-y`, `CFLAGS_$(target-stem).o`,
  `KBUILD_CFLAGS_KERNEL`, and the removal by `CFLAGS_REMOVE_$(target-stem).o`.
- `__cc-option`: no caller outside `scripts/Makefile.compiler` and `tools/`.
- **Potentially unsafe usage**: `cc-option` for objects that are not built
  with `KBUILD_CPPFLAGS` and `KBUILD_CFLAGS`.
  - Unsafe: when the probe expands before the makefile replaces
    `KBUILD_CFLAGS`, or the objects use another compiler; the answer is for
    flags the object is not built with.
  - Safe: assign `KBUILD_CFLAGS :=` first, then probe, as
    `arch/x86/boot/compressed/Makefile` does; `cc-option` reads
    `KBUILD_CFLAGS` at expansion.
  - Safe: a local probe on `try-run` with the other compiler, as `cc32-option`
    in `arch/arm64/kernel/vdso32/Makefile` does for `CC_COMPAT`.
- **Unsafe usage**: `cc-option` in the top `Makefile`, or a file it includes,
  after a `-fplugin=` flag is in `KBUILD_CFLAGS`.
  - Unsafe: on a clean tree the plugin is not built when the `Makefile` is
    parsed, so the compile fails and the probe yields the fallback.
  - Safe: probe before `scripts/Makefile.randstruct`,
    `scripts/Makefile.kstack_erase` and `scripts/Makefile.gcc-plugins` are
    included, as `scripts/Makefile.warn` does.
  - Safe: `ld-option` after them, as `Makefile` does; it passes only
    `KBUILD_LDFLAGS`.
- **Unsafe usage**: a literal comma inside a probe argument, in make or in
  Kconfig.
  - Unsafe: in Kconfig the text after the comma becomes `$(2)`, which
    `cc-option` in `scripts/Kconfig.include` never reads; the option tested is
    cut at the comma. In make `cc-option` takes it as the fallback.
  - Safe: write `$(comma)`, as `arch/mips/Makefile` and the `as-instr` calls
    in `arch/riscv/Kconfig` do; `scripts/kconfig/preprocess.c` splits
    arguments at every top-level comma.
- `scripts/Kconfig.include` has no `try-run`; its probes are built on
  `success` and `if-success`.
- `scripts/Kconfig.include` has no `as-option`, `cc-option-yn`,
  `cc-disable-warning` or `__cc-option`.
- Assembler option in Kconfig: tested with `$(cc-option,-Wa$(comma)...)`, as
  in `arch/arm64/Kconfig`.
- Kconfig `cc-option`: `$(CC) -Werror $(CLANG_FLAGS) $(1) -c -x c /dev/null`;
  no `-Wno-` rewrite.
- Kconfig `as-instr`: `$(CLANG_FLAGS)`, the optional second argument and
  `-Wa,--fatal-warnings`; no `-Werror`, which the makefile `as-instr` has.
- Kconfig `cc-option-bit`: not built on `cc-option`; runs `$(CC) -Werror $(1)
  -E`, without `CLANG_FLAGS`, and yields the flag or empty, not `y` or `n`.
- Kconfig `rustc-option`: `$(RUSTC) $(1) --crate-type=rlib /dev/null`; no
  `--target`, no `--sysroot=/dev/null`, no `no_core` crate, no
  `KBUILD_RUSTFLAGS_OPTION_CHKS`.
- External module build (`KBUILD_EXTMOD` set): `may-sync-config` is cleared,
  so Kconfig probes are not re-run and the values of probed symbols, for
  example `CONFIG_CC_HAS_ASM_INLINE`, are those of the compiler that
  configured the kernel; makefile probes run the current `$(CC)`.
