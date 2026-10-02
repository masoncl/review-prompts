- `include/linux/i2c.h` has three `#if IS_ENABLED(CONFIG_I2C)` blocks; in
  them only these names have an `#else` stub, all returning `NULL`:
  `i2c_verify_client()`, `i2c_find_device_by_fwnode()`,
  `i2c_find_adapter_by_fwnode()`, `i2c_get_adapter_by_fwnode()`.
- `i2c_get_adapter()`, `i2c_put_adapter()`: prototypes inside the guard, no
  stub.
- `module_i2c_driver()`, `builtin_i2c_driver()`, `i2c_add_driver()`: defined
  inside the guard, so they do not exist without `CONFIG_I2C`.
- Inline helpers inside the guard, absent without `CONFIG_I2C`: for example
  `i2c_8bit_addr_from_msg()`, `i2c_check_functionality()`,
  `i2c_check_quirks()`, `i2c_client_has_driver()`, `i2c_master_send()`.
- Inline helpers outside any guard: for example `i2c_get_clientdata()`,
  `i2c_lock_bus()`, `i2c_mark_adapter_suspended()`.
- Unguarded prototypes with no stub, which compile without `CONFIG_I2C` and
  fail at link: `i2c_verify_adapter()`, `i2c_match_id()`,
  `i2c_get_match_data()`, `i2c_recover_bus()`, `i2c_generic_scl_recovery()`,
  `i2c_for_each_dev()`, and the externs `i2c_bus_type`, `i2c_adapter_type`,
  `i2c_client_type`.
- `i2c_of_match_device()`: not in `include/linux/i2c.h`; it is in
  `drivers/i2c/i2c-core.h` under `#ifdef CONFIG_OF`, stub returns `NULL`.
- OF block: guard is `IS_ENABLED(CONFIG_OF)` alone, with no test of
  `CONFIG_I2C`.
- `of_i2c_get_board_info()`: with `CONFIG_OF` on it is a bare prototype,
  defined in `drivers/i2c/i2c-core-of.c`; with `CONFIG_OF` on and
  `CONFIG_I2C` off a caller fails at link.
- ACPI block: guard is `IS_REACHABLE(CONFIG_ACPI) && IS_REACHABLE(CONFIG_I2C)`,
  the only `IS_REACHABLE()` guard in the header.
- `i2c_acpi_new_device_by_fwnode()` stub: returns `ERR_PTR(-ENODEV)`;
  `i2c_acpi_find_adapter_by_handle()` stub: returns `NULL`.
- `CONFIG_I2C_BOARDINFO`: a promptless bool with `default y` inside `if I2C`
  in `drivers/i2c/Kconfig`; the header tests it with `#ifdef`.
- `i2c_slave_register()`, `i2c_slave_unregister()`, `i2c_slave_event()`:
  prototypes are unguarded and have no stub; a caller built with
  `CONFIG_I2C_SLAVE` off compiles and fails at link.
- `enum i2c_slave_event` and the `i2c_slave_cb_t` typedef: unguarded.
- `i2c_detect_slave_mode()`: the only target-mode function in
  `include/linux/i2c.h` with a stub; under
  `#if IS_ENABLED(CONFIG_I2C_SLAVE)`, the `#else` stub returns `false`.
- `slave_cb` in `struct i2c_client`: exists only under
  `#if IS_ENABLED(CONFIG_I2C_SLAVE)`.
- `drivers/i2c/i2c-core-slave.c`: added by `i2c-core-$(CONFIG_I2C_SLAVE)` in
  `drivers/i2c/Makefile`, so it is linked into `i2c-core.o`, not built as its
  own module.
- **Potentially unsafe usage**: a bus driver setting `reg_slave`,
  `unreg_slave`, `reg_target` or `unreg_target` in its
  `struct i2c_algorithm`.
  - Unsafe: when the initialisers can be compiled with `CONFIG_I2C_SLAVE`
    off; the members do not exist and the build fails.
  - Safe: the driver's Kconfig entry has `select I2C_SLAVE`, as `I2C_RCAR` in
    `drivers/i2c/busses/Kconfig`; `drivers/i2c/busses/i2c-rcar.c` has no
    `#if` around its initialisers.
  - Safe: the initialisers and callbacks are inside
    `#if IS_ENABLED(CONFIG_I2C_SLAVE)`, as in
    `drivers/i2c/busses/i2c-aspeed.c`.
  - Safe: the initialisers and callbacks are inside `#ifdef` of a driver
    option that has `select I2C_SLAVE`, as `CONFIG_I2C_PXA_SLAVE` in
    `drivers/i2c/busses/i2c-pxa.c`.
  - Safe: the initialisers are in a file that the Makefile builds only for a
    driver option that has `select I2C_SLAVE`, as
    `drivers/i2c/busses/i2c-at91-slave.c` for
    `CONFIG_I2C_AT91_SLAVE_EXPERIMENTAL`.
- `CONFIG_I2C_STUB`: has `depends on m`, so `drivers/i2c/i2c-stub.c` is never
  built in.
- KUnit: no suite under `drivers/i2c/`, but KUnit tests elsewhere fill in
  `struct i2c_adapter` and `struct i2c_algorithm` themselves, for example
  `drivers/gpu/drm/tests/drm_connector_test.c` and
  `drivers/gpu/drm/amd/display/amdgpu_dm/tests/amdgpu_dm_hdcp_test.c`.
- `drivers/of/unittest.c`: fills in its own `struct i2c_adapter`,
  `struct i2c_algorithm` and `struct i2c_driver` under
  `IS_BUILTIN(CONFIG_I2C)` and `CONFIG_OF_OVERLAY`.
- Rust: `rust/bindings/bindings_helper.h` includes `include/linux/i2c.h`;
  `rust/kernel/i2c.rs` is compiled only for `CONFIG_I2C = "y"` and writes
  `struct i2c_driver` members by name; `SAMPLE_RUST_DRIVER_I2C` and
  `SAMPLE_RUST_I2C_CLIENT` in `samples/rust/Kconfig` have `depends on I2C=y`.
- `include/trace/events/i2c_slave.h`: third tracepoint header of the I2C
  core, instantiated with `CREATE_TRACE_POINTS` in
  `drivers/i2c/i2c-core-slave.c`, so it is compiled only with
  `CONFIG_I2C_SLAVE`.
- `include/trace/events/i2c_slave.h` names the `enum i2c_slave_event` values
  in three places: the `TRACE_DEFINE_ENUM()` lines, `show_event_type()`, and
  the `switch` in `TP_fast_assign()` that decides whether `val` is copied; a
  new value falls to `default` and records no byte.
- `include/trace/events/smbus.h`: repeats the `I2C_SMBUS_*` protocol table in
  each of its four events and sizes `buf` as `I2C_SMBUS_BLOCK_MAX + 2` in
  three of them.
