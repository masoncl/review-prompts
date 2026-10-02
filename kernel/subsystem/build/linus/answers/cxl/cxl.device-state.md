- `devm_cxl_dev_state_create()` in `include/cxl/cxl.h`: wraps
  `_devm_cxl_dev_state_create()` (one leading underscore) in
  `drivers/cxl/core/memdev.c`.
- Driver structure: both requirements are build-time `static_assert()`s in the
  macro: the named member has type `struct cxl_dev_state`, and it is at
  offset 0.
- `to_cxl_memdev_state()` in `drivers/cxl/cxlmem.h`: tests `cxlds->type` only,
  then does `container_of()`; it cannot tell what structure really surrounds
  `cxlds`.
- **Unsafe usage**: passing `CXL_DEVTYPE_CLASSMEM` to
  `devm_cxl_dev_state_create()` with a driver structure other than
  `struct cxl_memdev_state`; `to_cxl_memdev_state()` then returns a non-NULL
  pointer to the wrong type.
  - Safe: `CXL_DEVTYPE_CLASSMEM` through `cxl_memdev_state_create()` in
    `drivers/cxl/core/mbox.c`.
  - Safe: a driver's own structure with `CXL_DEVTYPE_DEVMEM`, as
    `efx_cxl_init()` does.
- **Potentially unsafe usage**: dereferencing the result of
  `to_cxl_memdev_state()` with no NULL test.
  - Unsafe: on a path a `CXL_DEVTYPE_DEVMEM` memdev reaches, where the result
    is NULL; `cxl_mem_probe()` and endpoint decoder commit in
    `drivers/cxl/core/hdm.c` run for both types.
  - Safe: after a NULL test, as `cxl_memdev_poison_enable()` and
    `cxl_memdev_has_poison_cmd()` do.
  - Safe: in a sysfs attribute of `cxl_memdev_attribute_groups`, as
    `security_state_show()` does; `cxl_memdev_alloc()` gives a
    `CXL_DEVTYPE_DEVMEM` memdev `cxl_memdev_type`, which has no `.groups`.
  - Safe: in `__cxl_memdev_ioctl()`; `cxl_memdev_ioctl()` tests
    `cxlds->type == CXL_DEVTYPE_CLASSMEM` first and returns `-ENXIO`
    otherwise.
  - Safe: in `cxl_mem_get_poison()`; its only entry is
    `trigger_poison_list_store()`, and `cxl_poison_attr_visible()` hides that
    attribute when the result is NULL.
  - Safe: in `drivers/cxl/pci.c`, where the state came from
    `cxl_memdev_state_create()` in `cxl_pci_probe()`.
- `cxl_memdev_visible()`: hides only `numa_node`, and only without
  `CONFIG_NUMA`; it does not filter by device type.
- `to_cxl_memdev_state()` dereferences its argument: `cxlmd->cxlds` is NULL
  after `cxl_memdev_shutdown()`, so a path that can run after the parent
  unbinds must read `cxlmd->cxlds` under `cxl_memdev_rwsem` and test it first,
  as `cxl_memdev_ioctl()` does.
