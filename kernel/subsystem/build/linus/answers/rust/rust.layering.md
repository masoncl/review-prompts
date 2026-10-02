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
