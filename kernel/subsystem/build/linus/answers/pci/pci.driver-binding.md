- Before `pci_device_probe()`: `really_probe()` in `drivers/base/dd.c` sets
  `dev->driver` and calls `pci_dma_configure()`, which calls
  `pci_enable_acs()` and, unless `driver_managed_dma` is set,
  `iommu_device_use_default_domain()`. A failure there means probe is never
  called.
- `pci_dev->driver`: set by `local_pci_probe()` just before the callback, not
  by `pci_device_probe()`.
- `pci_call_probe()` does not call `work_on_cpu()`. It queues the probe with
  `queue_work_on()` on `pci_probe_wq`, a `WQ_PERCPU` workqueue allocated in
  `pci_driver_init()`, and waits with `flush_work()`.
- Target CPU: any CPU in `cpumask_of_node(node)` that is also in
  `housekeeping_cpumask(HK_TYPE_DOMAIN)`, chosen and queued inside one
  `rcu_read_lock()` section. `housekeeping_update()` in
  `kernel/sched/isolation.c` relies on that when it calls
  `pci_probe_flush_workqueue()`.
- Direct call in the calling thread, in exactly these cases: node negative,
  node not below `MAX_NUMNODES`, node offline, `pci_physfn_is_probed()` true,
  or no CPU found in the mask. There is no test of whether the current CPU
  is already on the node.
- VF: `pci_physfn_is_probed()` is true only while its PF has `is_probed` set,
  so a VF is not always probed directly.
- Positive return: `local_pci_probe()` warns and returns 0, leaving
  `pci_dev->driver` set and the runtime PM count held. `really_probe()` never
  sees the positive value.
- After remove returns, `pci_device_remove()` does not call
  `pci_disable_device()` and does not change `current_state`.
- Driver core after `pci_device_remove()`: `pci_dma_cleanup()` first, then
  `device_unbind_cleanup()`, which releases devres. Devres actions therefore
  run after `pcibios_free_irq()`, `pm_runtime_put_sync()` and `pci_dev_put()`.
