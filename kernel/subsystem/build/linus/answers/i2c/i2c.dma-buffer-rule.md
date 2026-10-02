- Models have this right; see `__i2c_transfer()` in
  `drivers/i2c/i2c-core-base.c`, which hands `msgs` to the adapter untouched.
