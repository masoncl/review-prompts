- "Booting kernel" pass, per word: `parse_one()` tries the `struct kernel_param`
  table first; `unknown_bootoption()` → `obsolete_checksetup()` runs only when
  no parameter name matches.
- `__setup()` handlers and level -1 set functions therefore run interleaved, in
  command-line order, not grouped by kind.
- Per-level buffer: there is no initcall_command_line in this tree;
  `do_initcalls()` owns a local `kzalloc()` buffer and copies
  `saved_command_line` into it before each call of `do_initcall_level()`.
- Level other than -1: set only by the `__level_param_cb()` wrappers in
  `include/linux/moduleparam.h`, which cover levels 1 to 7.
- `core_param()`: level -1, parsed in the "Booting kernel" pass;
  `core_param_cb()` is level 1.
- Bootconfig `kernel` keys: `setup_command_line()` puts them in
  `static_command_line` and `saved_command_line`, not in `boot_command_line`;
  `parse_early_param()` parses a copy of `boot_command_line`, so
  `early_param()` handlers do not run for them.
- `CONFIG_CMDLINE_FROM_BOOTCONFIG` (x86): `setup_arch()` calls
  `xbc_prepend_embedded_cmdline()` on `boot_command_line` before
  `parse_early_param()`, when `bootconfig_cmdline_requested()` is true or
  `CONFIG_BOOT_CONFIG_FORCE` is set, so early handlers do see the embedded
  keys.
