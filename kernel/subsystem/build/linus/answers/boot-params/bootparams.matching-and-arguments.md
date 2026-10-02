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
