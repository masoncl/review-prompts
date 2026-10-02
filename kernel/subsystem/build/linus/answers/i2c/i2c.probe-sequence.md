- `client->irq`: reloaded from `client->init_irq` at the start of every probe;
  the lookup runs only when that is 0.
- OF IRQ lookup: `fwnode_irq_get_byname()` for "irq", then `fwnode_irq_get()`
  index 0 when that returned -EINVAL or -ENODATA.
- Wake IRQ setup: keyed on `I2C_CLIENT_WAKE` in `client->flags`, not on a
  property read in probe; the ACPI IRQ lookup can set the flag during probe.
- `client->debugfs`: directory created under `client->adapter->debugfs` just
  before the driver's probe.
- `dev_pm_domain_attach()`: called with `PD_FLAG_DETACH_POWER_OFF`.
- `i2c_device_remove()` does not call `dev_pm_domain_detach()`;
  `device_unbind_cleanup()` in `drivers/base/dd.c` does, after
  `devres_release_all()`, on unbind and on failed probe.
- `i2c_device_remove()` after the driver's remove, in order:
  1. `debugfs_remove_recursive()` on `client->debugfs`;
  2. `devres_release_group()` on `client->devres_group_id`;
  3. `dev_pm_clear_wake_irq()`, then `device_init_wakeup()` with false;
  4. `client->irq = 0`;
  5. `pm_runtime_put()` on the adapter if `I2C_CLIENT_HOST_NOTIFY`.
- Device-managed resources: released inside `i2c_device_remove()`, in step 2,
  after the driver's remove returns, before the wake IRQ is cleared and before
  the driver core detaches the PM domain.
- Failed driver probe: `i2c_device_probe()` undoes steps 1 to 3 and the
  adapter runtime PM reference, but leaves `client->irq` set.
