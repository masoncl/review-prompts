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
