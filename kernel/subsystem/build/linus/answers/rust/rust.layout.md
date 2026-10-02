| Crate | Root | Vendored |
|---|---|---|
| `zerocopy` (target, `zerocopy.o`) | `rust/zerocopy/src/lib.rs` | yes; see `rust/zerocopy/README.md` |
| `zerocopy_derive` (host proc macro) | `rust/zerocopy-derive/lib.rs` | yes; see `rust/zerocopy-derive/README.md` |
| `proc_macro2` (host rlib in `rust/host/` of the object tree) | `rust/proc-macro2/lib.rs` | yes; see `rust/proc-macro2/README.md` |
| `quote` (host rlib in `rust/host/` of the object tree) | `rust/quote/lib.rs` | yes; see `rust/quote/README.md` |
| `syn` (host rlib in `rust/host/` of the object tree) | `rust/syn/lib.rs` | yes; see `rust/syn/README.md` |
| `pin_init` | `rust/pin-init/src/lib.rs` | synced with an outside repository (see `rust/pin-init/CONTRIBUTING.md`), but not treated as vendored: no `skip_clippy` in `rust/Makefile`, not pruned by `rustfmt` |
| `pin_init_internal` (host proc macro) | `rust/pin-init/internal/src/lib.rs` | same as `pin_init` |
| `doctests_kernel_generated` (only under `CONFIG_RUST_KERNEL_DOCTESTS`) | `rust/doctests_kernel_generated.rs` in the object tree, written by `scripts/rustdoc_test_gen.rs` | no |
| `alloc` | not built: `rust/Makefile` has no rule for it | n/a |

- `zerocopy` and `zerocopy_derive`: passed with `--extern` to `kernel` in
  `rust/Makefile`, and by `rust_common_cmd` in `scripts/Makefile.build` to
  every `.rs` file that the generic `.rs` rule compiles, which covers Rust
  drivers and the samples outside `samples/rust/hostprogs/`.
- The table omits the other crates that `rust/Makefile` builds, for example
  `kernel`, `macros` and `bindings`.
- Rust drivers: under `drivers/`.
- Rust samples: `samples/rust/`.
