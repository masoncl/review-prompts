| Pointer | Created in | Relative to uevent and probe | Removed in, relative to the remove callback |
|---|---|---|---|
| `dev_groups` in `struct class`, `groups` in `struct device_type`, `groups` in `struct device` | `device_add_attrs()` | before `KOBJ_ADD` and probe | `device_remove_attrs()` in `device_del()`, before `bus_remove_device()` unbinds, so before the callback |
| `dev_groups` in `struct bus_type` | `bus_add_device()` | before `KOBJ_ADD` and probe | `bus_remove_device()`, before its `device_release_driver()`, so before the callback |
| `dev_groups` in `struct device_driver` | `really_probe()` | after `KOBJ_ADD`, after `call_driver_probe()` returned 0, before `KOBJ_BIND` | `device_remove()` in `drivers/base/dd.c`, before it calls the callback |
| `groups` in `struct device_driver` | `driver_register()` | driver directory; after `bus_add_driver()` returned, so after `driver_attach()`; before the driver's `KOBJ_ADD` | `driver_unregister()`, before `bus_remove_driver()`, so before `driver_detach()` |
| `drv_groups` in `struct bus_type` | `bus_add_driver()` | driver directory; after `driver_attach()`; before the driver's `KOBJ_ADD` | `bus_remove_driver()`, before `driver_detach()` |
| `bus_groups`, `class_groups` | `bus_register()`, `class_register()` | after `kset_register()` has sent `KOBJ_ADD` for the directory | `bus_unregister()`, `class_unregister()` |
| `default_groups` in `struct kobj_type` | `create_dir()` in `lib/kobject.c`, from `kobject_add_internal()` | with the directory; `kobject_add()` sends no uevent; no probe | `__kobject_del()`, before `sysfs_remove_dir()`; no remove callback |

- Probe before the `kobject_uevent()` call for `KOBJ_ADD` in `device_add()`:
  cannot happen; `__driver_probe_device()` returns `-EPROBE_DEFER` until
  `device_add()` has called `dev_set_ready_to_probe()`, which comes after
  `kobject_uevent()`.
- `dev_groups` of the driver, creation fails: `really_probe()` calls
  `device_remove()`, so the remove callback runs, and the bind fails.
- `drv_groups` creation fails: `bus_add_driver()` prints an error and still
  returns 0.
- `driver_override` in `struct bus_type`: a `bool`, not a group pointer; when
  set, `bus_add_device()` creates `driver_override_dev_group` right after the
  bus `dev_groups`, and `bus_remove_device()` removes it.
