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
