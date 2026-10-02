- `i2c_bus_type`: holds adapters as well as clients; `i2c_register_adapter()`
  puts the adapter's device on it with type `i2c_adapter_type`, clients have
  `i2c_client_type`.
- Iterating `i2c_bus_type` or an adapter's children yields both kinds (and
  mux child adapters among the children); `i2c_verify_client()` and
  `i2c_verify_adapter()` tell them apart by `dev->type`.
- Target mode outside `struct i2c_algorithm`: only slave spellings exist:
  `i2c_slave_register()`, `i2c_slave_event()`, `enum i2c_slave_event`,
  `I2C_CLIENT_SLAVE`, `slave_cb`, `CONFIG_I2C_SLAVE`. The core has no
  target-named functions, events or client flags.
- SMBus emulation, outside atomic mode: `__i2c_smbus_xfer()` emulates when
  `smbus_xfer` is NULL, and also when `smbus_xfer` returns `-EOPNOTSUPP` and
  `master_xfer` is set.
- `i2c_smbus_xfer_emulated()`: calls `__i2c_transfer()`, not
  `i2c_transfer()`; `i2c_smbus_xfer()` already holds the lock.
- `i2c_transfer()` on a mux-locked child (`i2c_mux_lock_ops`): holds only
  `parent->mux_lock` around `select`; the parent's lock is taken later, inside
  the `i2c_transfer()` on the parent.
- Mux child adapter's `dev.parent`: the parent adapter, set in
  `i2c_mux_add_adapter()`. The mux device (`muxc->dev`) is not the
  `dev.parent`; it is linked by the `mux_device` and `channel-%u` sysfs
  symlinks.
- `struct i2c_atr` (`drivers/i2c/i2c-atr.c`, API in
  `include/linux/i2c-atr.h`): an address translator. Like a mux it creates one
  child adapter per channel, but a transfer rewrites message addresses to
  aliases valid on the parent bus instead of selecting a channel.
- `struct i2c_atr` differs from `struct i2c_mux_core` in three relations:
  - child adapter's `dev.parent` is `desc->parent`, or the ATR device when
    that is NULL, not the parent adapter;
  - `i2c_atr_lock_ops` takes `atr->lock`, one mutex shared by all channels,
    and touches no parent lock;
  - aliases are attached and detached from a notifier on `i2c_bus_type`
    (`i2c_atr_bus_notifier_call()`) when a client is added to or removed from
    a child adapter.
- `i2c_parent_is_i2c_adapter()`: looks only at the direct `dev.parent`;
  `i2c_adapter_depth()` walks every ancestor. They disagree for an adapter
  whose parent is a client device, as under an ATR.
- Address uniqueness: `i2c_check_addr_busy()` compares
  `i2c_encode_flags_to_addr()` values, so a client with `I2C_CLIENT_SLAVE` or
  `I2C_CLIENT_TEN` does not collide with a plain 7-bit client of the same
  number.
- `struct i2c_client` creation: not reserved to the core; whoever calls
  `i2c_new_client_device()` gets the pointer and passes it to
  `i2c_unregister_device()` later. Chip drivers do this for secondary
  addresses with `i2c_new_dummy_device()` or `i2c_new_ancillary_device()`.
- `struct i2c_client` memory of a registered client: freed in
  `i2c_client_dev_release()`, the `release` of `i2c_client_type`;
  `i2c_unregister_device()` does not free it, it ends in
  `device_unregister()`.
- Unregistered `struct i2c_client`: `i2cdev_open()` in
  `drivers/i2c/i2c-dev.c` and `i2c_detect()` build one with `kzalloc_obj()`
  and never register it; its `dev` is all zeroes. The `detect` callback gets
  such a client.
- Core-tracked clients: only `i2c_detect_address()` (onto `driver->clients`)
  and `new_device_store()` (onto `adap->userspace_clients`) link a client
  through `client->detected`. Clients created any other way are on neither
  list.
