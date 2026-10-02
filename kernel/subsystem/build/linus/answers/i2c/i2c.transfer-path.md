- Order for `i2c_transfer()`, each step returning before the adapter is called:
  1. `__i2c_lock_bus_helper()`: in atomic mode a failed `i2c_trylock_bus()`
     returns `-EAGAIN`.
  2. `__i2c_transfer()`, `master_xfer` is NULL: `-EOPNOTSUPP`.
  3. `WARN_ON(!msgs || num < 1)`: `-EINVAL`.
  4. `__i2c_check_suspended()` in `drivers/i2c/i2c-core.h`: `-ESHUTDOWN`.
  5. `adap->quirks` set and `i2c_check_for_quirks()` fails: `-EOPNOTSUPP`.
- Steps 2 to 5 are in `__i2c_transfer()`, so a caller that holds the lock and
  calls it directly, as `__i2c_mux_master_xfer()` does, gets them too.
- Step 1 `-EAGAIN`: comes from outside the retry loop and is never retried.
- Step 2 tests `master_xfer` only; an adapter that sets only
  `master_xfer_atomic` fails every transfer with `-EOPNOTSUPP`.
- The adapter pointer is not tested; `__i2c_transfer()` dereferences it first.
- `retries`: the core never gives it a default. Of `retries` and `timeout`,
  `i2c_register_adapter()` defaults only `timeout` (to `HZ` when 0).
- `retries` of 0: one attempt, so `-EAGAIN` from the callback goes straight
  back to the caller.
- `retries` is set by whoever fills in the adapter; search for `retries =`.
  For example the `I2C_RETRIES` ioctl in `drivers/i2c/i2c-dev.c` sets it,
  `__i2c_bit_add_bus()` in `drivers/i2c/algos/i2c-algo-bit.c` overwrites it
  with 3, and `i2c_mux_add_adapter()` and `i2c_atr_add_adapter()` copy the
  parent's.
- `timeout` in the core: compared only after a callback has returned
  `-EAGAIN`; the core does not bound one callback invocation with it.
