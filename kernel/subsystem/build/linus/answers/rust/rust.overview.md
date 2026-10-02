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
