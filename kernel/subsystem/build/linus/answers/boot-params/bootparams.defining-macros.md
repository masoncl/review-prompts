| Macro | Command-line prefix | sysfs | File built as a module |
|---|---|---|---|
| `__setup()` | none | none | defined as nothing under `MODULE` in `include/linux/init.h`: no `.init.setup` entry, handler never called; the use itself compiles |
| `early_param()` | none | none | not defined under `MODULE`; a use does not build |
| `core_param()` | none | `/sys/module/kernel/parameters/<name>` if `perm` is non-zero; see `param_sysfs_builtin()` in `kernel/params.c` | not defined under `MODULE` in `include/linux/moduleparam.h`; a use does not build |
| `module_param()` | `MODULE_PARAM_PREFIX` | if `perm` is non-zero. Built in: `/sys/module/<text before the first "." of the full name>/parameters/<rest>`, so a file that overrides `MODULE_PARAM_PREFIX` moves the directory. Module: `/sys/module/<mod->name>/parameters/<full name>` | default prefix is empty and the value comes from the load arguments. A file that defines `MODULE_PARAM_PREFIX` unconditionally keeps that prefix in the module too, in both the load argument name and the sysfs file name; `drivers/mmc/core/block.c` is such a file |
