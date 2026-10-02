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
