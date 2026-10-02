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
