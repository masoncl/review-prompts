- "ACPI" in `__devm_v4l2_sensor_clk_get()` is `!is_of_node(dev_fwnode(dev))`;
  any device without an OF node takes that path.
- `clock-frequency` present with value 0, or a read error other than `-EINVAL`,
  through `devm_v4l2_sensor_clk_get()`: `ERR_PTR(-EINVAL)` on every platform,
  whether or not a clock was found.
- Clock found on a non-OF node with `clock-frequency` present: `clk_set_rate()`
  to that rate first; its error is returned.
- Clock found on an OF node through `devm_v4l2_sensor_clk_get()`: returned
  untouched, `clock-frequency` is not applied.
- No clock from `devm_clk_get_optional()`, through
  `devm_v4l2_sensor_clk_get()`:

| Case | Result |
|---|---|
| OF node, `clock-frequency` present or not | `ERR_PTR(-ENOENT)`, no fixed clock |
| `CONFIG_COMMON_CLK` off | `ERR_PTR(-ENOENT)` |
| `CONFIG_COMMON_CLK` on, non-OF node, `clock-frequency` absent | `ERR_PTR(-EPROBE_DEFER)` |
| `CONFIG_COMMON_CLK` on, non-OF node, `clock-frequency` valid | fixed-rate clock registered and returned |

- Fixed clock name: "clk-<dev_name>-<id>", or "clk-<dev_name>" when `id` is
  NULL.
- `Documentation/driver-api/media/camera-sensor.rst`: does not tell drivers to
  make the clock optional on ACPI; it says the helper returns a fixed clock
  there.
