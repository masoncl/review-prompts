# GICv5

## Main structures

### Objects and how they relate

- No "IRI domain" exists: PPI, SPI and LPI each have their own parentless
  domain, kept in `gicv5_global_data`, the single `struct gicv5_chip_data`.
- `gicv5_iri_irq_mask()` and the other helpers with that prefix in
  `drivers/irqchip/irq-gic-v5.c` are code shared by the SPI and LPI chips,
  not a domain.
- hwirq in the PPI, SPI and LPI domains: the ID only, never the type.
  - The type is in the firmware specifier: DT cell 0, or bits
    `GICV5_HWIRQ_TYPE` of ACPI `param[0]`.
- Domain hierarchy, with what each level stores:

| Domain | Parent | hwirq | `chip_data` |
|---|---|---|---|
| `ppi_domain` | none | PPI ID | `NULL` |
| `spi_domain` | none | SPI ID | owning `struct gicv5_irs_chip_data` |
| `lpi_domain` | none | LPI ID | `NULL` |
| `ipi_domain` | `lpi_domain` | index in the IPI block | `NULL` |
| ITS domain, one per ITS | `lpi_domain` | EventID << 32 \| DeviceID | `struct gicv5_its_dev` |
| IWB per-device MSI domain | ITS domain | wire number | `struct gicv5_iwb_chip_data` |

- SPIs: no in-memory table; trigger mode goes through IRS MMIO in
  `gicv5_spi_irq_set_type()`, which is why an SPI's `chip_data` is its IRS.
- IRS list and CPU binding, all in `drivers/irqchip/irq-gic-v5-irs.c`:
  `irs_nodes` is the list, `per_cpu_irs_data` the CPU's IRS, `cpu_iaffid` the
  CPU's IAFFID.
- IAFFID and CPU-to-IRS binding: filled from firmware at IRS probe (DT `cpus`
  and `arm,iaffids` of the IRS node; ACPI `iaffid` and `irs_id` of the MADT
  GICC entry), not read from the CPU.
- `struct gicv5_its_chip_data`: has no link to any IRS object; the parent of
  its domain is `gicv5_global_data.lpi_domain`.
- `struct gicv5_its_dev`: `event_map` is a bitmap of EventIDs in use; the LPI
  of an event is not stored there, it is `d->parent_data->hwirq`.
- EventID-to-LPI link in the ITT: exists only between
  `gicv5_its_irq_domain_activate()` and `gicv5_its_irq_domain_deactivate()`,
  not from allocation.
- Translate frame (doorbell) address: per device, in `its_trans_phys_base` of
  `struct gicv5_its_dev`; an ITS may have several translate frames.
- DeviceID and translate frame address: resolved by `its_v5_pci_msi_prepare()`
  and `its_v5_pmsi_prepare()` in `drivers/irqchip/irq-gic-its-msi-parent.c`,
  a file shared with the GICv3 ITS.
- DT nesting: the `arm,gic-v5` node holds IRS nodes, each IRS node holds its
  ITS nodes, each ITS node holds its translate frame nodes; see
  `gicv5_irs_its_probe()`.

## Where to look

**Core files**

| Job | File |
|---|---|
| IRS part of the host driver | `drivers/irqchip/irq-gic-v5-irs.c`, a file of its own beside `drivers/irqchip/irq-gic-v5.c` |
| ACPI probe | no file of its own: `CONFIG_ACPI` blocks in `drivers/irqchip/irq-gic-v5.c`, `drivers/irqchip/irq-gic-v5-irs.c`, `drivers/irqchip/irq-gic-v5-its.c` and `drivers/irqchip/irq-gic-v5-iwb.c`; IWB lookup is `iort_iwb_handle()` in `drivers/acpi/arm64/iort.c` |
| `ICC_` and `ICH_` system register layouts | `arch/arm64/tools/sysreg`; `include/linux/irqchip/arm-gic-v5.h` has none of them |
| Barrier macros `gsb_ack()`, `gsb_sys()` | `arch/arm64/include/asm/barrier.h`; only the encodings `GSB_ACK_BARRIER_INSN` and `GSB_SYS_BARRIER_INSN` are in `arch/arm64/include/asm/sysreg.h` |
| KVM at EL1 | `arch/arm64/kvm/vgic/vgic-v5.c`; it registers `KVM_DEV_TYPE_ARM_VGIC_V5` unless `is_protected_kvm_enabled()`, and `KVM_DEV_TYPE_ARM_VGIC_V3` too on `ARM64_HAS_GICV5_LEGACY` hosts |
| KVM at EL1, outside `vgic-v5.c` | `kvm_arm_vgic_v5_ops` in `arch/arm64/kvm/vgic/vgic-kvm-device.c`; `vgic_v5_setup_private_irq()` in `arch/arm64/kvm/vgic/vgic-init.c`; trap handlers such as `access_gicv5_ppi_enabler()` in `arch/arm64/kvm/sys_regs.c` |
| KVM at hyp | `arch/arm64/kvm/hyp/vgic-v5-sr.c`, built into both the VHE and nVHE objects; hypercall handlers in `arch/arm64/kvm/hyp/nvhe/hyp-main.c` |
| Device tree binding, IWB | `Documentation/devicetree/bindings/interrupt-controller/arm,gic-v5-iwb.yaml` |
| KVM device documentation | `Documentation/virt/kvm/devices/arm-vgic-v5.rst` |
| Selftests | `tools/testing/selftests/kvm/arm64/vgic_v5.c` |
| Selftest helpers | `tools/testing/selftests/kvm/include/arm64/gic_v5.h` has its own copies of `gic_insn()`, `gicr_insn()`, `gsb_ack()`, `gsb_sys()`; there is no GICv5 file under `tools/testing/selftests/kvm/lib/arm64/` |

**Entry points**

| Job | Start reading from | Easy to miss |
|---|---|---|
| Probe from ACPI | `gic_acpi_init()` in `drivers/irqchip/irq-gic-v5.c`, then `gicv5_irs_acpi_probe()` | static; `drivers/irqchip/irq-gic-v3.c` has a static function of the same name |
| Probe the ITS, DT or ACPI | `gicv5_irs_its_probe()` in `drivers/irqchip/irq-gic-v5-irs.c` | it picks `gicv5_its_of_probe()` or `gicv5_its_acpi_probe()` |
| Probe an IWB | `gicv5_iwb_device_probe()` in `drivers/irqchip/irq-gic-v5-iwb.c` | a platform driver, for DT and ACPI alike |
| Bring up a CPU's interface | `gicv5_starting_cpu()` | the hotplug callback is this, not `gicv5_cpu_enable_interrupts()`; `gicv5_init_common()` calls it directly for the boot CPU |
| Allocate an LPI | `gicv5_irq_lpi_domain_alloc()` in `drivers/irqchip/irq-gic-v5.c` | there is no gicv5_alloc_lpi() or gicv5_free_lpi(); static `alloc_lpi()` and `release_lpi()` do that; child domains use `irq_domain_alloc_irqs_parent()` |
| Configure an SPI's trigger | `gicv5_spi_irq_set_type()` | defined in `drivers/irqchip/irq-gic-v5-irs.c`, installed in `gicv5_spi_irq_chip` in `drivers/irqchip/irq-gic-v5.c`; there is no gicv5_irs_spi_set_type() |
| Register a device with an ITS | `gicv5_its_msi_prepare()`, then `gicv5_its_alloc_device()`, then `gicv5_its_device_register()` | reached from `its_v5_pci_msi_prepare()` and `its_v5_pmsi_prepare()` in `drivers/irqchip/irq-gic-its-msi-parent.c` |
| Map an event to an LPI | `gicv5_its_irq_domain_activate()`, then `gicv5_its_map_event()` | done at activate, not in `gicv5_its_irq_domain_alloc()` |
| Enable an IWB wire | `gicv5_iwb_irq_enable()`, then `gicv5_iwb_enable_wire()` | it is the `.irq_enable` callback; `.irq_unmask` is `irq_chip_unmask_parent()`; there is no gicv5_iwb_irq_domain_alloc() |

**KVM entry points**

| Job | GICv5 function | Called from |
|---|---|---|
| Create the device | none of its own: `kvm_arm_vgic_v5_ops` uses the shared `vgic_create()`, which calls `kvm_vgic_create()` in `arch/arm64/kvm/vgic/vgic-init.c`; there is no vgic_v5_create | `.create` of `struct kvm_device_ops`, called by `kvm_ioctl_create_device()` in `virt/kvm/kvm_main.c` |
| Create: per-vCPU PPIs | `vgic_v5_setup_private_irq()`, static in `arch/arm64/kvm/vgic/vgic-init.c` | `vgic_allocate_private_irqs_locked()` |
| Initialise | `vgic_v5_init()` | `vgic_init()`, reached by `KVM_DEV_ARM_VGIC_CTRL_INIT` in `vgic_v5_set_attr()`; on a vgic that is not initialised `vgic_lazy_init()` returns `-EBUSY` for any model but `KVM_DEV_TYPE_ARM_VGIC_V2` |
| Initialise: first run | `vgic_v5_map_resources()`; `vgic_v5_finalize_ppi_state()` | `kvm_vgic_map_resources()`; `kvm_arch_vcpu_run_pid_change()` in `arch/arm64/kvm/arm.c` |
| Reset a vCPU | `vgic_v5_reset()` | static `kvm_vgic_vcpu_reset()`, whose one caller is `vgic_init()`; not `kvm_vgic_vcpu_init()` |
| Load and put a vCPU | `vgic_v5_load()`, `vgic_v5_put()` | `kvm_vgic_load()`, `kvm_vgic_put()` in `arch/arm64/kvm/vgic/vgic.c`, by `vgic_model` |
| Load and put: at hyp | `__vgic_v5_restore_vmcr_apr()`, `__vgic_v5_save_apr()` | `kvm_call_hyp()` in `vgic_v5_load()` and `vgic_v5_put()` |
| Flush state before entry | `vgic_v5_flush_ppi_state()`, then `vgic_v5_restore_state()` | `kvm_vgic_flush_hwstate()`, through static `vgic_flush_state()` and `vgic_restore_state()`; the second only if `can_access_vgic_from_kernel()` |
| Save and fold after exit | `vgic_v5_save_state()`, then `vgic_v5_fold_ppi_state()` | `kvm_vgic_sync_hwstate()`, through static `vgic_save_state()` and `vgic_fold_state()`; the first only if `can_access_vgic_from_kernel()` |
| Restore and save: nVHE | `__vgic_v5_restore_state()` with `__vgic_v5_restore_ppi_state()`; `__vgic_v5_save_state()` with `__vgic_v5_save_ppi_state()` | `__hyp_vgic_restore_state()`, `__hyp_vgic_save_state()` in `arch/arm64/kvm/hyp/nvhe/switch.c` |
| Check for a pending interrupt | `vgic_v5_has_pending_ppi()` | `kvm_vgic_vcpu_pending_irq()`, as its first test |

## Interrupt IDs, domains and chips

**System components**

- `gicv5_init_common()` in `drivers/irqchip/irq-gic-v5.c`: holds the probe
  steps that both paths share after the IRS probe; `gicv5_of_init()` and the
  ACPI entry both call it.
- ACPI entry: `gic_acpi_init()` in `drivers/irqchip/irq-gic-v5.c` (the GICv3
  driver has a function of the same name); it calls
  `gicv5_irs_acpi_probe()`, and `gicv5_its_acpi_probe()` is reached through
  `gicv5_init_common()`.
- IRS probe: `gicv5_irs_init()` tests `GICV5_IRS_IDR2_LPI` on every IRS; an
  IRS that fails is dropped with a `WARN()`, and the probe returns
  `-ENODEV` only when no IRS is left on `irs_nodes`.
- Boot CPU: `gicv5_starting_cpu()` fails the probe when the CPU lacks
  `ARM64_HAS_GICV5_CPUIF` or when `gicv5_irs_register_cpu()` fails, for
  example with no valid IAFFID or no IRS recorded for that CPU.
- Several IRSes: the IST is set up on the first entry of `irs_nodes` only; SPI
  trigger config goes to the IRS found by `gicv5_irs_lookup_by_spi_id()`; a
  CPU registers with the IRS in `per_cpu_irs_data`.
- ITS device tree nodes: children of an IRS node, not of the GIC node;
  `gicv5_irs_its_probe()` calls `gicv5_its_of_probe()` once per IRS.
- IWB: not probed by the GIC driver; a platform driver
  (`gicv5_iwb_platform_driver`) bound by "arm,gic-v5-iwb" or ACPI
  "ARMH0003"; `gicv5_iwb_init_bases()` returns `ERR_PTR(-EINVAL)` when
  firmware left `GICV5_IWB_CR0_IWBEN` clear.

**Typed IDs and bare IDs**

- Instruction operand fields: the per-instruction type and ID masks, for
  example `GICV5_GIC_CDAFF_TYPE_MASK` and `GICV5_GIC_CDAFF_ID_MASK`, are in
  `arch/arm64/include/asm/sysreg.h`, not in
  `include/linux/irqchip/arm-gic-v5.h`.
- Host `hwirq`: always the bare ID in the PPI, SPI and LPI domains; each
  helper adds the type with `FIELD_PREP()` when it builds an operand, for
  example `gicv5_iri_irq_write_pending_state()`.
- `GIC CDEOI`: takes no ID; `gicv5_handle_irq()` issues `gic_insn(0, CDEOI)`.
  `GIC CDDI` in `gicv5_hwirq_eoi()` carries type and ID.
- Host places that hold a typed ID: the `GICR CDIA` result, split in
  `handle_irq_per_domain()`; and `param[0]` of an ACPI fwspec, split in
  `gicv5_irq_domain_translate()` and the two `select` callbacks.
- ACPI GSI with `GICV5_GSI_IC_TYPE` equal to `GICV5_GSI_IWB_TYPE`: not a typed
  interrupt ID; bits 28:0 hold IWB frame and wire, see
  `gic_v5_get_gsi_domain_id()`.
- KVM helpers that build and take apart a typed ID, for example
  `vgic_v5_make_ppi()` and `vgic_v5_get_hwirq_id()`: defined in
  `include/kvm/arm_vgic.h`; see "KVM interrupt ID helpers".
- KVM `intid` of `struct vgic_irq`: typed on a GICv5 VM, set by
  `vgic_v5_setup_private_irq()`; `__irq_is_ppi()`, `__irq_is_spi()` and
  `__irq_is_lpi()` read the type field.
- `kvm_vm_ioctl_irq_line()`: userspace passes a bare number; the function
  range-checks a PPI number bare and makes no check on an SPI number, then
  converts with `vgic_v5_make_ppi()` or `vgic_v5_make_spi()` before
  `kvm_vgic_inject_irq()`.
- **Unsafe usage**: passing a bare PPI number to `vgic_get_vcpu_irq()` on a
  GICv5 VM.
  - Unsafe: type field 0 fails `__irq_is_ppi()`, the call falls through to
    `vgic_get_irq()`, which returns `NULL` for a GICv5 VM.
  - Safe: wrap the loop index with `vgic_v5_make_ppi()`, as
    `vgic_v5_flush_ppi_state()` does.
- **Unsafe usage**: using a typed KVM `intid` as a bit or array index.
  - Unsafe: the type bits put the index far outside a
    `VGIC_V5_NR_PRIVATE_IRQS` bitmap.
  - Safe: take `vgic_v5_get_hwirq_id()` first, as `vgic_v5_set_ppi_dvi()`
    does; `vgic_get_vcpu_irq()` does the same before indexing `private_irqs`.

**Hardware IRQ numbers per domain**

- ITS domain `hwirq`: 64-bit, DeviceID in `GICV5_ITS_HWIRQ_DEVICE_ID`, EventID
  in `GICV5_ITS_HWIRQ_EVENT_ID`; it is not the LPI. The LPI is
  `d->parent_data->hwirq`, read in `gicv5_its_irq_domain_activate()`.
- IPI domain `hwirq`: the index inside the one allocation, set in
  `gicv5_irq_ipi_domain_alloc()`; the LPI is in the parent `irq_data`.
- IWB domain `hwirq`: the wire number; `gicv5_iwb_domain_set_desc()` copies it
  to `alloc_info->hwirq`, and `MSI_ALLOC_FLAGS_FIXED_MSG_DATA` makes
  `gicv5_its_alloc_eventid()` use it as the EventID.
- LPI domain `hwirq`: taken from `alloc_lpi()` inside
  `gicv5_irq_lpi_domain_alloc()`; the `arg` pointer is not used, and
  `gicv5_its_irq_domain_alloc()` passes `NULL` to the parent.
- Typed ID split on the host: in `handle_irq_per_domain()`;
  `gicv5_handle_irq()` only extracts `GICV5_HWIRQ_INTID`.
- ITS `hwirq` readers: only the EventID half is read back, into a `u16` in
  the domain callbacks; no code reads `GICV5_ITS_HWIRQ_DEVICE_ID` back out,
  the DeviceID comes from `struct gicv5_its_dev`.
- MSI address: `its_trans_phys_base` of `struct gicv5_its_dev`, copied from
  `info->scratchpad[1]` in `gicv5_its_msi_prepare()`;
  `its_v5_pci_msi_prepare()` and `its_v5_pmsi_prepare()` in
  `drivers/irqchip/irq-gic-its-msi-parent.c` fill it per device.

**Interrupt domains**

| Domain | Created in | Parent | fwnode | Bus token |
|---|---|---|---|---|
| PPI | `gicv5_init_domains()` | none | GIC | `DOMAIN_BUS_WIRED` |
| SPI | `gicv5_init_domains()` | none | GIC | `DOMAIN_BUS_WIRED` |
| LPI | `gicv5_init_lpi_domain()` | none | `NULL` | none |
| IPI | `gicv5_init_domains()` | LPI | `NULL` | none |
| ITS | `gicv5_its_init_domain()` | LPI | ITS | `DOMAIN_BUS_NEXUS` |
| IWB | `gicv5_iwb_create_device_domain()` | ITS | IWB device | `DOMAIN_BUS_WIRED_TO_MSI` |

- `gicv5_init_lpi_domain()`: creates the LPI domain only; called from
  `gicv5_irs_init()` for the first IRS, so before `gicv5_init_domains()` and
  before the IST exists (`gicv5_irs_enable()` runs later).
- PPI and SPI domains: `irq_domain_create_linear()`, with no parent.
- LPI and IPI domains: no fwnode and no token, so no fwnode lookup finds them;
  code reaches them through `gicv5_global_data`.
- `gicv5_init_lpi_domain()`: does not check the result of
  `irq_domain_create_tree()`; with no LPI domain `gicv5_init_domains()` warns,
  creates no IPI domain and still returns 0.
- `gicv5_free_domains()`: removes PPI, SPI and IPI domains, not the LPI
  domain; `gicv5_free_lpi_domain()`, called from `gicv5_irs_remove()`, does.
- ACPI: the PPI and SPI fwnode is `gsi_domain_handle`, allocated in
  `gic_acpi_init()`.
- ITS domain: created with `IRQ_DOMAIN_FLAG_FWNODE_PARENT`, so
  `msi_lib_irq_domain_select()` compares the parent of the looked-up fwnode
  with the ITS fwnode.

**Chip operations per interrupt kind**

- `gicv5_ppi_irq_chip`: has `irq_set_vcpu_affinity`; it marks the PPI
  forwarded, and `gicv5_ppi_irq_eoi()` then skips the `GIC CDDI`.
- `gicv5_spi_irq_set_type()`: defined in `drivers/irqchip/irq-gic-v5-irs.c`;
  writes `GICV5_IRS_SPI_SELR` then `GICV5_IRS_SPI_CFGR` by MMIO under
  `spi_config_lock`; it does not issue `GIC CDHM`.
- `gicv5_spi_irq_set_type()`: treats high/low and rising/falling as the same;
  any other value, such as `IRQ_TYPE_EDGE_BOTH`, returns `-EINVAL`.
- SPI flow handler: `handle_fasteoi_irq()` for edge and level alike.
- `gicv5_its_irq_chip`: no `irq_retrigger`, no `irq_set_type`, no `flags`.
- Resend of an ITS interrupt: `try_retrigger()` in `kernel/irq/resend.c` falls
  back to `irq_chip_retrigger_hierarchy()`, which reaches
  `gicv5_lpi_irq_retrigger()`.
- SPI and LPI `irq_set_irqchip_state`: accepts `IRQCHIP_STATE_PENDING` only,
  anything else returns `-EINVAL`; `irq_get_irqchip_state` handles pending and
  active.
- PPI `irq_set_irqchip_state`: accepts pending and active.
- Software pending for SPI and LPI: `gicv5_iri_irq_write_pending_state()`;
  there is no gicv5_iri_irq_set_irqchip_state() here.
- IWB chip: its type callback is `gicv5_iwb_set_type()`, in `iwb_msi_template`.

**Inter-processor interrupts**

- Backing: each IPI is an LPI; count is `GICV5_IPIS_PER_CPU * nr_cpu_ids`,
  with `GICV5_IPIS_PER_CPU` defined as `MAX_IPI`.
- `gicv5_irq_ipi_domain_alloc()`: makes one `irq_domain_alloc_irqs_parent()`
  call for the whole range; `gicv5_irq_lpi_domain_alloc()` picks each LPI.
- Routing: not done at allocation. `ipi_setup_lpi()` in
  `arch/arm64/kernel/smp.c`, reached from `set_smp_ipi_range_percpu()`, calls
  `irq_force_affinity()` for each CPU, so the target may be offline.
- `gicv5_ipi_send_single()`: calls `irq_chip_retrigger_hierarchy()`, not
  `irq_chip_set_parent_state()`; that reaches `gicv5_lpi_irq_retrigger()` and
  ends in `GIC CDPEND`.
- `gicv5_ipi_irq_chip`: has no `irq_retrigger` of its own;
  `irq_chip_retrigger_hierarchy()` starts at the parent `irq_data`.
- Send to a mask: `arm64_send_ipi()` loops over the mask and calls
  `__ipi_send_single()` with that CPU's own descriptor.
- IPI allocation failure in `gicv5_smp_init()`: `WARN()` and return;
  `set_smp_ipi_range_percpu()` is not called.

**LPI number allocation**

- `alloc_lpi()` with no IST set up: `num_lpis` is 0, returns `-ENOSPC`.
- `num_lpis`: `BIT(lpi_id_bits)`, set by `gicv5_irs_init_ist()`. See there for
  the bit count; the part that is easy to miss is the final cap by
  `gicv5_global_data.cpuif_id_bits`, read from the boot CPU.
- Two-level support of the IRS: the bit `GICV5_IRS_IDR2_IST_LEVELS`, tested in
  `gicv5_irs_init_ist()`; it selects the starting bit count, see "LPI ID bits
  and layout".
- `lpi_ida`: one allocator for the IPIs and for every ITS.
- `alloc_lpi()` and `release_lpi()`: static, called only by the LPI domain
  callbacks. There is no gicv5_alloc_lpi() or gicv5_free_lpi() here.
- `gicv5_lpi_config_reset()`: sets handling mode to edge and clears pending;
  it does not touch enable, priority, affinity or active state.
- `gicv5_hwirq_init()`: writes priority only (`GIC CDPRI`); nothing in
  `gicv5_irq_lpi_domain_alloc()` writes a route for the new LPI.

**LPI domain allocation unwind**

- `gicv5_irq_lpi_domain_alloc()`: loops over `nr_irqs` and calls `alloc_lpi()`
  itself; it does not reject `nr_irqs != 1` and does not take an LPI from
  `arg`.
- `alloc_lpi()` failure at index `i`: nothing is in flight; the function only
  frees interrupts 0 to `i - 1`.
- `gicv5_irs_iste_alloc()` failure: `release_lpi()` for the in-flight LPI,
  then the same free of 0 to `i - 1`.
- Interrupts already set up: undone by `gicv5_irq_lpi_domain_free()` with
  count `i`; the LPI domain has no parent, so
  `irq_domain_free_irqs_parent()` plays no part.
- Not undone: an L2 IST that `gicv5_irs_iste_alloc()` installed stays; the
  priority and handling mode written to hardware stay.
- `gicv5_irq_ipi_domain_alloc()` and `gicv5_its_irq_domain_alloc()`: neither
  frees an LPI; each makes one parent call for the whole range and the loop
  after it cannot fail. The ITS error path releases the EventID range only.
- **Unsafe usage**: returning an error from a domain `alloc` callback while
  earlier interrupts of the range still hold resources.
  - Unsafe: `irq_domain_alloc_irqs_locked()` does not call the `free` callback
    when `alloc` fails; it frees only `irq_data` and descriptors, so the LPIs
    stay allocated in `lpi_ida`.
  - Safe: free 0 to `i - 1` before returning, as
    `gicv5_irq_lpi_domain_alloc()` does.
  - Safe: do every step that can fail before the per-interrupt loop, as
    `gicv5_its_irq_domain_alloc()` does.
- **Unsafe usage**: passing the in-flight interrupt, or all `nr_irqs`, to
  `gicv5_irq_lpi_domain_free()` from the error path.
  - Unsafe: `gicv5_irq_lpi_domain_free()` calls `release_lpi()` on `d->hwirq`,
    which is not set until `irq_domain_set_info()` has run for that interrupt.
  - Safe: `release_lpi()` on the local value for the in-flight interrupt, then
    `gicv5_irq_lpi_domain_free()` with count `i`, as
    `gicv5_irq_lpi_domain_alloc()` does.

**Firmware specifier translation**

- `*hwirq` from `gicv5_irq_domain_translate()`: the bare ID in both the device
  tree and the ACPI case, never a typed ID.
- Wanted type: only `GICV5_HWIRQ_TYPE_PPI` and `GICV5_HWIRQ_TYPE_SPI` have a
  translate wrapper; an LPI specifier matches neither domain.
- ACPI fwnode (`is_fwnode_irqchip()`): `param_count` must be exactly 2;
  `param[0]` is a typed ID split with `GICV5_HWIRQ_TYPE` and
  `GICV5_HWIRQ_ID`; `param[1]` is the trigger. `acpi_register_gsi()` in
  `drivers/acpi/irq.c` builds it from the GSI.
- ACPI GSI with `GICV5_GSI_IC_TYPE` equal to `GICV5_GSI_IWB_TYPE`:
  `gic_v5_get_gsi_domain_id()` returns the IWB fwnode, so the fwspec never
  reaches the PPI or SPI domain.
- PPI trigger: `IRQ_TYPE_LEVEL_LOW` when the HMR bit is set, else
  `IRQ_TYPE_EDGE_RISING`; the HMR is read on the CPU that runs the translate.
- `gicv5_irq_ppi_domain_select()` and `gicv5_irq_spi_domain_select()`: ignore
  the `bus_token` argument; they match on fwnode and type only.
- `irq_find_matching_fwspec()`: calls `select` only when the token is not
  `DOMAIN_BUS_ANY`; with `DOMAIN_BUS_ANY` it compares fwnodes and returns the
  first domain on the list with the GIC fwnode, whatever the type.
- `fwspec_to_domain()`: asks with `DOMAIN_BUS_WIRED` first, so wired lookups
  go through `select`; `DOMAIN_BUS_ANY` is the fallback.
- `gicv5_iwb_irq_domain_translate()`: for an ACPI device node the wire is
  `GICV5_GSI_IWB_WIRE` of `param[0]`; for device tree it is `param[0]` as is.

**Interrupt affinity**

- Target CPU: with `force`, `cpumask_first()` of the mask, online or not;
  without, `cpumask_any_and()` of the mask and `cpu_online_mask`.
- Return value on success: `IRQ_SET_MASK_OK_DONE`.
- CPU with no IAFFID: `gicv5_irs_cpu_to_iaffid()` prints an error and returns
  `-ENODEV`, not `-EINVAL`; the callback returns it before `GIC CDAFF` and
  before the effective affinity is updated.
- `gicv5_irs_cpu_to_iaffid()`: tests only the `valid` flag of `cpu_iaffid`; it
  has no present or online test.
- `cpu_iaffid`: filled at IRS probe, not at CPU bring-up, by
  `gicv5_irs_of_init_affinity()` or `gic_acpi_parse_iaffid()`; a CPU whose
  IAFFID exceeds the IRS IAFFID bits is left invalid.
- **Potentially unsafe usage**: calling `gicv5_iri_irq_set_affinity()` without
  `force` and with a mask that holds no online CPU.
  - Unsafe: the callback does not range-check the result of
    `cpumask_any_and()` before `gicv5_irs_cpu_to_iaffid()` indexes per-CPU
    data with it.
  - Safe: through `irq_do_set_affinity()` in `kernel/irq/manage.c`, which
    passes only a mask already reduced to online CPUs when `force` is false.

## Instructions, barriers and the interrupt path

**GIC system instructions**

- The table has only the instructions where this tree differs from the usual
  picture, and covers kernel code only, not `tools/`.

| Instruction | Issued as | Only issued from | Easy to miss |
|---|---|---|---|
| CDEOI | `gic_insn(0, CDEOI)` | `gicv5_handle_irq()` | not issued by `gicv5_hwirq_eoi()` or any `irq_eoi` |
| CDDI | `gic_insn(cddi, CDDI)` | `gicv5_hwirq_eoi()`; `vgic_v3_deactivate_phys()` in `arch/arm64/kvm/vgic/vgic-v3.c` | the KVM site runs under `ARM64_HAS_GICV5_LEGACY` and hard-codes type 1 (PPI) |
| CDAFF | `gic_insn(cdaff, CDAFF)` | `gicv5_iri_irq_set_affinity()` | `gicv5_hwirq_init()` does not issue it; it issues CDPRI only |
| CDHM | `gic_insn(cdhm, CDHM)` | `gicv5_lpi_config_reset()` | LPI only, always HM 0 (edge) |
| CDNMIA | never issued | - | outside `tools/`, `GICV5_OP_GICR_CDNMIA` is used only in the trap table in `arch/arm64/kvm/emulate-nested.c` |

**Acknowledge and dispatch**

- `gicv5_handle_irq()` after a valid acknowledge: `gsb_ack()`, `isb()`, then
  `gic_insn(0, CDEOI)`, then `handle_irq_per_domain()`.
- Invalid acknowledge: returns before `gsb_ack()`, `isb()` and the
  `gic_insn(0, CDEOI)`.
- `handle_irq_per_domain()`: returns `void`; both failure paths log with
  `pr_err_once()`.
- Unknown type: returns with no CDDI; the priority has already been dropped.
- `generic_handle_domain_irq()` returns non-zero: calls `gicv5_hwirq_eoi()`,
  which only deactivates (CDDI); the drop was already done.

**Priority drop**

- `gic_insn(0, CDEOI)`: issued in `gicv5_handle_irq()`, straight after the
  `gsb_ack()` and `isb()` that follow the acknowledge.
- Order for one interrupt: acknowledge, drop, flow handler and action, then
  CDDI from `irq_eoi`.
- The handler therefore runs with the running priority already dropped and
  the interrupt not yet deactivated.
- Reason in the comment above it: to be able to receive the next interrupts
  when a handler runs long or the CPU directly enters a guest.

**Forwarded PPIs**

- Marking: `irqd_set_forwarded_to_vcpu()` and `irqd_clr_forwarded_to_vcpu()`;
  the driver keeps no bitmap of its own.
- The flag lives in the shared `struct irq_common_data`, so every chip
  stacked on the PPI sees it through `irqd_is_forwarded_to_vcpu()`.
- `gicv5_ppi_irq_eoi()` on a forwarded PPI: returns without issuing any
  instruction; the priority drop was already issued in `gicv5_handle_irq()`.
- KVM timer PPIs on a GICv5 host: `kvm_irq_init()` in
  `arch/arm64/kvm/arch_timer.c` pushes its own chip on top when
  `kvm_vgic_global_state.type == VGIC_V5`.
- `irq_set_vcpu_affinity()` stops at the first chip from the top that has
  the callback, so for those PPIs `timer_irq_set_vcpu_affinity()` sets the
  flag, not `gicv5_ppi_irq_set_vcpu_affinity()`.
- `timer_irq_eoi()`: skips `irq_chip_eoi_parent()` when forwarded, so
  `gicv5_ppi_irq_eoi()` is not reached for them.
- The host does not deactivate a forwarded PPI from `irq_eoi`; KVM owns its
  active state, and how depends on the guest:

| Guest | What KVM does with the host PPI |
|---|---|
| GICv5 | `timer_irq_set_irqchip_state()` turns an `IRQCHIP_STATE_ACTIVE` request into `irq_chip_mask_parent()` or `irq_chip_unmask_parent()`: masked in `kvm_timer_vcpu_load_gic()`, unmasked in `kvm_timer_vcpu_put()`; the PPI is handed to the guest with the bit `vgic_v5_set_ppi_dvi()` sets |
| GICv3 on GICv5 | the request passes through to `gicv5_ppi_irq_set_irqchip_state()`; when KVM emulates the guest's deactivate, `vgic_v3_deactivate_phys()` issues CDDI itself |

**Synchronisation after mask and unmask**

- `gicv5_ppi_irq_mask()` and `gicv5_ppi_irq_unmask()`: both end with
  `isb()`; neither uses `gsb_sys()`.
- PPI mask comment: the disable must take effect immediately for lazy
  disable to work, and a context synchronization event guarantees it.
- PPI unmask comment: the enable must take effect in finite time, and a
  context synchronization event cannot be taken for granted, for example a
  core going straight into idle.
- Both PPI comments cite `I_ZLTKB/R_YRGMH`; the SPI/LPI comments cite
  `R_XCLJC`.

**Reading SPI and LPI state**

- `gicv5_iri_irq_get_irqchip_state()`: `gic_insn(cdrcfg, CDRCFG)`, `isb()`,
  then the read of `SYS_ICC_ICSR_EL1`; there is no `gsb_sys()`.
- KVM keeps one copy, the guest's, in `vgic_icsr` of
  `struct vgic_v5_cpu_if`; nothing saves or restores the host's value.
- `__vgic_v5_save_state()` and `__vgic_v5_restore_state()` in
  `arch/arm64/kvm/hyp/vgic-v5-sr.c` do the save and restore.
- After a GICv5 guest has run on a CPU, `SYS_ICC_ICSR_EL1` there holds the
  guest's value, until the next CDRCFG.
- **Unsafe usage**: issuing CDRCFG and reading `SYS_ICC_ICSR_EL1` while
  preemptible; a GICv5 vCPU that enters the guest in between overwrites the
  register in `__vgic_v5_restore_state()`.
  - Safe: with `desc->lock` held and IRQs off, as both core paths to the
    callback do: `irq_get_irqchip_state()` and `__synchronize_hardirq()` in
    `kernel/irq/manage.c`.

**Completion of GIC operations**

- `gsb_sys()` and `gsb_ack()`: defined in
  `arch/arm64/include/asm/barrier.h`.
- Encodings: `GSB_SYS_BARRIER_INSN` and `GSB_ACK_BARRIER_INSN` in
  `arch/arm64/include/asm/sysreg.h`, built with `__SYS_BARRIER_INSN()`;
  there are no macros named GSB_SYS or GSB_ACK.
- Kernel callers: `gsb_sys()` only in `gicv5_iri_irq_mask()`, `gsb_ack()`
  only in `gicv5_handle_irq()`.
- Every other `gic_insn()` site has no GSB after it: CDEN, CDPRI, CDAFF,
  CDPEND, CDHM, CDDI and CDEOI have nothing, CDRCFG has `isb()`.
- IRS and ITS table memory: not ordered with `gsb_sys()`; for example
  `drivers/irqchip/irq-gic-v5-irs.c` uses `dsb(ishst)` or
  `dcache_clean_inval_poc()` before the MMIO write.
- `ICC_*` register writes: not every one is followed by `isb()`; for example
  `write_ppi_sysreg_s()` and the `SYS_ICC_CR0_EL1` write in
  `gicv5_cpu_enable_interrupts()` have none.
- **Potentially unsafe usage**: a `gic_insn()` with no `gsb_sys()` after it.
  - Unsafe: when the caller must be able to rely on the effect on return,
    as SPI/LPI `irq_mask` must for lazy disable.
  - Safe: when completion in finite time is enough, as in
    `gicv5_iri_irq_unmask()`; its comment cites `R_XCLJC` as the only
    requirement.
- **Unsafe usage**: ending a PPI `irq_mask` or `irq_unmask` after the
  `SYS_ICC_PPI_ENABLER0_EL1` or `SYS_ICC_PPI_ENABLER1_EL1` write with no
  `isb()`.
  - Safe: write, then `isb()`, as `gicv5_ppi_irq_mask()` and
    `gicv5_ppi_irq_unmask()` do; see "Synchronisation after mask and
    unmask".

**End-of-interrupt callbacks**

- `gicv5_hwirq_eoi()`: issues `gic_insn(cddi, CDDI)` and nothing else.

| Chip | `irq_eoi` does |
|---|---|
| `gicv5_ppi_irq_chip` | forwarded to a vCPU: nothing; else CDDI with `GICV5_HWIRQ_TYPE_PPI` |
| `gicv5_spi_irq_chip` | CDDI with `GICV5_HWIRQ_TYPE_SPI` |
| `gicv5_lpi_irq_chip` | CDDI with `GICV5_HWIRQ_TYPE_LPI` |

- The one priority drop per acknowledge is done by `gicv5_handle_irq()`,
  not by the callback; see "Priority drop".
- **Unsafe usage**: issuing `gic_insn(0, CDEOI)` from an `irq_eoi` callback
  or from a handler reached through `gicv5_handle_irq()`; it is a second
  drop for one acknowledge, and `CDEOI` names no interrupt.
  - Safe: deactivate only, with the acknowledged type and ID, as
    `gicv5_hwirq_eoi()` does.
- Chips stacked on the PPI, SPI or LPI domain: pass eoi down with
  `irq_chip_eoi_parent()`, as `gicv5_ipi_irq_chip` and `gicv5_its_irq_chip`
  do; `timer_irq_eoi()` in `arch/arm64/kvm/arch_timer.c` does so only when
  the PPI is not forwarded.

## CPU interface and PPIs

**Interrupt priorities**

- `GICV5_IRQ_PRI_MI`: `GICV5_IRQ_PRI_MASK & GENMASK(4, 5 - pri_bits)`, with
  `GICV5_IRQ_PRI_MASK` 0x1f; 5 bits gives 0x1f, 4 gives 0x1e, 1 gives 0x10.
- `pri_bits`: a file-static `u8` in `drivers/irqchip/irq-gic-v5.c`, default 5;
  it is not a field of `gicv5_global_data`, which holds the two inputs
  `cpuif_pri_bits` and `irs_pri_bits`.
- `pri_bits` is assigned in `gicv5_init_common()`, which both
  `gicv5_of_init()` and `gic_acpi_init()` call, as `min_not_zero()` of the
  two inputs.
- SPIs and LPIs: `gicv5_hwirq_init()` programs the priority with
  `gic_insn(cdpri, CDPRI)`, a system instruction, not an IRS MMIO write.
- `GICV5_IRS_SPI_CFGR`: `gicv5_spi_irq_set_type()` writes only the trigger
  mode `GICV5_IRS_SPI_CFGR_TM` to it, no priority.
- `gicv5_hwirq_init()`: issues `CDPRI` only, and does nothing for a type other
  than `GICV5_HWIRQ_TYPE_LPI` or `GICV5_HWIRQ_TYPE_SPI`.
- Mask equal to the interrupt priority: `gicv5_cpu_enable_interrupts()` writes
  `GICV5_IRQ_PRI_MI` to `SYS_ICC_PCR_EL1`, the value the interrupts get; that
  write is the driver's only access to `SYS_ICC_PCR_EL1`, it never compares a
  priority with the mask.

**CPU interface bring-up**

- Scope: the functions in `drivers/irqchip/irq-gic-v5.c`;
  `tools/testing/selftests/kvm/include/arm64/gic_v5.h` has its own functions
  named `gicv5_cpu_enable_interrupts()`, `gicv5_cpu_disable_interrupts()` and
  `gicv5_ppi_priority_init()`, which these bullets do not describe.
- `gicv5_cpu_disable_interrupts()`: the `SYS_ICC_CR0_EL1` write that clears
  EN is followed by `isb()`.
- `gicv5_cpu_enable_interrupts()`: the `SYS_ICC_PCR_EL1` write and the
  `SYS_ICC_CR0_EL1` write that sets EN are its last two writes, with no
  `isb()` after them; the body of `gicv5_starting_cpu()` adds none.
- `gicv5_ppi_priority_init()`: ends with one `isb()`, after all 16 priority
  writes.
- `SYS_ICC_PPI_ENABLER0_EL1` and `SYS_ICC_PPI_ENABLER1_EL1` clears: the
  first `isb()` after them is the one that ends `gicv5_ppi_priority_init()`.
- `SYS_ICC_CR0_EL1` in both functions: read, change `ICC_CR0_EL1_EN_MASK`
  only, write back; the other fields keep their value.
- `SYS_ICC_PCR_EL1`: written whole, not read-modify-write.
- `gicv5_cpu_disable_interrupts()` undoes EN only; PPI enables, PPI
  priorities and `SYS_ICC_PCR_EL1` keep what enable wrote.
- `gicv5_cpu_disable_interrupts()`: its one caller is the `out_int` label of
  `gicv5_init_common()`.
- `out_int` is reached when `gicv5_starting_cpu()` itself fails, as well as
  from later failures, so disable can run when
  `gicv5_cpu_enable_interrupts()` never ran.
- **Potentially unsafe usage**: adding an ICC system register write with no
  `isb()` after it.
  - Unsafe: when later code relies on the write having taken effect and no
    `isb()` runs in between; `gicv5_cpu_enable_interrupts()` has no `isb()`
    after its `gicv5_ppi_priority_init()` call.
  - Safe: before the `gicv5_ppi_priority_init()` call, where the `isb()` that
    ends that function follows it, as for the two enable-register clears.
  - Safe: with its own `isb()` after the write, as in
    `gicv5_cpu_disable_interrupts()` and `gicv5_ppi_irq_mask()`.

**PPI trigger type**

- `gicv5_ppi_irq_set_type()`: installed as `.irq_set_type` of
  `gicv5_ppi_irq_chip`.
- `gicv5_ppi_irq_set_type()` returns `-EINVAL` when the request has a bit of
  `IRQ_TYPE_EDGE_BOTH` and the hardware says level, or a bit of
  `IRQ_TYPE_LEVEL_MASK` and the hardware says edge.
- `gicv5_ppi_irq_set_type()` returns 0 otherwise, including for
  `IRQ_TYPE_NONE`; it writes no register.
- Polarity is not compared: high and low level both pass on a level PPI,
  rising and falling both pass on an edge PPI.
- `gicv5_ppi_irq_is_level()`: a set bit in the handling-mode register means
  level.
- Reported trigger: `gicv5_irq_domain_translate()` with
  `GICV5_HWIRQ_TYPE_PPI` discards the trigger from the firmware specifier.
- Specifier format in `gicv5_irq_domain_translate()`: an OF node needs at
  least 3 cells.

**PPI register banks**

- Enable: there are no separate set-enable and clear-enable registers; only
  `SYS_ICC_PPI_ENABLER0_EL1` and `SYS_ICC_PPI_ENABLER1_EL1`.
- `gicv5_ppi_irq_mask()` and `gicv5_ppi_irq_unmask()`: open-code the enable
  access with `sysreg_clear_set_s()` then `isb()`; `enum ppi_reg` has no
  enable value.
- `read_ppi_sysreg_s()`: switches on `which`, picks the bank with `irq < 64`,
  and returns the whole 64-bit register; the caller masks with
  `BIT_ULL(hwirq % 64)`.
- `read_ppi_sysreg_s()` reads pending and active state from the set
  registers, for example `SYS_ICC_PPI_SPENDR0_EL1`; the driver never reads a
  clear register.
- `write_ppi_sysreg_s()`: writes only the one bit, to the set or the clear
  register; no read-modify-write and no `isb()`.
- `write_ppi_sysreg_s()` has no `PPI_HM` case; passing it fails the build at
  `BUILD_BUG_ON(1)`.
- Per-PPI priority field: the driver never computes one;
  `gicv5_ppi_priority_init()` writes all 16 registers whole.
- `vgic_v5_sync_ppi_priorities()` in `arch/arm64/kvm/vgic/vgic-v5.c` is the
  in-tree per-PPI computation: register `i / 8`, field
  `GENMASK(pri_bit + 4, pri_bit)` with `pri_bit` equal to `(i % 8) * 8`.
- **Unsafe usage**: passing an INTID that still holds `GICV5_HWIRQ_TYPE` in
  bits 31:29 to `read_ppi_sysreg_s()` or `write_ppi_sysreg_s()`; `irq < 64`
  is then false for every PPI, so bank 1 is always used.
  - Safe: the `GICV5_HWIRQ_ID` field alone, which `handle_irq_per_domain()`
    extracts before `generic_handle_domain_irq()`; `d->hwirq` in the PPI
    domain is the bare ID too, set from `gicv5_irq_domain_translate()`, as
    used in `gicv5_ppi_irq_get_irqchip_state()`.

**ID register decoding**

- Unknown encoding, all three functions: log, store the smallest known width,
  return `void`; the probe continues.

| Function | Log | Stored |
|---|---|---|
| `gicv5_set_cpuif_pribits()` | `pr_err()` | `cpuif_pri_bits` = 4 |
| `gicv5_set_cpuif_idbits()` | `pr_err()` | `cpuif_id_bits` = 16 |
| `irs_setup_pri_bits()` | `pr_warn()` | `irs_pri_bits` = 1 |

- `irs_pri_bits` of 1 makes `pri_bits` 1 in `gicv5_init_common()`, so
  `GICV5_IRQ_PRI_MI` becomes 0x10.
- The two CPU interface decoders run once, on the boot CPU, from
  `gicv5_init_common()`; `gicv5_starting_cpu()` decodes nothing on a
  secondary CPU.
- `irs_setup_pri_bits()` runs only for the first IRS, under
  `list_empty(&irs_nodes)` in `gicv5_irs_init()`.
- **Unsafe usage**: using the raw value of `ICC_IDR0_EL1_PRI_BITS`,
  `ICC_IDR0_EL1_ID_BITS` or `GICV5_IRS_IDR1_PRIORITY_BITS` as a bit count;
  the values are encodings, for example `ICC_IDR0_EL1_PRI_BITS_4BITS` is
  0b0011 and `GICV5_IRS_IDR1_PRIORITY_BITS_1BITS` is 0b000.
  - Safe: a `switch` over the named encodings with a `default`, as in
    `gicv5_set_cpuif_pribits()`; the encodings are defined in
    `arch/arm64/tools/sysreg` and `include/linux/irqchip/arm-gic-v5.h`.
- Numeric ID fields are not decoded with a `switch`:
  `gicv5_irs_init_ist()` uses `GICV5_IRS_IDR2_ID_BITS` as read, and
  `gicv5_irs_of_init()` uses `GICV5_IRS_IDR1_IAFFID_BITS` plus 1.

## IRS probing and registers

**Probe order**

- LPI domain: created by `gicv5_init_lpi_domain()` from `gicv5_irs_init()`
  for the first IRS, not by `gicv5_init_domains()`; freed by
  `gicv5_free_lpi_domain()` in `gicv5_irs_remove()`.
- `gicv5_init_domains()`: creates the PPI domain, the SPI domain only when
  `global_spi_count` is non-zero, and the IPI domain as a child of
  `gicv5_global_data.lpi_domain`; `gicv5_free_domains()` removes those three.
- Last possible failure in `gicv5_init_common()`: `gicv5_irs_enable()`.
  `gicv5_smp_init()` and `gicv5_irs_its_probe()` return void, so the hotplug
  state, the IPIs and the ITSs are never unwound.
- `gicv5_irs_enable()` failure: the `out_handle` label calls
  `set_handle_irq(NULL)`; `set_handle_irq()` in `arch/arm64/kernel/irq.c`
  returns `-EBUSY` and changes nothing once a handler is installed.
- `gicv5_irs_remove()`, left to both callers: per IRS it also calls
  `gicv5_irs_clear_affinity()` and `gicv5_irs_disable()` before unmapping.
- ITS probing: `gicv5_irs_its_probe()` inside `gicv5_init_common()` on both
  paths; it picks `gicv5_its_of_probe()` or `gicv5_its_acpi_probe()` by
  `acpi_disabled`.

| | `gicv5_of_init()` | `gic_acpi_init()` |
|---|---|---|
| entered | once, for the `arm,gic-v5` node | once per MADT IRS entry of version `ACPI_MADT_GIC_VERSION_V5`; returns 0 at once when `gsi_domain_handle` is set |
| domain fwnode | `of_fwnode_handle()` of the node | `irq_domain_alloc_fwnode(&irs->config_base_address)` |
| an IRS fails to probe | `gicv5_irs_of_probe()` logs and tries the next child | non-zero return from `gic_acpi_parse_madt_irs()` ends the walk in `acpi_parse_entries_array()`; `gicv5_irs_acpi_probe()` ignores that and tests only `list_empty(&irs_nodes)` |
| affinity parse | can fail the IRS | `gicv5_irs_acpi_init_affinity()` always returns 0 |
| `fwnode` in `struct gicv5_irs_chip_data` | the IRS node | left NULL |
| KVM | `gic_of_setup_kvm_info()` | no call to `vgic_set_kvm_info()` |
| after success | nothing more | `acpi_set_irq_model()` with `ACPI_IRQ_MODEL_GIC_V5` |

**CPU affinity IDs**

- Device tree: `cpus` (phandles) and `arm,iaffids` (u16 array) on the IRS
  node, paired by index; the IAFFID is not derived from the MPIDR.
- ACPI: `gic_acpi_parse_iaffid()` in `drivers/irqchip/irq-gic-v5-irs.c`;
  `gicv5_irs_acpi_init_affinity()` walks every
  `ACPI_MADT_TYPE_GENERIC_INTERRUPT` entry once per IRS.
- ACPI match: `irs_id` of `struct acpi_madt_generic_interrupt` equal to
  `irs_id` of the IRS entry; the value is its `iaffid` field.
- ACPI CPU number: `get_logical_index(gicc->arm_mpidr)`; the code does not
  call `acpi_cpu_get_madt_gicc()`.
- ACPI entries with neither `ACPI_MADT_ENABLED` nor
  `ACPI_MADT_GICC_ONLINE_CAPABLE`: skipped silently.
- `gicv5_irs_cpu_to_iaffid()` for a CPU with `valid` false: returns
  `-ENODEV`, prints an error, leaves `*iaffid` unwritten.
- `gicv5_irs_clear_affinity()`: sets `valid` false and `per_cpu_irs_data`
  NULL again for every CPU of an IRS whose probe fails after the affinity
  parse, or that `gicv5_irs_remove()` removes.

**CPU registration with an IRS**

- `GICV5_IRS_PE_SELR`: gets the IAFFID; `GICV5_IRS_PE_CR0`: gets only
  `GICV5_IRS_PE_CR0_DPS` set to 1.

| Condition in `gicv5_irs_register_cpu()` | Return |
|---|---|
| no valid IAFFID | `-ENODEV` |
| `per_cpu_irs_data` is NULL | `-ENXIO` |
| wait after `GICV5_IRS_PE_SELR` fails, by timeout or V clear | `-ENXIO` |
| wait after `GICV5_IRS_PE_CR0` times out | `-ETIMEDOUT` |

- `-EIO` and `-EINVAL`: never returned by `gicv5_irs_register_cpu()`.
- `gicv5_starting_cpu()`: returns `-ENODEV` with a `WARN()` before
  registration when the CPU lacks `ARM64_HAS_GICV5_CPUIF`.
- Hotplug state: `CPUHP_AP_IRQ_GIC_STARTING`, installed by
  `cpuhp_setup_state_nocalls()` in `gicv5_smp_init()` with a NULL teardown.

**SPI ranges and chip data**

- Unclaimed SPI: `gicv5_irq_spi_domain_alloc()` passes the NULL from
  `gicv5_irs_lookup_by_spi_id()` to `irq_domain_set_info()` untested and
  returns 0.
- Lifetime of a non-NULL pointer: `struct gicv5_irs_chip_data` is freed only
  in `__init` code (`gicv5_irs_remove()` and the per-IRS probe error paths),
  so no reference or lock is needed to keep it alive.
- Chip data of the descriptor: reset by `irq_domain_reset_irq_data()` in
  `gicv5_irq_domain_free()`.
- There is no gicv5_irs_spi_set_type() here; `gicv5_spi_irq_set_type()` in
  `drivers/irqchip/irq-gic-v5-irs.c` reads `d->chip_data`.
- PPI, LPI and IPI: chip data is NULL; only the SPI domain stores an IRS.
- **Unsafe usage**: dereferencing the chip data of an SPI as
  `struct gicv5_irs_chip_data *` when nothing has shown that an IRS claims
  the SPI.
  - Unsafe: for an SPI ID outside every IRS range the pointer is NULL.
  - Safe: callbacks that address the SPI by `d->hwirq` alone and never read
    chip data, as `gicv5_spi_irq_set_affinity()` does.

**First-IRS assumptions**

- Global values set in `gicv5_irs_init()` under `list_empty(&irs_nodes)`:

| Register | Field | Stored in `gicv5_global_data` |
|---|---|---|
| `GICV5_IRS_IDR0` | `GICV5_IRS_IDR0_VIRT` | `virt_capable` |
| `GICV5_IRS_IDR1` | `GICV5_IRS_IDR1_PRIORITY_BITS` | `irs_pri_bits` |
| `GICV5_IRS_IDR5` | `GICV5_IRS_IDR5_SPI_RANGE` | `global_spi_count` |

- `GICV5_IRS_IDR2` IST fields: not read in `gicv5_irs_init()`; read in
  `gicv5_irs_init_ist()` from the first entry of `irs_nodes`, when
  `gicv5_irs_enable()` runs.
- Per IRS: `GICV5_IRS_IDR2_LPI` (clear gives `-ENODEV` with a `WARN()`),
  `GICV5_IRS_IDR6`, `GICV5_IRS_IDR7`, and `GICV5_IRS_IDR1_IAFFID_BITS`.
- `GICV5_IRS_IDR1_IAFFID_BITS`: read per IRS by `gicv5_irs_of_init()` and
  `gicv5_irs_acpi_init_affinity()`, although the comment in
  `gicv5_irs_init()` lists it as a global property.
- The IRS used: the first to pass the LPI test in `gicv5_irs_init()`; it is
  also the first entry of `irs_nodes`.
- An IRS that fails earlier (mapping, affinity parse) does not count, so on
  the device tree path the IRS used need not be the first child node.
- Later IRSs: no comparison with the stored values.

**IRS memory attributes**

- Function: `gicv5_irs_init_bases()`, called before any ID register is read.
- Non-coherent: `GICV5_IRS_CR1_SH` is not set; `GICV5_IRS_CR1_IC` and
  `GICV5_IRS_CR1_OC` are `GICV5_NON_CACHE`; allocation hints are the no-alloc
  values.
- `GICV5_IRS_CR1_VPET_WA` and `GICV5_IRS_CR1_VMT_WA`: set in neither branch.
- Non-coherent is selected by the presence of `dma-noncoherent` on the IRS
  node, or by `ACPI_MADT_IRS_NON_COHERENT` in `flags` of
  `struct acpi_madt_gicv5_irs`; the default is coherent.
- Flag name: `IRS_FLAGS_NON_COHERENT`, private to
  `drivers/irqchip/irq-gic-v5-irs.c`.
- `gicv5_irs_wait_for_idle()` after the `GICV5_IRS_CR0` write: its return
  value is ignored.
- `gicv5_irs_disable()`: writes 0 to `GICV5_IRS_CR0` and waits for idle.
- `gicv5_irs_disable()` callers: `gicv5_irs_remove()` for every IRS, and the
  error paths of `gicv5_irs_of_init()` and `gic_acpi_parse_madt_irs()` once
  the registers are mapped.
- All of these are `__init`; the driver has no suspend, shutdown or CPU PM
  hook that disables an IRS.

**IRS sync operation**

- `gicv5_irs_syncr()`: returns void; a timeout is only logged by the poll
  helper.
- Poll: `gicv5_wait_for_op()`, the sleeping variant, so the caller must be
  able to sleep.
- IRS addressed: takes no argument; always the first entry of `irs_nodes`;
  `WARN_ON_ONCE()` and return when the list is empty.
- Other IRSs: never written with `GICV5_IRS_SYNCR`.
- Only caller: `gicv5_its_irq_domain_free()`, as its last step, after
  `irq_domain_free_irqs_parent()` and `gicv5_its_syncr()`.
- Invalidation: `include/linux/irqchip/arm-gic-v5.h` defines no IRS
  invalidate register; `GICV5_ITS_INV_EVENTR` and `GICV5_ITS_INV_DEVICER`
  belong to the ITS.

**Idle and valid status bits**

| Helper | Register polled | Valid test | Poll |
|---|---|---|---|
| `gicv5_irs_wait_for_spi_op()` | `GICV5_IRS_SPI_STATUSR` | always | atomic |
| `gicv5_irs_wait_for_pe_selr()` | `GICV5_IRS_PE_STATUSR` | yes | atomic |
| `gicv5_irs_wait_for_pe_cr0()` | `GICV5_IRS_PE_STATUSR` | no | atomic |
| `gicv5_irs_wait_for_idle()` | `GICV5_IRS_CR0` | no | atomic |
| `gicv5_irs_ist_synchronise()` | `GICV5_IRS_IST_STATUSR` | no | atomic |
| `gicv5_irs_syncr()` | `GICV5_IRS_SYNC_STATUSR` | no | sleeping |

- Failed valid test: `-EIO`, not `-EINVAL`.
- `gicv5_irs_wait_for_irs_pe()`: tests `GICV5_IRS_PE_STATUSR_V` only when
  its `selr` argument is true; the two wrappers in the table fix it.
- `gicv5_irs_wait_for_spi_op()`: tests `GICV5_IRS_SPI_STATUSR_V` after the
  select write and again after the `GICV5_IRS_SPI_CFGR` write.
- Timeout: returned as `-ETIMEDOUT` before the valid bit is looked at.

**Selector register sequences**

- `gicv5_spi_irq_set_type()`: takes `spi_config_lock` itself, with
  `guard(raw_spinlock)`, after the trigger type is validated; there is no
  gicv5_irs_spi_set_type() in this tree.
- `spi_config_lock`: a `raw_spinlock_t` in `struct gicv5_irs_chip_data`, one
  per IRS.
- `GICV5_IRS_PE_SELR`: the driver takes no lock around it.
- **Potentially unsafe usage**: writing a selector register and then the
  matching configuration register with no lock held.
  - Unsafe: when another context can write the same selector of the same IRS
    before the final wait ends; the configuration lands on the other object.
  - Safe: under `spi_config_lock` from the `GICV5_IRS_SPI_SELR` write to the
    wait after `GICV5_IRS_SPI_CFGR`, as `gicv5_spi_irq_set_type()` does.
  - Safe: `GICV5_IRS_PE_SELR` in `gicv5_irs_register_cpu()`, which runs only
    for the boot CPU from `gicv5_init_common()` and from the
    `CPUHP_AP_IRQ_GIC_STARTING` callback; `arch/arm64/Kconfig` does not
    select `HOTPLUG_PARALLEL`, so CPUs start one at a time, each under
    `cpus_write_lock()` in `_cpu_up()`.
- **Unsafe usage**: writing the configuration register after the wait that
  follows the selector write returned an error.
  - Safe: return before the configuration write, as
    `gicv5_spi_irq_set_type()` and `gicv5_irs_register_cpu()` do.

**Poll timeout handling**

- Both variants: print with `pr_err_ratelimited()` and return `-ETIMEDOUT`.
- There is no gicv5_irs_spi_set_type() here; `gicv5_spi_irq_set_type()`
  returns the wait error.
- `gicv5_irs_register_cpu()`: replaces a failed select wait by `-ENXIO`;
  only the wait after `GICV5_IRS_PE_CR0` returns `-ETIMEDOUT` unchanged.
- **Unsafe usage**: reading the status value that
  `gicv5_wait_for_op_atomic()` hands back after it returned an error.
  - Unsafe: `gicv5_wait_for_op_s_atomic()` writes `*val` only on success.
  - Safe: test the return first, as `gicv5_irs_wait_for_spi_op()` does.
- **Unsafe usage**: calling `gicv5_wait_for_op()` where sleeping is not
  allowed.
  - Unsafe: `poll_timeout_us()` in `include/linux/iopoll.h` has
    `might_sleep_if()` for a non-zero sleep time.
  - Safe: `gicv5_wait_for_op_atomic()`, as `gicv5_irs_wait_for_spi_op()`
    uses under `spi_config_lock`.
- Unwinding in tree, IRS: on a failed `gicv5_irs_ist_synchronise()`,
  `gicv5_irs_iste_alloc()` clears the L1 entry, frees the L2 table and
  returns the error; `gicv5_irq_lpi_domain_alloc()` then calls
  `release_lpi()`.
- Void callers: the result is dropped, for example in `gicv5_irs_syncr()`
  and `gicv5_irs_init_bases()`.

**Bad firmware values**

- Scope of a fatal fault: it ends the probe of that one IRS;
  `gicv5_irs_of_init()` unwinds it and `gicv5_irs_of_probe()` goes on to the
  next node.
- `gicv5_irs_of_probe()`: returns `-ENODEV` only when no IRS is left on
  `irs_nodes`.
- Fatal faults: all are found before the per-CPU loop; the loop itself
  cannot fail.
- Missing `arm,iaffids`: caught as a count that differs from the `cpus`
  count, `-EINVAL`.

| Entry in the loop | Result | Message |
|---|---|---|
| `of_parse_phandle()` returns NULL | skipped | `pr_warn()` with `FW_BUG` |
| `of_cpu_node_to_id()` is negative | skipped | none |
| IAFFID has bits above the IRS width | skipped | `pr_warn()`, no `FW_BUG` |

- Fatal faults: `gicv5_irs_of_init_affinity()` prints nothing; its caller
  `gicv5_irs_of_init()` prints one `pr_err()`.
- Skipped CPU: `gicv5_irs_register_cpu()` returns `-ENODEV` when it comes
  online; for the boot CPU that fails `gicv5_init_common()`.
- `FW_BUG`: used in two messages of the IRS driver, the phandle one and
  `gic_request_region()`; other firmware faults are reported without it.
- `WARN()`: the driver uses it for conditions that hardware or firmware
  determine, for example a clear `GICV5_IRS_IDR2_LPI` in `gicv5_irs_init()`
  and an ITS found enabled in `gicv5_its_init_bases()`.
- **Unsafe usage**: storing an IAFFID from firmware and setting `valid`
  without testing it against the IAFFID width of the IRS.
  - Unsafe: the value is later placed in `GICV5_IRS_PE_SELR_IAFFID` and
    `GICV5_GIC_CDAFF_IAFFID_MASK` with no further test.
  - Safe: test against `GICV5_IRS_IDR1_IAFFID_BITS` + 1 bits of that IRS and
    skip the entry, as `gicv5_irs_of_init_affinity()` and
    `gic_acpi_parse_iaffid()` do.

## Interrupt state table

**IRS that programs the IST**

- One IST for the whole system: its state is `gicv5_global_data.ist`;
  `struct gicv5_irs_chip_data` holds no table state.
- `gicv5_irs_enable()`: does not write `GICV5_IRS_CR0`; it takes the first
  entry of `irs_nodes` and calls `gicv5_irs_init_ist()` on it, once, from
  `gicv5_init_common()`.
- `GICV5_IRS_CR0_IRSEN`: set earlier, for every IRS, by
  `gicv5_irs_init_bases()`.
- `GICV5_IRS_IST_CFGR` and `GICV5_IRS_IST_BASER`: accessed on that first IRS
  only; no other IRS has them programmed.
- `gicv5_irs_iste_alloc()`: maps level 2 tables through
  `per_cpu(per_cpu_irs_data, 0)`, the IRS of CPU 0, whichever CPU runs the
  call; with a two-level IST it returns `-ENOENT` if CPU 0 has no IRS.
- CPU 0's IRS need not be the first entry of `irs_nodes`; nothing in the
  driver ties the two together.
- LPI state after publishing: changed with `gic_insn()` system instructions
  in `drivers/irqchip/irq-gic-v5.c`, not through IRS MMIO registers.

**LPI ID bits and layout**

- Starting value, IRS supports two levels: `GICV5_IRS_IDR2_ID_BITS`.
- Starting value, IRS does not: `max(LPI_ID_BITS_LINEAR,
  GICV5_IRS_IDR2_MIN_LPI_ID_BITS)`, then `min()` with
  `GICV5_IRS_IDR2_ID_BITS`; so it exceeds 12 when the IRS minimum does.
- Either value is then capped with `gicv5_global_data.cpuif_id_bits`, which
  `gicv5_set_cpuif_idbits()` sets to 16 or 24.
- Entry size with `GICV5_IRS_IDR2_ISTMD` set: `GICV5_IRS_IST_CFGR_ISTSZ_8`
  when the capped `lpi_id_bits` is below `GICV5_IRS_IDR2_ISTMD_SZ`, else
  `GICV5_IRS_IST_CFGR_ISTSZ_16`; without it, `GICV5_IRS_IST_CFGR_ISTSZ_4`.
- Two-level table: chosen only when the IRS supports it and
  `lpi_id_bits > (10 - istsz) + 2 * l2sz`, that is when the IDs do not fit
  in one level 2 table; see the end of `gicv5_irs_init_ist()`.
- Linear table on a two-level-capable IRS: `LPI_ID_BITS_LINEAR` is not
  applied; the bound is the level 2 bit count above.
- `gicv5_irs_l2_sz()`: returns a `GICV5_IRS_IST_CFGR_L2SZ_4K` style
  encoding (0, 1, 2), not a byte count.
- `gicv5_irs_l2_sz()` preference: the size equal to `PAGE_SIZE`, then 4K,
  then 16K; 64K is returned last without testing its support bit.
- To the allocator: `gicv5_init_lpis(BIT(lpi_id_bits))` stores `num_lpis`
  in `drivers/irqchip/irq-gic-v5.c`; `alloc_lpi()` passes `num_lpis - 1`
  to `ida_alloc_max()` and returns `-ENOSPC` while `num_lpis` is 0.
- **Unsafe usage**: giving `gicv5_init_lpis()` a count above `BIT()` of the
  value written to `GICV5_IRS_IST_CFGR_LPI_ID_BITS`.
  - Unsafe: `lpi_id_bits` is passed by value to the table init functions, so
    a value lowered there does not reach `gicv5_init_lpis()`;
    `gicv5_irs_iste_alloc()` indexes `l1ist_addr` with `lpi >> l2_bits` and
    has no bounds check.
  - Safe: the same unchanged value feeds both, as on the
    `gicv5_irs_init_ist_two_level()` path.

**Publishing the table base**

- `gicv5_global_data.ist`: written after the `GICV5_IRS_IST_CFGR` write and
  before the `GICV5_IRS_IST_BASER` write; the linear path sets only `l2`.
- Coherent IRS: `dsb(ishst)` takes the place of the cache clean, before
  either register write; both register writes are relaxed.
- IST already valid: `gicv5_irs_init_ist()` tests
  `GICV5_IRS_IST_BASER_VALID` before anything else, prints an error and
  returns `-EPERM`; it neither adopts nor tears down the table.
- That `-EPERM` fails `gicv5_irs_enable()` and so `gicv5_init_common()`.
- `GICV5_IRS_IST_BASER`: written only by the two table init functions, with
  valid set; no code in this tree writes it with valid clear, including
  `gicv5_irs_remove()` and the failed-wait path.
- `kmemleak_ignore()` on success: called for the linear table; not called
  for the level 1 table, which stays reachable through
  `gicv5_global_data.ist.l1ist_addr`.

**Level 2 table allocation**

- No lock is taken in `gicv5_irs_iste_alloc()`, and the valid bit is not
  rechecked after the first test.
- Serialisation: `root->mutex` of `struct irq_domain`, taken by the
  irqdomain core, for example in `__irq_domain_alloc_irqs()`, before any
  `.alloc` callback runs.
- The LPI domain is the root of its hierarchy, so child domains share that
  mutex; for example the IPI domain created in
  `drivers/irqchip/irq-gic-v5.c`.
- Only caller: `gicv5_irq_lpi_domain_alloc()`.
- **Unsafe usage**: calling `gicv5_irs_iste_alloc()` without the LPI
  domain's `root->mutex` held.
  - Unsafe: two callers can both see the level 1 entry invalid, both store
    an address and both write `GICV5_IRS_MAP_L2_ISTR`.
  - Safe: from an irqdomain `.alloc` callback, as
    `gicv5_irq_lpi_domain_alloc()` does.
- Order: the level 1 entry is stored first, then maintenance covers both
  the level 2 table and the entry, then the register write.
- Non-coherent maintenance differs by object: `dcache_clean_inval_poc()`
  over the level 2 table, `dcache_clean_poc()` (clean only) over the one
  level 1 entry.
- Failed wait: the level 1 entry is set to 0, the level 2 table is freed
  with `kfree()`, and the poll's error is returned.

**Reading memory the IRS wrote**

- `gicv5_irs_ist_synchronise()`: only polls `GICV5_IRS_IST_STATUSR` for
  `GICV5_IRS_IST_STATUSR_IDLE`; it writes no register and does no cache
  maintenance.
- Poll timing: `gicv5_wait_for_op_s_atomic()` in
  `include/linux/irqchip/arm-gic-v5.h` polls every 1 µs for
  `10 * USEC_PER_MSEC` µs (10 ms), then returns `-ETIMEDOUT`.
- Ordering of poll and `dcache_inval_poc()`: the driver adds no explicit
  barrier; it relies on the non-relaxed `readl()` inside
  `readl_poll_timeout_atomic()`, whose `__io_ar()` in
  `arch/arm64/include/asm/io.h` is `dma_rmb()` plus a control dependency.
- **Unsafe usage**: polling for completion with `readl_relaxed()` before
  invalidating or reading memory the IRS wrote.
  - Safe: poll with `gicv5_wait_for_op_atomic()`, as
    `gicv5_irs_ist_synchronise()` does.
- Only readback site: the level 1 entry tested in `gicv5_irs_iste_alloc()`;
  the driver keeps no pointer to the linear table or to any level 2 table.
- Invalidated range: one 8-byte entry, less than a cache line, so
  `dcache_inval_poc()` cleans as well as invalidates the line; see
  `__dcache_inval_poc_nosync` in `arch/arm64/mm/cache.S`.
- **Potentially unsafe usage**: `dcache_inval_poc()` over a single level 1
  entry.
  - Unsafe: when the CPU has stored to that cache line since it was last
    cleaned; the clean writes the CPU's copy back over what the IRS wrote.
  - Safe: after `dcache_clean_poc()` of the entry with no store in between,
    as on the success path of `gicv5_irs_iste_alloc()`.

**Table sizing arithmetic**

- `istsz`: the `GICV5_IRS_IST_CFGR_ISTSZ` encoding 0, 1, 2 for entries of
  4, 8, 16 bytes; it is added to the exponent, not multiplied.
- Floor: `n` is at least 5 in both functions, so the linear table and the
  level 1 table are at least `BIT(6)` = 64 bytes, the granule of
  `GICV5_IRS_IST_BASER_ADDR_MASK`.
- Ceiling: of the two IST init functions, only
  `gicv5_irs_init_ist_linear()` has a `KMALLOC_MAX_SIZE` test.
- `gicv5_irs_init_ist_two_level()`: no size check; an oversized level 1
  table shows up as `kzalloc()` failure and `-ENOMEM`.
- `BIT()` is `unsigned long`, 64 bits here: `ARM_GIC_V5` is selected only
  from `arch/arm64/Kconfig`.
- `max(5, <u32 expression>)`: builds in this tree, because `__types_ok()` in
  `include/linux/minmax.h` accepts a non-negative signed constant against
  an unsigned operand; no `max_t()` is needed.
- That `max()` compares as unsigned, so the floor does not catch a wrapped
  subtraction.
- **Potentially unsafe usage**: subtracting the level 2 bit count from
  `lpi_id_bits` in `u32` and using the result as a shift count.
  - Unsafe: when nothing before it has established that `lpi_id_bits` is
    the larger; the wrapped value passes `max()` and reaches `BIT()`.
  - Safe: in `gicv5_irs_init_ist_two_level()`, called only after
    `gicv5_irs_init_ist()` tested
    `lpi_id_bits > (10 - l2_iste_sz) + (2 * l2sz)`.
- **Potentially unsafe usage**: storing a `BIT()` result in a field narrower
  than `unsigned long`.
  - Unsafe: when the exponent can reach the field width; the value is
    truncated without warning.
  - Safe: `l2_size` (`u32`) in `struct gicv5_chip_data`, because
    `gicv5_irs_l2_sz()` returns at most `GICV5_IRS_IST_CFGR_L2SZ_64K`,
    giving at most `BIT(16)`.

**Level 1 entry valid bit**

- `GICV5_ISTL1E_VALID`: set by the IRS, as a result of the write to
  `GICV5_IRS_MAP_L2_ISTR`; the driver never stores it.
- Driver's store: the level 2 physical address masked with
  `GICV5_ISTL1E_L2_ADDR_MASK`, valid clear; 0 after a failed wait.
- `GICV5_ISTL1E_L2_ADDR_MASK`: keeps bits 55:12, so a level 2 address that
  is not 4K aligned is truncated without warning.
- Access style in `gicv5_irs_iste_alloc()`: a plain load with
  `le64_to_cpu()` and a plain store with `cpu_to_le64()`; it uses neither
  `READ_ONCE()` nor `WRITE_ONCE()`.
- A valid level 1 entry makes `gicv5_irs_iste_alloc()` return 0 without
  writing `GICV5_IRS_MAP_L2_ISTR`; that test is the driver's only record
  that a block is mapped.

**Non-coherent cache maintenance**

- Source of the flags: firmware only; no GIC ID register is read for it.
- IRS, devicetree: `dma-noncoherent` on the IRS node, read in
  `gicv5_irs_of_init()`.
- IRS, ACPI: `ACPI_MADT_IRS_NON_COHERENT` in the MADT entry flags, read in
  `gic_acpi_parse_madt_irs()`.
- Both IRS paths pass the result as the `noncoherent` argument of
  `gicv5_irs_init_bases()`, which sets `IRS_FLAGS_NON_COHERENT`.
- `gicv5_its_dcache_clean()`: static to `drivers/irqchip/irq-gic-v5-its.c`
  and takes a `struct gicv5_its_chip_data`; IRS code cannot call it.
- IRS code has no helper: each site in `drivers/irqchip/irq-gic-v5-irs.c`
  tests `IRS_FLAGS_NON_COHERENT` itself, for example
  `gicv5_irs_iste_alloc()`.
- **Potentially unsafe usage**: a store to ITS table memory that is not
  followed at once by `gicv5_its_dcache_clean()`.
  - Unsafe: when the ITS can already reach the entry, or a register write
    that makes it reachable comes before any clean.
  - Safe: a single entry through `its_write_table_entry()`, which cleans
    that entry.
  - Safe: a loop of stores to a table not yet reachable, then one
    `gicv5_its_dcache_clean()` over the whole table, as
    `gicv5_its_create_itt_two_level()` does for its level 1 table.

## ITS entries and publishing

**ITS configuration model**

- One device or event mapping change is two calls: `its_write_table_entry()`
  (store plus clean or barrier), then `gicv5_its_itt_cache_inv()` or
  `gicv5_its_device_cache_inv()` (register writes plus the poll).
- `gicv5_its_dcache_clean()`: outside `its_write_table_entry()` it is called
  only on whole tables.
- `gicv5_its_cache_sync()`: called only from the two invalidate helpers.
- Device mapping: `gicv5_its_device_register()`, reached from
  `gicv5_its_msi_prepare()` through `gicv5_its_alloc_device()`.
- Event mapping: `gicv5_its_map_event()`, reached from
  `gicv5_its_irq_domain_activate()`.
- `gicv5_its_irq_domain_alloc()`: writes no ITS table entry; it reserves
  EventIDs in `event_map` and allocates the LPI through the parent domain.

**ITS table valid bits**

- There is no gicv5_its_write_dte() or gicv5_its_write_itte() here.

| Entry | Bit | Set in | Cleared in |
|---|---|---|---|
| L1 DTE | `GICV5_DTL1E_VALID` | `gicv5_its_alloc_l2_devtab()` | nowhere |
| L2 or linear DTE | `GICV5_DTL2E_VALID` | `gicv5_its_device_register()` | `gicv5_its_device_unregister()`; failed-invalidate path of `gicv5_its_device_register()` |
| L1 ITTE | `GICV5_ITTL1E_VALID` | `gicv5_its_create_itt_two_level()` | nowhere |
| L2 or linear ITTE | `GICV5_ITTL2E_VALID` | `gicv5_its_map_event()` | `gicv5_its_unmap_event()` |

- `gicv5_its_unmap_event()`: clears only `GICV5_ITTL2E_VALID` by
  read-modify-write; the LPI ID stays in the entry.
- DTE clears: both write the whole entry to 0.
- L1 ITTEs: stored with `WRITE_ONCE()` directly, all at ITT creation, then
  one `gicv5_its_dcache_clean()` over the L1 table.
- L1 ITT: never invalidated entry by entry; `gicv5_its_free_itt()` frees it.
- L2 device tables: never freed; for a two-level table
  `gicv5_its_deinit_devtab()` frees only the L1 table and the `l2ptrs`
  array.
- L1 IST entry, in `drivers/irqchip/irq-gic-v5-irs.c`: the IRS sets
  `GICV5_ISTL1E_VALID`, not software; `gicv5_irs_iste_alloc()` asks for it by
  writing the LPI ID, in `GICV5_IRS_MAP_L2_ISTR_ID`, to
  `GICV5_IRS_MAP_L2_ISTR`; see "Level 1 entry valid bit".
- Non-coherent IRS: `gicv5_irs_iste_alloc()` runs `dcache_inval_poc()` on
  the L1 entry after the poll, so that a later read sees the bit the IRS
  wrote.
- No code clears a valid L1 IST entry or frees a mapped L2 IST.
- Linear IST: has no L1 entries; `gicv5_irs_iste_alloc()` returns 0 at once
  when `gicv5_global_data.ist.l2` is false.
- Table base: software sets `GICV5_IRS_IST_BASER_VALID` for the IST;
  `GICV5_ITS_DT_BASER` is written with the address only, and the ITS is
  turned on with `GICV5_ITS_CR0_ITSEN` in `gicv5_its_enable()`.

**ITS cache invalidation and sync**

- Register macros carry the `GICV5_` prefix; there is no ITS_DIDR, ITS_EIDR
  or ITS_STATUSR identifier, and the sync idle bit is
  `GICV5_ITS_SYNC_STATUSR_IDLE`.
- `gicv5_its_itt_cache_inv()`: writes `GICV5_ITS_DIDR` (64-bit), then
  `GICV5_ITS_EIDR`, then `GICV5_ITS_INV_EVENTR`, then calls
  `gicv5_its_cache_sync()`.
- `GICV5_ITS_INV_EVENTR`: written with `GICV5_ITS_INV_EVENTR_I` only;
  `GICV5_ITS_INV_EVENTR_ITT_L2SZ` and `GICV5_ITS_INV_EVENTR_L1` are never
  set.
- `gicv5_its_device_cache_inv()`: writes `GICV5_ITS_DIDR`, then
  `GICV5_ITS_INV_DEVICER` (I bit, `event_id_bits` of the device,
  `GICV5_ITS_INV_DEVICER_L1` 0), then calls `gicv5_its_cache_sync()`.
- `gicv5_its_cache_sync()`: writes nothing; polls `GICV5_ITS_STATUSR` for
  `GICV5_ITS_STATUSR_IDLE` with `gicv5_wait_for_op_atomic()`.
- `gicv5_its_cache_sync()` and `gicv5_its_syncr()`: unrelated; neither
  calls the other.

| | `gicv5_its_cache_sync()` | `gicv5_its_syncr()` |
|---|---|---|
| Writes | nothing | `GICV5_ITS_SYNCR`, 64-bit: `GICV5_ITS_SYNCR_SYNC` plus DeviceID |
| Polls | `GICV5_ITS_STATUSR` | `GICV5_ITS_SYNC_STATUSR` |
| Wait helper | `gicv5_wait_for_op_atomic()`, busy-waits | `gicv5_wait_for_op()`, i.e. `readl_poll_timeout()`, may sleep |
| Result | returned | discarded; function is `void` |
| Scope | takes no ID; waits on the one idle bit of that ITS | one DeviceID |
| Called from | the two invalidate helpers | `gicv5_its_irq_domain_free()` only |

- `GICV5_ITS_SYNCR_SYNCALL`: defined, never used; no whole-ITS sync exists.
- `gicv5_its_syncr()` in `gicv5_its_irq_domain_free()`: runs after
  `irq_domain_free_irqs_parent()` and before `gicv5_irs_syncr()`; it
  follows no table write.
- `gicv5_its_syncr()`: needs a context that may sleep; the
  activate/deactivate callbacks are not one, they can run under
  `desc->lock`.

**ITS locking**

- `dev_alloc_lock` in `struct gicv5_its_chip_data`: the only lock the
  driver defines; there is no per-device lock, no bitmap lock and no lock
  around the invalidate registers.
- `dev_alloc_lock`: taken only in `gicv5_its_msi_prepare()` and
  `gicv5_its_msi_teardown()`.
- `gicv5_its_device_cache_inv()`: every path holds `dev_alloc_lock`; it is
  reached only through `gicv5_its_device_register()` and
  `gicv5_its_device_unregister()`.
- `gicv5_its_itt_cache_inv()`: reached only from `gicv5_its_map_event()`
  and `gicv5_its_unmap_event()`; the driver takes no lock on this path.
- Activate/deactivate callers: hold the per-device `mutex` of
  `struct msi_device_data` (`msi_init_virq()`, `__msi_domain_free_irqs()`)
  or the per-interrupt `desc->lock` (for example `irq_activate()` from
  `__setup_irq()`, `irq_shutdown_and_deactivate()`).
- `irq_domain_activate_irq()` and `irq_domain_deactivate_irq()`: do not
  take `domain->root->mutex`.
- `GICV5_ITS_DIDR`, `GICV5_ITS_EIDR`, `GICV5_ITS_STATUSR`: one set per ITS;
  no lock in this tree is per ITS on the event path, and none is held on
  every path to both `gicv5_its_itt_cache_inv()` and
  `gicv5_its_device_cache_inv()`.
- `event_map` allocation and release: in `gicv5_its_irq_domain_alloc()` and
  `gicv5_its_irq_domain_free()`, with no driver lock.
- `gicv5_its_irq_domain_alloc()` and `gicv5_its_irq_domain_free()`: run
  under `domain->root->mutex`, taken in `__irq_domain_alloc_irqs()` and
  `irq_domain_free_irqs()` in `kernel/irq/irqdomain.c`.
- `domain->root` for the ITS domain: `gicv5_global_data.lpi_domain`, so one
  mutex covers every ITS and every device.
- `gicv5_its_msi_teardown()`: tests `bitmap_empty()` and calls
  `bitmap_free()` under `dev_alloc_lock`, not under `domain->root->mutex`;
  it is reached from `msi_remove_device_irq_domain()`, which holds the
  per-device MSI mutex.
- **Unsafe usage**: calling `gicv5_its_device_register()`,
  `gicv5_its_device_unregister()` or `gicv5_its_devtab_get_dte_ref()` with
  `alloc` true, without `dev_alloc_lock`.
  - Unsafe: `gicv5_its_alloc_l2_devtab()` tests `GICV5_DTL1E_VALID` and then
    allocates, and `gicv5_its_alloc_device()` does `xa_load()` then
    `xa_store()`; both are check-then-act with no lock of their own.
  - Safe: under `guard(mutex)(&its->dev_alloc_lock)`, as
    `gicv5_its_msi_prepare()` does.

**Changing an ITS table entry**

- `gicv5_its_dcache_clean()` with `ITS_FLAGS_NON_COHERENT`: calls
  `dcache_clean_inval_poc()`, a clean and invalidate, not a clean alone.
- `gicv5_its_map_event()` and `gicv5_its_unmap_event()`: discard the result
  of `gicv5_its_itt_cache_inv()`; `gicv5_its_map_event()` returns 0 on a
  timeout and leaves the ITTE valid.
- `gicv5_its_device_register()`: the only caller that acts on a failed
  invalidate; it writes the DTE back to 0 and frees the ITT.
- Locks for callers: `dev_alloc_lock` for a DTE, no driver lock for an
  ITTE; see "ITS locking".
- **Potentially unsafe usage**: changing an entry with no invalidate after
  it.
  - Unsafe: when the ITS can already reach the entry, i.e. an L2 or linear
    DTE once `GICV5_ITS_DT_BASER` is programmed, or an L2 or linear ITTE of
    a device whose DTE is valid; the ITS may keep using its cached copy.
  - Safe: L1 ITTEs in `gicv5_its_create_itt_two_level()`; the ITT is not
    reachable until `gicv5_its_device_register()` writes the DTE, and that
    write is followed by `gicv5_its_device_cache_inv()`.
- **Potentially unsafe usage**: storing an entry without
  `its_write_table_entry()`.
  - Unsafe: when the ITS can already reach the table; nothing cleans the
    line for `ITS_FLAGS_NON_COHERENT` and nothing issues `dsb(ishst)`
    otherwise.
  - Safe: filling a table before it is handed to the ITS, then one
    `gicv5_its_dcache_clean()` over the whole table, as
    `gicv5_its_alloc_devtab_two_level()` does before it writes
    `GICV5_ITS_DT_BASER`.
- **Unsafe usage**: setting a parent entry valid before the table it points
  to has been through `gicv5_its_dcache_clean()`.
  - Unsafe: the zero fill from `kcalloc()` may still sit in the CPU cache,
    so a non-coherent ITS reads stale memory as entries.
  - Safe: `gicv5_its_create_itt_two_level()` cleans each L2 ITT before it
    stores the L1 entry that points to it.
  - Safe: `gicv5_its_create_itt_linear()` cleans the ITT before
    `gicv5_its_device_register()` writes the DTE.

**Table entry byte order**

- DT, ITT and L1 IST entries: `__le64`, read with `le64_to_cpu()` and
  stored with `cpu_to_le64()`; see `gicv5_its_map_event()` in
  `drivers/irqchip/irq-gic-v5-its.c` and `gicv5_irs_iste_alloc()` in
  `drivers/irqchip/irq-gic-v5-irs.c`.
- L2 and linear IST: held as `void *` in `gicv5_irs_iste_alloc()` and
  `gicv5_irs_init_ist_linear()`; the kernel never reads or writes an entry
  in them, so they have no entry type.
- `__le32`: not used anywhere in the GICv5 drivers.

## ITS devices and tables

**Device allocation and teardown**

- Device ID already in `its_devices`: `gicv5_its_alloc_device()` returns
  `ERR_PTR(-EBUSY)`, so `gicv5_its_msi_prepare()` returns `-EBUSY`.
- `gicv5_its_msi_teardown()`: does no lookup and no NULL test; it uses
  `info->scratchpad[0].ptr` as the `struct gicv5_its_dev`.
- Teardown's only check: `WARN_ON_ONCE(!bitmap_empty(its_dev->event_map,
  its_dev->num_events))`; when it fires the function returns, with the device
  still in `its_devices` and its device table entry still valid.
- Teardown order: `xa_erase()`, `bitmap_free()`,
  `gicv5_its_device_unregister()`, `kfree()`; the unregister return value is
  dropped.
- There is no gicv5_its_free_device() here; the teardown steps are inline in
  `gicv5_its_msi_teardown()`.

**Device table structure**

- Linear is chosen only when `GICV5_ITS_IDR1_DT_LEVELS` is clear or the device
  ID bits are below the L2 bits; see `gicv5_its_l2sz_two_level()`.
- Device ID bits equal to the L2 bits: two-level, with a one-entry L1 table.
- No L2 size advertised in `GICV5_ITS_IDR1`: does not force linear;
  `gicv5_its_l2sz_two_level()` falls back to `GICV5_ITS_DT_ITT_CFGR_L2SZ_4k`.
- Cap: there is no driver macro; the limit is `KMALLOC_MAX_SIZE`.

| Structure | What is held to `KMALLOC_MAX_SIZE` | Resulting device ID bits |
|---|---|---|
| linear, `gicv5_its_alloc_devtab_linear()` | whole table | `ilog2(KMALLOC_MAX_SIZE/sizeof(__le64))` |
| two-level, `gicv5_its_alloc_devtab_two_level()` | L1 table only | that value plus the L2 bits |

- Capped value: written to `GICV5_ITS_DT_CFGR` and kept in
  `its->devtab_cfgr.cfgr`; `gicv5_its_device_register()` checks device IDs
  against it.
- `gicv5_its_deinit_devtab()`, two-level table: frees the L1 table and the
  `l2ptrs` array, not the L2 tables; its only caller is the failure path of
  `gicv5_its_init_bases()`.

**Translation table structure**

- Two-level support bit: `GICV5_ITS_IDR1_ITT_LEVELS` in `GICV5_ITS_IDR1`;
  `GICV5_ITS_IDR2` only supplies the maximum, `GICV5_ITS_IDR2_EVENTID_BITS`.
- Two-level is chosen when that bit is set and `event_id_bits` is at least the
  L2 bits; with the bit set, `gicv5_its_l2sz_two_level()` returns false only
  for `l2_bits > id_bits`.
- `event_id_bits` equal to the L2 bits: `gicv5_its_create_itt_two_level()`
  returns `-EINVAL` (its test is `>=`); there is no fallback to
  `gicv5_its_create_itt_linear()`.
- **Unsafe usage**: making the index of the `out_free` loop in
  `gicv5_its_create_itt_two_level()` unsigned.
  - Unsafe: `i >= 0` is always true for an unsigned index, and a failure at
    slot 0 starts the loop at `i - 1`, so `l2ptrs` is indexed out of bounds.
  - Safe: `int i` counting down from `i - 1` while `i >= 0`, as the function
    does; `i` is the only signed index there, `num_ents` and the loop in
    `gicv5_its_free_itt_two_level()` are `unsigned int`.
- **Unsafe usage**: calling `gicv5_its_free_itt()` after
  `gicv5_its_create_itt_two_level()` failed.
  - Unsafe: `its_dev->itt_cfg.l2.l2ptrs`, `l1itt`, `num_l1_ents` and
    `l2itt = true` are set before the allocation loop and not cleared in
    `out_free`, so the tables would be freed twice.
  - Safe: return the error without freeing, as `gicv5_its_device_register()`
    does; `gicv5_its_alloc_device()` then jumps to `out_dev_free`, past
    `gicv5_its_device_unregister()`.

**Registering a device**

- Checks in `gicv5_its_device_register()`, in order, besides the two
  `-ENOMEM` allocations:

| Check | Error |
|---|---|
| `device_id >= BIT(device_id_bits)`, bits from saved `devtab_cfgr.cfgr` | `-EINVAL` |
| device table entry has `GICV5_DTL2E_VALID` | `-EBUSY` |
| `event_id_bits` above `GICV5_ITS_IDR2_EVENTID_BITS` | `-EINVAL` |
| `gicv5_its_create_itt_two_level()` with `event_id_bits` equal to L2 bits | `-EINVAL` |
| `gicv5_its_device_cache_inv()` times out | `-ETIMEDOUT` |

- L2 device table: allocated by `gicv5_its_devtab_get_dte_ref()` before the
  `-EBUSY` and event ID checks, so those returns leave a new L2 table in
  place.
- Device table entry: all fields and `GICV5_DTL2E_VALID` go in one
  `its_write_table_entry()`; there is no separate write of the valid bit and
  no barrier between fields.
- Final invalidation fails: the entry is written to 0 with
  `its_write_table_entry()`, `gicv5_its_free_itt()` runs, the error is
  returned.

**Unregistering a device**

- Entry not valid: `gicv5_its_device_unregister()` returns `-EINVAL` after a
  `pr_debug()`; the ITT is not freed.
- Invalidation fails: `gicv5_its_device_unregister()` returns the
  `-ETIMEDOUT`; nothing is restored or retried.
- Callers of `gicv5_its_device_unregister()`: `gicv5_its_msi_teardown()` and
  the `out_unregister` path of `gicv5_its_alloc_device()`; both drop the
  return value and go on to `kfree()` the device.
- **Unsafe usage**: freeing the ITT of a device before the invalidation of
  its cleared device table entry has completed.
  - Unsafe: `kfree()` in `gicv5_its_free_itt()` returns the memory for reuse
    while the ITS may still hold the old entry in its cache and read the
    memory as ITTEs.
  - Safe: freeing tables that no device table entry ever pointed to, as the
    `out_free` path of `gicv5_its_create_itt_two_level()` does.

**ITS initialisation**

- First register access in `gicv5_its_init_bases()`: `GICV5_ITS_CR0`; no ID
  register is read before `gicv5_its_init_devtab()`.
- `GICV5_ITS_CR0_ITSEN` set by firmware: `WARN()`, then `gicv5_its_disable()`;
  init fails only if that disable times out.
- Order after that: `GICV5_ITS_CR1` and `ITS_FLAGS_NON_COHERENT`,
  `gicv5_its_init_devtab()`, `gicv5_its_enable()`, `gicv5_its_init_domain()`.

| Failing step | Undone in `gicv5_its_init_bases()` |
|---|---|
| `gicv5_its_disable()` of a pre-enabled ITS | `kfree()` of the chip data |
| `gicv5_its_init_devtab()` | `kfree()` of the chip data |
| `gicv5_its_enable()` | `gicv5_its_deinit_devtab()`, chip data |
| `gicv5_its_init_domain()` | `gicv5_its_disable()` (return dropped), `gicv5_its_deinit_devtab()`, chip data |

- `iounmap()` of the ITS base: done by the callers, `gicv5_its_init()` and
  `gic_acpi_parse_madt_its()`, not by `gicv5_its_init_bases()`.
- `gic_acpi_parse_madt_its()` on failure also frees the translate frame
  tokens, the domain fwnode and the memory region.
- **Unsafe usage**: dereferencing `np` in `gicv5_its_init_bases()`.
  - Unsafe: `np` is `to_of_node(handle)`, which is NULL when `handle` is not
    an OF node, as on the ACPI path.
  - Safe: naming the ITS with `fwnode_get_name(its_node->fwnode)`, as
    `gicv5_its_print_info()` does; `irqchip_fwnode_ops` supplies `get_name`.

**ITS coherency flag**

- `noncoherent` argument of `gicv5_its_init_bases()`, device tree path:
  `gicv5_its_init()` passes `of_property_read_bool(node, "dma-noncoherent")`.
- `noncoherent` argument of `gicv5_its_init_bases()`, ACPI path:
  `gic_acpi_parse_madt_its()` passes
  `its_entry->flags & ACPI_MADT_GICV5_ITS_NON_COHERENT`.
- `of_dma_is_coherent()`: not called by the ITS driver.
- ACPI path, `np`: `handle` comes from `irq_domain_alloc_fwnode()`, so
  `to_of_node()` returns NULL.
- **Unsafe usage**: setting `ITS_FLAGS_NON_COHERENT` from a device tree
  property lookup in code that both probe paths reach.
  - Unsafe: on the ACPI path the node is NULL and `of_property_read_bool()`
    returns false, so the flag stays clear whatever
    `ACPI_MADT_GICV5_ITS_NON_COHERENT` says; `GICV5_ITS_CR1` gets the
    write-back, inner-shareable attributes and `gicv5_its_dcache_clean()`
    does only `dsb(ishst)`.
  - Safe: test the `noncoherent` argument, which both callers fill in, as
    `gicv5_irs_init_bases()` does for `IRS_FLAGS_NON_COHERENT`.

## ITS interrupts and MSIs

**MSI parent operations**

- `gic_v5_its_msi_parent_ops`: has no prepare member; its only callback is
  `.init_dev_msi_info`. `gicv5_its_msi_prepare()` is `.msi_prepare` of
  `gicv5_its_msi_domain_ops` in `drivers/irqchip/irq-gic-v5-its.c`; both
  child prepares reach it through
  `msi_get_domain_info(domain->parent)->ops->msi_prepare`.
- PCI device ID and controller node: `pci_msi_map_rid_ctlr_node()` in
  `drivers/pci/msi/irqdomain.c`. It calls `of_msi_xlate()` when the ITS
  domain has an OF node and `iort_msi_xlate()` otherwise.
- `pci_msi_domain_get_msi_rid()` and `iort_msi_map_id()`: used by the GICv3
  `its_pci_msi_prepare()`; the v5 path does not call them.
- Platform lookup: `of_pmsi_get_msi_info()` when `dev->of_node` is set,
  else `iort_pmsi_get_msi_info()` in `drivers/acpi/arm64/iort.c`. Both are
  shared with GICv3; a non-NULL `pa` argument selects the v5 behaviour.
- There is no iort_pmsi_get_dev_id() and no of_v5_pmsi_get_msi_info() in
  this tree.
- `of_pmsi_get_msi_info()` with `pa` set: the `msi-parent` phandle must
  target a child of the ITS domain's node (the translate frame
  `msi-controller` node). The match compares `of_get_parent()` of the target
  with the domain node, and the address is read from the target.
- DT PCI: the node `of_msi_xlate()` returns must also be the frame node,
  because `its_translate_frame_address()` looks for `"ns-translate"` in that
  node's `reg-names`; the ITS node's own entry is `"ns-config"`.
- ACPI frame address: `iort_its_translate_pa()` searches
  `iort_msi_chip_list` for the fwnode. `gic_acpi_parse_madt_its_translate()`
  fills that list from each MADT translate frame (`base_address`, keyed by
  `translate_frame_id`).
- `iort_msi_xlate()`: takes the fwnode from `its->identifiers[0]`, the first
  identifier of the IORT ITS group only.
- Prepare runs once per per-device domain: `msi_create_device_irq_domain()`
  passes `hwsize` as `nvec` and keeps the result in `info->alloc_data`.
  `populate_alloc_info()` copies it into every later allocation, so
  `num_events` is `roundup_pow_of_two()` of `hwsize`.
- **Unsafe usage**: using the `pa` output of `of_pmsi_get_msi_info()` when
  the `msi-parent` walk did not match.
  - Unsafe: when the device node has `msi-map`, the `of_map_msi_id()`
    fallback can return 0 with `*dev_id` set and `*pa` never written.
  - Safe: when the `msi-parent` walk matched; that branch calls
    `its_translate_frame_address()` before it returns 0.

**Event ID allocation**

- Ordinary failure: `-ENOMEM`, the value `bitmap_find_free_region()`
  returns, passed through unchanged by `gicv5_its_alloc_eventid()` and
  `gicv5_its_irq_domain_alloc()`; neither uses `-ENOSPC`.
- Fixed message data failures: all three return `-EINVAL`: `nr_irqs != 1`
  (with `WARN_ON_ONCE()`), `info->hwirq >= its_dev->num_events`, and bit
  already set. Neither `-EBUSY` nor `-EEXIST` is returned.
- `MSI_ALLOC_FLAGS_FIXED_MSG_DATA`: set by `iwb_msi_template` in
  `drivers/irqchip/irq-gic-v5-iwb.c`; `gicv5_iwb_domain_set_desc()` puts the
  wire number in `info->hwirq`, so the event ID equals the IWB wire.
- `gicv5_its_free_eventid()`: called only from the error path of
  `gicv5_its_irq_domain_alloc()`. `gicv5_its_irq_domain_free()` calls
  `bitmap_release_region()` directly.
- `gicv5_its_irq_domain_free()`: entered once per interrupt with
  `nr_irqs == 1`, because `irq_domain_free_irqs_hierarchy()` in
  `kernel/irq/irqdomain.c` calls `.free` that way; each call clears one bit.
- Fixed IDs are freed the same way; `clear_bit()` is not used.
- **Unsafe usage**: an ordinary allocation whose `nr_irqs` is not a power of
  two.
  - Unsafe: `bitmap_find_free_region()` sets `1 << get_count_order(nr_irqs)`
    bits and the per-interrupt free clears `nr_irqs` of them; with a bit
    left, `gicv5_its_msi_teardown()` hits `WARN_ON_ONCE()` and returns
    without unregistering the device.
  - Safe: `nr_irqs == 1`, as for an MSI-X descriptor
    (`msix_prepare_msi_desc()` sets `nvec_used` to 1) and for the fixed
    path, which rejects any other count.
  - Safe: the alloc error path, where `gicv5_its_free_eventid()` releases
    the whole region with the same order.

**ITS domain allocation**

- There is no gicv5_alloc_lpi() or gicv5_free_lpi() in this tree; the ITS
  domain neither allocates nor frees an LPI itself.
- Parent LPIs: one call
  `irq_domain_alloc_irqs_parent(domain, virq, nr_irqs, NULL)` for the whole
  range. `gicv5_irq_lpi_domain_alloc()` in `drivers/irqchip/irq-gic-v5.c`
  takes each LPI with the static `alloc_lpi()` and calls
  `gicv5_irs_iste_alloc()`; it ignores `arg`.
- LPI number: unknown to the ITS at alloc time; it is first read from
  `d->parent_data->hwirq` in `gicv5_its_irq_domain_activate()`.
- Steps that can fail, in order: `gicv5_its_alloc_eventid()`,
  `iommu_dma_prepare_msi()`, `irq_domain_alloc_irqs_parent()`.
- `iommu_dma_prepare_msi()` or parent failure: both jump to `out_eventid`,
  which calls `gicv5_its_free_eventid()` and nothing else.
- Partial parent failure: `gicv5_irq_lpi_domain_alloc()` releases the LPIs
  it already took through `gicv5_irq_lpi_domain_free()` before returning;
  the ITS has no per-interrupt unwind loop.
- After the parent call nothing can fail: `irq_domain_set_info()` returns
  void.
- Per-interrupt flags: `irqd_set_single_target()` and
  `irqd_set_affinity_on_activate()`; resend-when-in-progress is not set.
- `struct gicv5_its_dev`: not freed on any failure of
  `gicv5_its_irq_domain_alloc()`; once prepare has succeeded, only
  `gicv5_its_msi_teardown()` frees it.

**Mapping and unmapping events**

- PCI interrupts: mapped straight after allocation. `MSI_COMMON_FLAGS` in
  `drivers/pci/msi/irqdomain.c` includes `MSI_FLAG_ACTIVATE_EARLY`, so
  `msi_init_virq()` calls `irq_domain_activate_irq()` inside
  `__msi_domain_alloc_irqs()`. No other file sets that flag.
- `reserve` argument: ignored by `gicv5_its_irq_domain_activate()`; the
  event is always mapped.
- Entry written: an ITT entry (`GICV5_ITTL2E_LPI_ID`, `GICV5_ITTL2E_VALID`),
  not a device table entry.
- Invalidation: `gicv5_its_itt_cache_inv()`; there is no
  gicv5_its_invalidate_ite() in this tree.
- `gicv5_its_map_event()`: `-EEXIST` is its only error. The return value of
  `gicv5_its_itt_cache_inv()` is discarded by map and by unmap, so a timed
  out invalidation still returns 0.
- `-EEXIST` trigger: `irq_domain_activate_irq()` skips an interrupt that is
  already activated, so the error means the entry was left valid by an
  earlier user of that event ID.

**ITS domain free**

- Last two calls: `gicv5_its_syncr()` then `gicv5_irs_syncr()`.
  `gicv5_its_device_cache_inv()` is not called from free.
- Order before the syncs: `bitmap_release_region()`, then
  `irq_domain_reset_irq_data()`, then `irq_domain_free_irqs_parent()`. The
  event ID and the LPI are back in their allocators before either sync
  starts.
- LPI release: done by the parent. `irq_domain_free_irqs_parent()` reaches
  `gicv5_irq_lpi_domain_free()`, which calls `release_lpi()`; there is no
  gicv5_free_lpi() in this tree.
- Reuse before the syncs finish: prevented by `domain->root->mutex`.
  `irq_domain_free_irqs()` holds it across `.free`, and
  `__irq_domain_alloc_irqs()` takes the same mutex; the root of every ITS
  and per-device domain is the LPI domain.
- Per interrupt: `.free` runs with `nr_irqs == 1` (see "Event ID
  allocation"), so both syncs are issued once per freed interrupt.
- Guarantee to the caller: none is reported. Both functions return void and
  wait with `gicv5_wait_for_op()`; a timeout is only logged, and free
  completes anyway.
- Hardware meaning of the syncs: no comment or document in this tree states
  it.
- Context: `gicv5_wait_for_op()` uses `readl_poll_timeout()`, which may
  sleep, so free must run in sleepable context.
- LPI state: not cleaned at free. `gicv5_irq_lpi_domain_alloc()` calls
  `gicv5_lpi_config_reset()` when the LPI is handed out again.
- `struct gicv5_its_dev`: not released by free, even when `event_map`
  becomes empty; `gicv5_its_msi_teardown()` does that.
- **Unsafe usage**: freeing an interrupt whose event is still mapped.
  - Unsafe: `gicv5_its_irq_domain_free()` never writes the ITT, so the entry
    stays valid and names an LPI that `release_lpi()` has returned; the next
    `gicv5_its_map_event()` for that event ID returns `-EEXIST`.
  - Safe: through `__msi_domain_free_irqs()` in `kernel/irq/msi.c`, which
    calls `irq_domain_deactivate_irq()` on every activated interrupt before
    `irq_domain_free_irqs()`.
  - Safe: on the alloc error paths, where the interrupt was never activated,
    for example `out_free_irqs` in `irq_domain_alloc_irqs_locked()`.

## Interrupt wire bridge

**IWB device MSI domain**

- Domain creation: `gicv5_iwb_init_bases()` calls
  `gicv5_iwb_create_device_domain()`, which calls
  `msi_create_device_irq_domain()` with `MSI_DEFAULT_DOMAIN`; the driver does
  not call `irq_domain_create_hierarchy()` or
  `msi_create_parent_irq_domain()`.
- ITS device: allocated at probe, not at the first interrupt request;
  `msi_create_device_irq_domain()` runs the new domain's `msi_prepare`, which
  `its_v5_init_dev_msi_info()` set to `its_v5_pmsi_prepare()` in
  `drivers/irqchip/irq-gic-its-msi-parent.c`.
- ITS device size: the wire count rounded up by `roundup_pow_of_two()` in
  `its_v5_pmsi_prepare()`, stored as `num_events`.
- Device ID: read in `its_v5_pmsi_prepare()`; on DT it is the argument cell
  of `msi-parent`, through `of_pmsi_get_msi_info()`; on ACPI it comes from
  `iort_pmsi_get_msi_info()`.
- Wire number and MSI index: not the same thing;
  `msi_device_domain_alloc_wired()` allocates the index with `MSI_ANY_INDEX`.
- Wire number path: `msi_device_domain_alloc_wired()` puts the wire in the
  low 32 bits of `desc->data.icookie.value` (type in the high 32);
  `gicv5_iwb_domain_set_desc()` copies it to `alloc_info->hwirq`.
- `MSI_ALLOC_FLAGS_FIXED_MSG_DATA`: makes `gicv5_its_alloc_eventid()` in
  `drivers/irqchip/irq-gic-v5-its.c` take `info->hwirq` as the event ID
  instead of searching `event_map`; without the flag the wire and the event
  ID need not match.
- `iwb_msi_template` chip: `.irq_mask` and `.irq_unmask` are
  `irq_chip_mask_parent()` and `irq_chip_unmask_parent()`; the callbacks that
  write IWB registers are `gicv5_iwb_irq_enable()`,
  `gicv5_iwb_irq_disable()` and `gicv5_iwb_set_type()`.
- `gicv5_iwb_write_msi_msg()`: empty, but it cannot be removed;
  `msi_lib_init_dev_msi_info()` in `drivers/irqchip/irq-msi-lib.c` fails
  domain creation when `irq_write_msi_msg` is NULL.
- `MSI_FLAG_USE_DEV_FWNODE`: the domain's fwnode is the bridge device's own
  fwnode, so a consumer's DT or ACPI specifier that names the bridge finds
  this domain.

**Wire enable and trigger mode**

- Register names: there are no IWB_WENABLER, IWB_WTMR or IWB_WENABLE_STATUSR
  definitions; the tree has `GICV5_IWB_WENABLER`, `GICV5_IWB_WTMR` and
  `GICV5_IWB_WENABLE_STATUSR` in `include/linux/irqchip/arm-gic-v5.h`.
- `gicv5_iwb_irq_enable()`: writes the wire bit, then calls
  `irq_chip_enable_parent()`; `gicv5_iwb_irq_disable()` clears it, then
  calls `irq_chip_disable_parent()`.
- Parent of enable/disable: `gicv5_its_irq_chip` has no `irq_enable` or
  `irq_disable`, so the parent helpers end in the LPI unmask and mask.
- Poll of `GICV5_IWB_WENABLE_STATUSR`: only `__gicv5_iwb_set_wire_enable()`
  and the probe poll it, through `gicv5_iwb_wait_for_wenabler()`.
- `gicv5_iwb_set_type()`: no wait after the `GICV5_IWB_WTMR` write; it
  returns 0 straight after `iwb_writel_relaxed()`.
- Wait errors in `gicv5_iwb_set_type()`: none exist; its only failures are
  `-EINVAL` for a register index >= `nr_regs` and for an unhandled type.
- Trigger encoding in `GICV5_IWB_WTMR`:

| Requested type | Wire bit |
|---|---|
| `IRQ_TYPE_LEVEL_HIGH`, `IRQ_TYPE_LEVEL_LOW` | set |
| `IRQ_TYPE_EDGE_RISING`, `IRQ_TYPE_EDGE_FALLING` | cleared |
| anything else, for example `IRQ_TYPE_EDGE_BOTH` | `-EINVAL`, no write |

- Polarity: not programmed; high and low, rising and falling are treated
  alike.
- Failed wait in enable/disable: `gicv5_iwb_irq_enable()` and
  `gicv5_iwb_irq_disable()` ignore the return value of
  `__gicv5_iwb_set_wire_enable()` and still call the parent helper.
- Out-of-range wire in enable/disable: the `-EINVAL` from the `nr_regs`
  check is ignored the same way, so the LPI is still unmasked or masked.

**IWB probe requirements**

- Control register name: `GICV5_IWB_CR0`, bit `GICV5_IWB_CR0_IWBEN`; there
  is no IWB_CR definition.
- `GICV5_IWB_CR0`: read only; the driver never writes it, so it never
  enables the bridge.
- `GICV5_IWB_CR0_IWBEN` clear: `gicv5_iwb_init_bases()` returns `-EINVAL`,
  not `-ENODEV`, before any register is written.
- MSI parent: firmware must describe one (`msi-parent` on DT, an IORT IWB
  node on ACPI) so that `dev->msi.domain` is set;
  `gicv5_iwb_create_device_domain()` otherwise hits `WARN_ON_ONCE()` and
  the probe returns `-ENOMEM`.
- Wire count: `GICV5_IWB_IDR0_IW_RANGE` + 1 is `nr_regs`; the wire count is
  `nr_regs` * 32; nothing from DT or ACPI overrides it.
- Wire disable at probe: the driver writes 0 to every `GICV5_IWB_WENABLER`
  register; it does not rely on the reset state.
- Wait at probe: `gicv5_iwb_wait_for_wenabler()` follows those writes, and
  here a timeout fails the probe with the error it returned.
- Registers touched by the driver: `GICV5_IWB_IDR0`, `GICV5_IWB_CR0`,
  `GICV5_IWB_WENABLE_STATUSR`, `GICV5_IWB_WENABLER`, `GICV5_IWB_WTMR`.
- Wire domain assignment: no register for it is defined in this tree (there
  is no IWB_WDOMAINR); `GICV5_IWB_IDR0_INT_DOMS` is defined and unused.
- MMIO mapping: `platform_get_resource()` then `devm_ioremap()`, not
  `devm_platform_ioremap_resource()`; the region is not requested, and a
  missing resource returns `-EINVAL`.
- ACPI match: _HID `ARMH0003` in `iwb_acpi_match`.
- `acpi_device_clear_deps()`: called only after a successful probe;
  `drivers/acpi/scan.c` lists `ARMH0003` in `acpi_honor_dep_ids`, so ACPI
  consumers of an IWB wire are not enumerated until this call.
- Source of that dependency: `acpi_irq_add_auto_dep()` in
  `drivers/acpi/irq.c`, which asks `gic_v5_get_gsi_handle()` for the bridge
  behind each GSI of a consumer.

**IWB specifier translation**

- ACPI `param[0]`: the whole GSI, not a wire number; the wire is
  `FIELD_GET(GICV5_GSI_IWB_WIRE, fwspec->param[0])`.
- GSI layout, from `include/linux/irqchip/arm-gic-v5.h`:

| Field | Bits | Meaning |
|---|---|---|
| `GICV5_GSI_IC_TYPE` | [31:29] | `GICV5_GSI_IWB_TYPE` (0x7) marks an IWB |
| `GICV5_GSI_IWB_FRAME_ID` | [28:16] | which bridge |
| `GICV5_GSI_IWB_WIRE` | [15:0] | wire on that bridge |

- IWB recognition: decided by `GICV5_GSI_IC_TYPE` alone; a frame ID of 0 is
  a valid bridge, not a marker for a non-IWB interrupt.
- `gic_v5_get_gsi_domain_id()`: returns a `struct fwnode_handle *`, not an
  ID; for an IWB it is the fwnode of the bridge's ACPI device, from
  `iort_iwb_handle_fwnode()`.
- `iort_iwb_handle()`: called by `gic_v5_get_gsi_handle()`, the second
  callback passed to `acpi_set_irq_model()`; it returns the `acpi_handle`
  used for probe dependencies.
- Frame ID lookup: through the IORT only; `iort_match_iwb_callback()`
  compares the frame ID with `iwb_index` in `struct acpi_iort_iwb`, and
  `device_name` there names the ACPI device. The MADT has no IWB entry.
- Range check: `gicv5_iwb_irq_domain_translate()` has none, and the domain
  size does not bound the wire either.
- First range check: `gicv5_its_alloc_eventid()` returns `-EINVAL` when the
  wire is >= `num_events`, which is the wire count rounded up to a power of
  two.
- Wires between the wire count and `num_events`: get a mapping; when a
  trigger type is set they fail later, at the `nr_regs` check in
  `gicv5_iwb_set_type()`.
- Trigger validation: translate only masks `param[1]` with
  `IRQ_TYPE_SENSE_MASK`; unsupported types are refused by
  `gicv5_iwb_set_type()`.
- Other fwnode types: translate has no branch for them and returns 0 with
  `*hwirq` and `*type` unwritten; `-EINVAL` is returned only for
  `param_count` < 2.
- Why that is not reached: the domain's fwnode is the bridge device's
  fwnode (`MSI_FLAG_USE_DEV_FWNODE`), which is an OF node or an ACPI device
  node.

## Firmware, boot and CPU capabilities

**ACPI interrupt model**

- Model value: `gic_acpi_init()` registers `ACPI_IRQ_MODEL_GIC_V5`, not
  `ACPI_IRQ_MODEL_GIC`.
- Tests of `acpi_irq_model == ACPI_IRQ_MODEL_GIC` do not match on GICv5; for
  example `acpi_irq_create_hierarchy()` in `drivers/acpi/irq.c` returns NULL.
- `acpi_set_irq_model()`: takes three arguments here; GICv5 passes
  `gic_v5_get_gsi_domain_id()` (GSI to domain fwnode) and
  `gic_v5_get_gsi_handle()` (GSI to the `acpi_handle` it depends on).
- `IRQCHIP_ACPI_DECLARE()` validate callback: `acpi_validate_gic_table()`, not
  NULL; `gic_acpi_init()` runs only for an IRS entry whose `version` equals
  `ACPI_MADT_GIC_VERSION_V5`.
- MADT walks, all with `acpi_table_parse_madt()`:

  | For | MADT type | Callback | Started by |
  |---|---|---|---|
  | IRS | `ACPI_MADT_TYPE_GICV5_IRS` | `gic_acpi_parse_madt_irs()` | `gicv5_irs_acpi_probe()` |
  | CPU IAFFID | `ACPI_MADT_TYPE_GENERIC_INTERRUPT` | `gic_acpi_parse_iaffid()` | `gicv5_irs_acpi_init_affinity()` |
  | ITS config frame | `ACPI_MADT_TYPE_GICV5_ITS` | `gic_acpi_parse_madt_its()` | `gicv5_its_acpi_probe()` |
  | ITS translate frame | `ACPI_MADT_TYPE_GICV5_ITS_TRANSLATE` | `gic_acpi_parse_madt_its_translate()` | `gic_acpi_parse_madt_its()` |

- Translate-frame walk: nested in the ITS callback, so it runs once per ITS.
- `gic_acpi_parse_iaffid()` skips a GICC entry, returning 0, unless all hold:
  - `flags` has `ACPI_MADT_ENABLED` or `ACPI_MADT_GICC_ONLINE_CAPABLE`;
  - `irs_id` equals the `irs_id` of the IRS being probed;
  - `get_logical_index()` finds `arm_mpidr`;
  - `iaffid` fits the width read from `GICV5_IRS_IDR1`.
- ITS probe: `gicv5_its_acpi_probe()` is called from `gicv5_irs_its_probe()`
  at the end of `gicv5_init_common()`, before `acpi_set_irq_model()`.
- ITS frame match: `linked_translator_id` of the frame equals `translator_id`
  of the ITS.
- ITS frame fwnode: one per frame, from `irq_domain_alloc_parented_fwnode()`
  with the ITS fwnode as parent, registered with
  `iort_register_domain_token()` under `translate_frame_id`.
- ITS domain: one per ITS, on the ITS fwnode, with
  `IRQ_DOMAIN_FLAG_FWNODE_PARENT`; `msi_lib_irq_domain_select()` matches the
  parent of the frame fwnode that IORT returns.
- GSI layout, in `include/linux/irqchip/arm-gic-v5.h`:
  - bits 31:29 are `GICV5_GSI_IC_TYPE`, the same bits as `GICV5_HWIRQ_TYPE`;
  - type `GICV5_GSI_IWB_TYPE` (0x7): `GICV5_GSI_IWB_FRAME_ID` is bits 28:16,
    `GICV5_GSI_IWB_WIRE` is bits 15:0;
  - any other type: `GICV5_HWIRQ_ID` is bits 23:0.
- GIC fwnode: one for the whole GIC, `gsi_domain_handle`, allocated from the
  first IRS entry; `gic_v5_get_gsi_domain_id()` returns it for every non-IWB
  GSI.
- PPI and SPI domains: both sit on that fwnode with `DOMAIN_BUS_WIRED`;
  `gicv5_irq_ppi_domain_select()` and `gicv5_irq_spi_domain_select()` choose
  by the type bits of `fwspec->param[0]`.
- SPI domain: one global domain, not one per IRS;
  `gicv5_irs_lookup_by_spi_id()` only picks the chip data in
  `gicv5_irq_spi_domain_alloc()`.
- A GSI whose type is not PPI, SPI or IWB: `gicv5_irq_domain_translate()`
  returns `-EINVAL`, so no mapping is created.
- IWB domain: exists only after `gicv5_iwb_device_probe()` in
  `drivers/irqchip/irq-gic-v5-iwb.c`; before that `acpi_irq_get()` returns
  `-EPROBE_DEFER`, and the probe ends with `acpi_device_clear_deps()`.

**Boot requirements**

- Document scope: the GICv5 section of `Documentation/arch/arm64/booting.rst`
  has one condition, "entered at EL1 and EL2 is present", plus the line that
  the DT or ACPI tables must describe a GICv5.
- No EL3 item and no requirement on IRS or ITS state is in that section.
- Registers named by the document: `ICH_HFGRTR_EL2`, `ICH_HFGWTR_EL2` and
  `ICH_HFGITR_EL2`; every bit it lists must be 0b1.
- Bit 3 of `ICH_HFGRTR_EL2`: the document lists it as ICC_HAPR_EL1;
  `arch/arm64/tools/sysreg` declares it `Res1`, the tree has no field macro
  for it, and `__init_el2_gicv5` does not set it.
- Every other bit the document lists is in the masks `__init_el2_gicv5`
  writes.
- `__init_el2_gicv5` also writes `ICH_VCTLR_EL2_En` to `SYS_ICH_VCTLR_EL2`;
  the document has no matching item.
- `__init_el2_gicv5` feature test: reads `SYS_ID_AA64PFR2_EL1` from hardware;
  it does not use `check_override`.
- `__init_el2_gicv5` writes: whole-register values, not read-modify-write, so
  any bit not in the mask is written as 0.
- GICv3 compatibility: `__init_el2_gicv5` does nothing for it;
  `__init_el2_gicv3` is a separate macro keyed on `ID_AA64PFR0_EL1.GIC`.
- First EL1 access to a GICv5 register: `test_has_gicv5_legacy()` in
  `arch/arm64/kernel/cpufeature.c` reads `SYS_ICC_IDR0_EL1` from
  `setup_boot_cpu_features()`, before `init_IRQ()`.
- That read happens on the boot CPU when it reports GCIE, whether or not the
  firmware tables describe a GICv5.

**CPU capabilities**

- Types, in `arm64_features[]`:

  | Capability | Type | Matcher |
  |---|---|---|
  | `ARM64_HAS_GICV5_CPUIF` | `ARM64_CPUCAP_STRICT_BOOT_CPU_FEATURE` | `has_cpuid_feature()` |
  | `ARM64_HAS_GICV5_LEGACY` | `ARM64_CPUCAP_EARLY_LOCAL_CPU_FEATURE` | `test_has_gicv5_legacy()` |

- `ARM64_HAS_GICV5_CPUIF` mismatch on a secondary, in either direction: the
  type has `ARM64_CPUCAP_PANIC_ON_CONFLICT`, so `verify_local_cpu_caps()`
  calls `cpu_panic_kernel()` and the kernel panics; the CPU is not just
  refused.
- `ARM64_HAS_GICV5_LEGACY` on a late CPU: one that lacks it when the system
  has it goes to `cpu_die_early()`; one that has it when the system lacks it
  is allowed.
- `cpus_have_cap(ARM64_HAS_GICV5_LEGACY)` before `setup_system_features()`:
  can read true and later false; `update_cpu_capabilities()` sets the bit on
  the boot CPU and clears it when an early secondary lacks it.
- `cpus_have_cap(ARM64_HAS_GICV5_CPUIF)`: final once
  `setup_boot_cpu_features()` has run, which is before `init_IRQ()`.
- `cpus_have_final_boot_cap()`: valid for `ARM64_HAS_GICV5_CPUIF` after
  `setup_boot_cpu_features()`; no GICv5 code uses it.
- `cpus_have_final_boot_cap(ARM64_HAS_GICV5_LEGACY)`: after
  `setup_boot_cpu_features()` it reads false until `apply_alternatives_all()`,
  because only `SCOPE_BOOT_CPU` capabilities enter `boot_cpucaps`.
- `cpus_have_final_cap()`: tests the same capability bit whatever the scope,
  so it is valid for the local-scope `ARM64_HAS_GICV5_LEGACY`.
- There is no system_supports_gicv5() here; the irqchip driver's test is
  `gicv5_cpuif_has_gcie()` in `drivers/irqchip/irq-gic-v5.c`, which calls
  `this_cpu_has_cap()`.
- `this_cpu_has_cap(ARM64_HAS_GICV5_CPUIF)`: reads the calling CPU's
  `ID_AA64PFR2_EL1` from hardware, not the sanitised value.
- **Unsafe usage**: calling `cpus_have_final_cap()` on either capability
  before `setup_system_features()`, which runs from `smp_cpus_done()`; it
  hits `BUG()`. Irqchip probe and the boot CPU's first
  `gicv5_starting_cpu()` run before that.
  - Safe: `this_cpu_has_cap()` with IRQs off, as `gicv5_starting_cpu()` does
    through `gicv5_cpuif_has_gcie()`; `this_cpu_has_cap()` has no
    finalisation test.
  - Safe: `cpus_have_final_cap()` from KVM init, as `vgic_v5_probe()` does;
    it is reached from `kvm_arm_init()`, a `module_init()` call, after
    `smp_cpus_done()`.
  - Safe: `cpus_have_cap()` inside an alternative callback keyed on
    `ARM64_ALWAYS_SYSTEM`, as `kvm_patch_ich_vtr_el2()` does;
    `setup_system_capabilities()` runs `update_cpu_capabilities()` before
    `apply_alternatives_all()`.
- **Unsafe usage**: calling `this_cpu_has_cap()` from preemptible context; it
  hits `WARN_ON(preemptible())` and returns false without running the
  matcher. Affinity pinning or `migrate_disable()` does not satisfy the test.
  - Safe: with IRQs or preemption disabled, as in `gicv5_starting_cpu()`,
    which runs during `init_IRQ()` and as the `CPUHP_AP_IRQ_GIC_STARTING`
    callback.
  - Safe: from the matcher of a local-scope capability, as
    `can_trap_icv_dir_el1()` does for `ARM64_HAS_GICV5_LEGACY`;
    `setup_boot_cpu_features()` and `check_local_cpu_capabilities()` run
    those matchers with IRQs off on the CPU being probed. A system-scope
    matcher runs from `setup_system_capabilities()`, which is preemptible.

## KVM scope and probing

**KVM GICv5 support**

- `vgic_get_irq()` in `arch/arm64/kvm/vgic/vgic.c`: tests `vgic_is_v5(kvm)` before
  anything else and returns NULL for every intid, whatever its type field.
- `struct gicv5_vpe` (`include/linux/irqchip/arm-gic-v5.h`): one field,
  `bool resident`; no VPE table or doorbell state.
- `gicv5_vpe.resident`: only `vgic_v5_load()` and `vgic_v5_put()` use it, to
  skip the second load or put on the WFI path.
- Implemented PPIs: `vgic_v5_get_implemented_ppis()` sets the four timer PPIs
  (`GICV5_ARCH_PPI_CNTHP`, `GICV5_ARCH_PPI_CNTV`, `GICV5_ARCH_PPI_CNTHV`,
  `GICV5_ARCH_PPI_CNTP`) and `GICV5_ARCH_PPI_SW_PPI` unconditionally; for
  `GICV5_ARCH_PPI_PMUIRQ` see "PPI masks and iteration".

**Feature coverage of the device**

- Nested virtualisation: absent; `vgic_v5_init()` returns `-EINVAL` if any vCPU
  has `vcpu_has_nv()`.
- When the NV error surfaces: at `KVM_DEV_ARM_VGIC_CTRL_INIT` (through
  `vgic_init()`), not at device creation.
- NV with the GICv3 device on a GICv5 host: accepted; `init_subsystems()` in
  `arch/arm64/kvm/arm.c` allows `KVM_MODE_NV` when
  `kvm_vgic_global_state.has_gcie_v3_compat` is set.
- Protected KVM: absent; `vgic_v5_probe()` does not register
  `KVM_DEV_TYPE_ARM_VGIC_V5` when `is_protected_kvm_enabled()`.
- pKVM on a host without the legacy interface: `vgic_v5_probe()` returns
  `-ENODEV`, and `init_subsystems()` then fails KVM init.
- Save and restore to userspace: absent; `vgic_v5_set_attr()` and
  `vgic_v5_get_attr()` return `-ENXIO` for every group except
  `KVM_DEV_ARM_VGIC_GRP_CTRL`.
- `KVM_DEV_ARM_VGIC_GRP_CTRL` attributes: `KVM_DEV_ARM_VGIC_CTRL_INIT` and
  `KVM_DEV_ARM_VGIC_USERSPACE_PPIS`; the latter is get-only, a set returns
  `-ENXIO`.

**Handing the GIC to KVM**

- `struct gic_kvm_info` has no `has_gcie_v3_compat` field;
  `gic_of_setup_kvm_info()` sets only `type`, `no_maint_irq_mask` and
  `maint_irq`.
- `has_gcie_v3_compat`: exists only in `struct vgic_global`; `vgic_v5_probe()`
  sets it from `cpus_have_final_cap(ARM64_HAS_GICV5_LEGACY)`.
- `vgic_v5_probe()`: never reads its `info` argument.
- `gic_of_setup_kvm_info()` publishes nothing when any of these holds:
  - `CONFIG_KVM` is off (empty stub);
  - `gicv5_global_data.virt_capable` is false; `gicv5_irs_init()` sets it from
    `GICV5_IRS_IDR0_VIRT` of the first IRS;
  - `irq_of_parse_and_map(node, 0)` returns 0;
  - `gicv5_irs_of_probe()` or `gicv5_init_common()` failed, so
    `gicv5_of_init()` never reaches the call.
- ACPI: `gic_acpi_init()` in `drivers/irqchip/irq-gic-v5.c` does not call
  `vgic_set_kvm_info()`, and no other code publishes `GIC_V5`.
- ACPI-booted GICv5 host: `kvm_vgic_hyp_init()` returns `-ENODEV`;
  `init_subsystems()` treats that as "no vgic" and continues, except under
  pKVM, where KVM init fails.

**KVM probe**

| Device | Skipped when | Registration failure |
|---|---|---|
| `KVM_DEV_TYPE_ARM_VGIC_V5` | `is_protected_kvm_enabled()` | tolerated, probe continues |
| `KVM_DEV_TYPE_ARM_VGIC_V3` | `!cpus_have_final_cap(ARM64_HAS_GICV5_LEGACY)` | returned, even if the GICv5 device registered |

- `-ENODEV`: returned only when the legacy cpucap is absent and the GICv5
  device was not registered.
- `KVM_DEV_TYPE_ARM_VGIC_V3` registration: `kvm_register_vgic_device()` also
  registers the ITS device, so an ITS registration failure fails the probe.
- `max_gic_vcpus`: `VGIC_V5_MAX_CPUS` on the non-pKVM path; overwritten with
  `min(VGIC_V3_MAX_CPUS, VGIC_V5_MAX_CPUS)` once the GICv3 device registered.
- `VGIC_V3_MAX_CPUS` and `VGIC_V5_MAX_CPUS`: both 512 in
  `include/kvm/arm_vgic.h`.
- `vgic_v5_get_implemented_ppis()`: fills `impl_ppi_mask`; skipped under pKVM
  together with the GICv5 registration.
- `nr_lr`: `(vgic_ich_vtr() & 0xf) + 1`; the probe does not call
  `__vgic_v3_get_gic_config()`.
- `kvm_vgic_global_state.type`: set to `VGIC_V5` first and stays so, even when
  only the GICv3 device ends up registered.
- `gicv3_cpuif` static key and `vgic_v3_enable_cpuif_traps()`: done inside
  `vgic_v5_probe()` on the compat path, not in `kvm_vgic_hyp_init()`.

**GICv3 guests on GICv5**

- Cpucap: `ARM64_HAS_GICV5_LEGACY`, matched per CPU by
  `test_has_gicv5_legacy()` from `ICC_IDR0_EL1_GCIE_LEGACY`.
- Host type in this mode: `kvm_vgic_global_state.type` is `VGIC_V5`, so a test
  for `VGIC_V3` is false; `vgic_host_has_gicv3()` in
  `arch/arm64/kvm/vgic/vgic.h` covers both hosts.
- `vgic_v3_deactivate_phys()` in `arch/arm64/kvm/vgic/vgic-v3.c`: issues
  `gic_insn(..., CDDI)` when `ARM64_HAS_GICV5_LEGACY` is set, else
  `gic_write_dir()`.
- CDDI type field: hard-coded to 1, which is `GICV5_HWIRQ_TYPE_PPI`; the
  physical interrupt is assumed to be a PPI.
- When `vgic_v3_deactivate_phys()` runs: only for a HW-mapped interrupt
  that is not in a list register (EOIcount replay in
  `vgic_v3_fold_lr_state()`, trapped DIR write in `vgic_v3_deactivate()`).
- Interrupt in a list register: `vgic_v3_compute_lr()` still sets `ICH_LR_HW`
  on a GICv5 host, and KVM issues no CDDI for it; deactivation is left to the
  hardware.

**Leaving compatibility mode**

- Control: `ICH_VCTLR_EL2_V3`; `__vgic_v5_compat_mode_disable()` clears it and
  issues `isb()`, `__vgic_v3_compat_mode_enable()` sets it.
- Write site: first statement of `__vgic_v5_restore_vmcr_apr()` in
  `arch/arm64/kvm/hyp/vgic-v5-sr.c`.
- When it runs: at vCPU load, from `vgic_v5_load()` through `kvm_call_hyp()`;
  not at each guest entry.
- `vgic_v5_load()`: returns early when `gicv5_vpe.resident` is true, so V3 is
  cleared once per load and put pair.
- `__vgic_v5_compat_mode_disable()`: has no cpucap test; only
  `__vgic_v3_compat_mode_enable()` tests `ARM64_HAS_GICV5_CPUIF`.
- Putting a GICv3 vCPU: nothing clears V3; apart from the boot write, only
  `__vgic_v5_compat_mode_disable()` clears it.
- Boot value: `arch/arm64/include/asm/el2_setup.h` writes only
  `ICH_VCTLR_EL2_En`, so V3 starts clear.
- **Potentially unsafe usage**: writing a GICv5-layout `ICH_*_EL2` register in
  a function that does not itself clear `ICH_VCTLR_EL2_V3`.
  - Unsafe: on a path that can run before `vgic_v5_load()` has run for this
    vCPU on this CPU, or with no `isb()` after the clear; a GICv3 vCPU loaded
    earlier leaves V3 set.
  - Safe: in the same function after the clear and `isb()`, as
    `__vgic_v5_restore_vmcr_apr()` does for `SYS_ICH_VMCR_EL2` and
    `SYS_ICH_APR_EL2`.
  - Safe: at guest entry of a GICv5 vCPU, as `__vgic_v5_restore_ppi_state()`
    does; `kvm_vgic_load()` has already called `vgic_v5_load()`.

**KVM device creation**

- vCPU limit: `kvm->max_vcpus = min(VGIC_V5_MAX_CPUS,
  kvm_vgic_global_state.max_gic_vcpus)`; `-E2BIG` if more vCPUs are online.
- Allocation: `kvm_vgic_create()` calls `vgic_allocate_private_irqs_locked()`
  for each existing vCPU; `vgic_allocate_private_irqs()` is the wrapper
  `kvm_vgic_vcpu_init()` uses for vCPUs created later.
- GICv5 layout selection: by `vgic_is_v5(vcpu->kvm)`, not by the `type`
  argument, so `vgic_model` must be set before the allocation.
- `vgic_v5_setup_private_irq()`: `intid` is `vgic_v5_make_ppi(i)`; SW_PPI is
  edge, every other PPI level; installs `vgic_v5_ppi_irq_ops`.
- `kvm_vgic_finalize_idregs()`: clears `ID_AA64PFR0_EL1.GIC`,
  `ID_AA64PFR2_EL1.GCIE` and `ID_PFR1_EL1.GIC`, then sets GCIE to IMP for
  `KVM_DEV_TYPE_ARM_VGIC_V5`.
- Second call: `kvm_finalize_sys_regs()` calls `kvm_vgic_finalize_idregs()`
  again before the first vCPU run.

**Timer setup at creation**

- Helper: `kvm_vgic_create()` calls `kvm_timer_init_vm()`
  (`arch/arm64/kvm/arch_timer.c`) for `KVM_DEV_TYPE_ARM_VGIC_V5` only.
- When: after private IRQ allocation succeeded, under `config_lock`; an
  earlier failure leaves the timer PPIs untouched.
- What it sets: every entry of `kvm->arch.timer_data.ppi[]` to
  `get_vgic_ppi(kvm, default_ppi[i])`.
- Values: the ID field keeps `default_ppi[]` (30, 27, 28, 26);
  `get_vgic_ppi()` only adds `GICV5_HWIRQ_TYPE_PPI` in the type field.

## KVM interrupt IDs and PPI state

**KVM interrupt ID helpers**

- Build macros: `vgic_v5_make_ppi()`, `vgic_v5_make_spi()`,
  `vgic_v5_make_lpi()`; each takes the bare ID.
- Take-apart macro: `vgic_v5_get_hwirq_id()` returns the bare ID.
- `vgic_v5_set_hwirq_id()`: places the ID field only; the result has type 0
  and is not a usable interrupt ID.
- `get_vgic_ppi()`: a macro in `include/kvm/arm_arch_timer.h`, not a function
  in `arch/arm64/kvm/arch_timer.c`; it open-codes the two `FIELD_PREP()` and
  returns the number unchanged for other models.
- Timer: `kvm_timer_init_vm()` stores the typed ID in
  `kvm->arch.timer_data.ppi[]`; every user reads it with `timer_irq()`.
- PMU: `kvm_arm_pmu_v3_init()` stores `KVM_ARMV8_PMU_GICV5_IRQ`, a typed
  literal, in `irq_num`; `kvm_pmu_update_state()` passes it on.
- **Unsafe usage**: passing a bare ID for a GICv5 guest.
  - Unsafe: to `kvm_vgic_set_irq_ops()`, `kvm_vgic_map_phys_irq()` or, once
    the vgic is initialised, `kvm_vgic_unmap_phys_irq()`: the lookup returns
    `NULL` and they `BUG_ON()` it.
  - Unsafe: to `kvm_vgic_get_map()`, `kvm_vgic_reset_mapped_irq()` or, once
    the vgic is initialised, `kvm_vgic_map_is_active()`: they dereference the
    `NULL` result.
  - Unsafe: to `kvm_vgic_inject_irq()` or `kvm_vgic_set_owner()`: once the
    vgic is initialised they return `-EINVAL`, so nothing is injected and no
    owner is set.
  - Safe: a typed ID from `timer_irq()`, as `kvm_timer_enable()` passes;
    `__irq_is_ppi()` in `vgic_get_vcpu_irq()` defines what the lookup
    accepts.

**Interrupt type predicates**

| Predicate | Test for a GICv5 guest |
|---|---|
| `__irq_is_sgi()` | always false |
| `__irq_is_ppi()` | type is PPI and ID < `VGIC_V5_NR_PRIVATE_IRQS` |
| `__irq_is_spi()` | type is SPI; ID not bounded |
| `__irq_is_lpi()` | type is LPI; ID not bounded |
| `vgic_valid_spi()` | type is SPI and ID < `nr_spis` |

- `irq_is_private()`: equals `irq_is_ppi()` for a GICv5 guest.
- `nr_spis`: stays 0 for a GICv5 guest; `vgic_init()` does not set it and
  `vgic_v5_set_attr()` rejects `KVM_DEV_ARM_VGIC_GRP_NR_IRQS`, so
  `vgic_valid_spi()` is false.
- **Potentially unsafe usage**: indexing per-interrupt state with
  `vgic_v5_get_hwirq_id()` after only a type predicate.
  - Unsafe: after `irq_is_spi()` or `irq_is_lpi()`; the 24-bit ID can be
    anything.
  - Safe: after `irq_is_ppi()`; its bound is the size of `private_irqs[]`
    and of every PPI bitmap, and `kvm_vgic_set_owner()` relies on it before
    it dereferences the lookup result.

**Private interrupt lookup**

- PPIs per vCPU: 64, `VGIC_V5_NR_PRIVATE_IRQS` in `include/kvm/arm_vgic.h`,
  not 128; only the architected half is supported.
- `__vgic_v5_save_ppi_state()`: has `BUILD_BUG_ON(VGIC_V5_NR_PRIVATE_IRQS !=
  64)`; raising the count needs the hyp code changed too.
- PPIs that can be exposed: at most six, those in `impl_ppi_mask`; see
  `vgic_v5_get_implemented_ppis()` in `arch/arm64/kvm/vgic/vgic-v5.c`.
- `vgic_get_vcpu_irq()`: gates on `__irq_is_ppi()`, then has both an explicit
  range test that returns `NULL` and `array_index_nospec()`.
- An ID that fails the gate (bare ID, other type, PPI ID of 64 or more):
  falls through to `vgic_get_irq()`, which returns `NULL` for every ID of a
  GICv5 guest.

**PPI masks and iteration:** All bitmaps are `VGIC_V5_NR_PRIVATE_IRQS` (64)
bits and indexed by bare ID.

| Bitmap | Stored in | Computed by, when |
|---|---|---|
| `impl_ppi_mask` | `kvm_vgic_global_state.vgic_v5_ppi_caps` | `vgic_v5_get_implemented_ppis()` at probe; no register is read: five fixed PPIs, plus `GICV5_ARCH_PPI_PMUIRQ` if `system_supports_pmuv3()` |
| `userspace_ppis` | `struct vgic_v5_vm` | `vgic_v5_init()`, at `KVM_DEV_ARM_VGIC_CTRL_INIT` |
| `vgic_ppi_mask` | `struct vgic_v5_vm` | `vgic_v5_finalize_ppi_state()`, first vCPU run |
| `vgic_ppi_hmr` | `struct vgic_v5_vm` | same; bit set means level, from `irq->config` |
| `vgic_ppi_dvir` | `struct vgic_v5_cpu_if` | `vgic_v5_set_ppi_dvi()`, on map and unmap of a physical interrupt |
| `vgic_ppi_enabler` | `struct vgic_v5_cpu_if` | `access_gicv5_ppi_enabler()` in `arch/arm64/kvm/sys_regs.c`, on a trapped guest write, anded with `vgic_ppi_mask` |
| `vgic_ppi_activer` | `struct vgic_v5_cpu_if` | `vgic_v5_fold_ppi_state()`, at exit |
| `pendr` | `vgic_v5_ppi_state` in `struct kvm_host_data` | `vgic_v5_flush_ppi_state()` before entry; overwritten by `__vgic_v5_save_ppi_state()` at exit |
| `activer_exit` | `vgic_v5_ppi_state` in `struct kvm_host_data` | `__vgic_v5_save_ppi_state()`, at exit |

- `vgic_ppi_hmr`: written only; nothing in this tree reads it.
- `for_each_visible_v5_ppi()`: defined in `arch/arm64/kvm/vgic/vgic.h`; walks
  `vgic_ppi_mask`.
- `vgic_ppi_mask` before the first vCPU run: all zeroes, so the loop body
  never runs.
- `vgic_v5_finalize_ppi_state()`: the one loop over `impl_ppi_mask`, because
  it is what builds `vgic_ppi_mask`.
- **Potentially unsafe usage**: dereferencing the result of
  `vgic_get_vcpu_irq()` in a PPI loop with no `NULL` test.
  - Unsafe: when the loop passes the bare index, or an index of 64 or more;
    the lookup returns `NULL`.
  - Safe: index from a `for_each_set_bit()` over a 64-bit PPI mask, passed
    through `vgic_v5_make_ppi()`, as `vgic_v5_flush_ppi_state()` does;
    `__irq_is_ppi()` defines the bound and `private_irqs[]` has 64 entries.

**Shadow and hardware state**

- Three places hold PPI state, not two: the `struct vgic_irq` entries of
  `private_irqs[]`, `struct vgic_v5_cpu_if`, and `vgic_v5_ppi_state` in
  `struct kvm_host_data`.
- `vgic_v5_ppi_state`: guest state staged per physical CPU
  (`host_data_ptr()`), not host state; it has one `pendr`, used for entry and
  for exit, and `activer_exit`.
- `struct vgic_v5_cpu_if`: defined in `include/kvm/arm_vgic.h`; has no
  pending and no handling-mode field.

| Point | What moves | Current afterwards |
|---|---|---|
| load, `vgic_v5_load()` | VMCR and APR to hardware; no PPI state | PPI state still in memory |
| entry, `vgic_v5_flush_ppi_state()` then `__vgic_v5_restore_ppi_state()` | pending from `struct vgic_irq` via `pendr`; DVI, active, enable, priority from `struct vgic_v5_cpu_if` | hardware |
| exit, `__vgic_v5_save_ppi_state()` then `vgic_v5_fold_ppi_state()` | active and pending to `vgic_v5_ppi_state`, priority to `struct vgic_v5_cpu_if`, then folded into `struct vgic_irq` | memory |
| put, `vgic_v5_put()` | APR from hardware; no PPI register is read | memory |

**Per-interrupt operations**

- `struct irq_ops` members: `get_flags`, `get_input_level`,
  `queue_irq_unlock`, `set_direct_injection`.
- `vgic_v5_ppi_irq_ops`: sets `queue_irq_unlock` and `set_direct_injection`;
  `vgic_v5_setup_private_irq()` installs it on all 64 PPIs of every vCPU.
- `arch_timer_irq_ops_vgic_v5`: `kvm_timer_enable()` installs it on the PPIs
  of the vCPU's `nr_timers()` timers; it repeats both GICv5 ops and adds
  `get_input_level`.
- `get_flags`: set by neither GICv5 structure, so
  `vgic_irq_needs_resampling()` is false.
- SPIs and LPIs: have no `struct vgic_irq` for a GICv5 guest, so no ops.
- `vgic_v5_ppi_queue_irq_unlock()`: records nothing; the caller has already
  set `line_level` or `pending_latch`.
- `vgic_v5_ppi_queue_irq_unlock()`: makes `KVM_REQ_IRQ_PENDING` and kicks
  `irq->target_vcpu` without testing enabled or pending, and returns `true`.
- **Unsafe usage**: installing on a GICv5 PPI a `struct irq_ops` that lacks
  the two GICv5 ops; `kvm_vgic_set_irq_ops()` replaces the whole pointer.
  - Unsafe: without `queue_irq_unlock`, `vgic_queue_irq_unlock()` asks
    `vgic_target_oracle()`, which returns `NULL` for a pending PPI because
    `vgic.enabled` is never set for GICv5, so the vCPU is not kicked; an
    active PPI is put on `ap_list`, which `kvm_vgic_sync_hwstate()` never
    prunes for GICv5.
  - Unsafe: without `set_direct_injection`, mapping does not set the bit in
    `vgic_ppi_dvir`, while `kvm_timer_update_irq()` still skips the
    injection.
  - Safe: a structure that repeats both, as `arch_timer_irq_ops_vgic_v5`
    does.

**Finalising PPI state**

- Caller: `kvm_arch_vcpu_run_pid_change()` in `arch/arm64/kvm/arm.c`, on each
  vCPU's first run, after `kvm_timer_enable()` and
  `kvm_arm_pmu_v3_enable()`; not from `kvm_vgic_map_resources()`.
- Lock: the function takes `kvm->arch.config_lock` itself; the caller must
  not hold it.
- Done-once guard: the `GICV5_ARCH_PPI_SW_PPI` bit of `vgic_ppi_mask`, tested
  under the lock; there is no separate flag.
- Exposed set: each PPI in `impl_ppi_mask` whose `struct vgic_irq` on vCPU 0
  has `owner` set, plus `GICV5_ARCH_PPI_SW_PPI`.
- `config`: only read, to fill `vgic_ppi_hmr`; not written.
- Timer `owner`: set per vCPU by `timer_irqs_are_valid()`, on that vCPU's own
  first run.
- PMU `owner`: set by `kvm_arm_pmu_v3_init()`, at
  `KVM_ARM_VCPU_PMU_V3_INIT`.
- Readers of `vgic_ppi_mask` (`for_each_visible_v5_ppi()` users) take no
  lock; each vCPU passes through the function, and so through the lock,
  before it first enters the guest.
- **Potentially unsafe usage**: deriving VM-wide state from one vCPU's
  `struct vgic_irq` fields on the first-run path.
  - Unsafe: when the field is set on each vCPU's own first run and the vCPU
    read is not the one running; the mask is computed once and a PPI whose
    field is set later stays hidden.
  - Safe: a field set for every vCPU before any run, such as `config`, which
    `vgic_v5_setup_private_irq()` sets at allocation.
- **Unsafe usage**: writing `vgic_ppi_mask` after the guard bit is set;
  vCPUs that have passed the guard walk it with no lock.
  - Safe: write only before the guard bit, under `config_lock`, as
    `vgic_v5_finalize_ppi_state()` does.

**PPIs driven from userspace**

- Drivable PPIs: only `GICV5_ARCH_PPI_SW_PPI`; `vgic_v5_init()` sets
  `userspace_ppis` to that bit anded with `impl_ppi_mask`.
- Attribute: `KVM_DEV_ARM_VGIC_USERSPACE_PPIS` in
  `KVM_DEV_ARM_VGIC_GRP_CTRL`; `vgic_v5_get_attr()` reads it through
  `vgic_v5_get_userspace_ppis()`.
- Value returned: two `u64`; the second is always 0.
- Before `KVM_DEV_ARM_VGIC_CTRL_INIT`: the read succeeds and returns 0.
- `vgic_lazy_init()`: returns `-EBUSY` for a GICv5 guest that is not
  initialised, for both PPI and SPI.

| Type | Checks, in order | Then |
|---|---|---|
| `KVM_ARM_IRQ_TYPE_PPI` | vCPU exists; number < `VGIC_V5_NR_PRIVATE_IRQS`; bit set in `userspace_ppis`; each failure is `-EINVAL` | `vgic_v5_make_ppi()`, `kvm_vgic_inject_irq()` with `NULL` owner |
| `KVM_ARM_IRQ_TYPE_SPI` | none on the number | `vgic_v5_make_spi()`, `kvm_vgic_inject_irq()`; `vgic_get_irq()` returns `NULL`, so the result is `-EINVAL` |

**Arch timers with GICv5**

- `kvm_timer_init_vm()`: runs twice for a GICv5 guest; `kvm_arch_init_vm()`
  stores bare numbers, then `kvm_vgic_create()` calls it again and stores
  typed IDs.
- `kvm_arm_timer_set_attr()`: not refused for GICv5; it stores any ID that
  passes `irq_is_ppi()`, so a bare 27 gets `-EINVAL` and a typed PPI is
  accepted.
- `timer_irqs_are_valid()`: fails if the ID of any of the vCPU's
  `nr_timers()` timers (two without NV) differs from `get_vgic_ppi()` of its
  default; `kvm_timer_enable()` then returns `-EINVAL` on first run.
- Directly injected timer: `kvm_timer_update_irq()` returns before
  `kvm_vgic_inject_irq()` for `direct_vtimer` and `direct_ptimer`; hardware
  raises the PPI through the bit in `vgic_ppi_dvir`.
- Physical active state at load: `kvm_timer_vcpu_load_gic()` sets it
  unconditionally for a GICv5 guest, whatever the pending state.
- Physical active state at put: `kvm_timer_vcpu_put()` clears it for the
  direct timers; other models do nothing there.
- Mechanism: on a GICv5 host the timer interrupts sit behind `timer_chip`;
  for a GICv5 guest `timer_irq_set_irqchip_state()` turns the active state
  of a forwarded interrupt into `irq_chip_mask_parent()` or
  `irq_chip_unmask_parent()`.
- GICv3 guest on a GICv5 host: `timer_irq_set_irqchip_state()` passes the
  active state to the parent instead.

**PMU interrupt with GICv5**

- `KVM_ARMV8_PMU_GICV5_IRQ`: `0x20000017` in `include/kvm/arm_pmu.h`, PPI 23
  as a typed ID.
- `KVM_ARM_VCPU_PMU_V3_IRQ`: userspace passes the typed value;
  `pmu_irq_is_valid()` compares for equality, so any other typed ID gets
  `-EINVAL`; a bare 23 gets `-EINVAL` from the `irq_is_ppi()` and
  `irq_is_spi()` test before it.
- No IRQ set: `kvm_arm_pmu_v3_init()` stores `KVM_ARMV8_PMU_GICV5_IRQ` for a
  GICv5 guest and goes on; for other models it returns `-ENXIO`.
- `kvm_arm_pmu_v3_init()`: returns `-ENODEV` if the vgic is not initialised,
  before it looks at the IRQ.
- `kvm_arm_pmu_irq_initialized()`: tests `irq_num != 0`, which holds for the
  typed value.

## KVM entry and exit

**Flushing state before entry**

- Destination: `pendr` in the `vgic_v5_ppi_state` member of
  `struct kvm_host_data` (`arch/arm64/include/asm/kvm_host.h`), reached with
  `host_data_ptr()`. It is per physical CPU, not in `struct vgic_v5_cpu_if`.
- There is no vgic_ppi_pendr_entry or vgic_ppi_pendr_exit. The one `pendr` is
  written by flush and overwritten by `__vgic_v5_save_ppi_state()` on exit.
- PPIs walked: flush loops with `for_each_visible_v5_ppi()`, so only over the
  PPIs in `vgic_ppi_mask` of `kvm->arch.vgic.gicv5_vm`; see "PPI masks and
  iteration".
- Edge: `irq->pending_latch` is set to false in flush, in the same `irq_lock`
  hold that sampled `irq_is_pending()`.
- No filtering in flush: it tests none of `irq->enabled`, `irq->active`,
  `irq->hw` or `vgic_ppi_dvir`. Directly injected PPIs are masked later, in
  `__vgic_v5_restore_ppi_state()`.

**Folding state after exit**

- Scope: `vgic_v5_fold_ppi_state()` walks every exposed PPI. It does not
  compare entry state with exit state.
- `irq->active`: assigned from `activer_exit`, for edge and level alike.
- Edge: `irq->pending_latch |=` the PPI's bit in `pendr`. A clear bit never
  clears the latch.
- Level: no pending state is copied back. `irq->line_level` and
  `irq->pending_latch` are left as they were.
- Directly injected PPIs: not skipped. Fold tests neither `irq->hw` nor
  `vgic_ppi_dvir`.
- After the loop: `activer_exit` is copied to `cpu_if->vgic_ppi_activer`, which
  is the value written on the next entry.
- Aborted entry: `kvm_arch_vcpu_ioctl_run()` calls `kvm_vgic_sync_hwstate()`
  after a flush even when the guest was not entered. The OR puts back the edge
  bit that flush moved into `pendr`.
- **Unsafe usage**: assigning the saved pending bit to `irq->pending_latch`
  of an edge PPI. `kvm_vgic_inject_irq()` sets the latch while the guest runs,
  and the assignment drops that edge.
  - Safe: OR the bit in under `irq->irq_lock`, as `vgic_v5_fold_ppi_state()`
    does.
- **Unsafe usage**: sampling `irq_is_pending()` and clearing
  `irq->pending_latch` in two separate holds of `irq->irq_lock`. An edge that
  `kvm_vgic_inject_irq()` latches between them is cleared without reaching the
  bitmap.
  - Safe: both in one hold, as `vgic_v5_flush_ppi_state()` does.
- **Unsafe usage**: using `pendr` or `activer_exit` of `vgic_v5_ppi_state`
  across a point where the task can be preempted. They are per physical CPU, so
  another vCPU's flush or save overwrites them.
  - Safe: inside the window where `kvm_arch_vcpu_ioctl_run()` holds
    `preempt_disable()` from before `kvm_vgic_flush_hwstate()` until after
    `kvm_vgic_sync_hwstate()`; `activer_exit` is this vCPU's only once
    `__vgic_v5_save_ppi_state()` has run in that window. Between runs, pending
    state lives in `struct vgic_irq` and active state in `vgic_ppi_activer`.

**PPI register world switch**

- State kept: bank 0 only, enforced by
  `BUILD_BUG_ON(VGIC_V5_NR_PRIVATE_IRQS != 64)`, plus priority registers 0 to 7.
- `__vgic_v5_save_ppi_state()`, in order:
  1. read `SYS_ICH_PPI_ACTIVER0_EL2` into `activer_exit`
  2. read `SYS_ICH_PPI_PENDR0_EL2` into `pendr`
  3. read `SYS_ICH_PPI_PRIORITYR0_EL2` to `SYS_ICH_PPI_PRIORITYR7_EL2` into
     `cpu_if->vgic_ppi_priorityr[]`
  4. write 0 to `SYS_ICH_PPI_DVIR0_EL2` and `SYS_ICH_PPI_DVIR1_EL2`
- Not read on save: the enable and DVI registers. `vgic_ppi_enabler` is
  updated by the trap handler `access_gicv5_ppi_enabler()` in
  `arch/arm64/kvm/sys_regs.c`.
- `__vgic_v5_restore_ppi_state()`, in order:
  1. `SYS_ICH_PPI_DVIR0_EL2` from `vgic_ppi_dvir`
  2. `SYS_ICH_PPI_ACTIVER0_EL2` from `vgic_ppi_activer`
  3. `SYS_ICH_PPI_ENABLER0_EL2` from `vgic_ppi_enabler`
  4. `SYS_ICH_PPI_PENDR0_EL2` from `pendr` AND NOT `vgic_ppi_dvir`
  5. `SYS_ICH_PPI_PRIORITYR0_EL2` to `SYS_ICH_PPI_PRIORITYR7_EL2`
  6. write 0 to `SYS_ICH_PPI_DVIR1_EL2`, `SYS_ICH_PPI_ACTIVER1_EL2`,
     `SYS_ICH_PPI_ENABLER1_EL2`, `SYS_ICH_PPI_PENDR1_EL2`, and
     `SYS_ICH_PPI_PRIORITYR8_EL2` to `SYS_ICH_PPI_PRIORITYR15_EL2`
- nVHE: `__hyp_vgic_save_state()` and `__hyp_vgic_restore_state()` in
  `arch/arm64/kvm/hyp/nvhe/switch.c`.
- VHE: nothing in `arch/arm64/kvm/hyp/vhe/switch.c` calls them. The kernel
  wrappers `vgic_v5_save_state()` and `vgic_v5_restore_state()` in
  `arch/arm64/kvm/vgic/vgic-v5.c` do, and add a `dsb(sy)`.
- The wrappers are reached from `vgic_save_state()` and
  `vgic_restore_state()` in `arch/arm64/kvm/vgic/vgic.c`, gated by
  `can_access_vgic_from_kernel()`: in `kvm_vgic_sync_hwstate()` before the
  fold, and in `kvm_vgic_flush_hwstate()` after the flush.
- On both paths `__vgic_v5_save_state()` or `__vgic_v5_restore_state()` runs
  just before the PPI function.

**Direct injection of PPIs**

- Path: `kvm_vgic_map_phys_irq()` calls `kvm_vgic_map_irq()`, which sets
  `irq->hw` and then calls `irq->ops->set_direct_injection(vcpu, irq, true)`.
- `set_direct_injection`: member of `struct irq_ops` in
  `include/kvm/arm_vgic.h`. Both `vgic_v5_ppi_irq_ops` and
  `arch_timer_irq_ops_vgic_v5` point it at `vgic_v5_set_ppi_dvi()`.
- Recorded in: per-vCPU `vgic_ppi_dvir` in `struct vgic_v5_cpu_if`, not per
  VM. The per-interrupt mark is `irq->hw`; `struct vgic_irq` has no separate
  direct-injection flag.
- Switched on: every guest entry, first write of
  `__vgic_v5_restore_ppi_state()`. Not at load.
- Switched off: every guest exit, last writes of
  `__vgic_v5_save_ppi_state()`. Not at put.
- Software injection: for a GICv5 guest `kvm_timer_update_irq()` returns
  before `kvm_vgic_inject_irq()` when the timer is `direct_vtimer` or
  `direct_ptimer`, so it does not update the shadow `line_level` of those
  PPIs.
- Unmap: `kvm_vgic_unmap_irq()` passes `irq->target_vcpu` and false. The only
  callers of `kvm_vgic_unmap_phys_irq()` are in
  `kvm_timer_vcpu_load_nested_switch()`, which `kvm_timer_vcpu_load()` does not
  call for a GICv5 guest.

**Loading and putting a vCPU**

- Flag: `resident` in `struct gicv5_vpe`
  (`include/linux/irqchip/arm-gic-v5.h`), the `gicv5_vpe` member of
  `struct vgic_v5_cpu_if`.
- Priorities: copied only by `vgic_v5_put()` when the vCPU flag `IN_WFI` is
  set, and only after the `resident` test has passed. A put outside WFI, or a
  put that returns early, copies nothing.
- `IN_WFI`: set by `kvm_vcpu_wfi()` in `arch/arm64/kvm/arm.c` just before its
  `kvm_vgic_put()`.
- Helper: `vgic_v5_sync_ppi_priorities()`; it writes `irq->priority` under
  `irq_lock` for exposed PPIs only.
- Source: `cpu_if->vgic_ppi_priorityr[]`, which
  `__vgic_v5_save_ppi_state()` refreshes on every exit; one byte per PPI, 5
  bits used.

**Control and active priority registers**

| Register | Saved | Restored |
|---|---|---|
| `SYS_ICH_VMCR_EL2` | every exit, `__vgic_v5_save_state()` | load only, `__vgic_v5_restore_vmcr_apr()` |
| `SYS_ICH_APR_EL2` | put only, `__vgic_v5_save_apr()` | load only, `__vgic_v5_restore_vmcr_apr()` |
| `SYS_ICC_ICSR_EL1` | every exit, `__vgic_v5_save_state()` | every entry, `__vgic_v5_restore_state()` |

- There is no __vgic_v5_restore_apr here; `__vgic_v5_restore_vmcr_apr()`
  writes both registers.
- `__vgic_v5_restore_state()`: writes only `SYS_ICC_ICSR_EL1`. The VMCR is
  not written on entry.
- `vgic_v5_put()`: saves only the APR. The VMCR image it leaves is the one
  from the last exit.
- Hypercalls: only `__vgic_v5_save_apr()` and `__vgic_v5_restore_vmcr_apr()`
  have `HANDLE_FUNC()` entries in `arch/arm64/kvm/hyp/nvhe/hyp-main.c`. They
  are issued with `kvm_call_hyp()` from `vgic_v5_put()` and `vgic_v5_load()`.
- `kvm_call_hyp()` under VHE: calls the function directly, then `isb()`.
- `__vgic_v5_save_state()` and `__vgic_v5_restore_state()`: not hypercalls;
  they run with the PPI save and restore functions (see "PPI register world
  switch").

**Pending interrupt check**

- Mask helper: `vgic_v5_get_effective_priority_mask()` in
  `arch/arm64/kvm/vgic/vgic-v5.c`.
- Enable bit: if `FEAT_GCIE_ICH_VMCR_EL2_EN` is clear in the saved
  `vgic_vmcr`, the mask is 0.
- Mask of 0: `vgic_v5_has_pending_ppi()` returns false before it looks at any
  PPI.
- Mask otherwise: the minimum of VPMR plus one and the trailing-zero count of
  `vgic_apr` (32 when no bit is set).
- Comparison: `irq->enabled && irq->priority < mask`. With no active
  priority, a priority equal to VPMR passes; a priority equal to the highest
  active priority never does.
- `irq->active`: not tested.
- Hardware-mapped PPI: `irq->hw` selects `vgic_get_phys_line_level()`;
  `pending_latch`, `line_level` and the saved pending register are not used.
- `vgic_get_phys_line_level()`: calls `irq->ops->get_input_level()` when set,
  and `irq_get_irqchip_state()` on `irq->host_irq` only otherwise.
- Timers: the hook is `kvm_arch_timer_get_input_level()`. It takes only the
  INTID and evaluates `kvm_timer_pending()` for the timer of
  `kvm_get_running_vcpu()`, not of the `vcpu` passed to
  `vgic_v5_has_pending_ppi()`.
- Age of the inputs: `vgic_vmcr` is from the last exit, `vgic_apr` from the
  last put, `irq->priority` from the last put made in WFI.

**Shared bitmaps and per-interrupt locks**

- `vgic_v5_set_ppi_dvi()`: only asserts `irq->irq_lock` with
  `lockdep_assert_held()`. `kvm_vgic_map_phys_irq()` and
  `kvm_vgic_unmap_phys_irq()` take it.
- **Potentially unsafe usage**: `__set_bit()`, `__clear_bit()` or
  `__assign_bit()` on a bitmap indexed by interrupt while holding
  `irq->irq_lock`.
  - Unsafe: when the bitmap is shared and the writers of its other bits hold
    only their own `irq_lock`, as for `vgic_ppi_dvir`. Two non-atomic updates
    of one word lose a bit.
  - Safe: the atomic `assign_bit()`, as `vgic_v5_set_ppi_dvi()` does.
  - Safe: when one lock covers the whole walk. `vgic_v5_finalize_ppi_state()`
    writes `vgic_ppi_mask` and `vgic_ppi_hmr` with `__set_bit()` and
    `__assign_bit()` under `kvm->arch.config_lock`.
  - Safe: on an on-stack bitmap. `vgic_v5_flush_ppi_state()` builds its
    pending bitmap with `__assign_bit()` and publishes it with one
    `bitmap_copy()` after the loop.

## KVM traps and emulated registers

**PPI enable register trap**

- Second bank (`ICC_PPI_ENABLER1_EL1`, odd `p->Op2`): the write is discarded;
  `access_gicv5_ppi_enabler()` returns `true` before it stores or masks
  anything.
- Storage: `vgic_ppi_enabler` in `struct vgic_v5_cpu_if` holds
  `VGIC_V5_NR_PRIVATE_IRQS` (64) bits; there is no second-bank shadow and no
  second mask.
- First bank: the shadow is replaced by `p->regval` ANDed with the mask; the
  previous shadow value is not kept, although the comment says "merge".
- Mask: `vgic_ppi_mask` in `struct vgic_v5_vm`, one per VM, filled by
  `vgic_v5_finalize_ppi_state()` in `arch/arm64/kvm/vgic/vgic-v5.c`.
- After the store: `irq->enabled` is set from the shadow for every PPI in the
  mask, each under `irq->irq_lock`; `vgic_v5_has_pending_ppi()` reads
  `irq->enabled`.
- Hardware: the handler writes no register. `__vgic_v5_restore_ppi_state()` in
  `arch/arm64/kvm/hyp/vgic-v5-sr.c` writes the shadow to
  `SYS_ICH_PPI_ENABLER0_EL2` and the constant 0 to `SYS_ICH_PPI_ENABLER1_EL2`.
- Exit: `__vgic_v5_save_ppi_state()` does not read the enable registers back;
  no code reads `SYS_ICH_PPI_ENABLER0_EL2`.
- Reads: not trapped for a GICv5 guest; `__compute_ich_hfgwtr()` forces only
  the write trap.
- A read that reaches the handler: `WARN_ON_ONCE()`, then `undef_access()`.

**Fine-grained traps for the guest**

- GICv5 guest: three trap bits are forced, and no others. They cover reads of
  `ICC_IDR0_EL1` and `ICC_IAFFIDR_EL1` (`__compute_ich_hfgrtr()`) and
  writes of `ICC_PPI_ENABLER0_EL1` and `ICC_PPI_ENABLER1_EL1`
  (`__compute_ich_hfgwtr()`, one bit for both registers).
- Not trapped for a GICv5 guest: the PPI pending, priority, active and
  handling-mode registers, `ICC_CR0_EL1`, `ICC_PCR_EL1`, `ICC_APR_EL1`,
  `ICC_ICSR_EL1`, `ICC_HPPIR_EL1`.
- Instructions: none trapped for a GICv5 guest; `kvm_vcpu_load_fgt()` runs
  plain `__compute_fgt()` on `ICH_HFGITR_EL2`, with no forced bits.
- Polarity: a set bit means no trap. Every GICv5 `SR_FGT()` entry in
  `arch/arm64/kvm/emulate-nested.c` has polarity 0, so a forced trap is
  `&= ~bit` after `__compute_fgt()`.
- Guest without GICv5, host with `ARM64_HAS_GICV5_CPUIF`: every trap bit of
  the three registers maps to `FEAT_GCIE` in `arch/arm64/kvm/config.c`, so all
  land in `kvm->arch.fgu[]` and `__compute_fgt()` clears them all.
- UNDEF for that guest: injected by `triage_sysreg_trap()` from
  `kvm->arch.fgu[]`, before any handler in `arch/arm64/kvm/sys_regs.c` runs.
- GICv5 handlers: make no feature test of their own; `kvm_has_gicv5()` has no
  caller under `arch/arm64`. The FGU test in `triage_sysreg_trap()` is the
  only gate.
- Host without `ARM64_HAS_GICV5_CPUIF`: `kvm_vcpu_load_fgt()` computes none
  of the three registers and `__activate_traps_ich_hfgxtr()` writes none.

**Emulated ID registers**

- `ICC_IAFFIDR_EL1`: `access_gicv5_iaffid()` in `arch/arm64/kvm/sys_regs.c`
  returns `vcpu->vcpu_id` in the `IAFFID` field; a write gets
  `undef_access()`.
- `ICC_IDR0_EL1`: only `PRI_BITS` and `ID_BITS` are filled; every other bit,
  `ICC_IDR0_EL1_GCIE_LEGACY` included, reads 0.
- `vgic_v5_reset()`: stores two constants and reads no host register.
  `num_id_bits` is `ICC_IDR0_EL1_ID_BITS_16BITS` (raw field value 0, the
  lowest encoding); `num_pri_bits` is the count 5.
- Userspace: no path writes either field for a GICv5 VM.
  `vgic_v5_set_attr()` in `arch/arm64/kvm/vgic/vgic-kvm-device.c` returns
  `-ENXIO` for `KVM_DEV_ARM_VGIC_GRP_CPU_SYSREGS`; `vgic_v5_reset()` is the
  only writer.
- **Unsafe usage**: storing a bit count in `num_id_bits`, or a raw field value
  in `num_pri_bits`.
  - Unsafe: `access_gicv5_idr0()` emits `num_id_bits` unchanged and
    `num_pri_bits - 1`, so the guest reads the wrong width.
  - Safe: raw value for ID bits and count for priority bits, as
    `vgic_v5_reset()` does; count 5 gives `ICC_IDR0_EL1_PRI_BITS_5BITS`.
- **Unsafe usage**: letting a GICv5 vCPU enter the guest while `num_pri_bits`
  is still 0.
  - Unsafe: `num_pri_bits - 1` wraps and `access_gicv5_idr0()` returns
    `PRI_BITS` as all ones.
  - Safe: set the field from `vgic_init()`, which calls `vgic_v5_reset()` for
    every vCPU with `kvm->arch.config_lock` asserted.
    `kvm_arch_vcpu_precreate()` refuses new vCPUs once `vgic_initialized()`,
    and `vgic_v5_map_resources()` returns `-EBUSY` at first run until then.
- **Unsafe usage**: emulating a GICv5 register value while only
  `__compute_fgt()` computes its trap bit.
  - Unsafe: a GICv5 guest has no FGU bits in the GICv5 groups, so the bit
    stays set, the access does not trap and the guest reads the hardware
    value.
  - Safe: clear the bit after `__compute_fgt()`, as `__compute_ich_hfgrtr()`
    does for `ICH_HFGRTR_EL2_ICC_IDRn_EL1`.
- **Unsafe usage**: a userspace setter that lets `num_pri_bits` or
  `num_id_bits` grow past the value reset stored.
  - Safe: return `-EINVAL` for a value greater than the stored one, as
    `set_gic_ctlr()` in `arch/arm64/kvm/vgic-sys-reg-v3.c` does for GICv3.

## Model gaps

### Other mistakes models make

- Models take the ITS and IPI domains to free LPI numbers themselves. Both
  free callbacks call `irq_domain_free_irqs_parent()`, which reaches
  `release_lpi()` in `gicv5_irq_lpi_domain_free()`; a child that releases an
  LPI itself frees it twice.
- Models take a GICv5 vCPU to have 128 private interrupts. 128 is the host
  driver's `PPI_NR` in `drivers/irqchip/irq-gic-v5.c`; for the vCPU count see
  `VGIC_V5_NR_PRIVATE_IRQS`.
- Models take an IRS to stay enabled once probed. When `gicv5_init_common()`
  fails, `gicv5_irs_remove()` disables every IRS and also calls
  `gicv5_deinit_lpis()`.
- Models take a guest to see `ID_AA64PFR2_EL1.GCIE` only once a GICv5 device
  exists. On a GICv5 host `sanitise_id_aa64pfr2_el1()` presents it as IMP with
  no test for a vgic device; `kvm_vgic_create()` and `kvm_finalize_sys_regs()`
  fix it up, and the latter clears it when there is no in-kernel irqchip.
- Models do not know that a GICv5 guest changes the WFI trap choice. Under the
  default policy `kvm_vcpu_should_clear_twi()` in `arch/arm64/kvm/arm.c`
  returns `single_task_running()` for it, with no vLPI or vSGI test.
- Models take `acpi_set_irq_model()` to have two parameters. The third, a
  GSI-to-`acpi_handle` callback, is NULL in the GICv3 driver.
- Models expect `kzalloc(sizeof(*p), GFP_KERNEL)`. The GICv5 drivers allocate
  typed objects with `kzalloc_obj()` and `kzalloc_objs()` from
  `include/linux/slab.h`; an omitted flags argument means `GFP_KERNEL`.
