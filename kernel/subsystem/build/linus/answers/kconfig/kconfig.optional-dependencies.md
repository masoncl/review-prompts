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
