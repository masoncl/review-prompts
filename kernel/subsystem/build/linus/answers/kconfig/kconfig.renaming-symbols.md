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
