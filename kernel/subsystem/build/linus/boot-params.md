# Boot Parameters

## Main structures

### Objects and how they relate

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

## Defining a parameter

**Defining macros**

| Macro | Command-line prefix | sysfs | File built as a module |
|---|---|---|---|
| `__setup()` | none | none | defined as nothing under `MODULE` in `include/linux/init.h`: no `.init.setup` entry, handler never called; the use itself compiles |
| `early_param()` | none | none | not defined under `MODULE`; a use does not build |
| `core_param()` | none | `/sys/module/kernel/parameters/<name>` if `perm` is non-zero; see `param_sysfs_builtin()` in `kernel/params.c` | not defined under `MODULE` in `include/linux/moduleparam.h`; a use does not build |
| `module_param()` | `MODULE_PARAM_PREFIX` | if `perm` is non-zero. Built in: `/sys/module/<text before the first "." of the full name>/parameters/<rest>`, so a file that overrides `MODULE_PARAM_PREFIX` moves the directory. Module: `/sys/module/<mod->name>/parameters/<full name>` | default prefix is empty and the value comes from the load arguments. A file that defines `MODULE_PARAM_PREFIX` unconditionally keeps that prefix in the module too, in both the load argument name and the sysfs file name; `drivers/mmc/core/block.c` is such a file |

**Module parameters at boot**

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

## Parsing at boot

**Order of parsing**

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

**Matching and handler arguments**

- `do_early_param()`: has no special case for `console`; the test is only
  `p->early && parameq(param, p->str)`.
- `console=` reaching earlycon: a separate `early_param("console", ...)`,
  `param_setup_earlycon_console_alias()` in `drivers/tty/serial/earlycon.c`.
- `obsolete_checksetup()`: always a prefix match,
  `parameqn(line, p->str, strlen(p->str))`; there is no whole-word compare for
  `__setup()` strings without `=`.
- `__setup("foo", fn)`: also matches `foobar` and `foo-bar`; `-` and `_` are
  equal here too.
- `__setup()` handler argument: `line + strlen(p->str)`, so
  `__setup("foo", fn)` gets `"=bar"` for `foo=bar` and `""` for `foo`, never the
  whole word and never NULL.
- Bare word matching a `struct kernel_param` whose level is in the pass:
  `parse_one()` returns `-EINVAL` without calling the set function unless the
  ops have `KERNEL_PARAM_OPS_FL_NOARG`; only then does set receive NULL.
- Parameter whose level is outside the pass: `parse_one()` returns 0, so the
  word is consumed and no unknown handler sees it.

**Words matching several registrations**

- `__setup()` strings that overlap as prefixes: each matching entry is called
  in table order; the first to return non-zero ends the walk, so a shorter
  string linked earlier can claim a word meant for a longer one.
- Early entry in `obsolete_checksetup()`: not called; if its string equals the
  word's name (next character `\0` or `=`) it sets `had_early_param`.
- `had_early_param`: is the return value when no `__setup()` handler claimed
  the word, so the word counts as handled and is not passed to init.

**Handler return values**

- `__setup()` handler returning 0 for a bad value: the word is treated as
  unclaimed; see "Unclaimed words".
- `__setup()` example returning 1: `set_reset_devices()` and `init_setup()` in
  `init/main.c`; `quiet_kernel()` and `debug_kernel()` are `early_param()`
  handlers and return 0.
- `early_param()` handler returning non-zero: only the `pr_warn()`;
  `obsolete_checksetup()` still counts the word as handled.
- `parse_args()` after a failing word: goes on to the next word; `err` is
  overwritten each time, so the value returned is the last error.
- `parse_args()` messages: "Unknown parameter" for `-ENOENT`, "too large for
  parameter" for `-ENOSPC`, "invalid for parameter" for any other non-zero
  value.
- Set function returning a positive value: logged as invalid and stored with
  `ERR_PTR()`; `IS_ERR_OR_NULL()` in `start_kernel()` does not recognise it, so
  if it is the last error `start_kernel()` passes it to `parse_args()` as the
  init-argument string.

**Init arguments after an error**

- `parse_args()`: does not stop at the failing word; it parses up to `--` and
  there returns `err ?: args`.
- Words after `--`: `start_kernel()` skips them when `after_dashes` is an
  error (`IS_ERR_OR_NULL()` test); nothing is logged about them, the only
  message is the `pr_err()` for the failing word.
- `extra_init_args` from bootconfig: still passed to `set_init_arg()`; that
  call does not test `after_dashes`.
- Source of the error: only a word whose name matches a `struct kernel_param`
  of level -1, because `unknown_bootoption()` returns 0 on every path.

**Unclaimed words**

- `unknown_bootoption()` tests, in order:
  - `sysctl_is_alias()` on the name alone: claimed, `unknown_bootoption()`
    returns 0.
  - `repair_env_string()`.
  - word starts with `BOOT_IMAGE=` or `kexec`: dropped.
  - `obsolete_checksetup()`.
  - `.` in the name: dropped.
  - `panic_later` set: dropped.
- `kexec` test: `strstarts()`, so any word beginning with `kexec` is dropped
  before `obsolete_checksetup()` and is neither logged nor passed to init; a
  `__setup()` string with that start never runs.
- `.` test: covers the name only (`len` is taken before
  `repair_env_string()`); a `.` in the value does not count.
- `init_setup()` and `rdinit_setup()`: clear `argv_init[1]` onwards, so bare
  unknown words that came before `init=` or `rdinit=` are neither passed to
  init nor logged.
- `print_unknown_bootoptions()`: there is no counter; it returns early when
  `panic_later` is set or when `argv_init[1]` and `envp_init[2]` are both
  NULL.
- Log output: one `pr_notice()` for all words, no line per word.
- Logged text: the words as modified in place in `static_command_line`
  (quotes stripped), not text from `saved_command_line`.

**Value parsing helpers**

- `memparse()` on overflow: returns `ULLONG_MAX`, both when the digits
  overflow (`_parse_integer_limit()` saturates) and when the suffix shift does
  (`check_shl_overflow()`); `*retptr` advances as for a valid value.
- `cpulist_parse()`: returns `-EINVAL`, `-ERANGE` or `-EOVERFLOW`; see
  `bitmap_parselist()` in `lib/bitmap-str.c`.
- `cpulist_parse()` on error: the mask was zeroed first and holds the regions
  parsed before the bad one.
- Integer `param_set_` functions built by `STANDARD_PARAM_DEF()`: return what
  the kstrto helper returns, for example `kstrtouint()`: `-EINVAL` for a parse
  error and `-ERANGE` for a value that does not fit the type.
- `-EPERM`: comes from `parse_one()` and `param_attr_store()` when
  `param_check_unsafe()` refuses, not from a `param_set_` function in
  `kernel/params.c`.
- Array parameters: `param_array()` writes each element as it parses, so on
  an error the earlier elements and `*num` are already changed.

**Input the helpers accept**

- `kstrtobool()`: also accepts `e` and `E` as true, `d` and `D` as false, on
  the first character alone.
- `memparse()` suffix with no number before it (for example `K`): the suffix
  is not consumed; the result is 0 and `*retptr == ptr`.

**Environment of early handlers**

- Call site: not always `setup_arch()`; for example powerpc calls
  `parse_early_param()` from `early_init_devtree()` in
  `arch/powerpc/kernel/prom.c`.
- `parse_early_options()`: runs the early handlers on any string and is not
  covered by the `done` flag; `sh_early_platform_driver_register_all()` in
  `arch/sh/drivers/platform_early.c` calls it directly.
- Static keys: generic code orders `jump_label_init()` before
  `parse_early_param()` only in `start_kernel()`; an architecture that parses
  earlier has that order only if it calls `jump_label_init()` itself.
- Architectures that parse without calling `jump_label_init()` first: for
  example arm and mips; search `arch/` for both names to see the rest.
- memblock: not guaranteed; for example `parse_early_param()` runs before
  `e820__memblock_setup()` on x86 and before `arm_memblock_init()` on arm.
- **Potentially unsafe usage**: calling `static_branch_enable()` or
  `static_branch_disable()` from an `early_param()` handler.
  - Unsafe: when the handler can be built for an architecture that calls
    `parse_early_param()` without `jump_label_init()` before it;
    `STATIC_KEY_CHECK_USE()` in `include/linux/jump_label.h` warns.
  - Safe: when the handler is built only where `jump_label_init()` comes
    first, as `early_randomize_kstack_offset()` in `init/main.c`, which
    depends on `HAVE_ARCH_RANDOMIZE_KSTACK_OFFSET`.
  - Safe: store the value and flip the key later, as `early_init_on_alloc()`
    with `mem_debugging_and_hardening_init()` in `mm/mm_init.c`.

**Lifetime of the value string**

- `static_command_line`: a copy of the `command_line` that `setup_arch()`
  returned, after `extra_command_line`; not a copy of `boot_command_line`.
- Per-level set functions: the buffer is the `kzalloc()` copy local to
  `do_initcalls()`; it is overwritten before the next level and freed with
  `kfree()` after the last.
- Module load: there is no mod->args here; `load_module()` passes a local
  `args` from `strndup_user()` and calls `kfree()` on it right after
  `parse_args()`.
- sysfs write: `param_attr_store()` passes the sysfs buffer to the set
  function.
- `param_set_charp()`: the test is `slab_is_available()`; it keeps the raw
  pointer only when that is false.
- **Potentially unsafe usage**: keeping the `char *` passed to a handler after
  the handler returns.
  - Unsafe: in an `early_param()` handler, when the pointer is read after
    `free_initmem()`; `tmp_cmdline` in `parse_early_param()` is `__initdata`.
  - Unsafe: in a set function, when `slab_is_available()` is true; the
    buffer is then one of the three short-lived ones above.
  - Safe: in a `__setup()` handler; `static_command_line` comes from
    `memblock_alloc_or_panic()` in `setup_command_line()` and is not freed,
    as `init_setup()` relies on for `execute_command`.
  - Safe: in an `early_param()` handler whose text is read only by `__init`
    code, before `free_initmem()`; `hugetlb_add_param()` in `mm/hugetlb.c`
    copies it to `hstate_cmdline_buf`, also `__initdata`, for
    `hugetlb_parse_params()`.
  - Safe: in a set function that copies whenever `slab_is_available()` is
    true, as `param_set_charp()` does.

## Documenting a parameter

**Submit checklist and checkpatch**

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

**Parameter list and entries**

- Order: `Documentation/admin-guide/kernel-parameters.rst` defines it as
  "English Dictionary order": ignore all punctuation, digits before letters,
  case insensitive; "alphabetical" alone is not the whole rule.
- Order is not checked by any script, and the list in
  `Documentation/admin-guide/kernel-parameters.txt` is not fully sorted; for
  example `autoconf=` sits between `apicpmtimer` and `apm=`. Place a new
  entry by the rule, not by its neighbours.
- Form stated by the `.rst`: only three things, namely the bracketed text at
  the start of the description, the trailing `=`, and that names are case
  sensitive. Tabs, `Format:` lines and column layout are convention.
- Trailing `=`: the `.rst` words it as "will be entered as an environment
  variable", and its absence as a kernel argument readable via
  `/proc/cmdline`; it does not say "takes a value".
- Description lines: the prevailing indent in the `.txt` is three tabs, with
  the name at one tab.
- Bracketed tags: may be on the name line or on the next line, and some
  entries have none, for example `apicpmtimer`.

**Restriction tags**

- Tag definitions: the list is at the head of
  `Documentation/admin-guide/kernel-parameters.txt`, ahead of the line
  "Kernel parameters"; it is not in
  `Documentation/admin-guide/kernel-parameters.rst`.
- `Documentation/admin-guide/kernel-parameters.rst`: holds only the sentence
  that bracketed text states restrictions, and the paragraph on `BOOT`.
- `EARLY`: defined as "Parameter processed too early to be embedded in
  initrd."; it states a consequence and names neither `early_param()` nor
  `parse_early_param()`.
- `EARLY` is in use throughout the `.txt`, for example
  `acpi=		[HW,ACPI,X86,ARM64,RISCV64,EARLY]`.
- Undefined tags: entries use tags that have no line in the list, for example
  `MM` and `KEYS`; a tag in an entry is not proof that it is defined.

## Model gaps

### Other mistakes models make

- Models take every boolean parameter to accept a bare word. In
  `kernel/params.c` only `param_ops_bool`, `param_ops_bool_enable_only` and
  `param_ops_bint` set `KERNEL_PARAM_OPS_FL_NOARG`; `param_ops_invbool` and
  ops built by `module_param_call()` do not, so `parse_one()` gives `-EINVAL`.
- Models take `core_param_cb()` to be `core_param()` with custom ops. It is
  the level 1 macro and keeps `MODULE_PARAM_PREFIX`; the unprefixed level -1
  form is `__core_param_cb()` in `include/linux/moduleparam.h`, as
  `kernel/panic.c` uses.
- Models take `scripts/checkpatch.pl` to check a `__setup()` name against the
  tree. `UNDOCUMENTED_SETUP` searches only the `+` lines the same patch adds
  to `Documentation/admin-guide/kernel-parameters.txt`.
- Models take any string to be a legal `MODULE_PARAM_PREFIX`.
  `__module_param_call()` has a `static_assert` that the prefix is no longer
  than `__MODULE_NAME_LEN`.
- Models take the command line to be parsed only from `start_kernel()` and
  `do_initcall_level()`. `dynamic_debug_init()` (an `early_initcall`) and
  `bootconfig_cmdline_requested()` each run their own `parse_args()` pass;
  search for `parse_args(` to list the rest.
- Models take `hugepages`, `hugepagesz` and `default_hugepagesz` to be
  handled when parsed. `hugetlb_early_param()` in `mm/hugetlb.c` only copies
  the value; `hugetlb_parse_params()` runs the real handlers later.
- Models take "Kernel command line:" to be one log line.
  `print_kernel_cmdline()` in `init/main.c` splits it at spaces according to
  `CONFIG_CMDLINE_LOG_WRAP_IDEAL_LEN`, each piece with the prefix repeated.
