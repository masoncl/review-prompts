These are conventions that the maintainers of the I2C subsystem ask for. No
code in a kernel tree states them, so they are kept by hand and inserted as
they are.

- A driver must declare an initialized array of `struct i2c_device_id` const.
- New or changed entries of such an array should use named initializers.
  Positional entries in existing tables are not bugs.
