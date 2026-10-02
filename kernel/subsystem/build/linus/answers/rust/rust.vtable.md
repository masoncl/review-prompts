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
