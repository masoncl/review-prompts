- `print_symbol_for_rustccfg()` in `scripts/kconfig/confdata.c`: for a bool or
  tristate set to `y` or `m` it emits both `--cfg=CONFIG_X` and
  `--cfg=CONFIG_X="y"` or `--cfg=CONFIG_X="m"`.
- `#[cfg(CONFIG_X)]`: true for `y` and for `m`; no cfg with a _MODULE suffix
  is emitted.
- Built-in only: `#[cfg(CONFIG_X = "y")]`; modular only:
  `#[cfg(CONFIG_X = "m")]`.
- `#[cfg(MODULE)]`: tells whether the crate being compiled is itself a module;
  it comes from `KBUILD_RUSTFLAGS_MODULE`, not from Kconfig.
- Compiler-version example in `Documentation/rust/general-information.rst`:
  `RUSTC_HAS_SPAN_FILE` (`def_bool RUSTC_VERSION >= 108800` in
  `init/Kconfig`), tested in `rust/macros/helpers.rs`.
- Example in the `kernel` crate: `CONFIG_RUSTC_HAS_FILE_WITH_NUL` and
  `CONFIG_RUSTC_HAS_FILE_AS_C_STR` in `file_from_location()` in
  `rust/kernel/lib.rs`.
- RUSTC_HAS_COERCE_POINTEE and RUSTC_VERSION_MIN_107900 do not exist in this
  tree.
