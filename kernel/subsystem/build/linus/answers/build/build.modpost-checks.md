- Severity is fixed by the macro: `mod_error()`, `error()` and `fatal()` are
  errors, `mod_warn()` and `warn()` are warnings. Only two calls pick it at run
  time, both `modpost_log()` in `check_exports()`.
- Switches that soften an error, in `scripts/Makefile.modpost`:

| Switch | modpost flag | What becomes a warning |
|---|---|---|
| `KBUILD_MODPOST_WARN`, any non-empty value | `-w` | undefined symbol, nothing else |
| `CONFIG_MODULE_ALLOW_MISSING_NAMESPACE_IMPORTS`, or `KBUILD_NSDEPS` (set by `make nsdeps`) | `-N` | namespace used but not imported |
| `CONFIG_SECTION_MISMATCH_WARN_ONLY=y` (`default y`) | omits `-E` | the "Section mismatches detected." summary is not printed |

- `W=1` (`-W`): sets `extra_warn`, which nothing in `scripts/mod/` reads; it
  enables no check.
- `make -i`: adds `-n`; `parse_elf()` then prints "(ignored)" for a module object
  it cannot open instead of exiting.
- Message format: `ERROR: modpost: <mod>.ko: symbol '<sym>' undefined!`; there is
  no `"sym" [mod.ko]` form to grep for.

| Problem | Where | Severity |
|---|---|---|
| section mismatch, each reference | `default_mismatch_handler()` | warning, always |
| "Section mismatches detected." | `main()` | error, only with `-E` |
| `__ex_table` reference to a section outside the text list | `default_mismatch_handler()` | `fatal()` if the section is black-listed, warning if it is executable, error otherwise |
| missing `MODULE_DESCRIPTION()` | `read_symbols()` | warning on every build |
| `MODULE_IMPORT_NS()` of a `module:` namespace | `read_symbols()` | error; `-N` does not soften it |
| undefined symbol | `check_exports()` | error; weak ones are never reported |
| symbol exported twice | `sym_add_exported()` | error; with `-e` silent unless the earlier export is in vmlinux or the same module |
| symbol exported without definition | `check_exports()` | error |
| local symbol exported, unknown export license | `check_export_symbol()` | error |
| `EXPORT_SYMBOL` on an init or exit section symbol | `check_export_symbol()` | warning |
| module name too long | `check_modname_len()` | error |
| too long symbol | `add_versions()` | error, only with `CONFIG_BASIC_MODVERSIONS` and without `CONFIG_EXTENDED_MODVERSIONS` |
| symbol has no CRC, version generation failed | `add_versions()`, `add_exported_symbols()` | warning |
| device table size mismatch or no terminator | `do_table()` in `scripts/mod/file2alias.c` | error, not `fatal()` |
| COMMON symbol, non-allocatable section | `handle_symbol()`, `check_section()` | warning |
| `$(objtree)/Module.symvers` or `vmlinux.o` missing | `cmd_modpost` in `scripts/Makefile.modpost` | message only; `-w` is not added, undefined symbols stay errors |
| a `-i` dump file cannot be opened | `read_text_file()` | `exit(1)`; the `!buf` test in `read_dump()` never fires |

- vmlinux: `read_symbols()` skips the `.modinfo` checks (license, description,
  import) and `main()` skips `check_exports()` and `check_modname_len()`; the
  section and device-table checks run on `vmlinux.o` too, and the export checks
  do under `CONFIG_MODULES` (`-M`).
