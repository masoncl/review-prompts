# PCI Subsystem

## Main structures

### Objects and how they relate

- Global lists: there is no global pci_devices list. A `struct pci_dev` is on
  `pci_bus->devices` and in the driver core's list for `pci_bus_type`;
  `pci_get_device()` searches the latter with `bus_find_device()`. The global
  list of buses is `pci_root_buses`, of root buses only.
- `struct pci_host_bridge` per domain: a domain can hold several, as under
  ACPI; each is identified by domain plus root bus number, and
  `pci_register_host_bridge()` rejects a pair for which `pci_find_bus()`
  already finds a bus, root or child.
- `pci_register_host_bridge()`: static in `drivers/pci/probe.c`. Its callers
  are `pci_scan_root_bus_bridge()`, which `pci_host_probe()` calls, and
  `pci_create_root_bus()`, which allocates the `struct pci_host_bridge`
  itself.
- `struct pci_ops` on a child bus: `pci_alloc_child_bus()` takes the host
  bridge's `child_ops` when set, else the parent bus's `ops`. The root bus
  gets the host bridge's `ops`.
- Root bus windows: held on the `pci_bus->resources` list, not in
  `pci_bus->resource[]`, which `pci_register_host_bridge()` leaves empty. The
  child bus of a transparent bridge has both once `pci_read_bridge_bases()`
  has run. `pci_bus_for_each_resource()` walks both.
- SR-IOV virtual bus (`virtfn_add_bus()` in `drivers/pci/iov.c`): besides
  `self`, `pci_bus->bridge` and every `pci_bus->resource[]` slot are NULL.
- VF created by `pci_iov_add_virtfn()`: its `resource[]` entries are children
  of the PF's `PCI_IOV_RESOURCES` entries, not of a bridge window, and its
  `dev.parent` is the PF's parent.
- Reference chain: a `struct pci_dev` holds a reference on its
  `struct pci_bus`; a bus holds one on `bus->bridge`; a `struct pci_slot`
  holds one on its bus; a VF holds one on its PF.
- Bound driver: `struct pci_dev` has its own `driver` field, set in
  `local_pci_probe()` before `probe` is called and cleared in
  `pci_device_remove()`. The core's reset, error-recovery, PM and SR-IOV
  paths read it rather than `to_pci_driver()` of `dev.driver`; the PM
  callbacks in `drivers/pci/pci-driver.c` still take `struct dev_pm_ops`
  from `dev->driver->pm`.
- `struct pci_saved_state`: a detached copy made by
  `pci_store_saved_state()` and put back into the `struct pci_dev` buffers by
  `pci_load_saved_state()`. `pci_save_state()` and `pci_restore_state()` use
  `pci_dev->saved_config_space` and the `struct pci_cap_saved_state` entries
  on `pci_dev->saved_cap_space`.
- `struct pci_slot`: also created with no hotplug driver, for example by
  `drivers/acpi/pci_slot.c`, so `slot->hotplug` may be NULL. A slot numbered
  `PCI_SLOT_ALL_DEVICES` covers every device on the bus, except with
  `per_func_slot`, which is set under `CONFIG_S390`.
- `struct pci_error_handlers`: called, for example, from
  `pcie_do_recovery()`, from the reset path (`pci_dev_save_and_disable()` and
  `pci_dev_restore()` in `drivers/pci/pci.c`), and from arch recovery code
  such as `arch/powerpc/kernel/eeh_driver.c`.
- `struct pcie_device` and `struct pcie_port_service_driver`: private to
  `drivers/pci/pcie/portdrv.h`. There are five services; the one easy to
  miss is `PCIE_PORT_SERVICE_BWCTRL`, whose state is
  `struct pcie_bwctrl_data` at `pci_dev->link_bwctrl`.
- `struct pci_pwrctrl` (`include/linux/pci-pwrctrl.h`): context of a platform
  device that powers a PCI device and shares its OF node. The host
  controller driver creates and powers these with
  `pci_pwrctrl_create_devices()` and `pci_pwrctrl_power_on_devices()`; the
  code in `drivers/pci/pwrctrl/core.c` does not rescan the bus and creates
  no device link.
- `struct pci_tsm` (`include/linux/pci-tsm.h`): per-function TEE security
  context at `pci_dev->tsm`, under `CONFIG_PCI_TSM`; `dsm_dev` names the
  function that manages it, which may be another `struct pci_dev`.
- `struct pci_ide` (`include/linux/pci-ide.h`): one Selective IDE Stream
  between an endpoint and its Root Port, under `CONFIG_PCI_IDE`;
  `host_bridge_stream` is allocated from the `struct pci_host_bridge`, and
  each partner's `stream_index` from that port's `struct pci_dev`.

## Where to look

**Newer facilities**

| Job | File under `drivers/pci/` | Who calls it; what is easy to get wrong |
|---|---|---|
| Power before enumeration | `drivers/pci/pwrctrl/core.c`; drivers `drivers/pci/pwrctrl/generic.c` (slots, `CONFIG_PCI_PWRCTRL_GENERIC`), `drivers/pci/pwrctrl/pci-pwrctrl-pwrseq.c`, `drivers/pci/pwrctrl/pci-pwrctrl-tc9563.c`. No drivers/pci/pwrctrl/slot.c, no pci_pwrctrl_register(). | Controller drivers, not the PCI core: `drivers/pci/probe.c` and `drivers/pci/bus.c` make no pwrctrl call. `pci_pwrctrl_create_devices()` and `pci_pwrctrl_power_on_devices()` are called from controller drivers, for example `drivers/pci/controller/dwc/pcie-qcom.c`. Probe of the three pwrctrl drivers applies no power; it sets `power_on` and `power_off` in `struct pci_pwrctrl`; power is applied by `pci_pwrctrl_power_on_devices()`, which returns `-EPROBE_DEFER` when a pwrctrl platform device exists and its driver is not bound. |
| Link bandwidth control and notification | `drivers/pci/pcie/bwctrl.c`, built under `CONFIG_PCIEPORTBUS`; there is no CONFIG_PCIE_BWCTRL. | `pcie_set_target_speed()` has two callers: the PCI core, in `pcie_failed_link_retrain()` in `drivers/pci/quirks.c`, and `drivers/thermal/pcie_cooling.c` (`CONFIG_PCIE_THERMAL`), which also defines `pcie_cooling_device_register()`. No controller or hotplug driver calls it. `pcie_reset_lbms()` is called from `pcie_retrain_link()` in `drivers/pci/pci.c` and from `drivers/pci/hotplug/pciehp_ctrl.c`; `drivers/pci/quirks.c` only tests `PCI_LINK_LBMS_SEEN`. |
| Data object exchange | `drivers/pci/doe.c` (`CONFIG_PCI_DOE`) | PCI core creates every mailbox: `pci_doe_init()` from `pci_init_capabilities()`. Exports are only `pci_find_doe_mailbox()` and `pci_doe()`; `pci_doe_create_mb()`, `pci_doe_submit_task()`, `pci_doe_destroy_mb()` are static; there is no pci_doe_supports_prot(), the static `pci_doe_supports_feat()` does that. `pci_doe()` is called from `drivers/pci/tsm.c` and from other subsystems, for example `drivers/cxl/core/pci.c`. |
| Link encryption and device security | `drivers/pci/ide.c` (`CONFIG_PCI_IDE`: no prompt, selected by `CONFIG_PCI_TSM`); `drivers/pci/tsm.c` (`CONFIG_PCI_TSM`, selects `CONFIG_PCI_DOE`). There is no drivers/pci/cma.c and no CONFIG_PCI_CMA. | PCI core calls `pci_ide_init_host_bridge()`, `pci_ide_init()`, `pci_tsm_init()` in `drivers/pci/probe.c` and `pci_tsm_destroy()`, `pci_ide_destroy()` in `drivers/pci/remove.c`. Stream setup, for example `pci_ide_stream_alloc()`, is called by another subsystem, which also supplies `struct pci_tsm_ops`: the one in-tree platform TSM driver is `drivers/crypto/ccp/sev-dev-tsm.c`. `drivers/virt/coco/tsm-core.c` defines no `struct pci_tsm_ops`; its `tsm_register()` reaches `pci_tsm_register()` when the caller passes ops. `pci_tsm_bind()`, `pci_tsm_unbind()`, `pci_tsm_guest_req()`: exported, no caller in this tree. |
| Steering hints for memory writes | `drivers/pci/tph.c` (`CONFIG_PCIE_TPH`) | PCI core calls `pci_tph_init()`, `pci_save_tph_state()`, `pci_restore_tph_state()`. `pcie_enable_tph()`, `pcie_tph_get_cpu_st()`, `pcie_tph_set_st_entry()` are called only by endpoint drivers, for example `drivers/net/ethernet/broadcom/bnxt/bnxt.c`; nothing under `drivers/dma/` or `drivers/vfio/`. |
| Enclosure LEDs | `drivers/pci/npem.c` (`CONFIG_PCI_NPEM`) | PCI core: `pci_npem_create()` from `pci_device_add()` in `drivers/pci/probe.c`, not from `pci_bus_add_device()`; `pci_npem_remove()` from `pci_destroy_dev()` in `drivers/pci/remove.c`, not from `pci_stop_dev()`. |
| Resizable BARs | `drivers/pci/rebar.c`, which also holds `pci_resize_resource()`; it is not in `drivers/pci/setup-res.c`. Release and reassignment: `pci_do_resource_release_and_resize()` in `drivers/pci/setup-bus.c`. VF BARs: `pci_iov_vf_bar_set_size()` in `drivers/pci/iov.c`. | PCI core calls `pci_rebar_init()`, `pci_restore_rebar_state()`, and `pci_resize_resource()` from `__resource_resize_store()` in `drivers/pci/pci-sysfs.c`. Other callers of `pci_resize_resource()` are GPU drivers under `drivers/gpu/drm/`; no controller driver calls it. |

## Configuration space

**Configuration accessor results**

- `pci_read_config_dword()` and its byte, word and write siblings: return
  the bus op's result unconverted; they do not call
  `pcibios_err_to_errno()`.
- Sign of a failure: positive `PCIBIOS_BAD_REGISTER_NUMBER` or
  `PCIBIOS_DEVICE_NOT_FOUND` when the core generates it, whatever the op
  returned otherwise, which can be a negative errno.
- Misaligned offset, device not disconnected: `pci_read_config_dword()`
  returns positive `PCIBIOS_BAD_REGISTER_NUMBER` to its caller, before the
  output is written.
- `pci_user_read_config_dword()` and its byte, word and write siblings: the
  only accessors in `drivers/pci/access.c` that convert; a misaligned offset
  returns `-EINVAL` directly, output unwritten.
- Without `CONFIG_PCI`: the accessors are `_PCI_NOP` stubs in
  `include/linux/pci.h`; they return `PCIBIOS_FUNC_NOT_SUPPORTED` and leave
  the output unwritten.
- `pcibios_err_to_errno()`: a positive value that is not one of the six
  codes in its switch becomes `-ERANGE`.
- **Potentially unsafe usage**: using the value read without testing the
  return value.
  - Unsafe: when the output variable is uninitialised and the offset can be
    misaligned for the width; the `PCI_word_BAD` and `PCI_dword_BAD` tests
    return before the output is written.
  - Safe: with an aligned offset under `CONFIG_PCI`, where every path writes
    the value or all ones, and the caller tests `PCI_POSSIBLE_ERROR()`, as
    `pci_dev_config_accessible()` in `drivers/pci/pci.c` does.

**PCI Express capability accessors**

- Failed read of an implemented register: output is reset to 0, not all
  ones; the return is the unconverted result of `pci_read_config_word()` or
  `pci_read_config_dword()`.
- Misaligned `pos`: `PCIBIOS_BAD_REGISTER_NUMBER` with output 0, not
  `-EINVAL`.
- `PCI_EXP_SLTSTA` on a port with no slot: `pcie_capability_read_word()`
  gives `PCI_EXP_SLTSTA_PDS` when `pcie_downstream_port()` is true, 0
  otherwise.
- `pcie_capability_read_dword()` has the same `PCI_EXP_SLTSTA` test, but it
  cannot fire: `PCI_EXP_SLTSTA` fails `pos & 3` and returns
  `PCIBIOS_BAD_REGISTER_NUMBER` first.
- `pos` not listed in the switch of `pcie_capability_reg_implemented()`:
  treated as unimplemented on every device, for example `PCI_EXP_SLTCTL2`;
  reads give 0 with return 0, writes are dropped with return 0.
- `pcie_capability_clear_and_set_word()` in `include/linux/pci.h`: locks for
  `PCI_EXP_LNKCTL`, `PCI_EXP_LNKCTL2` and `PCI_EXP_RTCTL`; no other `pos`.
- The lock: `pcie_cap_lock` in `struct pci_dev`, taken with
  `spin_lock_irqsave()` in `pcie_capability_clear_and_set_word_locked()`; it
  is not `pci_lock`.
- `pcie_capability_clear_and_set_dword()`: does not take `pcie_cap_lock` for
  any register.
- **Unsafe usage**: open-coded read-modify-write of `PCI_EXP_LNKCTL2` with
  `pcie_capability_read_word()` then `pcie_capability_write_word()` while
  another context can update it; the write helper does not take
  `pcie_cap_lock`.
  - Safe: `pcie_capability_clear_and_set_word()`, as
    `drivers/pci/pcie/bwctrl.c` does for `PCI_EXP_LNKCTL2_TLS`.

**Saved configuration state**

- `pci_bus_add_device()` in `drivers/pci/bus.c`: saves every device it adds,
  after the `pci_fixup_final` fixups and before `pm_runtime_enable()`.
- `pci_set_power_state()` and the AER and DPC recovery code: do not call
  `pci_save_state()`.
- `pci_pm_poweroff_noirq()`: does not save; only its legacy branch,
  `pci_legacy_suspend_late()`, does, when `state_saved` is clear.
- `pci_pm_suspend_noirq()` with no `pm` ops: saves without testing
  `state_saved`.
- `pci_dev_save_and_disable()`: skips the save when
  `pci_dev_config_accessible()` reads all ones; `pci_dev_restore()` still
  calls `pci_restore_state()`, which restores the older saved state.
- `pci_restore_state()`: does not test `state_saved`; it restores whatever
  `saved_config_space` and the capability save buffers hold.
- `pci_restore_state()` with no save in the same path: relied on by
  `pcibios_reset_secondary_bus()`.
- `pci_restore_state()`: clears `state_saved` as its last step and leaves the
  buffers intact, so a second restore restores the same state again.
- `pci_store_saved_state()`: returns `NULL` while `state_saved` is clear, for
  example after a restore with no save since.
- `pci_load_saved_state()` with a `NULL` state: clears the flag, returns 0,
  leaves the buffers as they were.
- `state_saved` outside PM: set by `pci_bus_add_device()` and stays set until
  a restore, `pci_load_saved_state()` or a PM callback clears it, so a set
  flag alone does not show that a driver saved state.
- Clearing before the driver callback: unconditional in
  `pci_legacy_suspend()`, in `pci_pm_freeze()` when the driver has `pm` ops
  and, with a driver bound, in `pci_pm_runtime_suspend()`;
  `pci_pm_suspend()` and `pci_pm_poweroff()` clear it only on the branch that
  calls `pm_runtime_resume()`.
- Flag set after the callback: `pci_pm_suspend_noirq()` and
  `pci_pm_runtime_suspend()` skip `pci_save_state()` and also
  `pci_prepare_to_sleep()` or `pci_finish_runtime_suspend()`.
- Flag clear after the `suspend_noirq` or `runtime_suspend` callback,
  `current_state` neither `PCI_D0` nor `PCI_UNKNOWN`:
  `pci_pm_suspend_noirq()` and `pci_pm_runtime_suspend()` skip the save too,
  and warn once if the callback changed the state.
- Flag clear in `pci_pm_poweroff_noirq()`, device with no subordinate bus:
  `pci_prepare_to_sleep()` runs with no save.
- Flag still set in `pci_pm_resume()` or `pci_pm_restore()`: taken to mean
  the noirq-phase restore did not run; they call
  `pci_restore_standard_config()`.

## Devices and their drivers

**Device lifecycle**

- `pci_device_add()` in `drivers/pci/probe.c` makes the device visible to
  lookups in two steps: the `bus->devices` insertion serves `pci_get_slot()`
  and `pci_walk_bus()`; the later `device_add()` serves `pci_get_device()`
  and `for_each_pci_dev`, which go through `bus_find_device()`.
- `pci_bus_add_device()` in `drivers/pci/bus.c` does not call `device_add()`.
- Binding gate: bit `PCI_DEV_ALLOW_BINDING` in `priv_flags`. `pci_bus_match()`
  returns 0 while `pci_dev_binding_disallowed()` is true. There is no
  match_driver field in this tree.
- `pci_dev_allow_binding()`: called only from `pci_bus_add_device()`, and only
  if the device has no OF node or `of_device_is_available()` is true. A
  device with an unavailable node is still marked added, and
  `pci_bus_match()` keeps returning 0 for it.
- Attach call: `device_initial_probe()`, not `device_attach()`. It does
  nothing when the bus `drivers_autoprobe` is off, and it allows async probe,
  so a probe can still be running after `pci_bus_add_device()` returns.
- Order in `pci_bus_add_device()`: `pcibios_bus_add_device()` runs before
  `pci_fixup_device(pci_fixup_final, dev)`; `pci_save_state()` and
  `pm_runtime_enable()` run before the gate opens. It makes no pwrctrl call.
- Code that must precede any probe: in `pci_device_add()`, or in
  `pci_bus_add_device()` before `pci_dev_allow_binding()`.
- `pci_fixup_enable` is not a pre-probe pass: its only call site is
  `do_pci_enable_device()` in `drivers/pci/pci.c`.
- sysfs files: attribute groups (`pci_dev_groups`, `pci_dev_attr_groups` in
  `drivers/pci/pci-sysfs.c`) created by `device_add()`, so userspace can reach
  them before final fixups. `pci_bus_add_device()` creates none of them and
  `pci_stop_dev()` removes none; `device_del()` removes them. There is no
  pci_create_sysfs_dev_files() here.
- Added state: bit `PCI_DEV_ADDED` in `priv_flags`, through
  `pci_dev_assign_added()`, `pci_dev_is_added()` and
  `pci_dev_test_and_clear_added()` in `drivers/pci/pci.h`. `struct pci_dev`
  has no added member; in `include/linux/pci.h`, `is_added` is a member of
  `struct pci_bus` only.
- Removed state: bit `PCI_DEV_REMOVED`, set by
  `pci_dev_test_and_set_removed()`. Its only user is `pci_destroy_dev()`,
  which returns early on a second call. There is no read-only helper for it.
- `PCI_DEV_ADDED` during a synchronous probe started by
  `pci_bus_add_device()`: still clear, because `pci_dev_assign_added()` runs
  after `device_initial_probe()`.
- `PCI_DEV_ADDED` during remove from `pci_stop_dev()`: already clear, because
  the bit is cleared before `device_release_driver()`.
- `pci_destroy_dev()`: `device_del()` runs before the `bus->devices` removal,
  so for a moment `pci_get_slot()` finds a device that `pci_get_device()`
  does not.
- `pci_release_dev()`: drops the `pci_bus_get()` reference taken in
  `pci_alloc_dev()`, so `dev->bus` stays valid while a device reference is
  held. It does not free a driver override string.

**Probe and remove**

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

**Core locks**

- Functions that require a lock held by the caller:

| function | lock | checked by |
|---|---|---|
| `pci_stop_and_remove_bus_device()` | `pci_rescan_remove_lock` | `lockdep_assert_held()` |
| `pci_rescan_bus()`, `pci_rescan_bus_bridge_resize()` | `pci_rescan_remove_lock` | comment above the mutex in `drivers/pci/probe.c` only |
| `pci_walk_bus_locked()` | `pci_bus_sem` | `lockdep_assert_held()` |
| `pci_set_power_state_locked()` | `pci_bus_sem` | its own `lockdep_assert_held()` |
| `pci_enable_link_state_locked()`, `pci_disable_link_state_locked()` | `pci_bus_sem`, read | `lockdep_assert_held_read()` |
| `pci_bus_max_d3cold_delay()` | `pci_bus_sem` | `lockdep_assert_held()` |
| `pci_wait_cfg()` | `pci_lock` | `__must_hold()` annotation only |

- `pci_stop_and_remove_bus_device()`: the only assertion on
  `pci_rescan_remove_lock` in the tree.
- `pci_bus_sem`: declared in `drivers/pci/pci.h` and not exported; no code
  outside `drivers/pci` takes it. A driver holds it when the core calls it
  under the lock, for example in a `pci_walk_bus()` callback; the `_locked`
  functions are the forms that do not take it again there, as
  `vmd_pm_enable_quirk()` in `drivers/pci/controller/vmd.c` uses them.
- `pci_get_device()` does not take `pci_bus_sem`; `pci_get_slot()` does.
- `pci_lock` with `CONFIG_PCI_LOCKLESS_CONFIG`: only
  `pci_bus_read_config_byte()`, `pci_bus_write_config_byte()` and their word
  and dword siblings skip it, through `pci_lock_config()` in
  `drivers/pci/access.c`. `pci_user_read_config_dword()` and its byte, word
  and write siblings, `pci_cfg_access_lock()`, `pci_bus_set_ops()` and
  `pci_check_and_set_intx_mask()` take it unconditionally.

**Lookups and references**

- `DEFINE_FREE(pci_dev_put, ...)` in `include/linux/pci.h`: sits inside
  `#ifdef CONFIG_PCI`. The other branch defines `pci_dev_put()` as an empty
  macro and has no `DEFINE_FREE()`, so `__free(pci_dev_put)` is usable only in
  code that is built with `CONFIG_PCI`.
- `pci_get_dev_by_id()` in `drivers/pci/search.c`: drops the reference on
  `from` after `bus_find_device()` has returned, so `from` is valid during the
  search and must not be used once the lookup returns, unless the caller
  holds another reference.
- `pci_get_slot()`: takes no starting device and drops no reference.
- Reverse forms: `pci_get_device_reverse()` and `for_each_pci_dev_reverse`
  follow the same reference rules as `pci_get_device()` and
  `for_each_pci_dev`.

## Interrupt vectors and managed devices

**Allocating interrupt vectors**

- PCI_IRQ_LEGACY: not defined in this tree; the INTx flag is `PCI_IRQ_INTX`
  in `include/linux/pci.h`.
- `pci_irq_type()` in `include/linux/pci.h`: returns `PCI_IRQ_MSIX`,
  `PCI_IRQ_MSI` or `PCI_IRQ_INTX` for the type that was granted; with
  `CONFIG_PCI` but without `CONFIG_PCI_MSI` it returns `PCI_IRQ_INTX`.
- `max_vecs < min_vecs`: `-ERANGE` from `__pci_enable_msix_range()` and
  `__pci_enable_msi_range()` in `drivers/pci/msi/msi.c`, not `-EINVAL`; not
  checked at all when only `PCI_IRQ_INTX` is set.
- `affd` passed without `PCI_IRQ_AFFINITY`: `WARN_ON()`, `affd` is dropped and
  the allocation proceeds; no error is returned.
- Failure value: the errno of the last of MSI-X and MSI that was tried, since
  each helper overwrites `nvecs`; the MSI-X errno is lost when `PCI_IRQ_MSI`
  is also set; `-ENOSPC` when neither flag is set.
- `-ENOSPC` is not the only "cannot satisfy" result: a device without the
  capability gives `-EINVAL` from `pci_msix_vec_count()` or
  `pci_msi_vec_count()`.
- `pci_msi_supported()` failing (for example MSI off globally, `dev->no_msi`,
  `PCI_BUS_FLAGS_NO_MSI` on the device's bus or a bus above it) or a device
  not in `PCI_D0`: `-EINVAL`.
- `-ENOTSUPP`: when `pci_msi_domain_supports()` is false; `-ENODEV`: when
  `pci_setup_msix_device_domain()` or `pci_setup_msi_device_domain()` fails.
- `PCI_IRQ_VIRTUAL`: MSI-X only; the count is not capped at the table size, so
  the return value can exceed `pci_msix_vec_count()`; the extra vectors are
  `is_virtual` and are not programmed into the device; for example
  `switchtec_init_isr()` in `drivers/pci/switch/switchtec.c`.
- With `CONFIG_PCI` but without `CONFIG_PCI_MSI`: the inline stub in
  `include/linux/pci.h` returns 1 on the same INTx condition as
  `pci_alloc_irq_vectors_affinity()` (`PCI_IRQ_INTX` set, `min_vecs` 1,
  `dev->irq` non-zero) but does not call `pci_intx()`; otherwise `-ENOSPC`.

**Older MSI functions**

- `pci_irq_vector()` after a legacy enable: works; it tests only
  `msi_enabled` and `msix_enabled`, then calls `msi_get_virq()`.
- `pci_irq_vector()` after `pci_enable_msix_range()`: `nr` is the MSI-X table
  index given in `entries[].entry`, not the position in the array.
- `pci_irq_get_affinity()` on a vector from a legacy enable: returns `NULL`.
- `pci_msi_vec_count()`: defined and exported in `drivers/pci/msi/msi.c`;
  `pci_msix_vec_count()` is in `drivers/pci/msi/api.c`.
- Kernel-doc "Legacy device driver API": on `pci_enable_msi()`,
  `pci_disable_msi()`, `pci_enable_msix_range()` and `pci_disable_msix()`;
  each adds that the newer pair "should, in general, be used instead".
- `pci_enable_msix_exact()`: static inline in `include/linux/pci.h` with no
  kernel-doc; no source comment calls it legacy or deprecated,
  `Documentation/PCI/msi-howto.rst` does.
- `Documentation/PCI/msi-howto.rst`, section "Legacy APIs": lists all five,
  both disable functions included, each marked `/* deprecated */`; the wording
  is "should not be used in new code".
- Multi-vector MSI: no legacy function gives it; `pci_enable_msi()` asks for
  exactly one vector.
- With `CONFIG_PCI` but without `CONFIG_PCI_MSI`: the legacy enable stubs
  return `-ENOSYS`, while the `pci_alloc_irq_vectors()` stub can still return
  1 for INTx.

**Managed functions**

- `pci_is_managed()`: one caller in the tree, `pcim_setup_msi_release()` in
  `drivers/pci/msi/msi.c`; `drivers/pci/pci.c` makes no devres call.
- Plain calls that become managed: only those that enable MSI or MSI-X, all
  through `pci_setup_msi_context()`: `pci_alloc_irq_vectors()`,
  `pci_alloc_irq_vectors_affinity()`, `pci_enable_msi()`,
  `pci_enable_msix_range()` and its inline wrapper `pci_enable_msix_exact()`.
- Implicit MSI release: installed only by a vector allocation made after
  `pcim_enable_device()`; `is_managed` is tested at allocation time.
- Comment above `pcim_setup_msi_release()`: calls this a legacy side-effect
  that is "dangerous and confusing", with a TODO to remove it.
- Managed vector allocator: there is none with a `pcim_` prefix.
- Deprecated in `drivers/pci/devres.c`: only `pcim_iomap_table()` and
  `pcim_iomap_regions()`.
- pcim_iomap_regions_request_all and pcim_iounmap_regions: not in this tree.
- `pcim_iomap_region()` and `pcim_iomap_range()`: do not enter the mapping in
  the legacy table, so `pcim_iomap_table()` has `NULL` for that BAR; only
  `pcim_iomap()` and `pcim_iomap_regions()` fill it.
- Failure value when converting: `pcim_iomap_region()` and
  `pcim_iomap_range()` return `IOMEM_ERR_PTR()`; `pcim_iomap()` returns `NULL`;
  `pcim_iomap_regions()` returns an int.
- `pcim_iounmap()`: releases only mappings from `pcim_iomap()` and
  `pcim_iomap_range()`; given an address from `pcim_iomap_region()` or
  `pcim_iomap_regions()` it finds no match and returns without unmapping.
- `pcim_iounmap_region()`: releases only BARs mapped by `pcim_iomap_region()`
  or `pcim_iomap_regions()`.
- `pcim_release_region()` and `pcim_release_all_regions()`: static in
  `drivers/pci/devres.c`; no exported function with a `pcim_` prefix undoes
  `pcim_request_region()` or `pcim_request_all_regions()` before detach.

**Freeing interrupt vectors**

- `Documentation/PCI/msi-howto.rst`: on a `pcim_enable_device()` device the
  driver "shouldn't call" `pci_free_irq_vectors()`.
- Kernel-doc of `pci_free_irq_vectors()`: "Do not call this function" on such
  a device, it "can lead to double-free issues".
- **Potentially unsafe usage**: `pci_free_irq_vectors()` on a
  `pcim_enable_device()` device.
  - Unsafe: while a handler from `devm_request_irq()` is still installed on a
    vector, as in remove or a probe error path; devres frees that handler only
    after remove or the failed probe returns.
  - Safe: when no handler is installed on any vector, as `ahci_init_irq()` in
    `drivers/ata/ahci.c` does before it allocates again; the later
    `pcim_msi_release()` frees only what is enabled then, since
    `pci_disable_msix()` and `pci_disable_msi()` return early when
    `msix_enabled` and `msi_enabled` are clear.
  - Safe: no explicit call, with `devm_request_irq()` after the allocation, as
    `switchtec_init_isr()` in `drivers/pci/switch/switchtec.c` does;
    `pcim_msi_release()` is registered at the first allocation, so it runs
    after the handlers are released.
- Handler still installed when vectors are freed: nothing in
  `drivers/pci/msi/` or `kernel/irq/msi.c` checks for it; there is no
  `BUG_ON()` for it there.
- With `CONFIG_SPARSE_IRQ`, on the irq domain path: `free_desc()` in
  `kernel/irq/irqdesc.c` deletes the descriptor; with `CONFIG_PROC_FS`,
  `remove_proc_entry()` warns "removing non-empty directory"; a later
  `free_irq()` finds no descriptor and returns `NULL` without freeing the
  action.
- After an INTx result: `pci_free_irq_vectors()` does nothing; the
  `pci_intx(dev, 1)` done by the allocation is not undone.

## Removal, reset and recovery

**Surprise removal**

- `pci_dev_is_disconnected()`: defined in `include/linux/pci.h`, so drivers may
  call it, as `nvme_timeout()` does. `pci_dev_set_disconnected()` and
  `pci_dev_set_io_state()` are private to the core, in `drivers/pci/pci.h`.
- `pci_dev_set_disconnected()` callers: hotplug and resume code, for example
  `pciehp_unconfigure_device()` and `pci_pm_bridge_power_up_actions()`.
  Nothing under `drivers/pci/pcie/` calls it: AER, DPC and EDR do not mark
  devices disconnected.
- `pciehp_unconfigure_device()` with `presence` false: reached for a Link Down
  event as well as a presence change; `pciehp_handle_presence_or_link_change()`
  passes `SURPRISE_REMOVAL` for both. A disconnected device may still be in
  the slot.
- `pci_dev_set_io_state()`: never leaves `pci_channel_io_perm_failure`; in
  that state a request for `pci_channel_io_frozen` or `pci_channel_io_normal`
  returns false.
- `pci_dev_set_disconnected()`: also calls `pci_doe_disconnected()`, which
  under `CONFIG_PCI_DOE` cancels the DOE mailbox tasks of the device.
- A clear flag does not prove presence: the flag is set by software, for
  example in `pciehp_unconfigure_device()`, which runs after the hardware
  event.
- `pcie_capability_read_word()` and `pcie_capability_read_dword()` on a
  disconnected device, for an implemented register: return
  `PCIBIOS_DEVICE_NOT_FOUND` with the value set to 0, not all ones.
- Config accesses with no disconnected test: `pci_bus_read_config_dword()`,
  `pci_user_read_config_dword()` and their byte, word and write siblings in
  `drivers/pci/access.c`; they call `bus->ops` directly.
- `__pci_read_msi_msg()`: has no disconnected test of its own; for MSI-X it
  reads the table with `readl()`. For a disconnected device
  `__pci_write_msi_msg()` and `pci_msix_shutdown()` skip the hardware.
- **Potentially unsafe usage**: `PCI_POSSIBLE_ERROR()` on a value from
  `pcie_capability_read_word()` as the only "device gone" test.
  - Unsafe: when the return value is not tested and nothing else bounds what
    the code does with the 0 read for a disconnected device, for example a
    wait with no timeout until a bit is set.
  - Safe: also test the return value, as `pciehp_check_link_active()` does;
    `pcie_capability_read_word()` defines the zeroing.
  - Safe: in a loop with a timeout, as `pcie_poll_cmd()` in
    `drivers/pci/hotplug/pciehp_hpc.c`.
  - Safe: where a value of 0 ends the work, as `pcie_pme_irq()` in
    `drivers/pci/pcie/pme.c` returns `IRQ_NONE` when `PCI_EXP_RTSTA_PME` is
    clear.

**Function reset**

- `pci_dev_lock()`: takes `device_lock()` first, then `pci_cfg_access_lock()`.
  `pci_dev_trylock()` uses the same order.
- `pci_reset_function()`: takes `pci_dev_lock()` on `pci_upstream_bridge()`
  first, if there is one, then on the device.
- `pci_try_reset_function()`: takes `pci_dev_trylock()` on the device only,
  never on the bridge.
- `device_lock_assert()`: called in `pci_reset_function_locked()`,
  `__pci_reset_function_locked()` and `pci_dev_save_and_disable()`. It is
  `lockdep_assert_held()` on the device mutex and nothing more.
- Config access lock: not tested on the device by any of the four function
  reset entry points. `pci_reset_function_locked()` and
  `__pci_reset_function_locked()` take no lock and run with user config
  access unblocked unless the caller took `pci_cfg_access_lock()`.
- `pci_bridge_secondary_bus_reset()`: tests `block_cfg_access` of the bridge,
  prints "unlocked secondary bus reset" once, and resets anyway. Reached by
  the `bus` method through `pci_parent_bus_reset()`.
- Callers of `__pci_reset_function_locked()` that lock the bridge themselves:
  `vfio_pci_core_disable()` uses `pci_dev_trylock()` on bridge then device;
  `mlxsw_pci_reset_at_pci_disable()` uses `pci_cfg_access_lock()` on both.
- Error callbacks: every walker in `drivers/pci/pcie/err.c` holds
  `device_lock()` around the driver callback, so a reset from there uses
  `pci_reset_function_locked()`, as `ionic_pci_error_resume()` does.
  `pci_reset_function()` would take the same mutex again.

**Reset methods and callbacks**

- Order in `pci_reset_fn_methods[]`: device_specific → acpi → flr → af_flr →
  pm → bus → cxl_bus. The `acpi` entry is `pci_dev_acpi_reset()`, which
  evaluates `_RST`.
- `__pci_reset_function_locked()`: does not probe. It calls each entry of
  `dev->reset_methods[]` with `PCI_RESET_DO_RESET`. `dev->reset_methods[]` is
  filled only by `pci_init_reset_methods()` and `reset_method_store()`, which
  probe.
- `pci_dev_wait()`: returns `-ENOTTY` on timeout and for a disconnected
  device. A method that reset the device and then timed out, such as
  `pcie_flr()`, makes the walk go on to the next method.
- `pci_bridge_wait_for_secondary_bus()`: also returns `-ENOTTY` on failure,
  so after a failed `bus` reset the walk goes on, to `cxl_bus` if that is the
  next entry of `dev->reset_methods[]`.
- Errors that stop the walk: any other code. For example the error from
  `pci_dev_reset_iommu_prepare()`, which each method calls before it resets,
  and `-EINVAL` from `pci_pm_reset()` when the device is not in `PCI_D0`.
- `pci_init_reset_methods()`: stops probing at the first probe result that is
  neither 0 nor `-ENOTTY`; later methods are left out of
  `dev->reset_methods[]`.
- `reset_done()`: called whether or not the reset succeeded;
  `pci_dev_restore()` runs unconditionally in `pci_reset_function()`,
  `pci_reset_function_locked()` and `pci_try_reset_function()`.
- `pci_dev_save_and_disable()`: calls `reset_prepare()` and
  `pci_set_power_state()`, then returns without `pci_save_state()` or the
  `PCI_COMMAND` write if `pci_dev_config_accessible()` reads all ones.

**Error recovery sequence**

- Order in `pcie_do_recovery()`: `error_detected()` walk, then the
  `mmio_enabled()` walk if the status is `PCI_ERS_RESULT_CAN_RECOVER`, then
  `reset_subordinates()`, then the `slot_reset()` walk, then `resume()`.
- `reset_subordinates()`: called when the state is `pci_channel_io_frozen` or
  the status is `PCI_ERS_RESULT_NEED_RESET`. A non-fatal error whose merged
  vote is `PCI_ERS_RESULT_NEED_RESET` gets a real reset.
- Frozen channel with status `PCI_ERS_RESULT_CAN_RECOVER`: `mmio_enabled()`
  runs before the reset, while `error_state` is still
  `pci_channel_io_frozen`.
- `slot_reset()` walk: runs only when the status is
  `PCI_ERS_RESULT_NEED_RESET`. A frozen recovery whose status is
  `PCI_ERS_RESULT_RECOVERED` after `mmio_enabled()` is reset and goes
  straight to `resume()`.
- Callers and states: `AER_NONFATAL` passes `pci_channel_io_normal`.
  `AER_FATAL`, DPC, EDR and, with `CONFIG_PCIEAER`,
  `pci_host_handle_link_down()` pass `pci_channel_io_frozen`.
- Reset callbacks: `aer_root_reset()`, `dpc_reset_link()` and
  `pci_host_reset_root_port()` in
  `drivers/pci/controller/pci-host-common.c`.
- `aer_root_reset()`: uses `pcie_reset_flr()` for an RCEC or RCiEP, otherwise
  `pci_bus_error_reset()`, which resets the slots when the bus has slots and
  every one of them can be reset, and does a secondary bus reset otherwise.
- Recovery scope: the device itself for `PCI_EXP_TYPE_ROOT_PORT`,
  `PCI_EXP_TYPE_DOWNSTREAM`, `PCI_EXP_TYPE_RC_EC` and `PCI_EXP_TYPE_RC_END`;
  otherwise `pci_upstream_bridge()`.
- `merge_result()` by current status:

| Current status | New vote that changes it |
|---|---|
| any, tested first | `PCI_ERS_RESULT_NO_AER_DRIVER` replaces it; `PCI_ERS_RESULT_NONE` never does |
| `PCI_ERS_RESULT_CAN_RECOVER`, `PCI_ERS_RESULT_RECOVERED` | any other vote replaces it |
| `PCI_ERS_RESULT_DISCONNECT` | besides the first row, only `PCI_ERS_RESULT_NEED_RESET` |
| `PCI_ERS_RESULT_NEED_RESET`, `PCI_ERS_RESULT_NO_AER_DRIVER` | nothing besides the first row |

- `PCI_ERS_RESULT_DISCONNECT` loses to `PCI_ERS_RESULT_NEED_RESET` in either
  order of voting.
- Disconnected device in `report_error_detected()`: votes
  `PCI_ERS_RESULT_DISCONNECT` and its callback is not called; the test comes
  before `pci_dev_set_io_state()`.
- `PCI_ERS_RESULT_NONE` from `report_error_detected()`: when
  `pci_dev_set_io_state()` fails, or for a bridge with no `error_detected()`.
- Non-bridge with no `error_detected()`: votes `PCI_ERS_RESULT_NO_AER_DRIVER`
  for both channel states. Bridge means `hdr_type` is
  `PCI_HEADER_TYPE_BRIDGE`.
- `report_slot_reset()` and `report_resume()`: set `error_state` to
  `pci_channel_io_normal` before they call the driver.
- On failure, `report_perm_failure_detected()` runs for each device: it calls
  `error_detected()` with `pci_channel_io_perm_failure` and sends
  `pci_uevent_ers()` with `PCI_ERS_RESULT_DISCONNECT`.
- `report_perm_failure_detected()`: does not write `error_state`. The devices
  are not disconnected for `pci_dev_is_disconnected()`, and config accesses
  still reach the hardware.
- `error_state` after failure: `pci_channel_io_frozen` if a fatal recovery
  failed before the `slot_reset()` walk, `pci_channel_io_normal` after it.
- Return value on failure: the merged status as it stands, for example
  `PCI_ERS_RESULT_NO_AER_DRIVER`. It is not rewritten to
  `PCI_ERS_RESULT_DISCONNECT`.

## Controller drivers

**Registering a host bridge**

- `devm_pci_alloc_host_bridge()`: sets `bridge->dev.parent` itself, then calls
  `devm_of_pci_bridge_init()` in `drivers/pci/of.c`.
- `devm_of_pci_bridge_init()` with an OF node: sets `swizzle_irq` and
  `map_irq`, then runs the static `pci_parse_request_of_pci_ranges()`; a
  driver cannot and need not call that itself.
- `pci_parse_request_of_pci_ranges()`: parses "bus-range", "ranges" and
  "dma-ranges", requests the windows with `devm_request_pci_bus_resources()`
  and remaps I/O windows with `devm_pci_remap_iospace()`.
- `devm_of_pci_bridge_init()` without an OF node: returns 0 and fills nothing;
  `bridge->windows` stays empty and `map_irq` stays NULL.
- Bus window on DT: always present; a missing "bus-range" becomes [0-0xff] in
  `devm_of_pci_get_host_bridge_resources()`.
- `bridge->busnr`: overwritten by `pci_scan_root_bus_bridge()` from the start
  of the first `IORESOURCE_BUS` window; a driver's own value survives only
  when no such window exists.
- No bus window: `pci_scan_root_bus_bridge()` logs with `dev_info()`, uses
  `bridge->busnr` to 0xff, and shrinks the end to the highest bus found
  after the scan.
- `bridge->ops`: must be non-NULL; `pci_register_host_bridge()` dereferences
  `bus->ops->add_bus` with no test.
- `pci_rescan_remove_lock`: taken twice in `pci_host_probe()`, around
  `pci_scan_root_bus_bridge()` and around `pci_bus_add_devices()`;
  `pci_scan_root_bus_bridge()` does not take it itself.
- Unlocked steps: `pci_bus_claim_resources()`,
  `pci_assign_unassigned_root_bus_resources()`,
  `pcie_bus_configure_settings()` and the runtime PM calls.
- Runtime PM state: `pci_host_probe()` tests nothing and discards the return
  values of `pm_runtime_set_active()` and `devm_pm_runtime_enable()`.
- **Potentially unsafe usage**: calling `pci_host_probe()` while the
  controller device is not both runtime-PM enabled and `RPM_ACTIVE`.
  - Unsafe: when the driver enables runtime PM on the controller afterwards
    while it is `RPM_SUSPENDED`; `pm_runtime_enable()` warns "Enabling runtime
    PM for inactive device with active children".
  - Unsafe: when runtime PM is enabled but the controller is not
    `RPM_ACTIVE`; `__pm_runtime_set_status()` returns `-EBUSY` and
    `bridge->dev` is enabled while suspended.
  - Safe: when the driver never enables runtime PM on the controller, as
    `pci_host_common_init()` does; the `-EBUSY` test in
    `__pm_runtime_set_status()` needs the parent's `power.disable_depth` to
    be 0, and the warning is only in `pm_runtime_enable()` of the
    controller.
  - Safe: `pm_runtime_enable()` then a successful `pm_runtime_get_sync()`
    first, as `rcar_pcie_probe()` does.
- `pci_host_probe()` failure: only `pci_register_host_bridge()` can fail it,
  before any device is scanned; once registration succeeds it returns 0.
- **Unsafe usage**: passing `bridge->bus` to `pci_stop_root_bus()` or
  `pci_remove_root_bus()` after `pci_host_probe()` returned an error;
  `pci_register_host_bridge()` frees the bus and leaves `bridge->bus`
  pointing at it, or NULL when `pci_alloc_bus()` failed.
  - Safe: on that error undo only the driver's own setup, as
    `dw_pcie_host_init()` does.
  - Safe: stop/remove after `pci_host_probe()` returned 0 and a later probe
    step failed, as `qcom_pcie_probe()` does through
    `dw_pcie_host_deinit()`.
- Bridge lifetime: the root bus holds its own reference on `bridge->dev`,
  taken in `pci_register_host_bridge()` and dropped in
  `release_pcibus_dev()`; the devres `put_device()` alone does not free the
  bridge or its private area while the bus exists.
- Bus left registered at unbind: what devres frees is the controller's other
  managed objects, including the `struct resource` objects behind
  `bridge->windows`, which `devm_of_pci_get_host_bridge_resources()`
  allocates on the controller device.
- `devm_pm_runtime_enable(&bridge->dev)`: is devres of `bridge->dev`, not of
  the controller; `device_del()` in `pci_remove_root_bus()` releases it.

**Configuration callbacks and locking**

- `pci_user_read_config_dword()`, `pci_user_write_config_dword()` and their
  byte and word siblings: hold `pci_lock` across the callback in every
  configuration; they use `raw_spin_lock_irq()` directly, not
  `pci_lock_config()`.
- `pci_check_and_set_intx_mask()` in `drivers/pci/irq.c`: calls
  `bus->ops->read` and `bus->ops->write` directly under
  `raw_spin_lock_irqsave(&pci_lock)`, in every configuration, for a
  read-modify-write of `PCI_COMMAND`.
- With `CONFIG_PCI_LOCKLESS_CONFIG`: the two paths above enter the callback
  with `pci_lock` held and `pci_bus_read_config_dword()` and its siblings
  enter it without, so `pci_lock` excludes nothing between them.
- `CONFIG_PCI_LOCKLESS_CONFIG`: has no prompt; `arch/x86/Kconfig` and
  `CONFIG_UML_PCI` select it. A driver in `drivers/pci/controller` that
  builds on x86 runs lockless; `vmd_pci_read()` and `vmd_pci_write()`
  serialise with their own raw spinlock `cfg_lock`.
- `raw_pci_read()` and `raw_pci_write()` on arm64, riscv and loongarch: call
  the bus's `ops->read` and `ops->write` without taking `pci_lock`, from
  `acpi_os_read_pci_configuration()` and `acpi_os_write_pci_configuration()`
  in `drivers/acpi/osl.c`. On these architectures a callback can run
  concurrently with a `pci_lock` holder although
  `CONFIG_PCI_LOCKLESS_CONFIG` is off.
- There are no config accessors with a noirq suffix in
  `drivers/pci/access.c`.
- Output on failure: the callback need not set it on the accessor paths;
  `PCI_OP_READ()` and `PCI_USER_READ_CONFIG()` pass a local `u32` and store
  `PCI_SET_ERROR_RESPONSE()` on any non-zero return.
- `pci_generic_config_read()` and `pci_generic_config_read32()`: return
  `PCIBIOS_DEVICE_NOT_FOUND` when `map_bus` returns NULL and do not write
  `*val`.
- Direct callers: get no fixup; `raw_pci_read()` in
  `arch/arm64/kernel/pci.c` hands the callback the caller's own pointer, so
  the caller gets whatever the callback left there.

## Endpoint framework

**Endpoint objects**

- `struct pci_epf_driver` in `include/linux/pci-epf.h`: holds `probe`,
  `remove` and `ops`; `bind` and `unbind` are not its members.
- `struct pci_epf_ops`: has exactly `bind`, `unbind` and `add_cfs`.
- `pci_epf_register_driver()`: a macro over `__pci_epf_register_driver()`,
  which returns `-EINVAL` if `ops`, `ops->bind` or `ops->unbind` is NULL.
- `probe` is mandatory: `pci_epf_device_probe()` returns `-ENODEV` without it.
- Bind sequence, in each configfs function that links a function to a
  controller: `pci_epc_add_epf()`, then `pci_epf_bind()`, then
  `pci_epc_notify_pending_init()`.
- `pci_epc_add_epf()`: only links the function and picks its number; it does
  not call `pci_epf_bind()`.
- `pci_epc_notify_pending_init()`: calls `epc_init` at once if
  `epc->init_complete` is set, so a function bound after controller init still
  gets the event.
- Three link functions in `drivers/pci/endpoint/pci-ep-cfs.c` run that
  sequence: `pci_epc_epf_link()`, `pci_primary_epc_epf_link()` and
  `pci_secondary_epc_epf_link()`; the last passes `SECONDARY_INTERFACE`.
- Unlink order: `pci_epf_unbind()` first, then `pci_epc_remove_epf()`, so
  `unbind` runs with the `epf->epc` or `epf->sec_epc` that is being unlinked
  still set.
- `pci_epc_start()` and `pci_epc_stop()`: call the op under `epc->lock`, not
  `epc->list_lock`.
- `epc->lock`: taken by every wrapper in
  `drivers/pci/endpoint/pci-epc-core.c` that calls an op, including
  `pci_epc_get_features()` and `pci_epc_raise_irq()`, with one exception.
- `align_addr` op: `pci_epc_mem_map()` calls it with no lock held.
- Nesting: event callbacks called from the list walkers, such as
  `pci_epc_init_notify()` and `pci_epc_linkup()`, run under `epc->list_lock`
  then `epf->lock`; `pci_epc_notify_pending_init()` holds only `epf->lock`.
  The callbacks call wrappers that take `epc->lock`, as
  `pci_epf_test_epc_init()` does with `pci_epc_write_header()`.

**Endpoint error returns**

| Function | On failure | Caller's test |
|---|---|---|
| `pci_epc_get()` | `ERR_PTR(-EINVAL)` only, for no such device and for a failed `try_module_get()` | `IS_ERR()` |
| `pci_epf_alloc_space()` | NULL on both failure paths, never an error pointer | `!ptr` |
| `pci_ep_cfs_add_epc_group()` | error pointer | `IS_ERR()` |
| `pci_ep_cfs_add_epf_group()` | error pointer | `IS_ERR()`, as `pci_epf_add_cfs()` does |
| `add_cfs` op of `struct pci_epf_ops` | error pointer; NULL means nothing to expose | both, as `pci_ep_cfs_add_type_group()` does |

- Without `CONFIG_PCI_ENDPOINT_CONFIGFS`: the two group functions are inline
  stubs in `include/linux/pci-ep-cfs.h` that return NULL.
- `__pci_epc_create()`: stores the result of `pci_ep_cfs_add_epc_group()` in
  `epc->group` untested and still returns the epc.
- `epc->group`: may therefore hold a group, NULL or an error pointer.
- `pci_epc_get_features()`: also returns NULL when the controller op itself
  returns NULL, as `dw_pcie_ep_get_features()` does when the glue driver has no
  `get_features`.

**Endpoint teardown**

| Function | Returns early for | Not checked |
|---|---|---|
| `pci_epf_destroy()` | nothing | `epf`; it calls `device_unregister()` |
| `pci_ep_cfs_remove_epc_group()` | NULL `group` | an error pointer is dereferenced |
| `pci_epf_remove_vepf()` | `IS_ERR_OR_NULL()` of either argument | whether `epf_vf` was added |
| `pci_epc_remove_epf()` | `IS_ERR_OR_NULL(epc)`, NULL `epf` | whether `epf` was added; `list_del()` is unconditional |
| `pci_epc_mem_free_addr()` | `phys_addr` in no window, after `pr_err()` | `epc`, `virt_addr` |
| `pci_epc_mem_exit()` | `epc->num_windows` of 0 | `epc` |
| `pci_epc_mem_unmap()` | invalid `epc` or function number, NULL `map`, NULL `map->virt_base` | whether the map succeeded |
| `pci_epf_free_doorbell()` | NULL `epf->db_msg` | `epf->epc`, dereferenced on the MSI path and, when `iova_size` is set, on the `PCI_EPF_DOORBELL_EMBEDDED` path |
| `pci_epf_unregister_driver()` | nothing | `driver` |

- `pci_epf_destroy()`: its only caller is `pci_epf_release()` in
  `drivers/pci/endpoint/pci-ep-cfs.c`; `pci_epf_drop()` only calls
  `config_item_put()`.
- There is no devm_pci_epc_destroy in this tree; `devm_pci_epc_release()`
  calls `pci_epc_destroy()` and is its only caller.
- `pci_epc_mem_exit()`: safe after a failed `pci_epc_multi_mem_init()` and
  when repeated, because both leave `epc->num_windows` at 0.
- `pci_epf_unregister_driver()` with `CONFIG_PCI_ENDPOINT_CONFIGFS`: walks
  `driver->epf_group`, which only `pci_epf_add_cfs()` initialises, so it needs
  a successful `__pci_epf_register_driver()` first.
- **Unsafe usage**: calling `pci_epc_destroy()` on an epc from
  `devm_pci_epc_create()`.
  - Unsafe: devres runs `devm_pci_epc_release()` later and unregisters the
    device a second time.
  - Safe: leave the epc to devres, as `dw_pcie_ep_init()` does.
- **Unsafe usage**: calling `pci_epc_mem_unmap()` on a map whose
  `pci_epc_mem_map()` failed.
  - Unsafe: after a failed `pci_epc_map_addr()` the memory is already freed
    and `map->virt_base` is still set, so it is freed twice.
  - Unsafe: on the `-EINVAL` return for a zero `pci_size`, `map` is not
    written, so an uninitialised `map` is used.
  - Safe: skip the unmap when the map call failed, as `pci_epf_test_read()`
    does.
- **Unsafe usage**: calling `pci_epf_free_space()` with a non-NULL `addr` once
  `pci_epc_remove_epf()` has cleared `epf->epc` or `epf->sec_epc`.
  - Unsafe: `pci_epf_free_space()` reads `epc->dev.parent` through the NULL
    pointer.
  - Safe: free in `unbind` the space of the interface whose epc pointer is
    still set; the configfs unlink functions call `pci_epf_unbind()` before
    `pci_epc_remove_epf()`, as `pci_epf_test_unbind()` relies on for
    `PRIMARY_INTERFACE`.
- **Unsafe usage**: calling `pci_epc_remove_epf()` for an epf that
  `pci_epc_add_epf()` did not add with the same `type`.
  - Unsafe: `list_del()` runs on a list entry that was never linked.
  - Safe: after `pci_epc_add_epf()` returned 0, as `pci_epc_epf_link()` does
    when `pci_epf_bind()` fails.

## Model gaps

### Other mistakes models make

- Models take pci_remove_sysfs_dev_files to remove the sysfs files of a
  device. It is defined nowhere in this tree.
- Models take `pci_device_remove()` to set `current_state` to `PCI_UNKNOWN`.
  `pci_pm_set_unknown_state()` in `drivers/pci/pci-driver.c` does that write,
  for a device in `PCI_D0`; it is defined under `CONFIG_PM_SLEEP` and called
  from `pci_legacy_suspend_late()`, `pci_pm_suspend_noirq()` and
  `pci_pm_freeze_noirq()`.
- Models take `driver_override` to be a string in `struct pci_dev`. It is a
  member of `struct device`; `pci_bus_type` sets `.driver_override = true`,
  and the code under `drivers/pci/` reads it only through
  `device_match_driver_override()` and `device_has_driver_override()`.
- Models take `pci_resize_resource()` to have three arguments and to leave
  the release of the BARs to the caller. It takes a fourth argument
  `exclude_bars`, releases the device's resources in the same bridge window
  itself through `pci_do_resource_release_and_resize()`, and restores them
  on failure.
- Models take a secondary bus reset always to toggle
  `PCI_BRIDGE_CTL_BUS_RESET`. For a port on a root bus whose host bridge sets
  `reset_root_port`, the `__weak` `pcibios_reset_secondary_bus()` in
  `drivers/pci/pci.c` calls that hook instead, and calls
  `pci_restore_state()` on the port when it succeeds.
- Models take the PCI core never to call `pcie_set_target_speed()`.
  `pci_device_add()` in `drivers/pci/probe.c` reaches it through
  `pcie_failed_link_retrain()`, with `CONFIG_PCI_QUIRKS` and
  `CONFIG_PCIEPORTBUS`.
- Models name pci_pwrctrl_register as the call a pwrctrl driver makes. A
  driver under `drivers/pci/pwrctrl/` calls `pci_pwrctrl_init()` and
  `devm_pci_pwrctrl_device_set_ready()`.
