- Output path: `rust/bindings/bindings_generated.rs` under the object tree,
  not directly under `rust/`.
- `rust/bindgen_parameters`: extra bindgen options, mostly per-item
  workarounds such as `--opaque-type` and `--blocklist-item`;
  `--no-doc-comments` and the `MaybeZeroable` derive lines apply to every
  item.
- Fixed bindgen flags such as `--no-debug`, `--with-derive-default`,
  `--no-layout-tests` and `--ctypes-prefix ffi`: in `cmd_bindgen` in
  `rust/Makefile`, not in `rust/bindgen_parameters`.
- `rust/bindgen_parameters` is used for `bindings_generated.rs` and
  `uapi_generated.rs`. The run that makes `bindings_helpers_generated.rs`
  does not read it.
- A `RUST_CONST_HELPER_` constant that bindgen recognises under some
  configurations also needs a `--blocklist-item` line for the plain name, or
  the two definitions conflict. See the `ARCH_SLAB_MINALIGN` entry in
  `rust/bindgen_parameters`.
- The `RUST_CONST_HELPER_` prefix is stripped only from
  `bindings_generated.rs`; the `uapi` target has no such `sed` step.
- `--newtype-enum` with `--with-attribute-custom-enum`: used for `lru_status`
  only, to give it a `#[cfi_encoding]` attribute; binder's
  `rust_shrink_free_page()` returns it from a callback that C calls
  indirectly.
