- `-D` in `rust_common_flags`: `non_ascii_idents` and
  `unsafe_op_in_unsafe_fn`, nothing else.
- `-W` rustc lints: `missing_docs`, `rust_2018_idioms`, `unreachable_pub`;
  there is no `-Wunexpected_cfgs`.
- `-W` rustdoc lints: `rustdoc::missing_crate_level_docs` and
  `rustdoc::unescaped_backticks`.
- Clippy lints: the `-Wclippy::` lines of `rust_common_flags`; they have no
  dbg_macro, needless_continue or std_instead_of_core entry.
- `-Wclippy::float_arithmetic`: in `KBUILD_RUSTFLAGS` only, so it does not
  apply to host programs or proc macro crates.
- Allowed with `-A`: `stable_features`, `unused_features`,
  `clippy::collapsible_if`, `clippy::collapsible_match`,
  `clippy::incompatible_msrv`, `clippy::needless_lifetimes`,
  `clippy::uninlined_format_args`, `clippy::unwrap_or_default`.
- `-Aclippy::precedence`: added by `rust_common_flags_per_version` only when
  rustc is older than 1.86.0.
- `-Dwarnings`: added to `KBUILD_RUSTFLAGS` and `KBUILD_HOSTRUSTFLAGS` by
  `scripts/Makefile.warn` under `CONFIG_WERROR` or `W=e`; without it every
  `-W` lint leaves the build successful.
