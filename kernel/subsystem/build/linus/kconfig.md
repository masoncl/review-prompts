# Kconfig

## Main structures

### Objects and how they relate

- Front-end programs: `conf`, `mconf`, `nconf`, `qconf`, `gconf`; `menuconfig`,
  `xconfig` and `gconfig` are make targets, mapped in
  `scripts/kconfig/Makefile`.
- `conf_write_autoconf()` in `scripts/kconfig/confdata.c`: also writes
  `include/generated/rustc_cfg`.
- Choice: a `struct symbol` whose `name` is NULL, tested by `sym_is_choice()`;
  there is no SYMBOL_CHOICE flag.
- Choice symbol: `sym_lookup(NULL, 0)` allocates a new one for each `choice`
  block, so it has exactly one `struct menu`.
- Choice state: the member list `choice_members` lives on the choice's
  `struct menu`, not on its symbol; `sym_calc_choice()`,
  `sym_choice_default()` and `choice_set_value()` take the menu node and
  return or accept the member symbol.
- Choice to members: two routes. `menu_for_each_sub_entry()` gives Kconfig
  order; the `choice_members` list (linked through `choice_link` in each
  member) gives priority order, which, for example, `choice_set_value()` and
  `conf_read_simple()` reorder with `list_move()`.
- Member to choice: `sym_get_choice_menu()` walks `parent` from the member's
  node that has a prompt; `sym_is_choice_value()` tests `choice_link` instead.
- Unquoted literal such as a number in `range` or `default`: an ordinary
  `struct symbol` of type `S_UNKNOWN` without `SYMBOL_CONST`;
  `sym_calc_value()` gives it its own name as string value.
- Quoted word: a separate `struct symbol` with `SYMBOL_CONST`, in the same
  hash table as a non-constant symbol of the same name.
- `enum prop_type`: has no help and no choice kind; help text is `help` on
  `struct menu`, one per definition site.
- `struct property` of a node without a symbol (`menu`, `comment`,
  `rootmenu`): on no symbol's list; reachable only through `menu->prompt`.
- `struct property` fields: `expr` is the payload (default value, selected
  symbol, range pair) and `visible.expr` is the `if` condition; the comment
  on `expr` in `scripts/kconfig/expr.h` says otherwise, see
  `menu_add_prop()` in `scripts/kconfig/menu.c`.
- `visible if` of enclosing menus: ANDed at parse time by `menu_add_prompt()`
  into a prompt added as `P_PROMPT`, and into no other property kind; a
  `menuconfig` prompt is added as `P_PROMPT` and retyped `P_MENU` afterwards,
  so it has them too.
- `dep` of the node and its ancestors: ANDed into every property condition of
  that node later, by `_menu_finalize()`.
- `dir_dep` is not built for a choice that has entries, or for a direct child
  of a choice node.
- Menu tree after `menu_finalize()`: children of a promptless node are moved
  up to follow it as siblings, so an `if` node (`M_IF`) ends up with no
  children.
- `struct expr`: interned; `expr_lookup()` in `scripts/kconfig/expr.c` is the
  only allocator and returns the existing node for an equal (type, left,
  right), so pointer equality means structural equality.
- `struct expr` nodes are never freed, and their `type`, `left` and `right`
  never change; the transform helpers, for example `expr_transform()` and
  `expr_eliminate_dups()`, return a node and leave the node they were given
  as it was.
- `struct expr` value: each node caches its tristate result until
  `expr_invalidate_all()`, which `sym_clear_all_valid()` calls.
- `struct file`: private to `scripts/kconfig/util.c`; `file_lookup()` uses it
  to intern file names and to exit on a repeated inclusion.
- Include stack: `struct buffer` in `scripts/kconfig/lexer.l`; `struct menu`
  and `struct property` hold only a `filename` string and a `lineno`.
- There is no struct kconf_id in this tree.

## References to undefined symbols

**Checking symbol references**

- Two scripts do this job; there is no "checkkconfigsymbols" make target.

| | `scripts/kconfig/kconfig-sym-check.pl` | `scripts/checkkconfigsymbols.py` |
|---|---|---|
| Run as | `make kconfig-sym-check` | by hand, from the top of a git checkout |
| Scans | Kconfig files only | Kconfig files, plus `CONFIG_` names in the other tracked files outside `tools/` |
| Kconfig lines read | `default`, `def_bool`, `def_tristate`, `select`, `imply`, `depends on`, `visible if`, `range`, `if`, and the condition after a type or `prompt` | lines that start with `if`, `select`, `imply`, `depends on` or `default` |
| git | not needed; falls back to `find` | needed, for `git ls-files` |
| Output | bare names on stdout, no file names | name, referencing files, similar symbols |
| Exit status | 1 if any name is reported, so the make target fails | 0 even when names are reported |

- `KCONFIG_SYM_CHECK_EXCLUDES`: optional make variable for
  `kconfig-sym-check`, naming a file of symbol names to accept, one per line,
  `#` for comments.
- No exclude file ships in the tree.
- `scripts/kconfig/kconfig-sym-check.pl` adds a hint when the name is `N`, `Y`
  or `M`: the tristate literals are lowercase.
- `scripts/checkkconfigsymbols.py` has no "--yes" or "--missing" option.
- `--find` lists the commits that touch each reported symbol. It needs
  `--diff`, and `--commit` turns it off.
- `--commit` and `--diff` run `git reset --hard` on the working tree.
- Both scripts count a name as defined if any Kconfig file they read has a
  `config` or `menuconfig` entry for it. Neither knows which files an
  architecture sources.
- `KCONFIG_WARN_UNKNOWN_SYMBOLS` checks the input `.config`, not references. It
  is exported when the make variable `W` (`KBUILD_EXTRA_WARN`) contains `c`;
  see `scripts/kconfig/Makefile`.
- `KCONFIG_WARN_UNKNOWN_SYMBOLS` stays silent for a `.config` name that some
  Kconfig expression references but no entry defines. `sym_find()` in
  `conf_read_simple()` returns the `S_UNKNOWN` symbol the reference created,
  and the line is dropped.
- The configurators have no check of their own for undefined references. The
  few warnings that can appear are listed under "Value of an undefined symbol".

**Value of an undefined symbol**

- `sym_calc_value()` on an undefined name: string value is the name itself, not
  the empty string; tristate value is `no`.
- `UNDEF = ""` is false. `UNDEF = n` is also false, although `!UNDEF` is y.
- `depends on X if UNDEF`: `menu_add_dep()` turns the condition into
  `UNDEF = n`, which is false. The dependency on `X` therefore applies, as if
  `UNDEF` were set.
- `depends on X if !UNDEF`: the dependency on `X` is dropped.
- `sym_check_prop()` is called from `_menu_finalize()` in
  `scripts/kconfig/menu.c`, once for each symbol that has an entry. It has no
  check for a missing prompt.
- `sym_check_prop()` prints a warning for an undefined name in three positions:

| Position | Warning | Value used |
|---|---|---|
| `default UNDEF` in an int or hex entry | "number is invalid" | the name, as a string |
| `range` bound | "range is invalid" | `strtoll()` of the name |
| `default UNDEF` in a `choice` | "choice default symbol ... is not contained in the choice" | default skipped |

- `menu_validate_number()` decides the first two. It accepts an `S_UNKNOWN`
  symbol whose name passes `sym_string_valid()` for the entry's type, whether
  quoted or not.
- A hex entry with `default FACE`, where `FACE` is undefined, therefore gets no
  warning.
- A string entry with `default UNDEF` gets no warning and takes the name as its
  value.
- These warnings go through `prop_warn()`, which `KCONFIG_WERROR` does not
  count. Configuration continues.
- `KCONFIG_WERROR` counts only `conf_warning()` in
  `scripts/kconfig/confdata.c` and `sym_warn_unmet_dep()`. Only
  `scripts/kconfig/conf.c` calls `conf_errors()` and `sym_dep_errors()`, so the
  menu front ends ignore it.
- **Potentially unsafe usage**: `depends on` naming a symbol that the Kconfig
  files read in this run do not define.
  - Unsafe: when no Kconfig file in the tree defines the name (misspelt,
    renamed or removed). The name is `n` on every architecture, so an entry
    with a plain `depends on UNDEF` is dead everywhere, and nothing is printed.
    `scripts/kconfig/kconfig-sym-check.pl` reports these names.
  - Safe: when the name is defined only under another architecture, which
    `arch/Kconfig` reaches through `source "arch/$(SRCARCH)/Kconfig"`. For
    example `depends on X86` in `drivers/vfio/pci/Kconfig` relies on
    `sym_calc_value()` giving `no` for the undefined `X86` elsewhere; `X86` is
    defined only in `arch/x86/Kconfig`.

## Value of a symbol

**Precedence of value sources**

- Default, used when there is no user value or `sym->visible` is `no`: capped
  by its own `prop->visible.tri`, not by `sym->dir_dep.tri`.
- `sym->dir_dep.tri`: ANDed in only inside the `sym->implied.tri != no` branch
  of `sym_calc_value()`.
- File value above `sym->visible`, with `sym->visible` not `no`: lowered to
  `sym->visible`, not discarded.
- `conf_read()` in `scripts/kconfig/confdata.c`: does not call
  `sym_set_tristate_value()`; on a mismatch between file value and computed
  value it only calls `conf_set_changed(true)`.
- `sym_calc_value()` on a dropped or changed file value: prints nothing; the
  only warning it prints is `sym_warn_unmet_dep()`.
- `KCONFIG_WARN_CHANGED_INPUT` set to a non-empty value: `conf_write()` and
  `conf_write_defconfig()` print to stderr
  "warning: user-provided values changed by Kconfig:", then one line per
  symbol in the form "  CONFIG_A: y -> n".
- Symbols reported: those with `SYMBOL_DEF_USER` whose stored user value
  differs from the computed one; see `sym_user_value_changed()`.
- `KCONFIG_WERROR`: `sym_warn_unmet_dep()` counts toward it through
  `sym_dep_errors()`; the changed-input warning does not, since
  `conf_changed_input_warning()` only calls `fputs()`.

**Default properties**

- Tristate value of the chosen default:
  `EXPR_AND(expr_calc_value(prop->expr), prop->visible.tri)` in
  `sym_calc_value()`.
- `prop->visible.expr`: the line's `if` ANDed with the entry's dependencies,
  built in `_menu_finalize()` in `scripts/kconfig/menu.c`.
- The line's `if` lowers the value as well as selecting the line: in a
  tristate symbol, `default y if FOO` with `FOO=m` gives `m`.
- Default that is a single `transitional` symbol holding a user value:
  `sym_calc_value()` stores the result in `sym->def[S_DEF_USER]` and sets
  `SYMBOL_DEF_USER`, so the symbol now counts as having a user value.
- int and hex with no active default and no usable user value:
  `sym_calc_value()` gives `"0"` for `S_INT` and `"0x0"` for `S_HEX`, not an
  empty string; only `S_STRING` starts empty. `sym_validate_range()` then
  moves it into an active `range`.

**Default value policy**

- `Documentation/kbuild/kconfig-language.rst` has the policy, in the paragraph
  and note that follow the `default` attribute.
- `Documentation/process/submit-checklist.rst`, "Review Kconfig changes": says
  new or modified options "default to off" unless they meet the exception
  criteria, and points to `Documentation/kbuild/kconfig-language.rst`.
- `Documentation/process/coding-style.rst`, section
  "10) Kconfig configuration files": covers indentation and marking dangerous
  features in the prompt, has no default-value policy, and points to
  `Documentation/kbuild/kconfig-language.rst`.
- Cases the note lists as meriting "default y/m":

  | Case | Value the note names |
  |---|---|
  | a) new option for something that used to always be built | `default y` |
  | b) new gatekeeping option that hides or shows other options and generates no code | `default y` |
  | c) sub-driver behavior or similar options for a driver that is `default n` | none named |
  | d) hardware or infrastructure everybody expects, such as `CONFIG_NET` or `CONFIG_BLOCK`; "rare exceptions" | none named |

- `default m`: appears only in the heading "default y/m"; no case names it.
- Drivers needed for a platform to boot: not among the listed cases; the only
  hardware case is d), hardware "that everybody expects".

## Select and compile testing

**Select semantics**

- Selects made by the selected symbol: each term is the selecting symbol ANDed
  with that entry's own dependencies (`dep` starts from `menu->dep` in
  `_menu_finalize()`, `scripts/kconfig/menu.c`). A symbol forced on while its
  dependencies are `n` passes `n` to its own selects; they follow only up to
  the minimum of its value and its dependencies.
- Choice member as target: `select` has no effect and never warns.
  `sym_calc_value()` in `scripts/kconfig/symbol.c` takes the value from
  `sym_calc_choice()` and does not OR in `rev_dep.tri`.
- Target not defined on the architecture being configured: the select does
  nothing and prints nothing. `sym_check_prop()` accepts a target of type
  `S_UNKNOWN`; `sym_calc_value()` leaves it at `no`.

**Unmet dependency warning**

- `make W=e`: sets `KCONFIG_WERROR`. `Makefile` copies `W` into
  `KBUILD_EXTRA_WARN`; `scripts/kconfig/Makefile` exports `KCONFIG_WERROR=1`
  when that contains `e`.
- `CONFIG_WERROR`: not tested by `scripts/kconfig/Makefile`; `Makefile` reads
  no variable named WERROR.
- `KCONFIG_WERROR` value: any value counts, including `0` and empty;
  `sym_dep_errors()` returns the `getenv()` result as a bool.
- Front ends: only `conf` calls `sym_dep_errors()`. `mconf`, `nconf`, `qconf`
  and `gconf` print the warning and never exit on it.
- `sym_dep_errors()` in `main()` of `scripts/kconfig/conf.c`: tested once,
  before `conf_write()`; on a hit `conf` exits 1 and writes no `.config`.
- Modes covered: those that call `conf_read()`, which evaluates every symbol,
  for example `olddefconfig`, `syncconfig` and `defconfig`.
- `allyesconfig`, `allmodconfig`, `allnoconfig`, `alldefconfig`, `randconfig`:
  do not call `conf_read()`; a warning first printed from `conf_write()` comes
  after the test and `conf` still exits 0.
- Bool target: `sym_calc_visibility()` promotes a `dir_dep` of `m` to `y`
  before the comparison, so a bool selected at `y` with a dependency at `m`
  does not warn; a tristate does.
- `Depends on` line: prints `[m]` when `dir_dep.tri` is `mod`, else `[n]`.
- `dir_dep` contents: the entry's `depends on` ANDed with every enclosing `if`
  and `menu` dependency; the `if` on a prompt is not part of it.
- Symbol defined in several places: `_menu_finalize()` ORs the dependencies of
  all definitions into `dir_dep.expr`; the warning needs all of them below
  `rev_dep.tri`.

**COMPILE_TEST**

- Documents with guidance: `Documentation/kbuild/kconfig-language.rst`
  (sections "Compile-testing" and "Architecture and platform dependencies"),
  the help text of `COMPILE_TEST` in `init/Kconfig`, and
  `Documentation/driver-api/gpio/consumer.rst`.
- `Documentation/kbuild/kconfig.rst` and `Documentation/process/`: say nothing
  about `COMPILE_TEST`.
- Asked of compile-tested code: only that it "should avoid crashing when run
  on a system where the dependency is not met".
- Building with the dependency unmet: the precondition for adding the clause,
  not a demand on the code; no document says the code must build on every
  architecture.
- Narrowing and ANDing: the documents give one form,
  `depends on ARCH_FOO_VENDOR || COMPILE_TEST`, and no rule on which
  dependencies stay outside it. In-tree entries narrow it, for example
  `HISI_PTT` with `depends on ARM64 || (COMPILE_TEST && 64BIT)`.
- `Documentation/driver-api/gpio/consumer.rst`: names compile coverage with
  `COMPILE_TEST` as one of two uses of the stubs in
  `include/linux/gpio/consumer.h`; it does not matter that the platform does
  not enable `GPIOLIB`.
- `COMPILE_TEST` in `init/Kconfig`: has `depends on HAS_IOMEM`.

**Selecting symbols with dependencies**

- **Potentially unsafe usage**: `select BAR` where `BAR` has dependencies.
  - Unsafe: when some configuration lets the select term exceed `BAR`'s
    dependencies; `sym_calc_value()` warns on `dir_dep.tri < rev_dep.tri` and
    still forces `BAR`. For a tristate `BAR`, the selector at `y` with the
    dependency at `m` is such a case.
  - Safe: the selector repeats the dependency, as `SENSORS_JC42` in
    `drivers/hwmon/Kconfig` does: `depends on I2C`, `select REGMAP_I2C`.
  - Safe: the select is conditional on the dependency, as `SENSORS_LM75` does:
    `select REGMAP_I3C if I3C`.
  - Safe: the selector also selects the dependency, as `DM_CRYPT` in
    `drivers/md/Kconfig` does: `select CRYPTO` beside `select CRYPTO_CBC`.
  - Safe: selector and target sit in the same `if` block and the target has
    no other dependency, as `GPIO_PL061` and `GPIOLIB_IRQCHIP` do inside
    `if GPIOLIB` in `drivers/gpio/Kconfig`.
- `SENSORS_LM75`: has `depends on I3C_OR_I2C`, not `depends on I2C`;
  `I3C_OR_I2C` is in `drivers/i3c/Kconfig`.
- Dependencies from an enclosing `if`: count like a `depends on` line.
  `CRYPTO_CBC` has none of its own but sits in `if CRYPTO`; `MTK_SMI` sits in
  `if MEMORY`, so `MTK_IOMMU` in `drivers/iommu/Kconfig` has `select MEMORY`.

**Selects in compile-tested drivers**

- **Potentially unsafe usage**: `select BAR` in a `config FOO` with
  `depends on ARCH_FOO_VENDOR || COMPILE_TEST`, where `BAR` depends on an
  architecture or platform.
  - Unsafe: when `BAR` is defined on the architecture being configured and its
    dependencies can be below `FOO` while `COMPILE_TEST=y`; `sym_calc_value()`
    warns and forces `BAR`.
  - Safe: the select is conditional on the architecture, as `HISILICON_LPC` in
    `drivers/bus/Kconfig` does: `select INDIRECT_PIO if ARM64`, where
    `INDIRECT_PIO` in `lib/Kconfig` has `depends on ARM64`.
  - Safe: the target carries `|| COMPILE_TEST` itself, as `MTK_SMI` in
    `drivers/memory/Kconfig` does for `select MTK_SMI` in `MTK_IOMMU`.
  - Safe: the target is defined only in one architecture's Kconfig and has no
    dependencies, as `ARM_DMA_USE_IOMMU` in `arch/arm/Kconfig` is for
    `ROCKCHIP_IOMMU`; elsewhere the symbol is undefined and the select does
    nothing, so the driver must build without it.
- Target's remaining dependencies: repeated on a separate `depends on` line,
  outside the `|| COMPILE_TEST`. `ARM_SMMU` has `depends on !GENERIC_ATOMIC64`
  because `IOMMU_IO_PGTABLE_LPAE` has it beside its
  `depends on ARM || ARM64 || COMPILE_TEST`; `HISILICON_LPC` repeats
  `depends on HAS_IOPORT`.
- `ARM_SMMU`: defined in `drivers/iommu/arm/Kconfig`, with
  `select ARM_DMA_USE_IOMMU if ARM`.
- `ROCKCHIP_IOMMU`: has plain `depends on ARCH_ROCKCHIP || COMPILE_TEST`; it
  does not narrow `COMPILE_TEST`.
- Placeholder names in `Documentation/kbuild/kconfig-language.rst`: for
  example `FOO`, `BAR`, `BAZ` and `ARCH_FOO_VENDOR`; there is no ARCH_FOO.

## Modules and built-in code

**Generated configuration files**

- Rust, y or m: `print_symbol_for_rustccfg()` in `scripts/kconfig/confdata.c`
  writes two lines for both values, `--cfg=CONFIG_FOO` and then
  `--cfg=CONFIG_FOO="y"` or `--cfg=CONFIG_FOO="m"`; a bare cfg test on the
  symbol is therefore true for m as well.
- Rust, n: no line.
- Rust, int: `--cfg=CONFIG_FOO="42"`; every value is quoted and escaped.
- There is no print_symbol_for_rustc_cfg() here; the Rust printer is
  `print_symbol_for_rustccfg()`.
- make, string: `include/config/auto.conf` gets `CONFIG_FOO=a b`, with no
  quotes and no escaping (`print_symbol_for_autoconf()` passes `escape_string`
  as false); makefiles use the value as is.
- Quoted and escaped strings: in `.config` (`print_symbol_for_dotconfig()`),
  in C and in Rust.
- make, hex: written as stored; only `print_symbol_for_c()` and
  `print_symbol_for_rustccfg()` add `0x` when it is missing.
- C, n: `print_symbol_for_c()` writes nothing, not even a comment;
  `# CONFIG_FOO is not set` comes only from `print_symbol_for_dotconfig()`.
- `conf_write_autoconf()` writes no tristate.conf and no per-symbol `.h` files;
  `conf_touch_deps()` touches empty files under `include/config/` named after
  the symbol with no suffix.
- `SYMBOL_WRITE` on a symbol with no visible prompt: `sym_calc_value()` still
  sets it when the symbol is selected, implied, has a default that is not n,
  or (numeric and string) has a default that applies; such symbols appear in
  `include/generated/autoconf.h`, `include/generated/rustc_cfg` and
  `include/config/auto.conf`, unless a bool or tristate ends at n.
- Numeric symbol with unmet dependencies: no `#define` is written; used in
  `#if` in C it evaluates as 0 and warns, because `-Wundef` is in the
  always-enabled set in `scripts/Makefile.warn`.

**Bool symbols below tristate symbols**

- `select LIB` in a bool with `depends on PARENT`, PARENT=m: the term added to
  the reverse dependency of LIB is `BOOL && PARENT`, which is `y && m` = m; a
  tristate LIB is forced to at least m, not to y. See the `P_SELECT` branch of
  `_menu_finalize()` in `scripts/kconfig/menu.c`.
- Enclosing `if PARENT` or menu dependency: same result, because
  `_menu_finalize()` ANDs the parent's dependency into the term.
- Term that evaluates to y while PARENT=m: when the bool's dependencies
  evaluate to y, for example a comparison such as `PARENT != n` (comparisons
  give y or n in `__expr_calc_value()`), or no tristate dependency at all.
- **Potentially unsafe usage**: a bool that depends on a tristate PARENT and
  selects a tristate LIB whose functions the bool's code calls.
  - Unsafe: when the bool's objects are linked into vmlinux while PARENT=m;
    LIB may then be only m, and built-in code references symbols that exist
    only in a module.
  - Safe: when the bool's objects are part of PARENT's composite object, so
    they are modular whenever LIB is; `SQUASHFS_ZLIB` in `fs/squashfs/Kconfig`
    selects `ZLIB_INFLATE`, and `fs/squashfs/Makefile` adds its object with
    `squashfs-$(CONFIG_SQUASHFS_ZLIB)`. `SQUASHFS_LZ4`, `SQUASHFS_XZ` and
    `SQUASHFS_ZSTD` follow the same form.
- `FS_ENCRYPTION` in `fs/crypto/Kconfig` and `BLK_DEV_INTEGRITY` in
  `block/Kconfig`: bools with no tristate dependency, so their selects force
  y; they are not examples of a bool below a tristate.

**Optional dependencies**

- `Documentation/kbuild/kconfig-language.rst`, "Optional dependencies",
  gives three spellings:
  - `depends on BAR if BAR`, the recommended one;
  - `depends on BAR || !BAR`, described as also widely used;
  - a helper symbol `BAR_OPTIONAL` with `def_tristate BAR || !BAR`, for
    several entries with the same dependency.
- Not in that section: a `BAR || BAR=n` spelling, and `imply`.
- Parser: the `depends` rule in `scripts/kconfig/parser.y` accepts
  `depends on <expr> if <expr>` and passes both to `menu_add_dep()`; the rule
  is shared by config, choice, menu and comment entries.
- `menu_add_dep()` in `scripts/kconfig/menu.c`: turns `depends on X if Y` into
  `X || (Y = n)`, built with `expr_trans_compare()`, not into `!Y || X`.
- Y=m: the condition counts as set and contributes n, so the entry is limited
  to X; `!Y || X` would have allowed at least m.
- `depends on BAR if BAR`: gives the same values as `BAR || !BAR`;
  `scripts/kconfig/tests/conditional_dep/` checks that `TEST_OPTIONAL=y` with
  `BAZ=m` becomes m.
- In-tree users: `MSHV_ROOT` in `drivers/hv/Kconfig` uses the conditional
  form; `PTP_1588_CLOCK_OPTIONAL` in `drivers/ptp/Kconfig` is a helper symbol,
  written with two `default` lines instead of `def_tristate`.

**IS_ENABLED and IS_REACHABLE**

- `Documentation/process/coding-style.rst`: recommends `IS_ENABLED()` in an
  ordinary C conditional; does not mention `IS_REACHABLE()`.
- `Documentation/kbuild/kconfig-language.rst`: mentions `IS_REACHABLE()` only
  in "Optional dependencies", not under `imply`; does not mention
  `IS_ENABLED()`.
- Wording on `IS_REACHABLE()`: a "much less favorable way" than the Kconfig
  dependency and "generally discouraged", because the code is silently
  discarded when BAR=m and the caller is built in.
- Stated use for `IS_REACHABLE()`: when BAR's header provides no stubs for
  the BAR=n case.
- `if (IS_REACHABLE(CONFIG_BAR))` in C: needs only a visible declaration; the
  header does not have to test `IS_REACHABLE()`. `include/linux/hwmon.h`
  declares its functions with no configuration test and no stubs, and
  `drivers/regulator/max5970-regulator.c` calls
  `devm_hwmon_device_register_with_info()` under
  `if (IS_REACHABLE(CONFIG_HWMON))`.
- **Potentially unsafe usage**: calling into tristate BAR from code guarded
  only by `IS_ENABLED(CONFIG_BAR)`, or by header stubs selected with
  `IS_ENABLED(CONFIG_BAR)`.
  - Unsafe: when Kconfig allows the caller to be y while BAR=m; the test is
    true (`IS_ENABLED()` in `include/linux/kconfig.h` includes `IS_MODULE()`)
    and vmlinux references a symbol that exists only in the module.
  - Safe: when the caller's entry carries the optional dependency;
    `HYPERV_UTILS` in `drivers/hv/Kconfig` depends on
    `PTP_1588_CLOCK_OPTIONAL`, and `include/linux/ptp_clock_kernel.h` selects
    `ptp_clock_register()` or its stub with
    `IS_ENABLED(CONFIG_PTP_1588_CLOCK)`.
  - Safe: when the guard is `IS_REACHABLE(CONFIG_BAR)` and losing the feature
    in a built-in caller is intended, as in
    `drivers/regulator/max5970-regulator.c`.

## Entries and syntax

**Keywords the parser accepts**

- Every rejected form below: a syntax error, counted in `yynerrs`;
  `conf_parse()` in `scripts/kconfig/parser.y` exits 1 right after
  `yyparse()`.

| Form | Accepted | In this tree |
|---|---|---|
| option line | no | no token in `scripts/kconfig/lexer.l`; the word lexes as `T_WORD` |
| optional in a choice | no | no token; `choice_option` has only `prompt` and `default` |
| name after `choice` | no | the rule is `choice: T_CHOICE T_EOL` |
| type line in a choice, with or without prompt text | no | `choice_option_list` has no `type` rule |
| dashed spelling of `help` | no | lexer class `n` contains `-`, so the whole word is one `T_WORD`, not `T_HELP` |
| `source "path"` | yes | the only form of `source` |
| relative or optional `source` variants | no | only `"source"` returns `T_SOURCE` |

- Choice type: the `choice` rule sets `S_BOOLEAN` itself.
- Choice prompt: written only as `prompt "text"`; the header also takes
  `default`, `depends on` and `help`.
- `source` path: `zconf_fopen()` tries it as given, then under `srctree`
  if it is not absolute; never relative to the including file.

**Choice blocks**

| Refused | Checked in | Result |
|---|---|---|
| choice with no `prompt` | `choice_entry` rule | error |
| member with no prompt | `config_stmt` rule | error |
| member whose type is not `S_BOOLEAN`, including no type line | `config_stmt` rule | error, "choice member must be bool" |
| member with `default` or `def_bool` | `choice_check_sanity()` | error |
| member with a prompt in another entry | `choice_check_sanity()` | error, "choice value must not have a prompt in another entry" |
| anything but `config`, `comment`, `if` inside the choice, `source` included | `stmt_list_in_choice` | error, "invalid statement" |
| choice `default` naming a non-member | `sym_check_prop()` in `scripts/kconfig/menu.c` | warning only, via `prop_warn()` |

- `choice_check_sanity()`: defined in `scripts/kconfig/parser.y`; it checks
  only the two rows that name it.
- Error counter: `yynerrs`, which `conf_parse()` increments when
  `choice_check_sanity()` returns -1.
- `conf_parse()` exits twice: after `yyparse()` for the grammar-rule rows,
  then after `menu_finalize()` for `choice_check_sanity()`. Grammar errors
  hide the later messages.
- `select` in a member: no choice-specific check.
- Tristate choices: none; `sym_calc_choice()` in `scripts/kconfig/symbol.c`
  sets each visible member to `yes` or `no`, never `mod`.
- No member set: only when no member is visible, as long as every choice
  `default` names a member. `sym_calc_choice()` tests member visibility, not
  the choice's own.
- Winner, in `sym_calc_choice()`, first match wins:
  1. first visible member in `choice_members` order with user value `y`;
  2. `sym_choice_default()`, unless the user set that member to `n`;
  3. first visible member in menu order with no user value;
  4. last visible member in `choice_members` order.
- Losing members set `y` in the file: no message by default; with
  `KCONFIG_WARN_CHANGED_INPUT` set to a non-empty value, `conf_write()` in
  `scripts/kconfig/confdata.c` lists them.

**Renaming or removing a symbol**

- Carry-over mechanism: the `transitional` keyword in a `config` entry; it
  sets `SYMBOL_TRANS`. Example: `CFI_CLANG` in `arch/Kconfig`; documented in
  `Documentation/kbuild/kconfig-language.rst`.
- Promptless old symbol without `transitional`: carries nothing.
  `sym_calc_value()` in `scripts/kconfig/symbol.c` uses the value from the
  file only when `sym->visible != no`.
- `SYMBOL_TRANS` symbol: `sym_calc_visibility()` forces `visible` to `yes`,
  so the old value is read.
- Allowed content: a type line with no prompt text, `transitional`, `help`.
- `transitional_check_sanity()` in `scripts/kconfig/parser.y`: any property
  (prompt, `default`, `select`, `imply`, `range`) or any dependency is an
  error that stops the configuration.
- Inherited dependency: the check runs after `menu_finalize()`, so an
  enclosing `if` or a menu with `depends on` also triggers the error.
- Missing type line: only the warning "config symbol defined without
  type"; `conf_set_sym_val()` stores no value, so nothing is carried.
- Old name in output: `sym_calc_value()` clears `SYMBOL_WRITE`, so it is
  absent from, for example, `.config`, `include/config/auto.conf` and
  `include/generated/autoconf.h`. C code and Makefiles that still test the
  old name see it unset.
- New symbol with `default OLD` as the chosen default, when the transitional
  `OLD` has a line in the file: marked user-set, so `oldconfig` does not
  prompt, even for `n`.
- Default whose value is not the single symbol `OLD`, for example
  `default y if OLD`: the value still follows `OLD`, but `prop_get_symbol()`
  does not return `OLD`, so `oldconfig` prompts for the new symbol.
- Unknown-name warning: opt-in through `KCONFIG_WARN_UNKNOWN_SYMBOLS`;
  `KCONFIG_WERROR` makes it fatal in `conf`. `scripts/kconfig/Makefile` sets
  them from `c` and `e` in `KBUILD_EXTRA_WARN`.

## Model gaps

### Other mistakes models make

- Models take only a recursive `source` to be fatal. A second `source` of the
  same path that is not recursive also exits 1, with "repeated inclusion of";
  see `file_lookup()` and `die_duplicated_include()` in
  `scripts/kconfig/util.c`.
- Models take `KCONFIG_WERROR` to make every Kconfig warning fatal.
  `menu_warn()` in `scripts/kconfig/menu.c` and the warnings in
  `scripts/kconfig/lexer.l` only print; `KCONFIG_WERROR` does not count them.
- Models take only a transitional entry's own lines to be restricted.
  `transitional_check_sanity()` in `scripts/kconfig/parser.y` walks
  `menu->sym->prop`, so a property from any other entry of the symbol is an
  error too.
- Models take a transitional symbol to be missing only from `.config`.
  `sym_calc_value()` clears its `SYMBOL_WRITE`, so `__conf_write_autoconf()` in
  `scripts/kconfig/confdata.c` leaves it out of `include/generated/rustc_cfg`
  too.
- Models take a `help` with no text to be harmless. Blank help text and a
  second help text in one entry are both `zconf_error()` in the `help` rule of
  `scripts/kconfig/parser.y`, and `conf_parse()` exits 1 after `yyparse()`.
- Models name SYMBOL_CHANGED and conf_unsaved. Neither is in this tree; unsaved
  state is `conf_set_changed()` and `conf_get_changed()`, per-entry change is
  `MENU_CHANGED`.
