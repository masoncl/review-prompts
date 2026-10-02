- `is_rust_noreturn()`: returns false at once unless the name starts with
  `_R`; there is no configuration or per-object guard, it runs for every
  non-local symbol passed to `__dead_end_function()`.
- Local-binding Rust symbol: never reaches `is_rust_noreturn()`; only the
  body scan in `__dead_end_function()` applies.
- Match list: longer than the `core::panicking` entries; it also covers, for
  example, `_4core6option13expect_failed`, `_4core3str16slice_error_fail` and
  three `_4core3num` radix panics. Read the function before adding a line.
- `rust_begin_unwind`: matched twice; the mangled suffix
  `_7___rustc17rust_begin_unwind` in `is_rust_noreturn()`, and the plain name
  as `NORETURN(rust_begin_unwind)` in `tools/objtool/noreturns.h`.
- `tools/objtool/noreturns.h` does hold Rust-side names: `rust_begin_unwind`
  and `rust_helper_BUG`.
- `rust_build_error`: exported under that plain name by
  `rust/build_error.rs`, and not listed in `tools/objtool/noreturns.h`.
- Adding a function: a mangled name needs a new `str_ends_with()` or
  `strstr()` line in `is_rust_noreturn()`; a plain name (`#[export_name]`,
  `#[no_mangle]`, or a C helper under `rust/helpers/`) needs `NORETURN()`.
