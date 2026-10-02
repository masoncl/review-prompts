- `saved_command_line`: not an untouched copy when bootconfig applies;
  `setup_command_line()` in `init/main.c` builds it as `extra_command_line`,
  then `boot_command_line`, with `extra_init_args` placed right after the
  ` -- `, ahead of any init arguments `boot_command_line` has.
- `static_command_line`: does not contain `extra_init_args`, which
  `start_kernel()` parses separately with `set_init_arg()`.
- `CONFIG_CMDLINE_FROM_BOOTCONFIG`: the build renders the `kernel` subtree of
  the embedded bootconfig to a flat string (`lib/embedded-cmdline.S`), and
  `setup_arch()` in `arch/x86/kernel/setup.c` prepends it to
  `boot_command_line` with `xbc_prepend_embedded_cmdline()`, so early handlers
  see those keys.
- `ARCH_SUPPORTS_CMDLINE_FROM_BOOTCONFIG`: selected only in `arch/x86/Kconfig`.
- `xbc_embedded_cmdline_applied()`: when true and the bootconfig came from the
  embedded copy, `setup_boot_config()` leaves `extra_command_line` unset, so the
  keys are not rendered twice.
- Bootconfig source: `setup_boot_config()` tries the initrd first, then
  `xbc_get_embedded_bootconfig()` (`CONFIG_BOOT_CONFIG_EMBED`).
- Bootconfig opt-in: `setup_boot_config()` and the x86 prepend each apply only
  if `bootconfig_cmdline_requested()` finds `bootconfig` before `--` in
  `boot_command_line`, or with `CONFIG_BOOT_CONFIG_FORCE`.
- `struct xbc_node` tree: only the `kernel` and `init` subtrees become
  command-line text; other keys are read from the tree itself, for example by
  `kernel/trace/trace_boot.c` and `fs/proc/bootconfig.c`.
- `console`: `drivers/tty/serial/earlycon.c` registers
  `early_param("console", ...)` beside `__setup("console=", ...)` in
  `kernel/printk/printk.c`, so one name has an entry of each kind.
- `parse_args()`: has no prefix argument; a built-in parameter's prefix is part
  of its `name` string through `MODULE_PARAM_PREFIX`, whose default is empty
  under `MODULE`.
- `load_module()`: passes `mod->name` to `parse_args()` only as the `doing`
  label.
- `load_module()` level range: -32768 to 32767, so `level` has no effect on a
  loadable module's parameters.
- Main pass in `start_kernel()`: runs before `mm_core_init()`, which calls
  `kmem_cache_init()`, so `__setup()` handlers and level -1 `->set` methods run
  at boot without the slab allocator; `param_set_charp()` tests
  `slab_is_available()` for this.
- Later re-parses: `do_initcalls()`, `do_sysctl_args()` in
  `fs/proc/proc_sysctl.c` and `dynamic_debug_init()` in `lib/dynamic_debug.c`
  each parse a fresh copy of `saved_command_line`, not `static_command_line`,
  so they see bootconfig `kernel` keys too.
- `parse_one()`: takes `kernel_param_lock()` around every `->set`, at boot as
  well as at module load; both lock functions are empty stubs without
  `CONFIG_SYSFS`.
- `struct module_kobject` for built-in code: created by
  `lookup_or_create_module_kobject()`, which `version_sysfs_builtin()` and
  `module_add_driver()` in `drivers/base/module.c` also call, so one can exist
  with no parameters.
- `param_sysfs_init()`: only creates `module_kset`, at `pure_initcall`; the
  built-in parameter files are created by `param_sysfs_builtin_init()` at
  `late_initcall`.
