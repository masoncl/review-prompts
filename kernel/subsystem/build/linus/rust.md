# Rust Subsystem Details

## Main structures

### Objects and how they relate

- Bus `Driver` traits (for example `pci::Driver`, `platform::Driver`): the
  implementing type may be only a marker. The per-device private data is the
  associated type `Data<'bound>` (often set to `Self`), and `probe()` returns
  `impl PinInit<Self::Data<'bound>, Error> + 'bound`.
- `post_unbind_rust` in `struct device_driver`: `device_unbind_cleanup()` in
  `drivers/base/dd.c` calls it just before `devres_release_all()`; on unbind
  `device_remove()` has already run. So driver data is dropped before devres
  entries are released.
- `DriverLayout` in `rust/kernel/driver.rs`: supertrait of `RegistrationOps`.
  It names the C driver type, the data type and the offset of the embedded
  `struct device_driver`; `Registration` uses it to install
  `post_unbind_rust`.
- `Devres::access()`: takes a `&Device<Bound>` of the same device and returns
  `Ok(&T)` without the `Revocable` check. Only `try_access()` and its variants
  make that check and can return `None`.
- `ForLt` and `CovariantForLt` in `rust/kernel/types/for_lt.rs`: traits whose
  implementor stands for "a type generic over one lifetime"; built with the
  `ForLt!` and `CovariantForLt!` macros.
- `DevresLt<F: ForLt>` in `rust/kernel/devres.rs`: stores `F::Of<'static>` in
  a `Devres` and shortens the lifetime on every access. `DevresBar` and
  `DevresIoMem` are aliases of it. `auxiliary::Registration<'a, F>` uses
  `ForLt` the same way.
- `#[vtable]` in `rust/macros/vtable.rs`: emits no C ops table. It adds one
  `HAS_` constant per method (for example `HAS_MMAP`), `USE_VTABLE_ATTR` and
  the associated type `OwnerModule`.
- C ops tables: each abstraction builds its own from the `HAS_` constants,
  for example `MiscdeviceVTable` in `rust/kernel/miscdevice.rs`.
- `OwnerModule`: a `#[vtable]` impl gets `type OwnerModule = crate::LocalModule`
  unless it defines one; `this_module()` returns its `ThisModule`, whose
  `as_ptr()` is the `owner` pointer.
- `LocalModule`: type alias that `module!` emits at the crate root for the
  module type. `module!` also implements `ModuleMetadata` for it, which
  carries `NAME` and `THIS_MODULE`.
- The `kernel` crate has no Ref type; `Arc` in `rust/kernel/sync/arc.rs` is
  its refcounted pointer, built on `Refcount` in
  `rust/kernel/sync/refcount.rs`.
- `ARef` and `AlwaysRefCounted`: defined in `rust/kernel/sync/aref.rs`;
  `rust/kernel/types.rs` does not re-export them.
- `CStr`: is `core::ffi::CStr`, re-exported by `rust/ffi.rs`. Kernel methods
  such as `as_char_ptr()` come from the `CStrExt` trait in
  `rust/kernel/str.rs`.
- C string literals: written `c"..."`. `c_str!` remains for constants that
  are not literals, such as `concat!()` output.
- Crates: `rust/Makefile` lists them. Easy to miss are the vendored `syn`,
  `quote`, `proc-macro2`, `zerocopy` and `zerocopy-derive`; `rust/macros/`
  parses with `syn`.

## Where to look

**Crates and directories**

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

## Building and toolchain

**Unstable language features**

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

**Minimum toolchain and build configurations**

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

**Lints and formatting checks**

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

**Separately run checks**

- `.clippy.toml` `msrv`: `"1.85.0"`.
- `.clippy.toml` `disallowed-macros`: one entry, `kernel::dbg`; no assert or
  panic macro is banned.
- `.clippy.toml` `[[disallowed-methods]]`: `core::ffi::CStr::as_ptr` and
  `core::ffi::CStr::from_ptr`, with `as_char_ptr` and `from_char_ptr` of
  `kernel::prelude::CStrExt` as replacements.
- `make LLVM=1 rustdoc`: besides the rustdoc lints, prints a warning for each
  `srctree/` link in the docs whose target file does not exist; there is no
  separate doc-check target.
- `make LLVM=1 rusttest`: `rusttest: rusttest-macros` only; it runs the
  `#[test]` tests and the doctests of `rust/macros/lib.rs`.
- `CLIPPY=1` does not lint targets marked `skip_clippy` in `rust/Makefile`
  (`core`, `zerocopy`, `zerocopy_derive`, `proc_macro2`, `quote` and `syn`;
  not `pin_init`) nor host programs, which `cmd_host-rust` builds with
  `HOSTRUSTC`.
- `rustfmt` and `rustfmtcheck`: skip `rust/proc-macro2`, `rust/quote`,
  `rust/syn`, `rust/zerocopy` and `rust/zerocopy-derive` (not
  `rust/pin-init`) and any file with `generated` in its name; both are in
  `no-dot-config-targets`, so they run without a `.config`.

**Kconfig in Rust code**

- `print_symbol_for_rustccfg()` in `scripts/kconfig/confdata.c`: for a bool or
  tristate set to `y` or `m` it emits both `--cfg=CONFIG_X` and
  `--cfg=CONFIG_X="y"` or `--cfg=CONFIG_X="m"`.
- `#[cfg(CONFIG_X)]`: true for `y` and for `m`; no cfg with a _MODULE suffix
  is emitted.
- Built-in only: `#[cfg(CONFIG_X = "y")]`; modular only:
  `#[cfg(CONFIG_X = "m")]`.
- `#[cfg(MODULE)]`: tells whether the crate being compiled is itself a module;
  it comes from `KBUILD_RUSTFLAGS_MODULE`, not from Kconfig.
- Compiler-version example in `Documentation/rust/general-information.rst`:
  `RUSTC_HAS_SPAN_FILE` (`def_bool RUSTC_VERSION >= 108800` in
  `init/Kconfig`), tested in `rust/macros/helpers.rs`.
- Example in the `kernel` crate: `CONFIG_RUSTC_HAS_FILE_WITH_NUL` and
  `CONFIG_RUSTC_HAS_FILE_AS_C_STR` in `file_from_location()` in
  `rust/kernel/lib.rs`.
- RUSTC_HAS_COERCE_POINTEE and RUSTC_VERSION_MIN_107900 do not exist in this
  tree.

**Abstractions for modular subsystems**

- Plain `#[cfg(CONFIG_X)]` on a tristate `X` is also true for `X=m`; see
  "Kconfig in Rust code".
- Three forms keep an abstraction for a tristate subsystem built-in only:

| Form | Abstraction gate | Driver carries | Examples |
|---|---|---|---|
| direct | `#[cfg(CONFIG_X = "y")]` | `depends on X=y` | `DRM` (`DRM_NOVA`, `DRM_TYR`), `I2C`, `USB` (samples) |
| bool that depends | plain `#[cfg]` on a bool symbol that has `depends on X=y` | `depends on` the bool | `RUST_PHYLIB_ABSTRACTIONS` (`AX88796B_RUST_PHY`), `RUST_FWCTL_ABSTRACTIONS` |
| bool that selects | plain `#[cfg]` on a bool symbol that has `select X` | `select` or `depends on` the bool | `RUST_FW_LOADER_ABSTRACTIONS` (`NOVA_CORE`, `DRM_TYR` select; `AMCC_QT2025_PHY` depends), `RUST_SERIAL_DEV_BUS_ABSTRACTIONS` |

- `RUST_FW_LOADER_ABSTRACTIONS`: `depends on RUST` and `select FW_LOADER`; it
  has no `depends on FW_LOADER=y`.
- `RUST_DRM_GPUVM` and `RUST_DRM_GEM_SHMEM_HELPER`: the "bool that selects"
  form for the tristate helpers `DRM_GPUVM` and `DRM_GEM_SHMEM_HELPER`,
  inside the `drm` module.
- `CONFIG_PCI`, `CONFIG_NET`, `CONFIG_BLOCK`, `CONFIG_AUXILIARY_BUS`: bool
  symbols, gated with plain `#[cfg(CONFIG_X)]`; drivers use `depends on PCI`
  or `select AUXILIARY_BUS`.
- `CONFIG_GPU_BUDDY = "y"`: `GPU_BUDDY` is a bool, so this equals the plain
  form.
- `phy` gate: `#[cfg(CONFIG_RUST_PHYLIB_ABSTRACTIONS)]` is in
  `rust/kernel/net/mod.rs`, not in `rust/kernel/lib.rs`.
- The driver itself may stay tristate in all three forms.

**Kinds of test**

- Option for a new `#[kunit_tests]` suite: add it to
  `rust/kernel/Kconfig.test`, inside `if RUST_KUNIT_TESTS`, and put a
  `#[cfg]` on that option above `#[kunit_tests(...)]`; follow
  `RUST_STR_KUNIT_TEST` and `rust/kernel/str.rs`.
- `kunit_tests()` in `rust/macros/kunit.rs`: adds
  `#[cfg(CONFIG_KUNIT="y")]` to the module itself, so a suite is not built
  with `KUNIT=m`.
- `RUST_KERNEL_DOCTESTS`: `depends on RUST && KUNIT=y`, default
  `KUNIT_ALL_TESTS`.
- Only examples reachable from `rust/kernel/lib.rs` become KUnit tests
  (`cmd_rustdoc_test_kernel` in `rust/Makefile`); examples in a driver or
  sample are not compiled by any target; `rusttest` runs those of
  `rust/macros/lib.rs`.
- `no_run`: has no effect on the KUnit tests; rustdoc is already run with
  `--no-run`, and `scripts/rustdoc_test_gen.rs` emits a call to `main()` for
  every example the builder saved, without reading attributes.
- **Potentially unsafe usage**: an example that touches hardware or user
  memory, relying on `no_run` to keep it from executing.
  - Unsafe: when the statements sit at the top level of the example; they
    become the body of `main()`, which the generated KUnit case calls.
  - Safe: when the statements are inside a function that the example never
    calls, as in the example on `Firmware` in `rust/kernel/firmware.rs`.
- `compile_fail`: `scripts/rustdoc_test_builder.rs` saves the source and
  compiles nothing, so an expected failure cannot be checked; under
  `rust/kernel/` the only use is `ignore,compile_fail` in
  `rust/kernel/types/for_lt.rs`.
- Example on a private item: the generated tests are a separate crate built
  with `--extern kernel`, so the example cannot name an item that is not
  `pub`; `Documentation/rust/testing.rst` states that doctests are not run for
  nonpublic functions.

## Reaching C from Rust

**Wrapping C structures**

- `rust/kernel/types.rs`: does not re-export `ARef` or `AlwaysRefCounted`, so
  a path through `kernel::types` does not resolve for either.
- `kernel::sync::aref`: the only path for `ARef` and `AlwaysRefCounted`;
  `rust/kernel/sync.rs` and `rust/kernel/prelude.rs` do not re-export them
  either.
- `Opaque::cast_into()`: `*const Opaque<T>` to `*mut T`, without creating a
  reference.
- `Opaque::cast_from()`: `*const T` to `*const Opaque<T>`; it returns a const
  pointer, so a caller that needs `*mut` must cast again.
- `Opaque<T>` has no `raw_get()` method; `raw_get()` in this tree belongs to
  `Work` and `HrTimer`.
- `Opaque::pin_init()`: the `Wrapper` trait method from `pin_init`, so the
  trait must be in scope to call it.

**C integer types**

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

**Generating bindings**

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

**C helper functions**

- `exports_helpers_generated.h`: generated by `rust/Makefile` and included by
  `rust/exports.c` only without `CONFIG_RUST_INLINE_HELPERS`. With that option
  `rust/Makefile` builds no `helpers/helpers.o`.
- Helpers bindgen run: `--allowlist-function 'rust_helper_.*'` in
  `rust/Makefile`, so a function in `rust/helpers/` without the prefix gets
  no binding from that run.
- `rust/helpers/bitops.c`: defines `_find_first_zero_bit()`,
  `_find_next_zero_bit()`, `_find_first_bit()` and `_find_next_bit()`
  without the prefix, each under an `#ifdef`. Rust reaches them through the
  declarations in `include/linux/find.h`.
- `rust/helpers/atomic.c`: generated by
  `scripts/atomic/gen-rust-atomic-helpers.sh`; a change goes into the script.

**Helper function attribute**

- `__rust_helper`: defined only in `rust/helpers/helpers.c`, before the
  `#include` lines of the helper files.
- Expansion in every C compile of the helpers: `__always_inline`.
- Expansion under bindgen: empty. `rust/Makefile` passes `-D__BINDGEN__` in
  `bindgen_c_flags_final`, because bindgen skips inline functions.
- The definition tests only `__BINDGEN__`. It does not depend on
  `CONFIG_RUST_INLINE_HELPERS`.
- `CONFIG_RUST_INLINE_HELPERS`: defined in `lib/Kconfig.debug`; among its
  `depends on` lines are `EXPERT` and `ARM64 || X86_64`.
- With `CONFIG_RUST_INLINE_HELPERS`: `rust/Makefile` compiles `helpers.c` to
  `helpers/helpers.bc` and `helpers/helpers_module.bc`.
  `scripts/Makefile.build` links one of them into each Rust object it builds
  (`helpers/helpers_module.bc` when the object is part of a module,
  `helpers/helpers.bc` otherwise), and `rust/Makefile` links
  `helpers/helpers.bc` into `kernel.o`.
- Coverage: every function body under `rust/helpers/` carries
  `__rust_helper`, including the macro-generated ones in
  `rust/helpers/atomic_ext.c`.
- `rust/helpers/build_assert.c`: holds only a `static_assert()`, so it has no
  function to annotate.

**Handing Rust data to C**

- Implementors of `ForeignOwnable`, all five: `Box<T, A>`,
  `Pin<Box<T, A>>`, `Arc<T>`, `ARef<T>` and `()`.
- `ARef<T>`: implemented in `rust/kernel/sync/aref.rs`.
- `Box<T, A>`: generic over the allocator, so `KBox`, `VBox` and `KVBox` all
  qualify.
- References: no `&T` impl exists.
- `Owned` in `rust/kernel/scatterlist.rs`: does not implement
  `ForeignOwnable`.
- `ARef<T>` and `Arc<T>`: `BorrowedMut` is the same shared type as
  `Borrowed`, so `borrow_mut()` gives no exclusive access.
- `FOREIGN_ALIGN` for `ARef<T>` and `()`: plain `align_of`, so it can be below
  4. `rust/kernel/xarray.rs` rejects such types with
  `build_assert!(T::FOREIGN_ALIGN >= 4)`.
- `FOREIGN_ALIGN` for `Box<T, A>`: the larger of `align_of::<T>()` and
  `A::MIN_ALIGN`.

**Vtable traits**

- `#[vtable]` on a trait: adds `type OwnerModule: ::kernel::ModuleMetadata;`
  unless the trait already declares a type named `OwnerModule`.
- `#[vtable]` on an impl: adds `type OwnerModule = crate::LocalModule;`
  unless the impl defines it.
- `LocalModule`: a type alias that `module!` emits at the crate root, in
  `rust/macros/module.rs`. `rust/kernel/lib.rs` and
  `scripts/rustdoc_test_gen.rs` define dummies with a null `THIS_MODULE`.
- Owner field: an abstraction reads it with
  `this_module::<T::OwnerModule>()`, for example `MiscdeviceVTable` in
  `rust/kernel/miscdevice.rs` and `GEM_FOPS` in `rust/kernel/drm/device.rs`.
- `drm::Driver` in `rust/kernel/drm/driver.rs`: an example of a `#[vtable]`
  trait whose `OwnerModule` an abstraction consumes.
- `HAS_<NAME>` on the trait: generated for every `fn`, required methods too.
  For example `MiscDevice::open()` has no default body and still gets
  `HAS_OPEN`.
- Optional method body: `build_error!(VTABLE_DEFAULT_ERROR)`, not an error
  return.
- `USE_VTABLE_ATTR`: declared without a value on the trait and defined on the
  impl, so an impl without `#[vtable]` fails to build.
- An impl that defines `HAS_<NAME>` itself: `handle_impl()` in
  `rust/macros/vtable.rs` keeps that value and does not generate its own.
- A method that the abstraction installs unconditionally may have an ordinary
  default body, as `MiscDevice::release()` does.

**Direct use of bindings**

- `drivers/gpu/`: no file uses `kernel::bindings`. `bindings::` in
  `drivers/gpu/nova-core/gsp/fw.rs` is `use r570_144 as bindings;`, the
  driver's own firmware module.
- `drivers/gpu/drm/nova/` and `drivers/gpu/drm/tyr/`: use `kernel::uapi`
  only.
- `lib/find_bit_benchmark_rust.rs`: calls
  `bindings::__get_random_u32_below()` directly, outside both `rust/` and
  `drivers/android/binder/`.
- `samples/rust/`: no file uses `bindings::`.
- `pub use bindings;` in `rust/kernel/lib.rs`: marked `#[doc(hidden)]`. The
  crate doc in `rust/bindings/lib.rs` says the crate may not be used directly.
- Nothing in the build enforces the rule; `rust/Makefile` exports every
  `bindings` symbol to modules.
- Binder's driver-private items: its headers are included from
  `rust/bindings/bindings_helper.h` under
  `IS_ENABLED(CONFIG_ANDROID_BINDER_IPC_RUST)`, and its helpers are in
  `rust/helpers/binder.c`.

## Unsafe code

**Safety comments and sections**

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

**Type invariants**

- `Documentation/rust/`: does not describe the convention; "invariant" occurs
  nowhere under it. The convention lives only in the code.
- Enforcement: no flag in `rust_common_flags` and no check in
  `scripts/checkpatch.pl` looks at `# Invariants` or `// INVARIANT:`.
- `ARef::from_raw()` in `rust/kernel/sync/aref.rs`: has the `// INVARIANT:`
  comment.
- `rust/kernel/types.rs`: its example is `struct ScopeGuard`.
- `rust/kernel/str.rs`: defines no `CStr` struct; its `# Invariants` sections
  are on `RawFormatter`, `NullTerminatedFormatter` and `CString`.
- `rust/kernel/sync/lock.rs`: has no `# Invariants` section and no
  `// INVARIANT:` comment; use `struct Guard` in `rust/kernel/sync/rcu.rs`.
- `// INVARIANT:` on a pointer cast: also marks a cast that yields a reference
  or `ARef` to such a type with no struct literal, for example
  `File::from_raw_file()` and `LocalFile::assume_no_fdget_pos()` in
  `rust/kernel/fs/file.rs`, and `probe_callback()` in
  `rust/kernel/platform.rs`.
- `// INVARIANT:` and `// SAFETY:`: may share one comment block above one
  `unsafe` expression, as in `LocalFile::fget()`.
- Temporary break: `rust/kernel/alloc/kvec.rs` marks both the statement that
  breaks the invariant and the one that restores it.
- Spelling: `# Invariant` (for example `rust/kernel/io.rs`) and
  `// INVARIANTS:` (for example `rust/kernel/sync/poll.rs`) also occur.
- Field visibility: under `rust/kernel/`, fields under an invariant are not
  `pub`, but `pub(crate)` occurs, for example `struct Task` in
  `rust/kernel/task.rs`.

**Thread safety markers**

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

**Soundness of safe functions**

- **Potentially unsafe usage**: a constructor that registers with C and
  relies on `Drop` to unregister.
  - Unsafe: when the constructor is a safe `fn` and the data C keeps a
    pointer to may hold borrows (the type carries a lifetime that is not
    `'static`); `mem::forget()` is safe, skips `Drop`, and C then calls back
    after the borrow has ended. Pinning keeps the registration's own memory
    alive, not what it borrows.
  - Safe: the constructor is an `unsafe fn` whose `# Safety` section forbids
    `mem::forget()`, as `Registration::new()` in `rust/kernel/irq/request.rs`
    and `Registration::new_with_lt()` in `rust/kernel/auxiliary.rs` are.
  - Safe: the data is bounded `'static`, as in `Registration::new()` in
    `rust/kernel/auxiliary.rs` (`F::Of<'a>: 'static`; its `// SAFETY:` states
    the reason), `Registration::new()` in `rust/kernel/driver.rs`
    (`T: 'static`) and `struct Devres` (`T: Send + 'static`).
  - Safe: C keeps no pointer to Rust data, so a leak only leaves the C object
    registered forever, as `Registration::new()` in `rust/kernel/faux.rs`
    (the type has no lifetime, the ops pointer is `null()`, and
    `faux_device_create_with_groups()` copies the name).
- `rust/kernel/time/hrtimer.rs`: the same split as two traits. `HrTimerPointer`
  has a safe `start()` and its handle may be leaked; `UnsafeHrTimerPointer`
  has `unsafe fn start()` for timers that die with a borrow.
- `Queue::enqueue()` in `rust/kernel/workqueue.rs`: safe because it requires
  `W: RawWorkItem<ID> + Send + 'static`; `RawWorkItem::__enqueue()` lists what
  the caller owes without those bounds.
- `WorkItem` in `rust/kernel/workqueue.rs`: a safe trait. The unsafe traits
  there are `RawWorkItem`, `RawDelayedWorkItem`, `WorkItemPointer`, `HasWork`
  and `HasDelayedWork`.
- Trampolines: both forms occur. `unsafe extern "C" fn` with a `# Safety`
  section in `rust/kernel/miscdevice.rs` and `rust/kernel/irq/request.rs`;
  plain `extern "C" fn` in bus adapters, for example `probe_callback()` in
  `rust/kernel/platform.rs` and `post_unbind_callback()` in
  `rust/kernel/driver.rs`.
- Bounds on callback data: match the context C calls from, for example
  `Handler: Sync` in `rust/kernel/irq/request.rs`,
  `MiscDevice::Ptr: ForeignOwnable + Send + Sync`, and
  `Driver::Data<'bound>: Send` in `rust/kernel/platform.rs`.
- Precondition a safe function cannot check: taken as a typed argument that
  only unsafe code can create. `Devres::new()` takes `&Device<Bound>`;
  `Device::as_bound()` is the `unsafe fn` that makes one.
- References built in bus callbacks: typed `Device<CoreInternal<'_>>`, handed
  to drivers as `Device<Core<'_>>`; the lifetime in `struct Core`
  (`rust/kernel/device.rs`) is invariant so the reference cannot outlive the
  callback.

## Assertions and panics

**Build-time assertions**

| Macro | Condition may use | Where | Failure |
|---|---|---|---|
| `static_assert!` | constants only; no generics, no variables | module level and inside bodies | compile error; evaluated even if the enclosing function is never used |
| `const_assert!` | constants and generics of the enclosing function or `impl`; no variables | statement position inside a body | compile error, only for instances that are actually instantiated |
| `build_assert!` | anything, including function arguments | statement position inside a body or const initializer block | const context: compile-time panic; otherwise undefined `rust_build_error` at link |
| `build_error!` | nothing; unconditional | expression position on a path that must be dead | same two modes as `build_assert!` |

- `const_assert!`: exists; defined in `rust/kernel/build_assert.rs` beside the
  other three, and all four are in `rust/kernel/prelude.rs`.
- `static_assert!`: defined in `rust/kernel/build_assert.rs`; there is no
  rust/kernel/static_assert.rs.
- `static_assert!` expands to an unnamed `const _: () = ...;` item, so it goes
  at module level or inside a body, not as an associated item of an `impl`.
- `build_error()` in `rust/build_error.rs` is a `const fn` that panics, so a
  `build_assert!` evaluated in const context fails in the compiler, not the
  linker; `rust/kernel/iov.rs` uses it that way in a `const _` block.
- `const_assert!` cannot refer to function arguments even inside a
  `const fn`; such a function uses `build_assert!`, as `_IOC()` in
  `rust/kernel/ioctl.rs` does.
- `build_assert!` on generics only (for example `LockedBy::new()` in
  `rust/kernel/sync/locked_by.rs`): works with no inline attribute; the module
  doc marks it "Discouraged" in favour of `const_assert!`.
- `CONFIG_RUST_BUILD_ASSERT_ALLOW`: `rust/Makefile` then links
  `build_error.o` and `rust/exports.c` exports `rust_build_error`, so a
  surviving call becomes a run-time panic; without it the object is built but
  not linked.
- **Potentially unsafe usage**: `build_assert!` or `build_error!` on a
  condition that depends on a function argument, in a function without
  `#[inline(always)]`.
  - Unsafe: when the function has a run-time caller; if it is emitted out of
    line the call to `build_error()` survives.
  - Safe: `#[inline(always)]` on the function and on every wrapper that
    forwards the argument, as `_IO()` and `_IOC()` in `rust/kernel/ioctl.rs`,
    and `io_view_assert()` with its callers in `rust/kernel/io.rs`; the
    kerneldoc of `build_assert!` states the requirement.
  - Safe: a `const fn` that is private or generic and has no run-time caller,
    as `DataDirection::const_cast()` in `rust/kernel/dma.rs` (private, called
    only for enum discriminants) and `ModInfoBuilder::push()` in
    `rust/kernel/firmware.rs` (generic over `N`, reached only from
    `module_firmware!`); the const evaluator panics instead.

**Panics**

- `CONFIG_RUST_OVERFLOW_CHECKS`: `default y` in `lib/Kconfig.debug`, so
  overflowing arithmetic panics in a default build; with it off the result
  wraps.
- `CONFIG_RUST_OVERFLOW_CHECKS` also gates explicit `assert!` calls in the
  `kernel` crate, for example adding a `Delta` to an `Instant` in
  `rust/kernel/time.rs`, and `raw_strncpy_from_user()` in
  `rust/kernel/uaccess.rs`.
- `Vec::remove()` and `Vec::insert_within_capacity()` in
  `rust/kernel/alloc/kvec.rs` do not panic on a bad index: `remove()` returns
  `Result<T, RemoveError>` and `insert_within_capacity()` returns
  `InsertError::IndexOutOfBounds`.
- `Vec` has no try_push or swap_remove here; `push()` takes GFP flags and
  `push_within_capacity()` does not allocate.
- `assert!` and `assert_eq!` inside doctests and inside `#[test]` functions of
  a `#[kunit_tests]` module do not panic: `scripts/rustdoc_test_gen.rs` and
  `rust/macros/kunit.rs` override them with `kunit_assert!` and
  `kunit_assert_eq!`, which report to KUnit.
- `unwrap()` and `expect()` in tests still panic;
  `Documentation/rust/testing.rst` asks for `?` instead in documentation
  tests.
- `Documentation/rust/coding-guidelines.rst`: requires a `# Panics` section on
  any function that may panic, and says panicking "should be very rare", with
  a `Result` return as the usual alternative.
- `unsafe_precondition_assert!`: defined in `rust/kernel/safety.rs`; checks,
  inside an `unsafe fn`, a precondition the caller promised in `# Safety`.
- `unsafe_precondition_assert!` expands to `::core::debug_assert!` with the
  prefix "unsafe precondition violated: ", so it is live only with
  `CONFIG_RUST_DEBUG_ASSERTIONS`, which has no `default` line and is off.
- `unsafe_precondition_assert!` when live: a failure is an ordinary panic and
  reaches `BUG()`.
- `unsafe_precondition_assert!` is not in `rust/kernel/prelude.rs`; it is
  `#[macro_export]`, so the path is `kernel::unsafe_precondition_assert!`.
- `unsafe_precondition_assert!` has no caller in this tree outside its own doc
  example; existing `unsafe fn`s use plain `debug_assert!`, for example
  `CpuId::from_i32_unchecked()` in `rust/kernel/cpu.rs`.

## Core types

**Errors and results**

- `Error::from_errno()`: the only public constructor from an integer.
- `Error::try_from_errno()` and `Error::from_errno_unchecked()`: private to
  `rust/kernel/error.rs`, so code outside that file cannot call them.
- `from_err_ptr()`: after `IS_ERR()` it uses `Error::from_errno_unchecked()` on
  `PTR_ERR()`, with no further range check and no warning.
- `from_err_ptr()` on NULL: returns `Ok(ptr)`; a C function that returns NULL on
  failure needs its own check.
- `from_result()`: the bound is `T: From<i16>` and the errno is cast `as i16`;
  there is no ReturnToKernelPort trait in this tree.
- `Error::to_blk_status()`: `pub(crate)` and only under `CONFIG_BLOCK`.

**Strings and formatting**

- `{:p}` through `fmt!`: hashed like C `%p`, not the raw address; see
  `HashedPtr` in `rust/kernel/fmt.rs`.
- `HashedPtr` output: `0x` prefix, zero-padded to pointer width; the real
  address appears only when `no_hash_pointers` is set.
- Types routed to `HashedPtr`: `*const T`, `*mut T`, `&T`, `&mut T` and
  `NonNull<T>`.
- `pr_info!` and the other macros built on `print_macro!`, and the macros built
  on `dev_printk!` (for example `dev_info!`): expand through `fmt!`, so `{:p}`
  in them is hashed too.
- `fmt::Pointer` in `rust/kernel/fmt.rs`: implemented only in that file; `{:p}`
  on any other type through `fmt!` does not compile.
- `{:?}`, `{:x}` and the other specifiers in `impl_fmt_adapter_forward!`:
  `Adapter` forwards them to `core::fmt` and they never reach `HashedPtr`.
- `{:?}` on a raw pointer, or on a struct deriving `Debug` over one: formatted
  by `core`, so not hashed.
- `c_str!`: matches `$str:expr`, not only a literal; in-tree uses are inside
  macros, over `concat!`, `stringify!`, `file!` or a macro argument.
- `CString::try_from_fmt()`: returns `EINVAL` when the formatted text has an
  interior NUL, besides the allocation failure.
- `CString::try_from_fmt()` and `to_cstring()`: take no flags and allocate with
  `GFP_KERNEL`.
- `as_char_ptr_in_const_context()` in `rust/kernel/str.rs`: the free function
  for `const` code, where the trait method cannot be called.

**Memory allocation**

| `Allocator` function | Arguments |
|---|---|
| `alloc()` | `layout`, `flags`, `nid: NumaNode` |
| `realloc()` | `ptr: Option<NonNull<u8>>`, `layout`, `old_layout`, `flags`, `nid` |
| `free()` | `ptr: NonNull<u8>`, `layout`; no flags, no node |

- `Allocator::MIN_ALIGN`: a required associated constant; every implementation
  must define it.
- `Kmalloc`, `Vmalloc`, `KVmalloc`: implement only `realloc()`, through
  `krealloc_node_align()`, `vrealloc_node_align()` and
  `kvrealloc_node_align()`; see `ReallocFunc` in
  `rust/kernel/alloc/allocator.rs`.
- `Box` and `Vec`: no public function takes a `NumaNode`; they pass
  `NumaNode::NO_NODE` on every allocation.
- `PushError`, `InsertError`, `RemoveError` in
  `rust/kernel/alloc/kvec/errors.rs`: convert to `EINVAL`, not `ENOMEM`.
- `Vec` has no set_len(); the unsafe way to grow the length is `inc_len()`.

**Byte conversion traits**

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

**Atomic operations**

- `core::sync::atomic` atomic types: not used outside the vendored crates and
  `rust/pin-init/examples/`; binder uses `Atomic<T>`, and `rust/kernel/` uses
  `Atomic<T>` and `AtomicFlag`.
- The one import of `core::sync::atomic` outside the vendored crates and
  `rust/pin-init/examples/`: `fence` and `Ordering` in
  `drivers/gpu/nova-core/gsp/cmdq.rs`; no atomic type is involved.
- `.clippy.toml`: has no rule against `core::sync::atomic`; only the module doc
  of `rust/kernel/sync/atomic.rs` says to avoid it.
- `AtomicType` implementations in `rust/kernel/sync/atomic/predefine.rs`:
  `bool`, `i8`, `i16`, `i32`, `i64`, `u32`, `u64`, `isize`, `usize`, `*mut T`
  and `*const T`; there is no `u8` or `u16`.
- `Atomic<T>` over `bool`, `i8`, `i16` and pointers: has `load()`, `store()`,
  `xchg()` and `cmpxchg()`; `add()`, `fetch_add()` and `fetch_sub()` exist only
  where `T: AtomicAdd`, which is the 32-bit, 64-bit and pointer-sized integers.
- `AtomicFlag` in `rust/kernel/sync/atomic.rs`: a boolean flag preferred over
  `Atomic<bool>` when `xchg()` or `cmpxchg()` is needed.
- Ordering: always an explicit value argument; there is no default.
- `load()` accepts only `Relaxed` or `Acquire`, `store()` only `Relaxed` or
  `Release`, and `add()` only `Relaxed`; anything else fails to compile.
- Raw-pointer forms: the free functions `atomic_load()`, `atomic_store()`,
  `xchg()` and `cmpxchg()` in `rust/kernel/sync/atomic.rs`; `atomic_load()` and
  `atomic_store()` stand in for `READ_ONCE()`, `smp_load_acquire()`,
  `WRITE_ONCE()` and `smp_store_release()` on C memory.
- Barriers in `rust/kernel/sync/barrier.rs`: the public functions are only
  `mb()`, `smp_mb()` and `dma_mb()`, each taking `Read`, `Write` or `Full`.
- There is no Rust `smp_rmb()` or `smp_wmb()` function; write `smp_mb(Read)` and
  `smp_mb(Write)`.

## Pinned initialization

**Initializer macros**

| Macro | Defined in | Pinned | Error type |
|---|---|---|---|
| `pin_init!` | `pin_init` crate | yes | `Infallible`, or `? Type` |
| `init!` | `pin_init` crate | no | `Infallible`, or `? Type` |
| `try_pin_init!` | `kernel`, `rust/kernel/init.rs` | yes | `Error`, or `? Type` |
| `try_init!` | `kernel`, `rust/kernel/init.rs` | no | `Error`, or `? Type` |

- All four macros: accept the same syntax, `? Type` included; a `try_` macro
  differs from its plain form only in the default error type.
- `pin_init!` and `init!` with `? Type`: fallible; `pin_init!(Foo { .. }? Error)`
  is valid.
- `pin_init` crate: defines no `try_pin_init!` and no `try_init!`.
- `kernel` crate: defines no `pin_init!` and no `init!`; the names in
  `rust/kernel/prelude.rs` are the `pin_init` crate's, with default
  `Infallible`.
- `try_pin_init!` and `try_init!`: exported from `kernel` and from the prelude;
  each forwards to the macro without `try_`.
- Zeroing trailer: only `..Zeroable::init_zeroed()` is accepted, see
  `get_init_kind()` in `rust/pin-init/internal/src/init.rs`.
- `..Zeroable::zeroed()` inside a macro: rejected; that spelling belongs to
  plain struct expressions, as in `rust/kernel/iommu/pgtable.rs`.
- `&this in` before the path: works in all four macros; binds a `NonNull` to
  the struct being initialized.
- Field names: must be identifiers, so a field of a tuple struct cannot be
  named.
- Field bindings: after each field, a `let` of the field's name is in scope for
  the rest of the initializer.
- Binding type in `pin_init!` and `try_pin_init!`: `Pin<&mut T>` for a `#[pin]`
  field, `&mut T` otherwise.
- Binding type in `init!` and `try_init!`: `&mut T` for every field.
- Binding shadows an outer variable of the same name: after `request,` a later
  `request.irq` reads the field, as in `Registration::new()` in
  `rust/kernel/irq/request.rs`.

**Pinned structs and in-place allocation**

- `pin_init!` and `try_pin_init!`: need `#[pin_data]` on the struct.
- `init!` and `try_init!`: work on a struct with no attribute.
- `#[pin_data]`: structs only, and every field must be named; enums and unions
  are rejected.
- `#[pin_data]` generates `project()`, which turns `Pin<&mut Self>` into
  `Pin<&mut T>` for `#[pin]` fields and `&mut T` for the others; used in
  `PinnedDrop::drop()`, for example in `drivers/gpu/nova-core/gpu.rs`.
- `trait InPlaceInit` in `rust/kernel/init.rs`: the one kernel code uses; every
  method takes `flags`.
- `trait InPlaceInit` in `rust/pin-init/src/alloc.rs`: takes no `flags` and is
  not built for the kernel; the examples in `rust/pin-init/src/lib.rs` use it.
- `pin_init()` and `init()` of `trait InPlaceInit` in `rust/kernel/init.rs`:
  need `Error: From<E>` and return `Result` with `Error`.
- `try_pin_init()` and `try_init()`: need `E: From<AllocError>` and return
  `Result<_, E>`.
- `ListArc`: does not implement `InPlaceInit`; its inherent `pin_init()` and
  `init()` need `E: From<AllocError>` and return `Result<Self, E>`.
- Preallocated slot: there is no pin_slot here; call `new_uninit()` on `Box` or
  `UniqueArc`, then `write_pin_init()` or `write_init()`.
- `stack_pin_init!`: accepts only an initializer with error `Infallible`; binds
  `Pin<&mut T>`.
- `stack_try_pin_init!(let x = init)`: binds `Result<Pin<&mut T>, E>`; with
  `=?` it propagates the error.
- Type annotation in the stack macros: names the value type `T`, not the
  `Result`.
- Stack macros: not in `rust/kernel/prelude.rs`; import them from `pin_init`.
- Failure inside a macro initializer: the fields initialized so far are dropped
  by `DropGuard` in `rust/pin-init/src/__internal.rs`; the struct's own
  `PinnedDrop` does not run.
- Failure in a `pin_chain()` or `chain()` closure: the complete value is
  dropped, so its `PinnedDrop` does run; see the `PinInit` impl for
  `ChainPinInit` in `rust/pin-init/src/lib.rs`.
- **Potentially unsafe usage**: a step in a macro initializer whose undo is
  only in the struct's `PinnedDrop`.
  - Unsafe: when a later field, `?` or `_: { }` block can return `Err`; the
    undo never runs and the memory is freed.
  - Safe: when the step is the last one that can fail, as in
    `Registration::new()` in `rust/kernel/irq/request.rs` and `TagSet::new()`
    in `rust/kernel/block/mq/tag_set.rs`.
  - Safe: when the undo is in the `Drop` of the field's own type; `DropGuard`
    drops that field on failure, as for `gsp_resources` in `Gpu::new()` in
    `drivers/gpu/nova-core/gpu.rs`.

## The driver model

**Device contexts**

- `DeviceContext` has five implementors in `rust/kernel/device.rs`: `Normal`,
  `Bound`, `BoundInternal`, `Core<'a>` and `CoreInternal<'a>`.

| Context | Proves | Reserved for bus abstractions |
|---|---|---|
| `Bound` | device is bound while the reference lives | no; class abstractions hand it out too, e.g. `PwmOps` callbacks |
| `BoundInternal` | same as `Bound` | yes; only use is `receive_buf_callback()` in `rust/kernel/serdev.rs` |
| `Core<'a>` | inside a bus callback; gates e.g. `enable_device_mem()` | no; it is what drivers receive |
| `CoreInternal<'a>` | same as `Core<'a>` | yes; adapters cast the raw pointer to it |

- `Core<'a>` and `CoreInternal<'a>`: `'a` is an invariant brand lifetime;
  callbacks write `Core<'_>`, separate from `'bound`.
- `set_drvdata()` and `drvdata_obtain()`: on `Device<CoreInternal<'a>>` only.
- `drvdata_borrow()`: on any `Ctx: InternalBoundContext`, that is
  `CoreInternal<'a>` and `BoundInternal`.
- `&'bound Device<Bound>` is stored in driver data, not only passed to a
  callback: `pci::Bar` and `IoMem` hold one.
- Context conversion is by `Deref`, not `From`; there are two chains:
  - `CoreInternal<'a>` → `Core<'a>` → `Bound` → `Normal`
  - `BoundInternal` → `Bound` → `Normal`
- To `ARef<Device>`: the generated `From` impls take `&Device<Ctx>`; no
  `ARef<Device<Ctx>>` exists for a non-`Normal` context.
- Upward: `Device::as_bound()` is an `unsafe fn` on `Device<Normal>` returning
  `&Device<Bound>`; the caller guarantees the device stays bound.
- `as_bound()` callers, for example: `parent()` on `auxiliary::Device<Bound>`
  (a safe fn) and `bound_parent_device()` in `rust/kernel/pwm.rs`.
- `AsBusDevice::from_device()`: `unsafe fn from_device(dev: &Device<Ctx>) ->
  &Self`; keeps `Ctx`, subtracts `OFFSET`, makes no bus-type check.

**Driver data and device resources**

- Probe return: `impl PinInit<Self::Data<'bound>, Error> + 'bound`; the data
  type is `type Data<'bound>: Send + 'bound`, which need not be `Self` and
  need not be `'static`; `serdev::Driver` also requires `Sync`.
- PCI `probe()` arguments: `dev: &'bound Device<device::Core<'_>>` and
  `id_info: Option<&'bound Self::IdInfo>`; see `rust/kernel/pci.rs`.
- `'bound` is the span of the binding; driver data may hold `&'bound`
  references to the device and resources that borrow it.
- Unbind order: bus remove calls `unbind()` (`disconnect()` on USB), then
  `post_unbind_callback()` in `rust/kernel/driver.rs` drops the data, then
  `devres_release_all()` runs.
- The last two steps are in `device_unbind_cleanup()` in `drivers/base/dd.c`;
  a `Devres` inside driver data is therefore not yet revoked when the data's
  `Drop` runs.
- The resource constructors below return lifetime-bound values, not `Devres`;
  of them only `irq::Registration::new()` returns a `PinInit`:

| Resource | Constructor | Returns |
|---|---|---|
| PCI BAR | `iomap_region_sized()` on `pci::Device<Bound>` | `Result<pci::Bar<'a, SIZE>>` |
| Platform MMIO | `io_request_by_index()` on `platform::Device<Bound>`, then `iomap_sized()` on the `IoRequest` | `Result<IoMem<'a, SIZE>>` |
| PCI IRQ vectors | `alloc_irq_vectors()` on `pci::Device<Bound>` | `Result<IrqVectorRegistration<'_>>` |
| IRQ handler | `irq::Registration::new()`, from an `IrqRequest<'a>` | `impl PinInit<Self, Error> + 'a` |

- `samples/rust/rust_driver_pci.rs`: `SampleDriverData<'bound>` holds
  `bar: Bar0<'bound>` and `pdev: &'bound pci::Device`; no `Devres`.
- The sample does I/O directly on the `Bar`, in `probe()` and `unbind()`, with
  no `access()` call; `probe()` returns `Ok(SampleDriverData { .. })`.
- `irq::Registration<'a, T>` and `irq::ThreadedRegistration<'a, T>`: hold an
  `IrqRequest<'a>`, no `Devres`; `free_irq()` runs in their drop.
- `irq::Registration::new()` is `unsafe`: the caller must not `mem::forget()`
  the registration.
- `irq::Handler`: `handle(&self)` takes no device argument.
- There is no `request_irq()` method on a bus device.
  - Platform: `request_irq_by_index()` and its siblings, all `unsafe fn`.
  - PCI: `IrqVectorRegistration::index()` gives an `IrqVector`, which converts
    to `IrqRequest` by `From`.
- A wrapper is not needed for a resource held in `Data<'bound>`.
- A wrapper is needed where the holder must be `'static`, for example data
  owned by a `pwm::Chip`, as in `drivers/pwm/pwm_th1520.rs`.
- `Devres<T>` requires `T: Send + 'static`, so it cannot hold a
  `pci::Bar<'bound, SIZE>`; `DevresLt<F: ForLt>` in `rust/kernel/devres.rs` can.
- `into_devres()` on `pci::Bar`, `IoMem` and `ExclusiveIoMem` is the safe way
  to a `DevresLt`.
- The results are aliased `DevresBar`, `DevresIoMem` and
  `DevresExclusiveIoMem`; `DevresLt::new()` itself is `unsafe`.
- `Devres::new()`: returns `Result<Self>`; `Devres` is not a pinned type.
- `new_foreign_owned()` is a method of `cpufreq::Registration`, not of
  `Devres`; the drop-on-unbind helper is `devres::register()`.
- Access through `DevresLt`:
  - `access()` takes `&Device<Bound>`, returns `Result<&F::Of<'a>>`, and needs
    `F: CovariantForLt`.
  - `access_with()` does the same through a closure, for any `ForLt`.
  - `try_access()` returns `Option<DevresGuard>`; `try_access_with()` takes a
    closure.
  - `try_access_with_guard()`: `Devres` has it, `DevresLt` does not.
- `access()` on a device other than the one the wrapper was created with:
  returns `EINVAL`.
- `try_access()` after revocation: returns `None`, not an error code.

## Model gaps

### Other mistakes models make

- Nothing to list here: every mistake found for this subsystem is corrected in
  the section of this guide that covers its subject.
