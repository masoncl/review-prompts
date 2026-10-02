- `c_char`: `u8` on every architecture; `rust/ffi.rs` does not follow the
  target.
- `rust/ffi.rs`: defines each integer alias itself; it re-exports only
  `c_void` and `CStr` from `core::ffi`.
- `size_t`: no alias in `rust/ffi.rs`; the generated bindings use `usize` for
  it.
- `__kernel_size_t`, `__kernel_ssize_t`, `__kernel_ptrdiff_t`: blocklisted in
  `rust/bindgen_parameters` and defined by hand in `rust/bindings/lib.rs`.
- Naming the aliases: `Documentation/rust/coding-guidelines.rst` asks for the
  single-segment name from the prelude, as in `c_int`, not a
  `kernel::ffi::` path.
- `core::ffi` integer aliases: `.clippy.toml` has no entry for them, so
  Clippy does not flag them.
