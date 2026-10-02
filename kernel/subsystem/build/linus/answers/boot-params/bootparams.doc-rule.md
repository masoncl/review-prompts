- `Documentation/process/submit-checklist.rst`, boot parameters: the item names
  `Documentation/admin-guide/kernel-parameters.rst`, not the `.txt`; the
  entries themselves go in `Documentation/admin-guide/kernel-parameters.txt`.
- `Documentation/process/submit-checklist.rst`, module parameters: the whole
  requirement is "documented with `MODULE_PARM_DESC()`"; it names no file and
  does not mention `module_param()`.
- `UNDOCUMENTED_SETUP` in `scripts/checkpatch.pl`: matches only
  `__setup("name"` with a literal string; `early_param()`, `core_param()`,
  `__setup_param()` and `module_param()` are not matched.
- `UNDOCUMENTED_SETUP`: issued with `CHK()`, not `WARN()`, so it prints only
  when `$check` is set.
- `$check`: set by `--strict`, and also forced on for files under
  `drivers/net/`, `net/` and `drivers/staging/`.
- `UNDOCUMENTED_SETUP`: runs only on added lines of `.c` and `.h` files.
- `MODULE_PARM_DESC()`: `scripts/checkpatch.pl` has no check that a module
  parameter has one.
- Module parameter permissions in `scripts/checkpatch.pl`: there is no
  OCTAL_PERMS type; the types are as follows.

| Type | Level | Fires on |
|---|---|---|
| `NON_OCTAL_PERMISSIONS` | `ERROR()` | decimal value, or octal not 4 digits long; a bare `0` is exempt for `module_param` |
| `EXPORTED_WORLD_WRITABLE` | `ERROR()` | octal value with the world-write bit |
| `SYMBOLIC_PERMS` | `WARN()` | a symbolic permission macro such as `S_IRUGO`, on any added line |
