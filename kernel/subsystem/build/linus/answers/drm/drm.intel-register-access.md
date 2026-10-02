- Wait names: every one carries a unit. intel_de_wait(),
  intel_de_wait_custom(), intel_de_wait_for_set(), intel_de_wait_for_clear()
  and intel_de_wait_fw() are not in this tree.

| Function | Reads with | Context |
|---|---|---|
| `intel_de_wait_us()`, `intel_de_wait_ms()` | `intel_de_read()` | may sleep |
| `intel_de_wait_for_set_us()`, `intel_de_wait_for_set_ms()` | `intel_de_read()`, no out value | may sleep |
| `intel_de_wait_for_clear_us()`, `intel_de_wait_for_clear_ms()` | `intel_de_read()`, no out value | may sleep |
| `intel_de_wait_fw_ms()` | `intel_de_read_fw()` | may sleep |
| `intel_de_wait_fw_us_atomic()` | `intel_de_read_fw()` | busy-waits |

- `intel_de_wait_for_register()`: exists, but is static in
  `drivers/gpu/drm/i915/display/intel_de.c`; callers use the functions above.
- `intel_wait_for_register()` and `__intel_wait_for_register()`: exist in
  `drivers/gpu/drm/i915/intel_uncore.h` for i915 core only;
  `drivers/gpu/drm/xe/compat-i915-headers/intel_uncore.h` has no wait helper,
  so display code cannot use them.
- `wait_for()`: lives in `drivers/gpu/drm/i915/i915_wait_util.h` and has no
  users under `drivers/gpu/drm/i915/display/`; display polls arbitrary
  conditions with `poll_timeout_us()` from `include/linux/iopoll.h`.
- Register type: `intel_reg_t` (typedef of `i915_reg_t` in
  `drivers/gpu/drm/i915/display/intel_display_reg_defs.h`), with
  `intel_reg_offset()` in place of `i915_mmio_reg_offset()`.
- First argument: `struct intel_display *` for every `intel_de_` function;
  none accepts i915.
- DMC wakelock: not taken by `intel_de_read_fw()`, `intel_de_write_fw()`,
  `intel_de_rmw_fw()`, `intel_de_read_notrace()`, `intel_de_write_notrace()`,
  `intel_de_read8()`, `intel_de_write8()`, `intel_de_read16()`,
  `intel_de_wait_fw_ms()` or `intel_de_wait_fw_us_atomic()`.
- `intel_de_write_dsb()` with a NULL `dsb`: falls back to
  `intel_de_write_fw()`, not `intel_de_write()`.
- I915_READ, I915_WRITE and POSTING_READ: not in this tree.
