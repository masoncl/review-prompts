- `struct Opaque` in `rust/kernel/types.rs`: has no `unsafe impl` of either
  marker, so it is never `Sync`, and is `Send` exactly when the wrapped C
  struct is.
- Opt-out on an `Opaque` wrapper: still written explicitly; `struct SeqFile`
  in `rust/kernel/seq_file.rs` holds both `Opaque<bindings::seq_file>` and
  `NotThreadSafe`.
- `NotThreadSafe`: `rust/kernel/types.rs` defines a type alias and a constant
  of that name, so the field type and the field value are both written
  `NotThreadSafe`.
- Device contexts: the impls are per context. `rust/kernel/device.rs` has
  `Send` for `Device` (context `Normal`) only, and `Sync` for `Device` and
  `Device<Bound>`.
- `Device<Core<'_>>`: has neither marker, so a `&Device<Core<'_>>` cannot be
  moved to another thread. Bus devices follow the same pattern, for example
  `rust/kernel/pci.rs` and `rust/kernel/platform.rs`.
- Property C does not guarantee for every instance: it is made a type
  invariant and a `# Safety` requirement of the constructor, and the
  `// SAFETY:` on the impl cites the invariant. See `struct Device` and
  `Device::get_device()` in `rust/kernel/device.rs` (`release` callable from
  any thread).
- Only some instances thread safe: two wrappers over one C struct. In
  `rust/kernel/fs/file.rs`, `File` has both impls and `LocalFile` has none;
  `LocalFile::assume_no_fdget_pos()` is the `unsafe fn` that converts.
