- There is no pm_start_workqueue() here; `pm_start_workqueues()` in
  `kernel/power/main.c` allocates `pm_wq`.
- Allocation: `alloc_workqueue("pm", WQ_UNBOUND, 0)`; it does not pass
  `WQ_FREEZABLE`, so `pm_wq` is not frozen during system suspend.
- Async resume request while tasks are frozen and runtime PM is still enabled
  for the device: `pm_runtime_work()` runs it without waiting for thaw.
- Async resume request after the disable in `device_suspend_late()`:
  `rpm_resume()` returns before it queues anything, for example with
  `-EACCES` or 1.
- Resume request still queued when the PM core reaches the device: run
  synchronously by `pm_runtime_barrier()` or `pm_runtime_disable()`, as
  "Runtime PM in each phase" says.
- Comment in `drivers/pci/pcie/pme.c` that calls `pm_wq` freezable: does not
  match the allocation.
- There is no pm_queue_pm_work() here; the helper is `queue_pm_work()` in
  `include/linux/pm_runtime.h`.
