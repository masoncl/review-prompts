- Two unrelated sets of traits exist side by side:

| Set | Traits | Defined in | In the prelude | Derive |
|---|---|---|---|---|
| kernel | `FromBytes`, `AsBytes` | `rust/kernel/transmute.rs` | no | none; `unsafe impl` by hand |
| zerocopy | `FromBytes`, `IntoBytes` | `rust/zerocopy/` (vendored) | yes | `#[derive(FromBytes)]`, `#[derive(IntoBytes)]` |

- Derive macros: come from `rust/zerocopy-derive/`; the prelude exports them
  under the same names as the traits.
- `#[derive(FromBytes)]` and `#[derive(IntoBytes)]`: implement the `zerocopy`
  traits only, never the `kernel::transmute` ones.
- Bare `FromBytes` after `use kernel::prelude::*`: the `zerocopy` trait, unless
  the file also imports `kernel::transmute::FromBytes` by name.
- No blanket impl links the two sets; a type used with both needs both, as
  `MyStruct` in `samples/rust/rust_dma.rs` does.
- `kernel::transmute` traits are the bound on, for example,
  `UserSliceReader::read()`, `UserSliceWriter::write()`, `dma::Coherent` and
  `CoherentBox`.
- `zerocopy` traits are the bound on, for example, `copy_read()` and
  `copy_write()` in `rust/kernel/io.rs`, and the blanket impls of
  `BinaryWriter` and `BinaryReaderMut` in `rust/kernel/debugfs/traits.rs`.
- `zerocopy::Immutable`: not in the prelude; import it from `zerocopy`, as
  `rust/kernel/debugfs/traits.rs` does.
- Hand-written `unsafe impl IntoBytes`: used only where the derive cannot see
  the no-padding property, as for `Region` in `rust/kernel/io.rs`.
