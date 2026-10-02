- `MODULE_PARAM_PREFIX` override: `include/linux/moduleparam.h` defines it
  with no `#ifndef` guard, so a file overrides it after the include, with
  `#undef` first, as `kernel/rcu/tree.c` does.
- Empty prefix: no file overrides `MODULE_PARAM_PREFIX` to empty; only
  `include/linux/moduleparam.h` defines it empty, under `MODULE`.
  `core_param()` passes `""` to `__module_param_call()` itself.
- `kernel/printk/printk.c` and `kernel/workqueue.c`: do not override
  `MODULE_PARAM_PREFIX`; `printk.` and `workqueue.` come from the object
  basename.
- Object that is part of a composite (`foo-y` or `foo-objs`): `KBUILD_MODNAME`
  is the composite's name, built in or not; see `modname-multi` in
  `scripts/Makefile.lib`.
- Loadable module, value on the kernel command line: the kernel keeps nothing
  for the module. `load_module()` in `kernel/module/main.c` calls
  `parse_args()` only on the argument string userspace passed to the load
  syscall.
- Unknown parameter name at load: `unknown_module_param_cb()` prints
  "unknown parameter ... ignored" and returns 0; the load continues.
- Declared parameter whose `set` fails at load: `parse_args()` returns an
  `ERR_PTR()` and `load_module()` fails the load.
