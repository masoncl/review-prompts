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
