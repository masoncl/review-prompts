- `.clippy.toml` `msrv`: `"1.85.0"`.
- `.clippy.toml` `disallowed-macros`: one entry, `kernel::dbg`; no assert or
  panic macro is banned.
- `.clippy.toml` `[[disallowed-methods]]`: `core::ffi::CStr::as_ptr` and
  `core::ffi::CStr::from_ptr`, with `as_char_ptr` and `from_char_ptr` of
  `kernel::prelude::CStrExt` as replacements.
- `make LLVM=1 rustdoc`: besides the rustdoc lints, prints a warning for each
  `srctree/` link in the docs whose target file does not exist; there is no
  separate doc-check target.
- `make LLVM=1 rusttest`: `rusttest: rusttest-macros` only; it runs the
  `#[test]` tests and the doctests of `rust/macros/lib.rs`.
- `CLIPPY=1` does not lint targets marked `skip_clippy` in `rust/Makefile`
  (`core`, `zerocopy`, `zerocopy_derive`, `proc_macro2`, `quote` and `syn`;
  not `pin_init`) nor host programs, which `cmd_host-rust` builds with
  `HOSTRUSTC`.
- `rustfmt` and `rustfmtcheck`: skip `rust/proc-macro2`, `rust/quote`,
  `rust/syn`, `rust/zerocopy` and `rust/zerocopy-derive` (not
  `rust/pin-init`) and any file with `generated` in its name; both are in
  `no-dot-config-targets`, so they run without a `.config`.
