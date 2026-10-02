- Label `free_hwmon`: calls `hwmon_dev_release(hdev)` directly, then falls
  into `ida_remove`; there are no separate `kfree()` calls in the unwind.
- Label `ida_remove`: every failure path after `ida_alloc()` ends there;
  `hwmon_dev_release()` does not call `ida_free()`.

| Failure | Frees device and attributes | `goto` label |
|---|---|---|
| `kzalloc_obj()` of the device | nothing to free | `ida_remove` |
| `kzalloc_objs()` of `hwdev->groups` | `hwmon_dev_release()`, direct | `free_hwmon` |
| `__hwmon_create_attrs()` | `hwmon_dev_release()`, direct | `free_hwmon` |
| `"label"` property read or `kstrdup()` | `hwmon_dev_release()`, direct | `free_hwmon` |
| `device_register()` | `put_device()`, which runs the release | `ida_remove` |
| `hwmon_thermal_register_sensors()` | `device_unregister()` | `ida_remove` |
| `hwmon_pec_register()` | `device_unregister()` | `ida_remove` |

- `__hwmon_create_attrs()` failure: it has already called
  `hwmon_free_attrs()` on its array if it allocated one, and
  `hwdev->group.attrs_const` is assigned only on success, so the direct
  release does not free the attributes a second time.
- `hwmon_dev_release()`: reads `hwdev->group.attrs_const`, not
  `hwdev->group.attrs`; the two are a union in `struct attribute_group`.
- `dev_set_name()`: allocates the kobject name, which
  `hwmon_dev_release()` does not free; a failure path added after it cannot
  use `free_hwmon`.
