- `Documentation/rust/coding-guidelines.rst`: its "must" sentences name only
  `unsafe` blocks (for `// SAFETY:`) and unsafe functions (for `# Safety`);
  traits appear only in the two sentences that say "(for traits)".
- `Documentation/rust/coding-guidelines.rst`: has no sentence that forbids
  describing the code; it requires the comment to say why the block "cannot
  trigger undefined behavior in any case".
- Clippy lints in `rust_common_flags` (top-level `Makefile`): take effect only
  when `RUSTC_OR_CLIPPY` is `clippy-driver`, i.e. a `CLIPPY=1` build.
- `-Dunsafe_op_in_unsafe_fn`: a rustc flag in the same variable, deny level,
  applied with or without `CLIPPY=1`.
- `clippy::missing_safety_doc`: not named in `rust_common_flags`; it comes in
  through `-Wclippy::all`.
- `check-private-items = true` in `.clippy.toml`: a private `unsafe fn` needs
  `# Safety` too; see the `#[allow(clippy::missing_safety_doc)]` on private
  functions in `rust/kernel/devres.rs`.
- Exempt code: `rust/bindings/lib.rs` allows `clippy::all`,
  `clippy::undocumented_unsafe_blocks` and `unsafe_op_in_unsafe_fn`; targets
  with `skip_clippy` in `rust/Makefile` are built with plain `$(RUSTC)`.
- Doc examples: carry the comment too, sometimes on hidden lines such as
  `# // SAFETY:` in `rust/kernel/sync/aref.rs`; `rust/kernel/init.rs` uses
  `# #![expect(clippy::undocumented_unsafe_blocks)]` instead.
