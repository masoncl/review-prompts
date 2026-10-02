- Quoting: `___EXPORT_SYMBOL()` in `include/linux/export.h` pastes the value
  after `.ascii`, so `-DDEFAULT_SYMBOL_NAMESPACE=NS` without quotes is not a valid
  form; write `ccflags-y += -DDEFAULT_SYMBOL_NAMESPACE='"NS"'`.
- Macros affected: only `EXPORT_SYMBOL()`, `EXPORT_SYMBOL_GPL()` and macros
  built on them, for example `EXPORT_PER_CPU_SYMBOL()`;
  `EXPORT_SYMBOL_NS()`, `EXPORT_SYMBOL_NS_GPL()` and
  `EXPORT_SYMBOL_FOR_MODULES()` name their own namespace.
- `ccflags-y` scope: C files of that one makefile; `scripts/Makefile.build`
  resets it per directory and `scripts/Makefile.lib` does not put it in
  `_a_flags`, so subdirectories and `.S` files are not covered.
- Softening the missing-import error: there is no
  KBUILD_ALLOW_MISSING_NS_IMPORTS; `-N` comes from
  `CONFIG_MODULE_ALLOW_MISSING_NAMESPACE_IMPORTS` or from `KBUILD_NSDEPS`.
- `make nsdeps`: modpost gets `-d modules.nsdeps`; `scripts/nsdeps` reads that
  file. There is no per-module ".nsdeps" file.
- Built-in users: `main()` in `scripts/mod/modpost.c` skips `check_exports()` for
  vmlinux, so code linked into vmlinux is never checked for imports.
- Not importable: only namespaces that start with `module:`
  (`MODULE_NS_PREFIX`); no other name is refused.
- `module:` namespaces are created by `EXPORT_SYMBOL_FOR_MODULES()`, which is a
  GPL-only export; there is no EXPORT_SYMBOL_GPL_FOR_MODULES() in this tree.
