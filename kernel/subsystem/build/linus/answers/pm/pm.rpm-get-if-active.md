- `pm_runtime_get_if_in_use()`: with the status `RPM_ACTIVE`, takes a
  reference and returns 1 when the usage counter is non-zero, and also when
  `dev->power.ignore_children` is clear and `child_count` is above zero,
  even with a usage counter of zero; see `pm_runtime_get_conditional()`.
- `Documentation/power/runtime_pm.rst`: describes
  `pm_runtime_get_if_in_use()` without the child condition.
- **Potentially unsafe usage**: testing the result only for non-zero, then
  touching the device and doing a put.
  - Unsafe: with `CONFIG_PM` on and runtime PM disabled, `-EINVAL` passes the
    test with no reference taken; a put other than `pm_runtime_put_noidle()`
    then makes `rpm_drop_usage_count()` warn of underflow, and any put can
    take another holder's reference.
  - Safe: with `CONFIG_PM` off; `pm_runtime_put_noidle()` is an empty stub and
    the other puts reach the stubs of `__pm_runtime_idle()` and
    `__pm_runtime_suspend()`, which touch no counter.
  - Safe: put only when the result is above zero, as `ipu6_buttress_isr()` in
    `drivers/media/pci/intel/ipu6/ipu6-buttress.c` does.
  - Safe: skip the access and the put on any result `<= 0`, as
    `mtk_iommu_tlb_flush_range_sync()` in `drivers/iommu/mtk_iommu.c` does.
