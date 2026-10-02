| Probe | Runs | Existing flags in the test |
|---|---|---|
| `as-option` | `$(CC) -Werror ... -c -x assembler-with-cpp /dev/null` | `KBUILD_CPPFLAGS`, `KBUILD_AFLAGS` |
| `as-instr` | `printf "%b\n"` piped to `$(CC) -Werror ... -Wa,--fatal-warnings -c -x assembler-with-cpp -` | `CLANG_FLAGS`, `KBUILD_AFLAGS`; not `KBUILD_CPPFLAGS`, not `KBUILD_CFLAGS` |
| `ld-option` | `$(LD) $(KBUILD_LDFLAGS) $(1) -v`; no input file, nothing is linked | `KBUILD_LDFLAGS` |
| `__rustc-option` | a `no_core` crate on stdin, `--sysroot=/dev/null --crate-type=rlib --emit=obj=-` | `KBUILD_RUSTFLAGS_OPTION_CHKS`, then the caller's flags minus `--sysroot=/dev/null` and words matching `--target=%target.json` |

- `KBUILD_RUSTFLAGS_OPTION_CHKS`: where an arch that builds with
  `--target=$(objtree)/scripts/target.json` gives the probe a built-in
  `--target=`; see `arch/x86/Makefile`.
- `--target=<built-in triple>` in `KBUILD_RUSTFLAGS`: not filtered, it reaches
  the `rustc-option` test.
- There is no cc-ifversion here; the version probes are `gcc-min-version`,
  `clang-min-version` and `rustc-min-version`.
- Version probes: yield `y` or empty, never `n` (`test-ge` in
  `scripts/Kbuild.include`).
- `CONFIG_GCC_VERSION` under clang and `CONFIG_CLANG_VERSION` under GCC: 0
  (`init/Kconfig`), so the other compiler's probe yields empty.
- `TMPOUT`: `.tmp_$$$$`, relative to the directory make runs in; it has no
  `KBUILD_EXTMOD` case.
- Option that disables a warning: `__cc-option` compiles with every word
  `-Wno-<x>` of the option replaced by `-W<x>`, and yields the option as it
  was given.
- `cc-option`, `cc-option-yn` and `cc-disable-warning` all go through
  `__cc-option`, so all three test the positive form.
- `cc-disable-warning`: makes no test of its own; it is
  `$(call cc-option,-Wno-$(strip $1))`.
- `as-option`, `as-instr`, `ld-option`, `__rustc-option` and a bare
  `try-run`: no rewrite, the option is passed as given.
