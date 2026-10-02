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
