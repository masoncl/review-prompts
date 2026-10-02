- `scripts/cc-version.sh`, `scripts/ld-version.sh`, `scripts/as-version.sh`: on
  a too-old tool print "... is too old." to stderr and exit 1 with nothing on
  stdout.
- `scripts/Kconfig.include`: aborts on the empty `cc-info`, `as-info` or
  `ld-info` through `$(error-if,...)`; its message is "Sorry, this C compiler
  is not supported." (and the like), not the "too old" text.
- `scripts/as-version.sh`: makes no version check when its arguments contain
  `-fintegrated-as`; it prints `LLVM 0`.
- llvm minimum: applied to Clang in `scripts/cc-version.sh`, to LLD in
  `scripts/ld-version.sh`, and to the libclang that bindgen uses in
  `scripts/rust_is_available.sh`.
- `scripts/rust_is_available.sh` at Kconfig time: only sets
  `CONFIG_RUST_IS_AVAILABLE`; `success` in `scripts/Kconfig.include` discards
  its output, so configuration continues.
- `scripts/rust_is_available.sh` at build time: `prepare` in the top-level
  `Makefile` runs it under `CONFIG_RUST`; a too-old tool stops the build there.
- Minimums that depend on the architecture, in `scripts/min-tool-version.sh`:

| Tool | Test | Minimum |
|---|---|---|
| `gcc` | `$ARCH` is `parisc64` | 12.0.0 |
| `gcc` | otherwise | 8.1.0 |
| `llvm` | `$SRCARCH` is `loongarch` | 18.0.0 |
| `llvm` | otherwise | 17.0.1 |
| `rustc` | `$SRCARCH` is `s390` | 1.96.0 |
| `rustc` | `$ARCH` is `powerpc` | 1.95.0 |
| `rustc` | otherwise | 1.85.0 |

- `binutils` (2.30.0) and `bindgen` (0.71.1): one minimum for every
  architecture.
- `Documentation/process/changes.rst`: lists only the general values (GNU C
  8.1, Clang/LLVM 17.0.1, Rust 1.85.0); it does not give the per-architecture
  values of `scripts/min-tool-version.sh`.
