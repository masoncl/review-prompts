- `rust_allowed_features` in `scripts/Makefile.build`: exactly
  `arbitrary_self_types`, `asm_goto`, `generic_arg_infer`, `used_with_arg`;
  nothing else is allowed outside `rust/`.
- `rust_common_cmd`: passes the list both as `-Zallow-features=` and as
  `-Zcrate-attr='feature(...)'`, so the four are already on in every such
  crate; no `.rs` file outside `rust/` contains `#![feature(`.
- Host programs (`scripts/Makefile.host`, `samples/rust/hostprogs`):
  `KBUILD_HOSTRUSTFLAGS` carries an empty `-Zallow-features=`, so they may use
  no unstable feature.
- `rust/kernel/lib.rs` enables `unsigned_is_multiple_of`, `generic_arg_infer`,
  `arbitrary_self_types`, `derive_coerce_pointee`, `used_with_arg`, and
  `file_with_nul` under `CONFIG_RUSTC_HAS_FILE_WITH_NUL`.
- `derive_coerce_pointee`: unconditional; there is no
  CONFIG_RUSTC_HAS_COERCE_POINTEE symbol and no fallback feature set.
- `asm_goto` is on the allow list but is not enabled in `rust/kernel/lib.rs`.
- Other crates under `rust/` enable their own features with no allow list, for
  example `extract_if` in `rust/macros/lib.rs` and `cfi_encoding` in
  `rust/bindings/lib.rs`.
- `rust/doctests_kernel_generated.rs`: built by the generic rule in
  `scripts/Makefile.build`, so documentation examples of the `kernel` crate
  get the four allowed features, not the crate's own set.
- `RUSTC_BOOTSTRAP`: `export RUSTC_BOOTSTRAP := 1` in the top-level
  `Makefile`; it is not scoped to a crate and restricts nothing.
