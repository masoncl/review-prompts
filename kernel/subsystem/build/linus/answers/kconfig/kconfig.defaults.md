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
