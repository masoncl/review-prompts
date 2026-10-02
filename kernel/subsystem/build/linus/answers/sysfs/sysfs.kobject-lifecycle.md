- After a failed `kobject_add_internal()`: the kset is left, the parent put and
  `kobj->parent` cleared; the name is all that remains allocated.
- Name: freed by `kobject_cleanup()` itself, after `release()` returned, from a
  pointer saved at entry; `release()` does not free it.
- `kset_register()` failure: frees the name and sets it to NULL itself;
  callers such as `kset_create_and_add()` and `bus_register()` then free the
  container with `kfree()`.
- `KOBJ_REMOVE` on the final put: sent inside `__kobject_del()`, only if
  `KOBJ_ADD` was sent and `KOBJ_REMOVE` was not, after `default_groups` are
  removed and before `sysfs_remove_dir()`; never sent for a kobject that is
  not in sysfs.
- `CONFIG_DEBUG_KOBJECT_RELEASE`: `kobject_release()` defers the whole of
  `kobject_cleanup()` by 1 to 4 seconds, so the directory and its files stay
  in sysfs after the final `kobject_put()` returned.
- Code that needs the directory gone at a known point: calls `kobject_del()`
  before the put.
- `__kobject_del()`: clears `kobj->parent` but does not put the parent.
- Parent reference: `kobject_del()` puts it right after `__kobject_del()`;
  without an explicit delete, `kobject_cleanup()` puts it last, after
  `release()` and after the name is freed.
- `struct kobj_type` with no `release()`: `kobject_cleanup()` only prints with
  `pr_debug()`; `device_release()` in `drivers/base/core.c` is what uses
  `WARN()`, for a `struct device`.
