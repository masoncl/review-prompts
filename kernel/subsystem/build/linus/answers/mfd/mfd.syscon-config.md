- `reg-io-width`: sets both `reg_stride` and `val_bits`; `reg_bits` stays 32
  from `syscon_regmap_config`.
- Width check: `of_syscon_register()` has none; `regmap_mmio_get_min_stride()`
  in `drivers/base/regmap/regmap-mmio.c` accepts `val_bits` 8, 16 and 32 only.
- `reg-io-width = <8>`: allowed by the enum in
  `Documentation/devicetree/bindings/mfd/syscon-common.yaml`, fails in
  `regmap_init_mmio()` with `-EINVAL`.
- Resource smaller than the width: `of_syscon_register()` fails with
  `-EFAULT`.
- `max_register` of 0 (resource exactly one register): `max_register_is_0` is
  set, so the limit is still enforced.
- Hardware spinlock: `of_syscon_register()` only sets `use_hwlock`,
  `hwlock_id` and `hwlock_mode = HWLOCK_IRQSTATE`; it does not call
  `hwspin_lock_request_specific()` and sets no `lock` or `unlock` callback.
- `__regmap_init()` in `drivers/base/regmap/regmap.c`: requests the lock and
  fails with `-ENXIO` if it gets none.
- `of_hwspin_lock_get_id()` errors: `-ENOENT` is ignored; `-EPROBE_DEFER`
  fails the lookup silently; any other error fails it with a `pr_err()`.
- `CONFIG_HWSPINLOCK` off: the `of_hwspin_lock_get_id()` stub returns 0, so a
  `hwlocks` property is ignored and the regmap is created without it.
- Without a hardware spinlock: the regmap locks with a spinlock because the
  `regmap_mmio` bus sets `fast_io`; `syscon_regmap_config` does not set it.
