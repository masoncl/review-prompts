- `scripts/min-tool-version.sh`: rustc 1.85.0, bindgen 0.71.1.
- rustc minimum differs by architecture: 1.96.0 when `SRCARCH` is s390,
  1.95.0 when `ARCH` is powerpc; bindgen does not differ.
- libclang used by bindgen: checked against the `llvm` entry, which is higher
  for loongarch.
- `scripts/rust_is_available.sh`: run, for example, by `RUST_IS_AVAILABLE` in
  `init/Kconfig`, by `make rustavailable`, and again by `prepare` in the
  top-level `Makefile` under `ifdef CONFIG_RUST`.
- `scripts/rust_is_available.sh` only warns for bindgen below 0.72.1 with
  libclang 22 or newer, and for a libclang/Clang version mismatch.
- The minimum is also hard-coded in `msrv` in `.clippy.toml`, in
  `--rust-target` of `cmd_bindgen` in `rust/Makefile`, and in
  `Documentation/process/changes.rst`.
- `RUSTC_SUPPORTS_ARM64` depends only on `CPU_LITTLE_ENDIAN` and
  `RUSTC_SUPPORTS_RISCV` only on `64BIT`; neither tests `RUSTC_VERSION`.
- Version-dependent Kconfig limits: search Kconfig files for `RUSTC_VERSION`;
  for example `RUST` needs `RUSTC_VERSION >= 109600` with `KASAN_SW_TAGS`.
- Architectures: search for `select HAVE_RUST`; the set includes
  `arch/arm`, `arch/powerpc` (including `PPC32`) and `arch/s390`.
- `make LLVM=1 rusttest`: runs only `rusttest-macros`, but that depends on
  `rusttestlib-kernel`, which compiles `rust/kernel/lib.rs` for the host with
  `--cfg testlib` and `rust_common_flags`; this is the only build of the
  `#[cfg(testlib)]` branches under `rust/kernel/`.
- `#[kunit_tests]` suites under `rust/kernel/`: need `CONFIG_KUNIT=y` and,
  where the module carries one, the suite's option from
  `rust/kernel/Kconfig.test`; those default to `KUNIT_ALL_TESTS`.
