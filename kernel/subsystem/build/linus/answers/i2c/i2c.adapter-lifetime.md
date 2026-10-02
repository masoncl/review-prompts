- `i2c_del_adapter()` start: replaces the adapter's `i2c_adapter_idr` slot with
  NULL, so `i2c_get_adapter()` fails from then on; the number is freed only
  after the wait.
- `memset()` of `adap->dev` after the wait also clears `dev.parent`, the
  firmware node pointers and the drvdata: `i2c_get_adapdata()` returns NULL
  after `i2c_del_adapter()`, and `dev.parent` is NULL on a re-add unless the
  driver sets it again.
- Adapter memory must be zeroed before the first registration: the core never
  initialises `addrs_in_instantiation`, and a stale bit makes
  `i2c_lock_addr()` return -EBUSY for that address.
- **Potentially unsafe usage**: registering the adapter with
  `devm_i2c_add_adapter()`.
  - Unsafe: when the driver's remove callback disables something the transfer
    path needs (clock, IRQ, runtime PM, reset); `devm_i2c_del_adapter()` runs
    only after remove returns, and client remove callbacks inside
    `i2c_del_adapter()` still transfer.
  - Safe: when no remove callback tears down anything the transfer path needs,
    because all of it was acquired through devres before
    `devm_i2c_add_adapter()`, as `hisi_i2c_probe()` in
    `drivers/i2c/busses/i2c-hisi.c` does (that driver has no remove
    callback); `release_nodes()` in `drivers/base/devres.c` releases in
    reverse order, so the adapter goes first.
  - Safe: `i2c_add_adapter()` with `i2c_del_adapter()` as the first step of
    remove, as `meson_i2c_remove()` in `drivers/i2c/busses/i2c-meson.c` does;
    `i2c_deregister_clients()` runs the client removes there.
