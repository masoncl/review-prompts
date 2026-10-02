- There is no __i2c_add_numbered_adapter() here; `i2c_allocate_adapter_id()` in
  `drivers/i2c/i2c-core-base.c` allocates the number, called from
  `i2c_register_adapter()`.
- `i2c_add_adapter()`: overwrites `adapter->nr` with the "i2c" alias id or -1,
  then calls `i2c_register_adapter()`; a number preset by the driver is lost.
- `devm_i2c_add_adapter()` goes through `i2c_add_adapter()`, so it cannot take
  a number preset by the driver.
- Checks at the start of `i2c_register_adapter()`, in order:

| Check | Result |
|---|---|
| `is_registered` false (core not initialised) | -EAGAIN, `WARN_ON()` |
| `adap->name[0]` empty | -EINVAL, `WARN()` |
| `adap->algo` NULL | -EINVAL, `pr_err()` |

- Transfer callbacks (`xfer`, `smbus_xfer`): no test and no warning.
- `algo->functionality`: not tested, but called during registration by
  `i2c_setup_host_notify_irq_domain()`; NULL oopses inside
  `i2c_register_adapter()`.
- `retries`, `owner`, `dev.parent`, `class`, `quirks`: neither checked nor
  defaulted; only `lock_ops` and `timeout` get defaults.
- `i2c_allocate_adapter_id()`: runs after the field checks and the host-notify
  domain setup; failure is logged with `pr_err()`.
- `i2c_allocate_adapter_id()` with a fixed `nr` already taken: -EBUSY; the
  -ENOSPC from `idr_alloc()` is translated only when `nr` is not -1.
- `i2c_init_recovery()`: only -EPROBE_DEFER fails registration; its -EINVAL
  for incomplete `bus_recovery_info` is ignored and the pointer is set to NULL.
- `i2c_setup_smbus_alert()` failure (`CONFIG_I2C_SMBUS`): fails registration
  after `device_add()`; already created clients are removed with
  `i2c_deregister_clients()`.
- Failures before `i2c_allocate_adapter_id()` return without touching
  `i2c_adapter_idr`; later ones remove the id.
