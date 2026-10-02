- **Potentially unsafe usage**: calling `__i2c_transfer()` or
  `__i2c_smbus_xfer()` from outside the core.
  - Unsafe: when the calling task does not hold the bus lock of the adapter it
    passes while another task can transfer on that adapter; neither function
    locks that adapter, so two `master_xfer` calls run at once.
  - Unsafe: on `muxc->parent` from the select or deselect of a mux-locked mux
    that has not locked the parent itself; the core holds only the parent's
    `mux_lock` there, not its bus lock.
  - Safe: between `i2c_lock_bus(adap, I2C_LOCK_SEGMENT)` and
    `i2c_unlock_bus()` on the same adapter, as `regmap_sccb_read()` in
    `drivers/base/regmap/regmap-sccb.c` and `iic_tpm_read()` in
    `drivers/char/tpm/tpm_i2c_infineon.c` do; this is the lock
    `i2c_transfer()` takes around `__i2c_transfer()`.
  - Safe: on `muxc->parent` from the select or deselect of a parent-locked
    mux when the mux core calls it; `i2c_parent_lock_bus()` or
    `i2c_parent_trylock_bus()` has locked the parent before
    `__i2c_mux_master_xfer()` or `__i2c_mux_smbus_xfer()` runs.
    `pca954x_select_chan()` and `mlxcpld_mux_select_chan()` do this.
  - Safe: the same callback or its helper called by the driver itself,
    outside a child transfer, after the driver locks the parent with
    `i2c_lock_bus()`: `idle_state_store()` in
    `drivers/i2c/muxes/i2c-mux-pca954x.c` and `pca9541_probe()`.
- `pca954x_reg_write()` in `drivers/i2c/muxes/i2c-mux-pca954x.c`: calls
  `__i2c_smbus_xfer()`; that file has no call to `__i2c_transfer()`, and there
  is no pca954x_regw() here.
- `drivers/media/dvb-frontends/rtl2830.c`: the regmap bus callbacks, for
  example `rtl2830_regmap_read()`, call `__i2c_transfer()` with no locking of
  their own; wrappers such as `rtl2830_update_bits()` take the lock, and
  `rtl2830_select()` calls regmap bare because the core already holds it.
- `drivers/media/dvb-frontends/rtl2832.c`: a mux-locked mux; it calls neither
  `i2c_lock_bus()` nor `__i2c_transfer()`.
- `drivers/mfd/88pm860x-i2c.c`: takes the bus lock but calls
  `adap->algo->master_xfer()` directly, so it skips the suspend check, the
  quirk check and the retry loop of `__i2c_transfer()`; it is not an example
  of the unlocked functions.
