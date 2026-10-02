# GICv3/v4 Subsystem Details

## Main structures

### Objects and how they relate

- `drivers/irqchip/irq-gic-its-msi-parent.c`: holds both
  `gic_v3_its_msi_parent_ops` and `gic_v5_its_msi_parent_ops`.
- ITS domain: one per `struct its_node`, an MSI parent domain made by
  `its_init_domain()` through `msi_create_parent_irq_domain()`; its parent is
  the main domain (`its_parent`).
- MSI layer above the ITS: per-device MSI domains only; there is no global
  PCI-MSI or platform-MSI domain, and no its_domain variable (only
  `its_domain_ops`).
- ITS domain `host_data`: a `struct msi_domain_info`, whose `data` is the
  `struct its_node`.
- Main domain (`gic_data.domain`): holds LPIs as well as SGI/PPI/SPI;
  `its_irq_gic_domain_alloc()` allocates each LPI in it, for device LPIs and
  for vPE doorbells.
- LPI numbers: one global space, `lpi_range_list` of `struct lpi_range`;
  device LPI blocks and vPE doorbell blocks both come from `its_lpi_alloc()`.
- `struct rdists`: holds no LPI allocation bitmap and no
  `struct redist_region`; its per-CPU part is an anonymous struct reached
  through `rdist`, there is no struct rdist_cpu.
- `struct redist_region`: array in `struct gic_chip_data`, one entry per MMIO
  region, not indexed by CPU.
- PPI partitions: there is no struct partition_desc and no partition domain;
  `struct partition_affinity` in `drivers/irqchip/irq-gic-v3.c` is a cpumask
  per DT partition node, reported by `gic_irq_get_fwspec_info()`.
- `struct its_collection`: `its->collections` is indexed by Linux CPU number,
  and `col_id` is that number once `its_cpu_init_collection()` has mapped the
  collection for that CPU; `event_map.col_map[]` and `vpe->col_idx` are both
  such indexes.
- vPE domain: one per `struct its_vm` (`vm->domain`), made in
  `its_alloc_vcpu_irqs()` directly on the main domain, not on an ITS domain;
  there is no its_vpe_domain variable, only `its_vpe_domain_ops`.
- vPE domain hwirq: the index of the vPE in the VM; the doorbell LPI
  (`vpe_db_lpi`) is the hwirq at the parent level; chip data is the
  `struct its_vpe`.
- vSGI domain: one per `struct its_vpe` (`sgi_domain`), linear, 16 interrupts,
  no parent domain; chip data is the `struct its_vpe`.
- `struct its_vm` and `struct its_vpe` storage: embedded in KVM's
  `struct vgic_dist` and `struct vgic_v3_cpu_if`; the only memory
  `vgic_v4_init()` allocates for them is the `vpes` pointer array.
- vPE tables: not part of `struct its_vm`; they belong to every v4 ITS
  (`struct its_baser` of type `GITS_BASER_TYPE_VCPU`) and, with `has_rvpeid`,
  to the redistributors; see `its_alloc_vpe_table()`.
- `struct its_vlpi_map`: the caller's object is copied into
  `event_map.vlpi_maps[]` by `its_vlpi_map()`; the array exists only while the
  device has forwarded events.
- `event_map.vm`: one `struct its_device` forwards events into one
  `struct its_vm` at a time.
- `struct its_cmd_info`: has three receivers, chosen by the irq it is sent
  on: device LPI (`its_irq_chip`), vPE doorbell, vSGI (`its_sgi_irq_chip`);
  each accepts a different subset of `enum its_vcpu_info_cmd_type`.
- KVM entry points: there is no its_vcpu_irq function; the calls are in
  `drivers/irqchip/irq-gic-v4.c`, for example `its_map_vlpi()` and
  `its_make_vpe_resident()`.
- `vpe_proxy`: file-static in `drivers/irqchip/irq-gic-v3-its.c`;
  `vpe_proxy.dev` is a `struct its_device` with no LPIs of its own, on the
  first ITS in `its_nodes`, whose events are mapped to vPE doorbells.
- `vpe_proxy` is built by `its_init_vpe_domain()` only when
  `gic_rdists->has_direct_lpi` is false; a set `has_rvpeid` keeps that flag
  true in the redistributor scan, so with `has_rvpeid` there is no proxy.

## Where to look

**Source files**

| Job | File in this tree |
|---|---|
| MSI parent glue | `drivers/irqchip/irq-gic-its-msi-parent.c` (no "v3" in the name); shared with the GICv5 ITS |
| fsl-mc MSI glue | no file of its own in `drivers/irqchip/`; handled in `its_pmsi_prepare()` in `drivers/irqchip/irq-gic-its-msi-parent.c` |
| GICv4 vPE and vSGI irqchips | `drivers/irqchip/irq-gic-v3-its.c`; `drivers/irqchip/irq-gic-v4.c` defines no `struct irq_chip`, it holds the API that KVM calls |
| Priority header | `include/linux/irqchip/arm-gic-v3-prio.h` |
| GICv3 register encodings | split: `SYS_ICC_IAR1_EL1` and most other GICv3 EL1 encodings are hand-written in `arch/arm64/include/asm/sysreg.h`; `ICH_HCR_EL2`, `ICH_VTR_EL2`, `ICH_VMCR_EL2` and the GICv5 registers are in `arch/arm64/tools/sysreg` |
| User-visible system register table | `gic_v3_icc_reg_descs[]` in `arch/arm64/kvm/vgic-sys-reg-v3.c`, one level above `vgic/`; there is no such file inside `arch/arm64/kvm/vgic/` |
| Guest trap table for the ICC registers | `sys_reg_descs[]` in `arch/arm64/kvm/sys_regs.c`; not the table userspace reads |
| KVM virtual GIC, per file | glob `arch/arm64/kvm/vgic/`; the rows below are the files that are easy to miss |
| KVM nested GICv3 | `arch/arm64/kvm/vgic/vgic-v3-nested.c` |
| KVM debugfs | `arch/arm64/kvm/vgic/vgic-debug.c` |
| KVM GICv5, and GICv3 guests on a GICv5 host | `arch/arm64/kvm/vgic/vgic-v5.c`; `vgic_v5_probe()` registers the GICv3 device when the host has `ARM64_HAS_GICV5_LEGACY` |
| Hypervisor save and restore, GICv5 | `arch/arm64/kvm/hyp/vgic-v5-sr.c`, beside `arch/arm64/kvm/hyp/vgic-v3-sr.c`; both are built into VHE and nVHE |

**Entry points**

| Job | Start reading from |
|---|---|
| Bringing up a secondary CPU | `gic_check_rdist()` runs first, at `CPUHP_BP_PREPARE_DYN`; then `gic_starting_cpu()`; both are registered in `gic_smp_init()` |
| Preparing MSIs for a device | `its_pci_msi_prepare()` or `its_pmsi_prepare()` in `drivers/irqchip/irq-gic-its-msi-parent.c`; each ends in `its_msi_prepare()` in `drivers/irqchip/irq-gic-v3-its.c` |
| Activating one LPI | `its_irq_domain_activate()`; it does not call `its_set_affinity()` |
| Initialising a guest's GICv3 | `vgic_set_common_attr()` on `KVM_DEV_ARM_VGIC_CTRL_INIT`, which calls `vgic_init()`; `kvm_vgic_map_resources()` and `vgic_lazy_init()` initialise only a GICv2 guest and fail with `-EBUSY` for an uninitialised GICv3; in `vgic_v3_map_resources()` the base address checks come first |
| Injecting an MSI into a guest | `kvm_set_msi()`, then `vgic_its_inject_msi()`; the irqfd fast path is `kvm_arch_set_irq_inatomic()`, then `vgic_its_inject_cached_translation()` |
| Saving the ITS tables for migration | `vgic_its_set_attr()`, then `vgic_its_ctrl()`, which calls `vgic_its_save_tables_v0()` through `struct vgic_its_abi`; `vgic_its_commit_v0()` is not on this path |
| All other jobs | names are unchanged in this tree: `gic_of_init()`, `gic_acpi_init()`, `gic_handle_irq()`, `gic_ipi_send_mask()`, `kvm_vgic_create()`, `kvm_vgic_flush_hwstate()`, `kvm_vgic_sync_hwstate()`, `kvm_vgic_inject_irq()`, `vgic_mmio_write_its_cwriter()` |

## Distributor, redistributors and interrupt chips

**Interrupt ID ranges**

- EPPI: `convert_offset_index()` leaves the offset unchanged and returns
  index = hwirq - `EPPI_BASE_INTID` + 32; only ESPI gets a remapped offset.
- Callers pass the `GICD_` offset names for redistributor interrupts too;
  there is no GICR_ISENABLERnE in this tree.
- ESPI offsets that `convert_offset_index()` remaps: `GICD_ISENABLER`,
  `GICD_ICENABLER`, `GICD_ISPENDR`, `GICD_ICPENDR`, `GICD_ISACTIVER`,
  `GICD_ICACTIVER`, `GICD_IPRIORITYR`, `GICD_ICFGR`, `GICD_IROUTER`.
- `GICD_IGROUPR` and `GICD_IGRPMODR` are not remapped.
- `convert_offset_index()` does no scaling: it returns the bank offset and an
  index relative to the bank; each caller turns the index into a register
  and bit (`gic_configure_irq()` does it for `GICD_ICFGR`).
- `convert_offset_index()` cannot fail: on an unknown ESPI offset, an LPI or
  an invalid range it does `WARN_ON(1)` and returns the unchanged offset with
  the raw hwirq as index, and the caller performs the access.
- `gic_dist_base()`: called only by `gic_irq_set_prio()` and
  `gic_set_affinity()`; neither tests the `NULL` it returns for an LPI.
- `gic_peek_irq()`, `gic_poke_irq()`, `gic_set_type()`: pick the frame with
  `gic_irq_in_rdist()`, which sends every other range to the distributor.
- Distributor accesses in `gic_peek_irq()` and `gic_set_type()` (the read
  and the write of `GICD_ICFGR`) go through `gic_dist_base_alias()`; writes
  in `gic_poke_irq()` use `gic_data.dist_base`.
- `gic_dist_base_alias()` with `gic_nvidia_t241_erratum` enabled: handles
  SPI and ESPI only, `unreachable()` for any other range.
- SGI, PPI and EPPI frame: `gic_data_rdist()` is `this_cpu_ptr()`, so the
  access reaches the copy of the interrupt owned by the executing CPU.
- `__get_intid_range()`: `LPI_RANGE` ends at `GENMASK(23, 0)`; above that is
  `__INVALID_RANGE__`, while the callbacks test `hwirq >= 8192`.
- No check against implemented counts: neither `gic_irq_domain_translate()`
  nor `gic_irq_domain_map()` compares hwirq with `GIC_LINE_NR`,
  `GIC_ESPI_NR` or `gic_data.ppi_nr`; those bound only the init loops in
  `gic_dist_init()` and `gic_cpu_init()`.
- `gic_irq_domain_map()`: maps an LPI when `gic_dist_supports_lpis()`;
  -EPERM only otherwise and for `__INVALID_RANGE__`.
- There is no gic_get_ppi_index() or __gic_get_ppi_index() here, and
  `gic_irq_nmi_setup()` keeps no per-PPI refcount.
- **Unsafe usage**: passing `convert_offset_index()` an offset outside its
  ESPI switch for an interrupt that can be an ESPI.
  - Safe: write the `nE` bank directly with an index from 0, as
    `gic_dist_init()` does for `GICD_IGROUPRnE`.
- **Potentially unsafe usage**: a chip callback that calls `gic_peek_irq()`,
  `gic_poke_irq()` or `gic_dist_base()` without testing the range.
  - Unsafe: in a callback that a child domain forwards for an LPI;
    `its_irq_chip` forwards `irq_eoi` with `irq_chip_eoi_parent()`. The
    access then uses the raw hwirq as index.
  - Safe: test first, as `gic_eoimode1_eoi_irq()` (`hwirq >= 8192`) and
    `gic_arm64_erratum_2941627_needed()` (range is SPI or ESPI) do.
  - Safe: a callback that every chip above an LPI implements itself, for
    example `gic_mask_irq()`; `its_irq_chip`, `its_vpe_irq_chip` and
    `its_vpe_4_1_irq_chip` each have their own `irq_mask`.

**Redistributor capability flags**

- `has_direct_lpi`: a redistributor keeps it set with any one of
  `GICR_TYPER_DirectLPIS`, `GICR_CTLR_IR`, or the running `has_rvpeid`.
- Redistributor with `GICR_TYPER_RVPEID` but without `GICR_TYPER_VLPIS`,
  while the running `has_rvpeid` is still set: `WARN_ON_ONCE()`, then
  `has_direct_lpi`, `has_vlpis` and `has_rvpeid` are cleared.
- `gic_nvidia_t241_erratum` enabled: `gic_init_bases()` never sets the four
  flags, so all stay false, `has_direct_lpi` included.
- No quirk and no command-line option clears a flag after the scan; there is
  no irqchip.gicv4_enable parameter.
- `its_init()` runs only when `gic_dist_supports_lpis()`; otherwise the flags
  stay as the redistributor scan left them.
- `its_init()` clears `has_vlpis` when no ITS was probed (returns -ENXIO),
  and when `its_init_vpe_domain()` or `its_init_v4()` fails.
- `its_init()` clears `has_rvpeid`, with `WARN_ON()`, when it is set and no
  ITS is `is_v4_1()`.
- `its_init()` with ITSs present but none `is_v4()`: leaves `has_vlpis` set.
- `its_cpu_init_lpis()`: clears `has_rvpeid` and `has_vlpis` when
  `allocate_vpe_l1_table()` fails; it runs on each CPU's first
  `its_cpu_init()`, so also on a secondary CPU long after boot.
- KVM's `has_v4` and `has_v4_1` in `struct gic_kvm_info`: copied once, in
  `gic_of_setup_kvm_info()` or `gic_acpi_setup_kvm_info()`, after
  `gic_init_bases()` returned; a later clear does not reach KVM.
- Code in `drivers/irqchip/irq-gic-v3-its.c` tests the flag in `gic_rdists`
  at the time of use, and `is_v4()` or `is_v4_1()` on the `struct its_node`
  for what is done through one ITS, for example
  `its_irq_set_vcpu_affinity()` and `its_build_vmapp_cmd()`.
- KVM code tests `kvm_vgic_global_state.has_gicv4` and `has_gicv4_1`, or
  `vgic_supports_direct_msis()` and `system_supports_direct_sgis()` in
  `arch/arm64/kvm/vgic/vgic-mmio-v3.c`.
- `gic_rdists_supports_plpis()`: tests `GICR_TYPER_PLPIS` of the local
  redistributor (physical LPIs); it is not a GICv4 test.

**The two interrupt chips**

- `gic_eoimode1_chip` differs from `gic_chip` in three callbacks only:
  `.irq_mask`, `.irq_eoi` and `.irq_set_vcpu_affinity`;
  `.irq_get_irqchip_state` is the same function in both.
- `gic_eoimode1_eoi_irq()`: deactivates (`gic_write_dir()`); it does not
  drop priority.
- `gic_eoimode1_mask_irq()`: masks, then clears the active state with
  `GICD_ICACTIVER` when the interrupt is forwarded.
- `irq_set_vcpu_affinity()` on an interrupt of `gic_chip`: returns -ENOSYS
  when no chip above it in the hierarchy has the callback.
- `gic_irq_set_vcpu_affinity()`: uses `vcpu` only as set-or-clear; it stores
  nothing but the forwarded flag.
- Forwarded state is per interrupt and persistent: for example
  `kvm_timer_hyp_init()` sets it once for the host timer PPIs.
- While forwarded, `gic_eoimode1_eoi_irq()` never deactivates, also when the
  handler ran with no guest loaded; KVM changes the active state itself with
  `irq_set_irqchip_state()`, see `set_timer_irq_phys_active()`.
- PPI, EPPI and SGI: `handle_percpu_devid_irq()` with either chip; there is
  no handle_percpu_devid_fasteoi_irq() in this tree.
- LPIs are mapped by `gic_irq_domain_map()` too (`LPI_RANGE`), with the
  selected chip and `handle_fasteoi_irq()`, as parent of the ITS domain.
- `IRQCHIP_SUPPORTS_NMI`: not in either initialiser;
  `gic_enable_nmi_support()` sets it at boot on the selected chip only.

**Split priority drop and deactivation**

- Decision: `gic_init_bases()` disables `supports_deactivate_key` when
  `is_hyp_mode_available()` is false; nothing else changes it.
- `gic_check_eoimode()` is the GICv2 driver's, in
  `drivers/irqchip/irq-gic.c`; here no devicetree region takes part.
- `is_hyp_mode_available()` on arm64: true when every CPU booted at EL2, or
  when `is_pkvm_initialized()`; a host that runs at EL1 after booting at EL2
  uses the split mode.

| Case | Priority drop | Deactivation |
|---|---|---|
| key off | `irq_eoi`: `gic_eoi_irq()` | same `ICC_EOIR1_EL1` write |
| key on | `gic_complete_ack()`, before the flow handler | `irq_eoi`: `gic_eoimode1_eoi_irq()` |
| key on, forwarded | `gic_complete_ack()` | not by the host `irq_eoi` |
| key on, LPI | `gic_complete_ack()` | none |

- `gic_cpu_sys_reg_init()` applies the mode per CPU, at bring-up and again on
  `CPU_PM_EXIT` in `gic_cpu_pm_notifier()`.
- `struct gic_kvm_info` has no field for the EOI mode; this driver never sets
  `no_hw_deactivation`.
- Key on is not enough for KVM to get the info: `gic_of_setup_kvm_info()`
  returns before `vgic_set_kvm_info()` when `irq_of_parse_and_map()` finds
  no maintenance interrupt.
- `gic_acpi_setup_kvm_info()` returns before `vgic_set_kvm_info()` when
  `gic_acpi_collect_virt_info()` or `acpi_register_gsi()` fails.
- Key off: `kvm_arm_init()` tests the same `is_hyp_mode_available()` and
  returns -ENODEV, so KVM does not initialise at all.

**Firmware interrupt specifiers**

- There is no GIC_IRQ_TYPE_PARTITION case and no partition domain in this
  tree; a partitioned PPI translates like any PPI or EPPI and
  `gic_irq_domain_translate()` ignores `param[3]`.
- Devicetree type cell: the code tests the literals 0 to 3 and
  `GIC_IRQ_TYPE_LPI`; `GIC_ESPI` and `GIC_EPPI` are the binding names in
  `include/dt-bindings/interrupt-controller/arm-gic.h`.
- One-cell form (`param_count == 1`, `param[0] < 16`): tested before the
  fwnode kind, gives the SGI with `IRQ_TYPE_EDGE_RISING`; `gic_smp_init()`
  uses it.
- LPI specifier: the trigger type comes from `param[2]` like the others, and
  the same `WARN_ON()` applies.
- Number out of range for its type (SPI > 987, PPI > 15, ESPI > 1023,
  EPPI > 63): `pr_warn_once()` only, translation succeeds with the plain
  sum; for example PPI number 16 becomes hwirq 32, an SPI.
- `WARN_ON(*type == IRQ_TYPE_NONE)`: the only trigger check in translate,
  for every devicetree type and for ACPI; it still returns 0.
- Trigger a SPI or ESPI cannot use: rejected later, by `gic_set_type()` with
  -EINVAL, not by translate.
- ACPI branch: `param_count != 2` and `param[0] < 16` return -EINVAL; a
  fwnode that is neither devicetree nor irqchip returns -EINVAL.
- Affinity lookup path: `platform_get_irq_affinity()` ->
  `get_irq_affinity()` -> `of_irq_get_affinity()` ->
  `irq_populate_fwspec_info()` -> `gic_irq_get_fwspec_info()`.
- `gic_irq_get_fwspec_info()` outcomes:

| Specifier | Result |
|---|---|
| not devicetree | 0, no affinity, flags 0 |
| exactly 4 cells, `param[3]` non-zero, type not 1 or 3 | 0, no affinity, flags 0 |
| exactly 4 cells, `param[3]` non-zero, PPI or EPPI | mask of the matching partition |
| same, phandle not found or no partition matches | -ENOENT |
| anything else, any type | `cpu_possible_mask`, valid |

- Partitions: `gic_data.parts`, an array of `struct partition_affinity`,
  matched by comparing `partition_id` with the fwnode of the phandle.
- `gic_populate_ppi_partitions()` fills `gic_data.parts` in `gic_of_init()`
  after `gic_init_bases()` returned; before that every PPI or EPPI lookup
  with a non-zero fourth cell gives -ENOENT.
- `of_irq_get_affinity()` returns `info.affinity` without testing
  `IRQ_FWSPEC_INFO_AFFINITY_VALID`; `acpi_irq_get_affinity()` tests it.

**Quirks and errata**

- `gic_enable_quirks()`: IIDR only; it skips every entry that has
  `compatible` or `property`.
- `gic_enable_of_quirks()`: handles only entries with `compatible` or
  `property`; an entry with both needs both to match.
- Both functions run every matching entry, and log only when `init` returns
  true.
- ITS: `its_enable_quirks()` runs the IIDR pass, then the devicetree pass
  only when `is_of_node()`; there is no ACPI-keyed quirk matching.
- `gic_quirks` on ACPI: in `drivers/irqchip/irq-gic-v3.c`
  `gic_enable_of_quirks()` is called from `gic_of_init()` only, so the
  `compatible` and `property` entries never apply.
- `gic_of_init()` runs the devicetree quirks before `gic_init_bases()` fills
  `gic_data.dist_base` and `rdists.gicd_typer`.
- `gic_quirks`, in `drivers/irqchip/irq-gic-v3.c`:

| `init` | Sets | Effect where tested |
|---|---|---|
| `gic_enable_quirk_msm8996()` | `FLAGS_WORKAROUND_GICR_WAKER_MSM8996` | `gic_enable_redist()` returns at once |
| `gic_enable_quirk_asr8601()` | `FLAGS_WORKAROUND_ASR_ERRATUM_8601001` | `gic_cpu_to_affinity()` moves Aff1 to Aff0 and Aff2 to Aff1, for every user |
| `gic_enable_quirk_hip06_07()` | clears bits 9:8 of `rdists.gicd_typer` | `GIC_ESPI_NR` is 0; returns false if ESPI bit was clear |
| `gic_enable_quirk_cavium_38539()` | `FLAGS_WORKAROUND_CAVIUM_ERRATUM_38539` | `gic_init_bases()` does not read `GICD_TYPER2` |
| `gic_enable_quirk_nvidia_t241()` | `gic_nvidia_t241_erratum` | `gic_dist_base_alias()`; GICv4 flags stay false |
| `gic_enable_quirk_arm64_2941627()` | `gic_arm64_2941627_erratum` | `gic_arm64_erratum_2941627_needed()` |
| `rd_set_non_coherent()` | `RDIST_FLAGS_FORCE_NON_SHAREABLE` | `rdists_support_shareable()` in the ITS driver |
| `gic_enable_quirk_rk3399()` | `FLAGS_WORKAROUND_INSECURE`, only on machine `rockchip,rk3399`, else returns false | `gic_prio_init()` |

- `gic_enable_quirk_nvidia_t241()`: also needs
  `arm_smccc_get_soc_id_version()` to match and at least three chips in the
  redistributor addresses, else returns false.
- Erratum 2941627 with `gic_chip`: `gic_eoi_irq()` still writes
  `ICC_EOIR1_EL1`, then also `GICD_ICACTIVER`; only
  `gic_eoimode1_eoi_irq()` replaces `gic_write_dir()` with
  `GICD_ICACTIVER`.
- `its_quirks`, in `drivers/irqchip/irq-gic-v3-its.c`:

| `init` | Sets | Effect where tested |
|---|---|---|
| `its_enable_quirk_cavium_22375()` | `ITS_FLAGS_WORKAROUND_CAVIUM_22375`, DEVBITS in `its->typer` | `its_alloc_tables()` uses `GITS_BASER_nCnB` |
| `its_enable_quirk_cavium_23144()` | `ITS_FLAGS_WORKAROUND_CAVIUM_23144` | `its_select_cpu()`, `its_cpu_init_collection()` stay on the ITS node |
| `its_enable_quirk_qdf2400_e0065()` | ITT entry size in `its->typer`, no flag | — |
| `its_enable_quirk_socionext_synquacer()` | `pre_its_base`, `get_msi_base`, no flag | clears `IRQ_DOMAIN_FLAG_ISOLATED_MSI` |
| `its_enable_quirk_hip07_161600802()` | `vlpi_redist_offset`, no flag | added to the VMAPP and VMOVP target |
| `its_enable_quirk_hip09_162100801()` | `ITS_FLAGS_WORKAROUND_HISILICON_162100801` | `its_vpe_set_affinity()` invalidates after `its_send_vmovp()` |
| `its_enable_rk3588001()` | `ITS_FLAGS_FORCE_NON_SHAREABLE` and `RDIST_FLAGS_FORCE_NON_SHAREABLE`, only on machine `rockchip,rk3588` or `rockchip,rk3588s`, else returns false | `its_alloc_tables()`, `its_probe_one()` |
| `its_set_non_coherent()` | `ITS_FLAGS_FORCE_NON_SHAREABLE` only | `its_alloc_tables()`, `its_probe_one()` |
| `its_enable_dma32()` | `GFP_DMA32` in `gfp_flags_quirk`, only on a machine in `dma_32bit_impaired_platforms`, else returns false | `its_alloc_pages_node()` |

- `its_enable_quirk_socionext_synquacer()`: returns false without the
  `socionext,synquacer-pre-its` property.
- `its_enable_dma32()`: its table entry has no `#ifdef`; the platforms in
  `dma_32bit_impaired_platforms` are under
  `CONFIG_RENESAS_ERRATUM_GEN4GICITS1` and
  `CONFIG_ROCKCHIP_ERRATUM_3568002`.

## Register writes and priorities

**Completing a register write**

- `GICR_CTLR_RWP`: bit 3 of `GICR_CTLR`; `GICD_CTLR_RWP`: bit 31 of
  `GICD_CTLR`; both in `include/linux/irqchip/arm-gic-v3.h`.
- `gic_do_wait_for_rwp()`: returns `void`; it uses
  `readl_relaxed_poll_timeout_atomic()` and only prints on `-ETIMEDOUT`.
- `gic_redist_wait_for_rwp()`: polls one frame, the calling CPU's
  (`gic_data_rdist()` is `this_cpu_ptr()`), not every redistributor.
- Waits in `drivers/irqchip/irq-gic-v3.c`: after the enable-clear write in
  `gic_mask_irq()`, after each `GICD_CTLR` write in `gic_dist_init()`, and
  after `gic_cpu_config()` in `gic_cpu_init()`; no other write is followed by
  one.
- `gic_set_affinity()`: waits only inside `gic_mask_irq()`, and only when the
  interrupt was enabled; nothing waits after the `GICD_IROUTER` write, although
  the comment before its `gic_unmask_irq()` call speaks of waiting.
- `redist_disable_lpis()` in `drivers/irqchip/irq-gic-v3-its.c`: has its own
  loop on `GICR_CTLR_RWP` and, unlike the helpers above, returns `-ETIMEDOUT`.
- **Potentially unsafe usage**: `gic_redist_wait_for_rwp()` after a
  redistributor write.
  - Unsafe: when the write went to another CPU's frame, or the task can
    migrate between write and wait; the poll then reads a frame that was not
    written and can return at once.
  - Safe: write through `gic_data_rdist_sgi_base()` and wait on the same CPU
    without migration, as `gic_cpu_init()` does from `gic_starting_cpu()`; the
    `this_cpu_ptr()` in `gic_data_rdist()` defines the requirement.

**Pending and active state**

- ID test: `d->hwirq >= 8192` is the only one, in both
  `gic_irq_set_irqchip_state()` and `gic_irq_get_irqchip_state()`; SGIs pass
  it, for every state.
- Comments beside the test ("SGI/PPI/SPI only", "PPI/SPI only"): narrower
  than the test; EPPI and ESPI pass too.
- Error code: `-EINVAL` is the only one, for an LPI and for an unknown
  `which`.
- Read-back: only after a write of `GICD_ISACTIVER` (set active), by
  `gic_peek_irq()` on the same register; not after `GICD_ICACTIVER` or a
  pending write.
- Reason given in the comment in `gic_irq_set_irqchip_state()`: the active
  state must have taken effect so that it cannot race with a guest-driven
  deactivation.
- Redistributor interrupt (`gic_irq_in_rdist()`): `gic_peek_irq()` and
  `gic_poke_irq()` use `gic_data_rdist_sgi_base()`, so state is read and
  written for the calling CPU only.
- LPI set, for a device LPI (`its_irq_chip`): handled by
  `its_irq_set_irqchip_state()` in `drivers/irqchip/irq-gic-v3-its.c`, which
  accepts only `IRQCHIP_STATE_PENDING`.
- LPI get: `its_irq_chip` has no `irq_get_irqchip_state`, so
  `__irq_get_irqchip_state()` walks to the parent and
  `gic_irq_get_irqchip_state()` returns `-EINVAL`.

**Distributor and PMR priority views**

- Views differ in one case only: `GICD_CTLR_DS` clear and Group 0 visible to
  the kernel (SCR_EL3.FIQ clear); with DS clear and no Group 0 both views are
  shifted alike and need no compensation.
- `gic_has_group0()`: probes through the PMR (write, read back, restore),
  with `gic_get_pribits()` for the value written; it does not access
  `GICD_CTLR`.
- Results: kept in `cpus_have_group0` and `cpus_have_security_disabled`; there
  is no gic_nonsecure_priorities static key in this tree.
- `dist_prio_irq` and `dist_prio_nmi`: start as `GICV3_PRIO_IRQ` and
  `GICV3_PRIO_NMI`; `gic_prio_init()` replaces them with
  `__gicv3_prio_to_ns()` of themselves when
  `cpus_have_group0 && !cpus_have_security_disabled`.
- The shift does not depend on pseudo-NMI support: `gic_prio_init()` runs
  before `gic_enable_nmi_support()` and tests neither
  `gic_prio_masking_enabled()` nor `gic_supports_nmi()`.
- `FLAGS_WORKAROUND_INSECURE` with DS clear and Group 0: `gic_prio_init()`
  sets `GICD_CTLR_DS`, then re-reads it; the re-read value decides whether the
  shift is applied.

**Making an interrupt a pseudo-NMI**

- No refcounts: there is no ppi_nmi_refs or rdist_nmi_refs in this tree, and
  `gic_enable_nmi_support()` allocates nothing.
- No per-CPU NMI flow handler: there is no handle_percpu_devid_fasteoi_nmi
  in this tree; `handle_percpu_devid_irq()` in `kernel/irq/chip.c` serves both
  IRQ and NMI context.

| Interrupt | `gic_irq_nmi_setup()` | `gic_irq_nmi_teardown()` |
|---|---|---|
| `gic_irq_in_rdist()` (SGI, PPI, EPPI) | priority byte of the calling CPU's frame set to `dist_prio_nmi`; `desc->handle_irq` untouched | priority byte set to `dist_prio_irq`; `desc->handle_irq` untouched |
| SPI, ESPI | `desc->handle_irq = handle_fasteoi_nmi`, then `dist_prio_nmi` in the distributor | `desc->handle_irq = handle_fasteoi_irq`, then `dist_prio_irq` |

- Redistributor interrupt: the enabled test and the priority write both act
  on the calling CPU's frame, so a CPU that has not run
  `prepare_percpu_nmi()` keeps `dist_prio_irq` for that interrupt.
- `gic_irq_nmi_teardown()`: returns `void`; on each failed check it returns
  early and leaves handler and priority unchanged.
- `gic_irq_nmi_teardown()` with `!gic_supports_nmi()`: `WARN_ON()`;
  `gic_irq_nmi_setup()` returns `-EINVAL` silently for the same test.
- The driver sets no NMI flag on the interrupt; `IRQS_NMI` in `desc->istate`
  is set by `request_nmi()` and `request_percpu_nmi()` in
  `kernel/irq/manage.c`.
- Forbidding: `gic_enable_nmi_support()` returns early on
  `!gic_prio_masking_enabled()` or `nmi_support_forbidden`; it tests nothing
  else (no priority-bit count, no hypervisor test).
- `nmi_support_forbidden`: set only in `gic_prio_init()`, when
  `FLAGS_WORKAROUND_INSECURE` is set, DS is clear and `gic_has_group0()` is
  false; `gic_enable_quirk_rk3399()` sets `FLAGS_WORKAROUND_INSECURE`.
- MediaTek "mediatek,broken-save-restore-fw": not a driver quirk; there is no
  FLAGS_WORKAROUND_MTK_GICR_SAVE; `detect_system_supports_pseudo_nmi()` in
  `arch/arm64/kernel/cpufeature.c` clears `enable_pseudo_nmi`, so
  `gic_prio_masking_enabled()` is false.
- `nmi_support_forbidden` leaves priority masking on: only
  `supports_pseudo_nmis` and `IRQCHIP_SUPPORTS_NMI` stay off, so
  `request_nmi()` fails at `irq_supports_nmi()`.

**Interrupt entry with pseudo-NMIs**

- Selection: `gic_handle_irq()` runs `__gic_handle_irq_from_irqsoff()` when
  `gic_supports_nmi() && !interrupts_enabled(regs)`, otherwise
  `__gic_handle_irq_from_irqson()`.
- `interrupts_enabled()` in `arch/arm64/include/asm/ptrace.h`: false when
  `PSR_I_BIT` is set in the saved pstate or, with
  `system_uses_irq_prio_masking()`, the saved `pmr` is not exactly
  `GIC_PRIO_IRQON`.

| Path | NMI decision | PMR around the acknowledge |
|---|---|---|
| `__gic_handle_irq_from_irqson()` | `gic_rpr_is_nmi_prio()` after the IAR read | untouched before; `gic_unmask_pnmis()` afterwards |
| `__gic_handle_irq_from_irqsoff()` | none; RPR is not read, the result always goes to `__gic_handle_nmi()` | saved, `gic_pmr_mask_irqs()`, `isb()`, IAR read, saved value written back |

- There is no gic_arch_enable_irqs() in this tree; `gic_unmask_pnmis()` in
  `arch/arm64/include/asm/arch_gicv3.h` writes `GIC_PRIO_IRQOFF` to the PMR
  and clears DAIF.I and DAIF.F.
- `gic_unmask_pnmis()`: tests `gic_prio_masking_enabled()`, not
  `gic_supports_nmi()`, so it also runs when NMIs are forbidden; it is an
  empty stub in `arch/arm/include/asm/arch_gicv3.h`.
- `gic_unmask_pnmis()` in the irqson path: runs in both cases, after
  `nmi_exit()` for an NMI and before `__gic_handle_irq()` for a regular
  interrupt.
- Special IDs in the irqson path: `gic_rpr_is_nmi_prio()` and
  `gic_unmask_pnmis()` run before `gic_irqnr_is_special()` is tested inside
  `__gic_handle_irq()`.

**After the acknowledge**

- Regular interrupt in `__gic_handle_irq_from_irqson()`: `gic_unmask_pnmis()`
  runs between `gic_read_iar()` and `gic_complete_ack()`, so with
  `gic_prio_masking_enabled()` a pseudo-NMI can be taken before the priority
  drop and the `isb()`.
- `__gic_handle_irq_from_irqsoff()`: writes the saved PMR back between
  `gic_read_iar()` and `gic_complete_ack()`; it does not touch DAIF.
- `gic_complete_ack()`: the one step that `__gic_handle_irq()` and
  `__gic_handle_nmi()` run between the `gic_irqnr_is_special()` test and
  `generic_handle_domain_irq()` or `generic_handle_domain_nmi()`.
- **Unsafe usage**: reading `ICC_RPR_EL1` to classify the interrupt after
  `gic_complete_ack()`; with `supports_deactivate_key` the EOIR write has
  already dropped the running priority.
  - Safe: read it after `gic_read_iar()` and before `gic_complete_ack()`, as
    `__gic_handle_irq_from_irqson()` does with `gic_rpr_is_nmi_prio()`.
- `gic_deactivate_unhandled()` with `supports_deactivate_key`: writes DIR
  only, through `gic_write_dir()`, and only for `irqnr < 8192`; it does not
  write EOIR again.
- `gic_deactivate_unhandled()` without `supports_deactivate_key`: writes
  `ICC_EOIR1_EL1`, then `isb()`.
- Non-zero return from the handler call: `-EINVAL` from `handle_irq_desc()`
  in `kernel/irq/irqdesc.c` for no mapping; it gets the `WARN_ONCE` and
  `gic_deactivate_unhandled()`.
- Names: `gic_write_eoir` is only a member of `struct gic_common_ops` in the
  KVM selftests, not a kernel function, and there is no ARCH_GICV3_SPECIAL;
  the driver uses `write_gicreg()` on `ICC_EOIR1_EL1` and
  `gic_irqnr_is_special()`.
- `gic_read_iar_common()` in `arch/arm64/include/asm/arch_gicv3.h`: always
  issues `dsb(sy)` after the IAR read; it is not an erratum workaround.
- `gic_read_iar_cavium_thunderx()`: used under
  `ARM64_WORKAROUND_CAVIUM_23154`; returns 0x3ff when `ICC_AP1R0_EL1` did not
  change across the IAR read.

**Priority constants and variables**

- PMR values: `GIC_PRIO_IRQON` is `GICV3_PRIO_UNMASKED` (IRQs enabled),
  `GIC_PRIO_IRQOFF` is `GICV3_PRIO_IRQ` (IRQs masked, NMIs pass); see
  `arch/arm64/include/asm/ptrace.h`.
- The flag is named `GICV3_PRIO_PSR_I_SET`; there is no GICV3_PRIO_PSR_I.
- `dist_prio_irq` and `dist_prio_nmi`: `static` in
  `drivers/irqchip/irq-gic-v3.c`, so no other file can use them.
- LPIs: `gic_init_bases()` passes `dist_prio_irq` to `its_init()`, which
  stores it in `lpi_prop_prio` in `drivers/irqchip/irq-gic-v3-its.c`; ITS code
  uses that variable for the property table.
- `irqs_priority_unmasked()`: with `system_uses_irq_prio_masking()`, compares
  the saved PMR for equality with `GIC_PRIO_IRQON`, so
  `GIC_PRIO_IRQON | GIC_PRIO_PSR_I_SET` counts as masked.

| `static_assert()` | Holds exactly when | Code that relies on it |
|---|---|---|
| `__gicv3_prio_valid_ns()` of `GICV3_PRIO_NMI` and of `GICV3_PRIO_IRQ` | bit 7 of the constant is set | `gic_prio_init()`: the left-shifted value, once the GIC shifts it right and sets bit 7, is the constant again |
| `GICV3_PRIO_NMI < GICV3_PRIO_IRQ` | as written | `gic_pmr_mask_irqs()`: PMR at `GIC_PRIO_IRQOFF` masks IRQs and passes NMIs |
| `GICV3_PRIO_IRQ < GICV3_PRIO_UNMASKED` | as written | PMR at `GIC_PRIO_IRQON` admits IRQs |
| `GICV3_PRIO_IRQ < (GICV3_PRIO_IRQ \| GICV3_PRIO_PSR_I_SET)` | bit 4 of `GICV3_PRIO_IRQ` is clear | `local_daif_mask()`: its debug `WARN_ON()` compares the PMR with `GIC_PRIO_IRQOFF \| GIC_PRIO_PSR_I_SET`, which must differ from `GIC_PRIO_IRQOFF` |

- Not asserted: the order of the shifted values, and the round trip of
  `GICV3_PRIO_UNMASKED`, which is never written to a distributor or
  redistributor.

**What the architecture specification says**

From the Arm Generic Interrupt Controller Architecture Specification, GICv3
and GICv4 (ARM IHI 0069), and what each statement means for this code. A
kernel tree cannot supply these, so they are kept by hand and inserted as
they are.

*   **The specification's negative is stronger for the Distributor than for the
    Redistributor, and a review should not over-claim.** `GICD_CTLR.RWP`'s
    description ends with an explicit exclusion clause: "Updates to other
    register fields are not tracked by this field." `GICR_CTLR.RWP`'s
    description has no equivalent sentence — it gives only the enumeration of
    what it does track. So on the redistributor side the correct argument is
    that the enumeration is exhaustive and does not include the active or
    pending registers, not that the specification states an exclusion. If a
    patch or a review comment claims a quoted exclusion clause for
    `GICR_CTLR.RWP`, it is quoting something that is not there.

*   **The Redistributor RWP list has a GICv4.1-only member.** Alongside
    `GICR_ICENABLER0`, the `GICR_CTLR` DPG fields and the `EnableLPIs` 1-to-0
    transition, it covers "In FEAT_GICv4p1, GICR_VPROPBASER, which clears Valid
    from 1 to 0". A GICv4.1 path that clears `GICR_VPROPBASER.Valid` and
    proceeds without the RWP poll is missing a completion the architecture
    provides.

*   **The software-generated interrupt ID field is four bits.** The
    architecture defines "INTID, bits [27:24] — The INTID of the SGI", and the
    driver's mask is correspondingly `0xf` shifted to bit 24. A wider mask, or a
    signed one, lets an out-of-range value through — which matters most in the
    KVM emulation of the register, where the value is guest-supplied.

## CPU bring-up and IPIs

**Per-CPU initialisation**

- `gic_cpu_sys_reg_init()`: `gic_get_pribits()` and `gic_has_group0()` run
  first, before the PMR write; `gic_write_bpr1(0)` sits between the PMR step
  and `gic_write_ctlr()`.
- `ICC_PMR_EL1` with `gic_prio_masking_enabled()` true: not written by
  `gic_cpu_sys_reg_init()`, apart from the probe-and-restore in
  `gic_has_group0()`.
  - It relies on `init_gic_priority_masking()` in `arch/arm64/kernel/smp.c`.
  - That runs in `secondary_start_kernel()` before `notify_cpu_starting()`,
    and in `smp_prepare_boot_cpu()`.
- Pseudo-NMI consistency check: compares this CPU with `cpus_have_group0` and
  `cpus_have_security_disabled`, which `gic_prio_init()` sets once on the boot
  CPU.
  - It runs only when `gic_supports_nmi()` is true.
  - A mismatch is a `WARN_ON()` and nothing more.
- `gic_cpu_config()` in `drivers/irqchip/irq-gic-common.c`: only writes; the
  wait is the `gic_redist_wait_for_rwp()` call that follows it in
  `gic_cpu_init()`.
- Boot-only inputs that every later `gic_cpu_init()` reads: `dist_prio_irq`
  (final after `gic_prio_init()`) and `gic_data.ppi_nr` (from
  `gic_update_rdist_properties()`); `gic_init_bases()` calls both first.
- SGI reachability check failing: `pr_crit()` for each CPU pair, and
  `pr_crit_once()` when RSS is needed and `gic_data.has_rss` is false.
  - There is no `WARN()`, no return value and no state change.
  - Per-CPU `has_rss` is read nowhere else; `gic_ipi_send_mask()` sends
    without consulting it.

**Enabling system register access**

- `gic_cpu_sys_reg_init()` and `gic_cpu_init()`: do not call
  `gic_cpu_sys_reg_enable()`.
  - Its callers are `gic_init_bases()`, `gic_starting_cpu()` and
    `gic_cpu_pm_notifier()` (exit path only), each before the other `ICC_*`
    accesses of that path.
  - `CPU_PM_ENTER` writes `gic_write_grpen1(0)` without calling it.
- `gic_enable_sre()`: defined in `include/linux/irqchip/arm-gic-v3.h`, not in
  the arch headers.
  - It touches only the EL1 register, through `gic_read_sre()` and
    `gic_write_sre()`; it writes nothing at EL2.
  - The `isb()` is inside `gic_write_sre()` in
    `arch/arm64/include/asm/arch_gicv3.h`.
  - It returns `true` without writing when `ICC_SRE_EL1_SRE` is already set.
- `gic_cpu_sys_reg_enable()` when the bit does not stick: `pr_err()` only.
  - It is void, and all three callers go on to the next step; there is no
    explicit panic or error return.
- Arch code calls `gic_enable_sre()` directly as well, so the driver is not
  the only place it happens:
  - `has_useable_gicv3_cpuif()` in `arch/arm64/kernel/cpufeature.c`:
    `pr_warn_once()` and the capability is reported absent.
  - `init_gic_priority_masking()` in `arch/arm64/kernel/smp.c`: `WARN_ON()`
    and returns without setting PMR.
- `gic_cpu_pm_notifier()`: saves nothing; no register is read into memory.
- `CPU_PM_ENTER_FAILED`: handled exactly as `CPU_PM_EXIT`.
- `gic_enable_redist()` in the notifier: called only when
  `gic_dist_security_disabled()` is true, on entry and on exit.
  - With security enabled, `CPU_PM_ENTER` does nothing at all, including no
    `gic_write_grpen1(0)`.
- On exit, besides that conditional `gic_enable_redist()`, the notifier redoes
  only `gic_cpu_sys_reg_enable()` and `gic_cpu_sys_reg_init()`.
  - It does not call `gic_populate_rdist()` or `gic_cpu_config()`; SGI/PPI
    group, priority and enable state in the redistributor is not rewritten.

**Sending an IPI**

- `gic_smp_init()`: passes a literal 8 to `irq_domain_alloc_irqs()` and to
  `set_smp_ipi_range()`; the count is not derived from `NR_IPI` or `MAX_IPI`.
- `set_smp_ipi_range()` on arm64: an inline wrapper in
  `arch/arm64/include/asm/smp.h` for `set_smp_ipi_range_percpu()` with
  `ncpus` 0.
- No headroom: `set_smp_ipi_range_percpu()` does `WARN_ON(n < MAX_IPI)` and
  sets `nr_ipi` to `min(n, MAX_IPI)`.
  - `MAX_IPI` is 8 on arm64 (`enum ipi_msg_type` in
    `arch/arm64/include/asm/smp.h`) and 8 on arm (`arch/arm/kernel/smp.c`).
  - A ninth entry in `enum ipi_msg_type` trips the `WARN_ON()` and gets no
    interrupt.
- `IPI_CPU_BACKTRACE` and `IPI_KGDB_ROUNDUP`: NMIs only when
  `ipi_should_be_nmi()` returns true, which needs
  `system_uses_irq_prio_masking()`.
  - Otherwise `ipi_setup_sgi()` requests them as ordinary per-CPU IRQs.
- RS field: there is no MPIDR_TO_SGI_RS_VALUE here; `MPIDR_TO_SGI_RS()` in
  `drivers/irqchip/irq-gic-v3.c` does that.
- The driver's own limit is 16, not 8, everywhere except `gic_smp_init()`:
  - `SGI_NR` sizes the group and priority setup in `gic_cpu_init()`.
  - `gic_irq_domain_translate()` accepts any one-cell fwspec below 16.
  - `gic_ipi_send_mask()` rejects only `d->hwirq >= 16`.
- `gic_send_sgi()`: shifts `irq` into place without masking it; the
  `WARN_ON()` in `gic_ipi_send_mask()` is the only range check.

**CPU hotplug callbacks**

- `gic_check_rdist()` (`CPUHP_BP_PREPARE_DYN`): returns `-EINVAL` when the
  CPU is in `broken_rdists`, and tests nothing else.
  - Only `gic_acpi_parse_madt_gicc()` sets bits in `broken_rdists`, for a GICC
    entry with `ACPI_MADT_GICC_ONLINE_CAPABLE` and without
    `ACPI_MADT_ENABLED`.
  - It does not look for the redistributor; a CPU for which
    `gic_populate_rdist()` later finds none passes this check.
- `gic_starting_cpu()`: always returns 0 and drops the return value of
  `its_cpu_init()`, which can be an error from `redist_disable_lpis()`.
- A STARTING callback that returns non-zero: `notify_cpu_starting()` uses
  `cpuhp_invoke_callback_range_nofail()`, which only does `pr_warn()` and
  continues.
- `its_cpu_memreserve_lpi()`: allocates no pending table.
  - Its only error is `-ENOMEM`, when `pend_page` is NULL.
  - A `gic_reserve_range()` failure is a `WARN_ON()` and is not returned.
  - `RD_LOCAL_MEMRESERVE_DONE` is set on the failing path too, so a second
    run on that CPU returns 0.
- First run of `its_cpu_memreserve_lpi()`: on the boot CPU, as a direct call
  from `cpuhp_setup_state()` in `its_lpi_memreserve_init()`.
  - That is inside `init_IRQ()`, before `start_kernel()` enables interrupts.
  - Later CPUs run it in the `CPUHP_AP_ONLINE_DYN` state.
- **Potentially unsafe usage**: allocating memory in code reached from
  `gic_starting_cpu()`.
  - Unsafe: with a gfp mask that allows blocking, such as `GFP_KERNEL`;
    `secondary_start_kernel()` has not yet unmasked interrupts, and
    `might_alloc()` does `might_sleep_if()` on such a mask.
  - Unsafe: under `CONFIG_PREEMPT_RT` with any mask, when the allocation can
    reach the page allocator; `zone->lock` is a `spinlock_t`, which sleeps
    there.
  - Unsafe: when the only report of failure is the callback's return value;
    nothing acts on it.
  - Safe: without `CONFIG_PREEMPT_RT`, `GFP_ATOMIC` with the failure handled
    in place, as `allocate_vpe_l1_table()` does; its caller
    `its_cpu_init_lpis()` clears `has_rvpeid` and `has_vlpis` on failure.
  - Safe: allocating for every possible CPU on the boot CPU, as
    `allocate_lpi_tables()` does from `its_init()` with `GFP_NOWAIT`;
    `its_cpu_init_lpis()` then only programs `pend_page`.
  - Safe: deferring to the `CPUHP_AP_ONLINE_DYN` callback, which a secondary
    CPU runs in `cpuhp_thread_fun()` with interrupts on, as
    `its_cpu_memreserve_lpi()` does for `gic_reserve_range()`, which reaches
    `memremap()` through `efi_mem_reserve_persistent()`.

## The ITS command queue

**ITS locks**

- `struct its_node` has two locks: `lock` (`raw_spinlock_t`) and
  `dev_alloc_lock` (`struct mutex`).
- `its_lock` in `drivers/irqchip/irq-gic-v3-its.c` is a file-scope raw
  spinlock, not a field of `struct its_node` and not a mutex.
- `cmd_lock` is a field of KVM's `struct vgic_its` in
  `include/kvm/arm_vgic.h`, not of `struct its_node`; there is no
  its_dev_lock in this tree.
- `lock` covers both the command queue (`cmd_write`, the slots,
  `GITS_CWRITER`) and `its_device_list`; there is no separate device-list
  lock.
- `dev_alloc_lock` is the only lock in the node that may be held across a
  sleep.
- `dev_alloc_lock` is taken in `its_msi_prepare()` and `its_msi_teardown()`
  of `drivers/irqchip/irq-gic-v3-its.c`.
- `its_irq_domain_free()` takes neither lock of the node.
- `its_init_vpe_domain()` calls `its_create_device()` for the proxy device
  without `dev_alloc_lock`.
- `its_restore_enable()` resets `cmd_write` and `GITS_CWRITER` holding only
  `its_lock`, not `lock`.
- `its_nodes` links nodes through the `entry` field.
- `its_lock` is taken in `its_probe_one()`, `its_cpu_init_collections()`,
  `its_save_disable()` and `its_restore_enable()`.
- Other walks of `its_nodes` do not take `its_lock`, for example
  `its_send_vmovp()`, `get_its_list()` and `its_alloc_vpe_table()`.
- `its_nodes` only grows: `its_probe_one()` holds the only `list_add()` to
  it, and nothing unlinks a node.
- `vmovp_lock` is a file-scope raw spinlock, taken only in
  `its_send_vmovp()` and only when `its_list_map` is non-zero.
- `lock` is the innermost lock: commands are sent with `its_lock`,
  `vmovp_lock`, `vpe_lock` or `vmapp_lock` held.

**Sending one command**

- `its_send_single_command()` and `its_send_single_vcommand()` are both
  instances of `BUILD_SINGLE_CMD_FUNC`; there is no BUILD_SINGLE_VCMD_FUNC
  macro.
- `GITS_CREADR` is read into `rd_idx` under `its->lock`, after the last
  `its_flush_cmd()` and immediately before `its_post_commands()`.
- `its_allocate_entry()` on a full queue: spins 1000000 times with
  `udelay(1)`, about 1 s, with `its->lock` held and IRQs off, then returns
  NULL.
- Sync slot allocation fails: the macro jumps to `post`, so the main command
  is still posted and waited for, with no SYNC or VSYNC after it.

**Publishing a command**

- `ITS_FLAGS_CMDQ_NEEDS_FLUSHING` set: `its_flush_cmd()` calls
  `gic_flush_dcache_to_poc()` on the block; clear: `dsb(ishst)` only.
- The flag comes only from the `GITS_CBASER` write and read-back in
  `its_probe_one()`; `GITS_TYPER` plays no part.
- `RDIST_FLAGS_FORCE_NON_SHAREABLE` is not tested for the command queue.
- `ITS_FLAGS_FORCE_NON_SHAREABLE` is set before the comparison of the
  `GITS_CBASER` read-back with the value written (what it does to that
  comparison is in "Non-coherent GICs"), either by an `its_quirks` entry or
  by `gic_acpi_parse_madt_its()`.
  - `its_enable_quirks()` runs first in `its_probe_one()`; the entries are
    `its_enable_rk3588001()` and the "dma-noncoherent" property.
  - `gic_acpi_parse_madt_its()` sets it from `ACPI_MADT_ITS_NON_COHERENT`,
    only when `acpi_get_madt_revision() >= 7`, before it calls
    `its_probe_one()`.

**Waiting for a command**

- `prev_idx` is the sender's raw read of `GITS_CREADR`, taken after the
  commands are built and flushed; it is not derived from the slot that
  `its_allocate_entry()` returned.
- Wrap-around: each poll adds the read pointer's advance since the previous
  poll to `linear_idx`, plus `ITS_CMD_QUEUE_SZ` when the pointer went
  backwards.
- The wait ends when `linear_idx >= to_idx`, not when the read pointer
  leaves a range.
- Timeout: `its_wait_for_range_completion()` returns -1 after printing
  "ITS queue timeout"; `BUILD_SINGLE_CMD_FUNC` then prints "ITS cmd %ps
  failed" and returns `void`.
- `GITS_CREADR` is used unmasked and no stall or error bit is tested, so a
  stalled ITS shows up only as a timeout, here or in
  `its_allocate_entry()`.

**Command builders**

- `its_fixup_cmd()` only stores the four words through `cpu_to_le64()`;
  cache maintenance is `its_flush_cmd()`, called by the sender.
- `its_build_sync_cmd()` and `its_build_vsync_cmd()` return `void`; they are
  of neither builder type.
- `its_build_mapd_cmd()` is the only builder that always returns NULL.
- `its_build_invall_cmd()` returns `desc->its_invall_cmd.col`, so a SYNC
  follows INVALL.
- `its_build_mapc_cmd()` and `its_build_invall_cmd()` return the
  descriptor's collection directly, without `valid_col()`.
- NULL that depends on the hardware:

| Builder | Returns NULL when |
|---|---|
| `its_build_vmapp_cmd()` | unmap on an ITS where `is_v4_1(its)` |
| `its_build_invdb_cmd()` | `WARN_ON(!is_v4_1(its))` fires |
| `its_build_vsgi_cmd()` | `WARN_ON(!is_v4_1(its))` fires |

- `its_build_invdb_cmd()` and `its_build_vsgi_cmd()` on that `WARN_ON()`
  path return before encoding anything and before `its_fixup_cmd()`; the
  sender still flushes and posts the all-zero slot.
- Every other builder returns NULL only when `valid_col()` or `valid_vpe()`
  rejects the target.
- `valid_col()` rejects a collection whose `target_address`
  `its_cpu_init_collection()` has not written: `its_alloc_collections()`
  presets `target_address` to `~0ULL`.
- `valid_col()` or `valid_vpe()` returning NULL drops only the sync; the
  command itself is still posted.
- There is no MOVALL builder; `GITS_CMD_MOVALL` is used only by
  `arch/arm64/kvm/vgic/vgic-its.c`.

**Synchronisation commands**

- `its_build_movi_cmd()` syncs against the collection the event is leaving
  (from `dev_event_to_col()`), not the destination it encodes.
- `its_set_affinity()` updates `col_map` only after `its_send_movi()`
  returns, so the builder still reads the old collection.
- `direct_lpi_inv()` is a redistributor write; it queues no ITS command.

**Unmapping a vPE**

- `its_build_vmapp_cmd()` computes `valid_vpe()` once at entry; that value
  is returned for a map on either version and for an unmap on GICv4.0.
- Only the unmap branch under `is_v4_1(its)` overwrites it with NULL.
- The version test is per ITS: `is_v4_1(its)` checks `GITS_TYPER_VMAPP` in
  the `typer` of the ITS receiving the command, not
  `gic_rdists->has_rvpeid`.
- On GICv4.0 the VSYNC after an unmap is still skipped when `valid_vpe()`
  returns NULL.

**Adding a command path**

- **Unsafe usage**: calling a send function with `lock` of the same
  `struct its_node` held.
  - Unsafe: `BUILD_SINGLE_CMD_FUNC` takes `its->lock` with
    `raw_spin_lock_irqsave()`, so the call deadlocks.
  - Safe: drop `lock` first, as `its_create_device()` does between its
    `list_add()` and `its_send_mapd()`.
  - Safe: sending with other raw spinlocks held or IRQs off; the path only
    spins with `udelay()`. `its_send_vmovp()` sends under `vmovp_lock`.
- **Potentially unsafe usage**: returning from a builder without calling
  `its_fixup_cmd()`.
  - Unsafe: once an encode helper such as `its_encode_cmd()` has written
    the block; on a big-endian kernel the words stay in CPU byte order.
  - Safe: only as a `WARN_ON()` guard before anything is encoded, for a
    state callers exclude, because the zeroed slot is still posted.
    `its_build_invdb_cmd()` does this; its caller takes the ITS from
    `find_4_1_its()`.
  - Safe: reach one common `its_fixup_cmd()` through `goto out`, as
    `its_build_vmapp_cmd()` does.
- **Potentially unsafe usage**: returning a collection as the sync object
  without `valid_col()`.
  - Unsafe: when `its_cpu_init_collection()` may not have written the
    collection's `target_address`; `its_build_sync_cmd()` then encodes the
    `~0ULL` preset by `its_alloc_collections()`.
  - Safe: when the caller has just written `target_address`, as for
    `its_build_mapc_cmd()` and `its_build_invall_cmd()`, reached only from
    `its_cpu_init_collection()`.
- **Unsafe usage**: a builder reading a `struct its_cmd_desc` member that
  the sender did not set.
  - Unsafe: senders declare the descriptor on the stack without an
    initialiser, so the builder encodes stack garbage.
  - Safe: set every member the builder reads, as `its_send_vmapp()` does.
  - Safe: zero the descriptor with `desc = {}`, as `its_send_vmovp()` does
    for `seq_num` and `its_list` on its single-ITS path.
- Builders read live driver state, not only the descriptor:
  `dev_event_to_col()` reads `col_map`, and `valid_vpe()` reads
  `vpe->col_idx`.
- `col_map` ordering around a send: `its_irq_domain_activate()` writes it
  before `its_send_mapti()`; `its_set_affinity()` writes it after
  `its_send_movi()`.

**What the architecture specification says**

From the Arm Generic Interrupt Controller Architecture Specification, GICv3
and GICv4 (ARM IHI 0069), and what each statement means for this code. A
kernel tree cannot supply these, so they are kept by hand and inserted as
they are.

*   **That ordering requirement comes from the base architecture, not from the
    GIC specification.** IHI 0069 contains no sentence requiring a barrier or
    cache maintenance on the queue before `GITS_CWRITER` is written; the GIC
    specification defers explicitly, saying "For more information on
    endianness, memory ordering, and barrier instructions, see Arm®
    Architecture Reference Manual for A-profile architecture". Do not ask a
    patch to cite a GIC-specification rule for this, and do not treat the
    absence of such a citation as evidence the barrier is unnecessary.

*   **The analogous requirement that *is* in the GIC specification concerns the
    ITS tables, not the queue.** For a two-level table, "A write to a level 1
    table entry that changes the valid bit from 0 to 1 must be globally visible
    before software adds a command to the ITS command queue that relies on that
    entry. Otherwise it is UNKNOWN if the command will succeed or if it will be
    ignored." A patch that publishes a new level 2 table and immediately queues
    a command referencing it needs that visibility, and this one you can cite.

*   **A command error has three architecturally permitted outcomes and software
    may assume none of them.** The specification states that "If the ITS
    detects an error in the data provided to a command, the resulting behavior
    is a CONSTRAINED UNPREDICTABLE choice of: • Ignoring the command ... •
    Stalling the ITS command queue ... • Treating the data as valid data". Code
    or a commit message that reasons "the ITS will just ignore the bad command"
    is relying on one arm of a CONSTRAINED UNPREDICTABLE choice.

*   **A `GITS_CWRITER` value outside the range implied by `GITS_CBASER` is a
    separate failure mode.** Behavior is a CONSTRAINED UNPREDICTABLE choice
    between treating the command queue as invalid until a valid value is
    written, and treating the value as valid and UNKNOWN. Validate the offset
    before forwarding a value that did not come from the driver's own ring
    arithmetic.

*   **Without one of the two, no ordering exists at all.** "In the absence of a
    SYNC or VSYNC command the ordering of ITS commands and translation requests
    is not defined by the architecture." There is no weaker in-between
    guarantee to rely on.

*   **On GICv4.1, unmapping a vPE is self-synchronizing and must not be
    followed by a VSYNC.** The specification states that "A VMAPP with {V,
    Alloc}=={0, x} is self-synchronizing. This means the ITS command queue does
    not show the command as consumed until all of its effects are completed."
    A VSYNC after it would name a vPE that no longer exists, which is a command
    error; the architected error code is `VSYNC_VCPU_INVALID`, and where
    `GITS_TYPER.SEIS` is 1 the implementation may report it as a System error.
    `its_build_vmapp_cmd()` implements this by setting its returned vPE to
    `NULL` on the unmap path, with the comment "Unmapping a VPE is
    self-synchronizing on GICv4.1, no need to issue a VSYNC".

*   **INVALL is completed by a SYNC.** INVALL "specifies that the ITS must
    ensure any caching associated with the interrupt collection defined by ICID
    is consistent with the LPI Configuration tables held in memory for all
    Redistributors", and the specification is explicit that "A SYNC command
    completes the INV and INVALL commands". An INVALL issued without its SYNC
    leaves a window in which the configuration in memory and the configuration
    the ITS is using disagree.

*   INVDB or VSGI with no explicit VSYNC at the call site. The specification
    states "INVDB is synchronized by a VSYNC command" and "VSGI is synchronized
    by VSYNC", and the driver reaches both through the virtual send path, which
    appends it.

## ITS tables and memory

**Allocating memory for the GIC**

- `its_alloc_pages_node()`: ORs the file-static `gfp_flags_quirk` into every
  request; `its_enable_dma32()` sets it to `GFP_DMA32` on the machines in
  `dma_32bit_impaired_platforms`.
- 32-bit limit: there is no retry and no check of the resulting address.
- `its_alloc_pages_node()`: after allocating, calls `set_memory_decrypted()`
  on `1 << order` pages; `its_free_pages()` calls `set_memory_encrypted()`
  before `free_pages()`.
- `its_free_pages()`: takes the kernel virtual address and the order, not the
  `struct page` that `its_alloc_pages_node()` and `its_alloc_pages()` return.
- Zeroing: `its_alloc_pages_node()` and `its_alloc_pages()` add no
  `__GFP_ZERO`; `itt_alloc_pool()` passes it itself.
- Cache maintenance: none of the helpers calls `gic_flush_dcache_to_poc()`;
  it is left to the caller, for example `its_create_device()` for the ITT.
- `itt_alloc_pool()`: does not round a size below `PAGE_SIZE`;
  `its_create_device()` raises `sz` to at least `ITS_ITT_ALIGN` first.
- `itt_alloc_pool()` with `size >= PAGE_SIZE`: bypasses `itt_pool` and calls
  `its_alloc_pages_node()` with `get_order(size)`.
- `itt_free_pool()`: picks the path by the same size test, so it needs the
  size given at allocation.
- `itt_pool` granule: `its_init()` passes `get_order(ITS_ITT_ALIGN)` to
  `gen_pool_create()`; that is 0, so the pool works in bytes and does not
  align chunks to `ITS_ITT_ALIGN` itself.
- Reused pool chunk: `__GFP_ZERO` applies only when a page is added to
  `itt_pool`; nothing clears a chunk that `gen_pool_free()` returned and
  `gen_pool_alloc()` hands out again.
- Pages are not returned to the allocator, for example:
  - `set_memory_decrypted()` fails: `its_alloc_pages_node()` returns `NULL`
    and leaks the pages.
  - `set_memory_encrypted()` fails: `its_free_pages()` returns without
    `free_pages()`.
  - a page added to `itt_pool`: stays there; the file never removes pool
    memory.

**Disabling and resuming an ITS**

- `its_force_quiescent()` timeout: returns `-EBUSY`.
- `its_force_quiescent()`: returns 0 at once if the ITS is already disabled
  and quiescent; otherwise clears `GITS_CTLR_ENABLE` and `GITS_CTLR_ImDe`,
  then polls `GITS_CTLR_QUIESCENT`.
- Probe: `its_map_one()` calls `its_force_quiescent()`, not
  `its_probe_one()`; `its_node_init()` and `its_reset_one()` reach it.
- Reset pass: `its_reset_one()` writes 0 to every `GITS_BASER` of every ITS
  before any ITS is probed, from `its_of_probe()` and `its_acpi_reset()`.
- There is no ITS_FLAGS_SAVE_SUSPEND_STATE in this tree;
  `its_save_disable()` and `its_restore_enable()` walk every entry of
  `its_nodes`, and `its_init()` registers them without testing a flag.
- `its_save_disable()`: saves `GITS_CTLR` and `GITS_CBASER` only;
  `GITS_BASER` is restored from the cached `baser->val`.
- `its_restore_enable()` when the ITS fails to quiesce: skips that ITS and
  restores nothing, so it stays disabled.
- Re-issued on resume: `its_cpu_init_collection()` for the CPU that runs the
  hook only, and only if its `col_id` is below `GITS_TYPER_HCC()`.
- `its_cpu_init_collection()`: sends MAPC, then INVALL; with
  `ITS_FLAGS_WORKAROUND_CAVIUM_23144` it returns first for a CPU on another
  node.
- No other command is replayed by `its_restore_enable()`.

**Programming the ITS tables**

- Page size: `its_probe_baser_psz()` settles it before the table is
  allocated, by changing only the page-size field of the register and
  reading it back, 64K then 16K then 4K; the result is `baser->psz`.
- Page size failure: `its_probe_baser_psz()` returns -1 after 4K;
  `its_alloc_tables()` frees the earlier tables and returns `-ENXIO`.
- `its_setup_baser()`: has no page-size retry; a page-size mismatch there
  ends in the "doesn't stick" `-ENXIO`.
- Shareability mismatch: sets no per-table flag; later code tests
  `GITS_BASER_SHAREABILITY_MASK` in `baser->val`.
- Attributes carry over: the cacheability and shareability that stuck on one
  `GITS_BASER` are the start values for the next.
- Flat or two-level: `its_parse_indirect_baser()` runs for
  `GITS_BASER_TYPE_DEVICE` and `GITS_BASER_TYPE_VCPU` only; other types are
  flat.
- Two-level needs both: `(esz << ids) > psz * 2`, and `GITS_BASER_INDIRECT`
  reading back set.
- Size caps: `MAX_PAGE_ORDER` in `its_parse_indirect_baser()` and
  `GITS_BASER_PAGES_MAX` in `its_setup_baser()`; there is no
  ITS_MAX_ALLOC_ORDER.
- `MAX_PAGE_ORDER` clamp: lowers the order returned through `*order`; the
  reduced `ids` is only a local that is printed in a warning and is not
  stored.
- PA above 48 bits: tested only under
  `IS_ENABLED(CONFIG_ARM64_64K_PAGES)`.
- PA above 48 bits with `psz` not `SZ_64K`: pages freed, `-ENXIO`, no retry.
- Level-1 entries: hold the raw `page_to_phys()` with `GITS_BASER_VALID`,
  not the folded form; in `drivers/irqchip/irq-gic-v3-its.c`
  `GITS_BASER_ADDR_48_to_52()` is used only by
  `inherit_vpe_l1_table_from_its()`.

**Second-level tables**

- Barrier: `dsb(sy)` after the level-1 entry is written and flushed, in both
  `its_alloc_table_entry()` and `allocate_vpe_l2_table()`.
- Zeroing: comes from `__GFP_ZERO`, not a separate step.
- Check-then-allocate on `table[idx]`: neither function locks or rechecks;
  `its_msi_prepare()` holds `its->dev_alloc_lock` around
  `its_create_device()`.
- `allocate_vpe_l2_table()` on a flat table: returns
  `id < npg * psz / (esz * SZ_8)`, not always true.
- `allocate_vpe_l2_table()`: returns true early without
  `gic_rdists->has_rvpeid` or when the CPU has no `rd_base`.
- Redistributor geometry: read from that CPU's `GICR_VPROPBASER` at each
  call; the entry size is `esz * SZ_8` bytes.
- Device ID with a device `GITS_BASER`: bounded only by the table size in
  `its_alloc_table_entry()`; `dev_id` is not compared with `device_ids()`.
- Device ID with no device `GITS_BASER`: `its_alloc_device_table()` tests
  `ilog2(dev_id) < device_ids(its)`.
- `device_ids()`: a macro over `its->typer`, not a field;
  `its_enable_quirk_cavium_22375()` and
  `its_enable_quirk_socionext_synquacer()` rewrite `GITS_TYPER_DEVBITS`
  there.
- Level-2 pages: nothing in the file clears a level-1 entry or frees a
  level-2 page.

**Redistributor grouping by affinity**

- `GICR_TYPER_COMMON_LPI_AFF` counts the affinity levels kept, from Aff3
  down: 0 keeps none, 1 keeps Aff3, 2 keeps Aff3.Aff2, 3 keeps
  Aff3.Aff2.Aff1.
- Aff0 is never kept; value 0 gives key 0 for every redistributor, which is
  the largest group.
- Comparers, all by equality, all in `drivers/irqchip/irq-gic-v3-its.c`:

| Function | Compares | Reached from |
|---|---|---|
| `find_sibling_its()` | one v4.1 ITS with another | `its_alloc_tables()` |
| `inherit_vpe_l1_table_from_its()` | this CPU's redistributor with each v4.1 ITS | `allocate_vpe_l1_table()` |
| `inherit_vpe_l1_table_from_rd()` | this CPU's redistributor with other CPUs' | `allocate_vpe_l1_table()` |

- `gic_populate_rdist()` does not compare the key.
- `inherit_vpe_l1_table_from_rd()`: returns at the first other CPU with a
  `rd_base` and an equal key, without testing `GICR_VPROPBASER_4_1_VALID`;
  `allocate_vpe_l1_table()` tests the bit on the returned value.

**Non-coherent GICs**

- Flags and setters:

| Flag | Set by |
|---|---|
| `ITS_FLAGS_FORCE_NON_SHAREABLE` | `its_set_non_coherent()`, `its_enable_rk3588001()`, `gic_acpi_parse_madt_its()` |
| `RDIST_FLAGS_FORCE_NON_SHAREABLE` | `rd_set_non_coherent()`, `its_enable_rk3588001()`, `gic_acpi_parse_madt_redist()`, `gic_acpi_parse_madt_gicc()` |
| `ITS_FLAGS_CMDQ_NEEDS_FLUSHING` | `its_probe_one()` |
| `RDIST_FLAGS_PROPBASE_NEEDS_FLUSHING` | `its_cpu_init_lpis()`, `allocate_lpi_tables()` |

- "dma-noncoherent": a `.property` entry in `its_quirks` and `gic_quirks`,
  run by `gic_enable_of_quirks()`; `gic_of_init()` does not read it
  directly.
- ACPI setters: act only when `acpi_get_madt_revision() >= 7`.
- `allocate_lpi_tables()`: sets `RDIST_FLAGS_PROPBASE_NEEDS_FLUSHING`
  together with `RDIST_FLAGS_RD_TABLES_PREALLOCATED`; `its_cpu_init_lpis()`
  then skips programming `GICR_PROPBASER` on a redistributor that has
  `GICR_CTLR_ENABLE_LPIS` set.
- The two derived flags: set on any shareability mismatch with what was
  written, not only on a read-back of 0; the rewrite with nC happens only
  on 0.
- `GITS_CBASER`, `GICR_PROPBASER`, `GICR_PENDBASER` under a force flag:
  written as inner-shareable first, then the read-back shareability is
  masked to 0, which forces the nC rewrite.
- `GITS_BASER` under `ITS_FLAGS_FORCE_NON_SHAREABLE`: no masking;
  `its_alloc_tables()` starts from `shr` 0 and `GITS_BASER_nC`.
- `GICR_PENDBASER` mismatch: sets no flag.
- `its_cpu_init_lpis()`: flushes no table; `gic_reset_prop_table()` and
  `its_allocate_pending_table()` flush at allocation, unconditionally.
- Write sites never test a force flag; each tests a derived value or
  flushes always:

| Object written | Test for the flush |
|---|---|
| command | `ITS_FLAGS_CMDQ_NEEDS_FLUSHING` |
| LPI or vLPI config byte | `RDIST_FLAGS_PROPBASE_NEEDS_FLUSHING` |
| `GITS_BASER` table | the `shr` about to be written, in `its_setup_baser()` |
| `GITS_BASER` level-2 page, level-1 entry | `GITS_BASER_SHAREABILITY_MASK` in `baser->val` |
| redistributor vPE level-2 page, level-1 entry | `GICR_VPROPBASER_SHAREABILITY_MASK` read from `GICR_VPROPBASER` |
| property table, pending table, ITT at allocation | none, always flushed |

## LPIs

**LPI property and pending tables**

- Pending tables: `allocate_lpi_tables()` allocates one for every possible
  CPU in one loop, from `its_init()` on the boot CPU; no CPU allocates its
  own later.
- Extra allocation flag: `its_alloc_pages()` calls `its_alloc_pages_node()`,
  which ORs `gfp_flags_quirk` into the caller's flags; see "Allocating memory
  for the GIC".
- Fill value of the property table: `lpi_prop_prio | LPI_PROP_GROUP1`; the
  driver does not use `LPI_PROP_DEFAULT_PRIO`.
- Property table reservation: done in `its_setup_lpi_prop_table()`, and only
  on the branch that allocates the table. `its_cpu_memreserve_lpi()` deals
  with the pending table only.
- Adopted tables (`RDIST_FLAGS_RD_TABLES_PREALLOCATED`,
  `RD_LOCAL_PENDTABLE_PREALLOCATED`): this kernel makes no
  `gic_reserve_range()` call for them.
- `gic_reserve_range()`: tests `efi_enabled(EFI_CONFIG_TABLES)` at run time,
  not a configuration symbol; a failed reservation is only a `WARN_ON()` at
  both call sites.
- `its_lpi_memreserve_init()`: not an initcall; `gic_init_bases()` calls it
  after `its_cpu_init()`. It registers `its_cpu_memreserve_lpi()` only when
  `efi_enabled(EFI_CONFIG_TABLES)` is true and `its_nodes` is not empty;
  otherwise the callback never runs.

**LPI ID width**

- Adopted path: `lpi_id_bits` is the `GICR_PROPBASER` field plus one, and is
  not clamped to `ITS_MAX_LPI_NRBITS` or to `GICD_TYPER_ID_BITS()`;
  `GICR_PROPBASER_IDBITS_MASK` is 0x1f.
- `GICD_TYPER_NUM_LPIS()`: returns the field plus one, used as an exponent;
  `its_lpi_init()` computes `numlpis = 1UL << GICD_TYPER_NUM_LPIS()`.
- `numlpis` is used when it is greater than 2 (the field is non-zero) and not
  greater than `(1UL << id_bits) - 8192`; when it is greater than that,
  `WARN_ON()` fires and the computed count stays.
- `numlpis` replaces only the count passed to `free_lpi_range()`;
  `lpi_id_bits`, the table sizes and the IDbits written to `GICR_PROPBASER`
  stay as chosen.
- Besides `lpi_id_bits` and `numlpis`, nothing in
  `its_setup_lpi_prop_table()` or `its_lpi_init()` lowers the count; there is
  no clamp by memory size.

**Booting with LPIs already enabled**

- `allocate_lpi_tables()`: tests `GICR_CTLR_ENABLE_LPIS` on the boot CPU's
  redistributor itself; `enabled_lpis_allowed()` only reads the
  `GICR_PROPBASER` address and passes it to `gic_check_reserved_range()`. It
  checks no attributes and no `GICR_TYPER` bit.
- Range checked by `enabled_lpis_allowed()`: 64K. `lpi_id_bits` is still 0
  at that point, so `LPI_PROPBASE_SZ` evaluates to `SZ_64K` whatever size
  the previous kernel used.
- On adoption `allocate_lpi_tables()` sets
  `RDIST_FLAGS_RD_TABLES_PREALLOCATED` and
  `RDIST_FLAGS_PROPBASE_NEEDS_FLUSHING`.
- Per CPU, `its_cpu_init_lpis()` adopts only when the global flag is set and
  that redistributor has `GICR_CTLR_ENABLE_LPIS`; a redistributor with LPIs
  off is programmed with the adopted property table and its newly allocated
  pending table.
- `GICR_PROPBASER` differing from `gic_rdists->prop_table_pa`: `WARN_ON()`
  and `add_taint()` only; the CPU still sets
  `RD_LOCAL_PENDTABLE_PREALLOCATED` and skips programming.
- `redist_disable_lpis()` first returns `-ENXIO` when `GICR_TYPER_PLPIS` is
  clear.
- `redist_disable_lpis()` returns 0 and changes nothing when
  `GICR_CTLR_ENABLE_LPIS` is clear, when `RD_LOCAL_LPI_ENABLED` is set, or
  when `RDIST_FLAGS_RD_TABLES_PREALLOCATED` is set.
- `redist_disable_lpis()` damage control: the warning and
  `add_taint(TAINT_CRAP, LOCKDEP_STILL_OK)` come before the attempt to clear
  the bit, so they happen even when the clear succeeds.
- `its_cpu_init()` return value: ignored by both callers, `gic_init_bases()`
  and `gic_starting_cpu()`. On an error the CPU still comes up, with
  `its_cpu_init_lpis()` and `its_cpu_init_collections()` skipped.

**Changing an LPI's configuration**

- `lpi_write_config()`: ORs in `LPI_PROP_GROUP1` and nothing else beyond
  `set`; the tree has no LPI_PROP_RES1.
- `lpi_write_config()` visibility step: `gic_flush_dcache_to_poc()` on the
  byte when `RDIST_FLAGS_PROPBASE_NEEDS_FLUSHING` is set, `dsb(ishst)` when
  it is clear.
- `lpi_update_config()`: adds no barrier of its own between the write and
  the invalidate.
- Table written: chosen by `irqd_is_forwarded_to_vcpu()` at the time of the
  call. `its_vlpi_map()` sets the bit before `lpi_write_config()` so the VM's
  table is written; `its_vlpi_unmap()` clears it before
  `lpi_update_config()` so the physical table is written.
- Invalidate chosen by `lpi_update_config()`:

  | Condition | Invalidate |
  |---|---|
  | `has_direct_lpi`, and not forwarded or `is_v4_1(its_dev->its)` | `direct_lpi_inv()` |
  | otherwise, not forwarded | `its_send_inv()` |
  | otherwise, forwarded | `its_send_vinv()` |

- **Potentially unsafe usage**: calling `lpi_write_config()` without
  `lpi_update_config()`.
  - Unsafe: when nothing after the write invalidates that LPI; the
    redistributor may keep its cached byte.
  - Safe: a vPE doorbell, where the caller invalidates itself:
    `its_vpe_mask_irq()` then `its_vpe_send_inv()`, and
    `its_vpe_4_1_mask_irq()` then `its_vpe_4_1_send_inv()`.
  - Safe: `PROP_UPDATE_VLPI` in `its_vlpi_prop_update()`, where the caller
    invalidates the whole vPE afterwards, as `vgic_its_invall()` does with
    `its_invall_vpe()`.

**Invalidating through the redistributor**

- Physical LPI: `irq_to_cpuid_lock()` takes no lock; it reads
  `its_dev->event_map.col_map` and relies on the caller holding the
  `irq_desc` lock, under which `its_set_affinity()` writes `col_map`.
- Doorbell detection: `irq_to_cpuid_lock()` tests only
  `d->chip == &its_vpe_irq_chip`. Doorbells of `its_vpe_4_1_irq_chip` never
  reach it; `its_vpe_4_1_send_inv()` invalidates them with
  `its_send_invdb()`.
- Lock order: `vpe->vpe_lock`, then `rd_lock`.
- `rd_lock`: taken with plain `raw_spin_lock()`. Interrupts are already off,
  through `raw_spin_lock_irqsave()` in `vpe_to_cpuid_lock()` or through the
  caller's `irq_desc` lock.
- All of a vPE's LPIs: `its_vpe_4_1_invall_locked()` writes `GICR_INVALLR`
  and takes only `rd_lock`. Both callers hold `vpe->vpe_lock`:
  `its_vpe_4_1_invall()` and `its_vpe_set_affinity()`, which passes the new
  CPU.
- `wait_for_syncr()`: spins on bit 0 of `GICR_SYNCR` with `cpu_relax()`; no
  timeout and no fallback to another register.

**The LPI number allocator**

- `alloc_lpi_range()`: all or nothing. It takes `nr_lpis` from the first
  range with `span >= nr_lpis`, and returns `-ENOSPC` when no single range is
  large enough; it never returns part of a request.
- `its_lpi_alloc()`: halves `nr_irqs` and retries by itself. On failure it
  returns NULL with `*base` and `*nr_ids` set to 0, not an error code.
- Shortfall in `its_create_device()`: the device keeps the smaller
  `nr_lpis`; `its_alloc_device_irq()` later returns `-ENOSPC` when
  `lpi_map` has no free region.
- Shortfall in `its_vpe_irq_domain_alloc()`: `nr_ids < nr_irqs` frees the
  range again and returns `-ENOMEM`.
- `free_lpi_range()`: allocates its node before taking the lock and returns
  `-ENOMEM` without touching the list; `its_lpi_free()` only does
  `WARN_ON()`, so those LPIs are not returned.
- **Unsafe usage**: calling `free_lpi_range()` for LPIs that are already in
  `lpi_range_list`. Nothing checks for overlap; `merge_lpi_ranges()` merges
  only on exact adjacency, so `alloc_lpi_range()` can then hand out the same
  LPI twice.
  - Safe: one `its_lpi_free()` with the `base` and `nr_ids` that
    `its_lpi_alloc()` returned, as `its_msi_teardown()` does after it finds
    `lpi_map` empty.

**One device behind an ITS**

- `nvecs` clamp: `its_create_device()` limits `nvecs` to
  `BIT(FIELD_GET(GITS_TYPER_IDBITS, its->typer) + 1)` before it computes
  `nr_ites` and before `its_lpi_alloc()`.
- ITT size: `max(sz, ITS_ITT_ALIGN)`; no padding is added.
- ITT allocation: `itt_alloc_pool()`, not `kzalloc_node()`. Sizes of
  `PAGE_SIZE` or more come from `its_alloc_pages_node()`; smaller ones from
  the gen_pool `itt_pool`.
- `its_encode_itt()`: encodes `itt_addr >> 8`; the low 8 bits of the ITT
  address are dropped.
- `gic_flush_dcache_to_poc()` on the ITT: unconditional.
- `shared`: set only in `its_msi_prepare()`: when `its_find_device()` finds
  the device ID, or when a new device is created with
  `MSI_ALLOC_FLAGS_PROXY_DEVICE` in `info->flags`.
- `MSI_ALLOC_FLAGS_PROXY_DEVICE`: set by `its_pci_msi_prepare()` in
  `drivers/irqchip/irq-gic-its-msi-parent.c` when the last DMA alias is not
  the device itself.
- Lifetime of a shared device: never freed. `its_free_device()` is called
  only from `its_msi_teardown()` in `drivers/irqchip/irq-gic-v3-its.c`,
  which returns at once when `shared` is set, and no code clears `shared`.

**Preparing a device for MSIs**

- Existing device ID: `its_msi_prepare()` always reuses the device found. It
  makes no test of the device's size against `nvec` and never creates a
  second device for the same ID.
- Lock: the mutex `its->dev_alloc_lock`, held across `its_find_device()` and
  `its_create_device()`. The raw spinlock `its->lock` is taken and released
  inside `its_find_device()` for the list walk, and again in
  `its_create_device()` for the `list_add()`; it is not held between the
  two.
- `its_msi_teardown()` in `drivers/irqchip/irq-gic-v3-its.c` with `lpi_map`
  not empty: `WARN_ON_ONCE()` and return; nothing is freed.
- `its_msi_teardown()` frees in this order: `its_lpi_free()` for the LPI
  range and bitmap, `its_send_mapd(its_dev, 0)`, then `its_free_device()`.
- `its_free_device()`: only unlinks the device and frees `col_map`, the ITT
  and the structure; it sends no MAPD and returns no LPIs.

**What the architecture specification says**

From the Arm Generic Interrupt Controller Architecture Specification, GICv3
and GICv4 (ARM IHI 0069), and what each statement means for this code. A
kernel tree cannot supply these, so they are kept by hand and inserted as
they are.

*   **The LPI Pending table is not shared.** The specification says of it:
    "This table is specific to a particular Redistributor." Extending a sharing
    argument from the configuration table to the pending table is a category
    error, and a patch that pins or shares the pending table across a group is
    doing something the architecture does not ask for.

*   **Divergent `GICR_PROPBASER` values within a group are UNPREDICTABLE.**
    "Setting different values in different copies of GICR_PROPBASER on
    Redistributors that are required to use a common LPI Configuration table
    when GICR_CTLR.EnableLPIs == 1 leads to UNPREDICTABLE behavior." A
    secondary sentence constrains it only partially: "If GICR_PROPBASER is
    programmed to different values on different Redistributors, it is
    IMPLEMENTATION DEFINED which copy or copies of GICR_PROPBASER are used when
    the GIC reads the LPI Configuration tables. However, the copy or copies
    that are used will correspond to a Redistributor on which
    GICR_CTLR.EnableLPIs == 1." Read that as a floor on how bad it can get, not
    as a licence: the only guarantee is that the chosen copy belongs to an
    enabled redistributor.

*   **There is no "it will be noticed eventually".** The specification states
    both that "A cached LPI Configuration table entry is not guaranteed to
    remain in the cache" and that "A cached LPI Configuration table entry is not
    guaranteed to remain incoherent with memory". Neither direction can be
    relied on, which is exactly why the explicit invalidation is the only way to
    publish a change.

## vPE mapping and movement

**The GICv4 interface**

- `enum its_vcpu_info_cmd_type` in `include/linux/irqchip/arm-gic-v4.h`: the
  vPE commands are `SCHEDULE_VPE`, `DESCHEDULE_VPE`, `COMMIT_VPE` and
  `INVALL_VPE`; the only vSGI command is `PROP_UPDATE_VSGI`.
- `its_unmap_vlpi()`: carries no command; it passes NULL, which
  `its_irq_set_vcpu_affinity()` tests before the switch and hands to
  `its_vlpi_unmap()`.
- Doorbell receiver: `its_vpe_set_vcpu_affinity()` for `its_vpe_irq_chip`,
  `its_vpe_4_1_set_vcpu_affinity()` for `its_vpe_4_1_irq_chip`;
  `its_vpe_irq_domain_alloc()` picks the chip from `has_rvpeid`.
- `irq_set_vcpu_affinity()` in `kernel/irq/manage.c`: holds the irq's
  `irq_desc` lock across the receiver, and walks up the hierarchy to the first
  chip that has the callback.
- vLPI INT and CLEAR take another route: `irq_set_irqchip_state()` on the host
  irq reaches `its_irq_set_irqchip_state()`, which calls `its_send_vint()` or
  `its_send_vclear()` when `irqd_is_forwarded_to_vcpu()`.
- Doorbell pending state: only `its_vpe_irq_chip` has
  `its_vpe_set_irqchip_state()`; `its_vpe_4_1_irq_chip` has no
  `irq_set_irqchip_state` member.
- Preemption disabled: `its_make_vpe_resident()`,
  `its_make_vpe_non_resident()` and `its_commit_vpe()` each do
  `WARN_ON(preemptible())` and then carry on; no other function in
  `drivers/irqchip/irq-gic-v4.c` has the check.
- Reason for the three: their receivers address the current CPU's
  redistributor through `gic_data_rdist_vlpi_base()`.
- `its_invall_vpe()`: no preemption check.

**GICv4 locks**

| Lock | Defined in | Protects |
|---|---|---|
| `vmapp_lock` | `struct its_vm` | `vlpi_count[]` of `struct its_vm` and the VMAPP sends decided from it; not `vmapp_count` |
| `vpe_lock` | `struct its_vpe` | `col_idx`; on GICv4.1 also `pending_last`, between `its_vpe_4_1_deschedule()` with `req_db` and `vgic_v4_doorbell_handler()` |
| `vmovp_lock` | one file-scope lock in `drivers/irqchip/irq-gic-v3-its.c` | `vmovp_seq_num` and the order of ITSList VMOVPs |
| `rd_lock` | per-CPU `rdist` of `struct rdists`, `include/linux/irqchip/arm-gic-v3.h` | a register write plus its poll on one redistributor: `GICR_INVLPIR` or `GICR_INVALLR` then `GICR_SYNCR`, `GICR_VSGIR` then `GICR_VSGIPENDR` |
| `vlpi_lock` | `struct event_lpi_map` | a device's `event_map.vm`, `nr_vlpis` and the `vlpi_maps` pointer; `its_irq_set_vcpu_affinity()` holds it across every request it handles |

- `vmapp_count`: an `atomic_t` in `struct its_vpe`, changed in
  `its_build_vmapp_cmd()`; no lock in this list covers it.
- `GICR_VPENDBASER` programming (`its_vpe_schedule()`,
  `its_vpe_deschedule()`, `its_vpe_4_1_schedule()`): takes no `rd_lock`.
- `vmovp_lock`: there is no per-VM lock of that name; `struct its_vm` has no
  such field.
- Written order: the comment above `vmapp_lock` in `struct its_vm`,
  `include/linux/irqchip/arm-gic-v4.h`: `vmapp_lock` -> `vpe_lock` ->
  `vmovp_lock`, for sequences that involve the ITSList.
- `rd_lock`, `vlpi_lock` and `vpe_proxy.lock`: not in that comment; their
  order is only in the code.
- `vlpi_lock` is outside `vmapp_lock`: `its_irq_set_vcpu_affinity()` ->
  `its_vlpi_map()` -> `its_map_vm()`.
- `rd_lock` is inside `vpe_lock` in `its_vpe_4_1_invall()`,
  `its_sgi_get_irqchip_state()` and `its_vpe_set_affinity()`.
- `__direct_lpi_inv()` on a physical LPI: takes `rd_lock` with no `vpe_lock`,
  because `irq_to_cpuid_lock()` locks nothing for that case.
- `its_vpe_invall()`: takes `vmapp_lock` whether or not `its_list_map` is set,
  and does not take `vpe_lock`.
- Not irqsave, for example: `vmapp_lock` in `its_vpe_set_affinity()`,
  `vmovp_lock` in `its_send_vmovp()`, and every `rd_lock` acquisition; they
  rely on interrupts being off already.
- irqsave: `vmapp_lock` in `its_map_vm()`, `its_unmap_vm()` and
  `its_vpe_invall()`.

**Moving a vPE**

- First test: `!atomic_read(&vpe->vmapp_count)`, made before the function
  takes any lock; it is not a test of the old CPU against the new one.
- `vmapp_count` zero under eager mapping: returns `-EINVAL` and changes
  nothing.
- `vmapp_count` zero under lazy mapping: only the effective affinity is set to
  `cpumask_first(mask_val)`; `col_idx` is left as it was and no command is
  sent.
- `its_vpe_set_affinity()` sends no VMAPP in any outcome; a move does not map
  the vPE on a destination ITS or unmap it from a source ITS.
- `vmapp_lock`: taken only `if (its_list_map)`, with plain `raw_spin_lock()`,
  before `vpe_lock`.
- `vpe_lock`: held from `vpe_to_cpuid_lock()` until after
  `irq_data_update_effective_affinity()`, also when the CPU does not change.
- `vmovp_lock`, `rd_lock` and `vpe_proxy.lock`: taken and dropped inside
  `its_send_vmovp()`, `its_vpe_4_1_invall_locked()` and
  `its_vpe_db_proxy_move()`, under `vpe_lock`, and under `vmapp_lock` when it
  was taken.

**Target CPU of a move**

- Order of choice: with a `vpe_table_mask` for the old CPU, keep the old CPU
  if it is in both `mask_val` and that mask; else any CPU in both; with no
  CPU in both, or with no `vpe_table_mask`, `cpumask_first(mask_val)`.
- `its_vpe_set_affinity()` makes no `cpu_online_mask` test of its own;
  `irq_do_set_affinity()` in `kernel/irq/manage.c` passes a mask already
  restricted to online CPUs unless `force` is set.
- `vpe->col_idx` is written before `its_send_vmovp()`, which reads it to pick
  the collection.
- Residency: the function does not deschedule or reschedule the vPE;
  `vgic_v4_load()` calls `irq_set_affinity()` first and
  `its_make_vpe_resident()` after.
- After VMOVP no VINVALL command is sent; the only invalidate is
  `its_vpe_4_1_invall_locked()` on the new CPU, when `find_4_1_its()` returns
  an ITS with `ITS_FLAGS_WORKAROUND_HISILICON_162100801`.
- `its_vpe_db_proxy_move()` then runs one of three cases:
  - `has_rvpeid`: nothing.
  - `has_direct_lpi`: clears the doorbell on the old redistributor through
    `GICR_CLRLPIR` and waits in `wait_for_syncr()`.
  - otherwise: under `vpe_proxy.lock`, maps the vPE in the proxy device and
    calls `its_send_movi()`.

**VMOVP and the ITS list**

- One command: only when `its_list_map` is zero; the number of ITSs is not
  tested.
- `its_list_map` non-zero, even with one bit set: the loop over `its_nodes`
  runs, with `vmovp_seq_num` and `get_its_list()`.
- `vmovp_lock`: taken with `guard(raw_spinlock)`, not irqsave.
- Skipped ITSs: exactly two tests, `!is_v4(its)` and
  `!require_its_list_vmovp()`; there is no test for a shared collection or
  for an ITS already handled.
- `has_rvpeid` set: `require_its_list_vmovp()` is true for every ITS, but the
  `is_v4()` test still skips an ITS that is not v4.
- **Unsafe usage**: calling `its_send_vmovp()` with `its_list_map` set and
  without the VM's `vmapp_lock`; `vlpi_count[]` is read in `get_its_list()`
  and again in the loop, and `its_map_vm()` and `its_unmap_vm()` change it
  under `vmapp_lock`.
  - Safe: take `vmapp_lock`, then `vpe_lock`, then call it, as
    `its_vpe_set_affinity()` does.

**Eager and lazy vPE mapping**

- Eager: when `its_list_map` is zero or `has_rvpeid` is set. Lazy: only when
  `its_list_map` is non-zero and `has_rvpeid` is clear.
- Eager mapping is done by `its_vpe_irq_domain_activate()`, on every
  `is_v4()` ITS; `its_map_vm()` returns at once when mapping is eager.
- Lazy mapping is done by `its_map_vm()`; `its_vpe_irq_domain_activate()`
  then only sets `col_idx` and the effective affinity.
- `its_vlpi_map()` on an irq that is already forwarded: sends VMOVI and does
  not call `its_map_vm()`, so under lazy mapping `vlpi_count[]` counts
  forwarded irqs, not `MAP_VLPI` requests; under eager mapping it stays 0.
- Two fields are named `vlpi_count`:
  - `vlpi_count[]` in `struct its_vm`, indexed by `list_nr`: drives the lazy
    case.
  - `vlpi_count` in `struct its_vpe`, an `atomic_t`: written and read only
    under `arch/arm64/kvm/`; the ITS driver does not use it.
- `vmapp_count`: every unmap sends VMAPP with V=0; reaching zero only sets
  ALLOC in that command, on a GICv4.1 ITS.
- PTZ: `its_build_vmapp_cmd()` always encodes it as false.

**A vPE's current redistributor**

- There is no vpe_to_cpuid_nolock() here; the lock-taking helpers are
  `vpe_to_cpuid_lock()` and `irq_to_cpuid_lock()`, with their unlock twins.
- Writers: `its_vpe_set_affinity()` under `vpe_lock`, and
  `its_vpe_irq_domain_activate()` without `vpe_lock`, before its own
  `its_send_vmapp()` calls.
- `irq_to_cpuid_lock()`: takes `vpe_lock` only for `its_vpe_irq_chip` and for
  an LPI with a vLPI map; any other `struct irq_data` is read as a physical
  LPI of a `struct its_device`.
- vLPI commands sent through the ITS (`its_send_vmovi()`, `its_send_vinv()`,
  `its_send_vint()`, `its_send_vclear()`, `its_send_vmapti()`): take no
  `vpe_lock`.
- **Unsafe usage**: passing the `struct irq_data` of a GICv4.1 doorbell
  (`its_vpe_4_1_irq_chip`) or of a vSGI (`its_sgi_irq_chip`) to
  `irq_to_cpuid_lock()`; its chip data is a `struct its_vpe`, which the
  function would use as a `struct its_device`.
  - Safe: `vpe_to_cpuid_lock()` on the `struct its_vpe`, as
    `its_vpe_4_1_invall()` and `its_sgi_get_irqchip_state()` do.
- **Potentially unsafe usage**: reading `vpe->col_idx` without `vpe_lock`.
  - Unsafe: on a vLPI or vSGI path that uses the value to pick `rd_base` or a
    collection for a command; that path holds another irq's `irq_desc` lock,
    and `its_vpe_set_affinity()` can change `col_idx` before the access.
  - Safe: in a callback of the doorbell irq, which runs under the same
    `irq_desc` lock as `its_vpe_set_affinity()`, as
    `its_vpe_set_irqchip_state()` does.
  - Safe: in `valid_vpe()`, which the command builders call; the value only
    selects the collection that `valid_col()` sanity-checks and is not
    encoded in the command.
  - Safe: in `its_vpe_irq_domain_activate()` for the doorbell, which
    `__setup_irq()` reaches through `irq_activate()` with the doorbell's
    `irq_desc` lock held, the lock `its_vpe_set_affinity()` runs under.

## Virtual LPIs and SGIs

**Mapping a virtual LPI**

- `event_map.vlpi_lock`: a raw spinlock, taken only in
  `its_irq_set_vcpu_affinity()`, which then calls `its_vlpi_map()` or
  `its_vlpi_unmap()`; there is no mutex on this path.
- Context: `irq_set_vcpu_affinity()` holds the irq descriptor lock as well, so
  neither function may sleep; `vlpi_maps` is allocated with `kzalloc_objs()`
  and `GFP_ATOMIC`.
- Both cases: the VM binding check and the copy of `*info->map` into
  `vlpi_maps[event]` run before the forwarded test.
- Already forwarded: tested with `irqd_is_forwarded_to_vcpu()`, not a
  counter; sends only `its_send_vmovi()`.
- Already forwarded: no property-table write, no DISCARD, `nr_vlpis`
  unchanged.
- Not yet forwarded, in order:
  1. `its_map_vm()`
  2. `irqd_set_forwarded_to_vcpu()`
  3. `lpi_write_config()` with `info->map->properties`
  4. `its_send_discard()`
  5. `its_send_vmapti()`
  6. `event_map.nr_vlpis++`
- Step 2 before step 3: `lpi_write_config()` picks the VM's `vprop_page`
  through `get_vlpi_map()`, which returns NULL until the irq is flagged
  forwarded.
- `its_send_vmapti()`: always VMAPTI; there is no VMAPI variant here.
- Last unmap (`nr_vlpis` reaches 0): sets `event_map.vm = NULL` and
  `kfree()`s `event_map.vlpi_maps`; the `vlpi_maps` pointer is left stale.
- `event_map.vm`: what the driver tests for "device has vLPIs"; a NULL test
  on `vlpi_maps` is wrong after the last unmap.
- `its_unmap_vm()`: called on every unmap, before the `nr_vlpis` test; its
  per-ITS count is `vm->vlpi_count[]`, separate from `nr_vlpis`.

**Forwarding a device interrupt**

- Exits that return 0 without mapping, in order:
  1. `vgic_supports_direct_msis()` is false
  2. `vgic_get_its()` returns an error; see `vgic_msi_to_its()` in
     `arch/arm64/kvm/vgic/vgic-its.c`
  3. `vgic_its_resolve_lpi()` returns non-zero, whatever the value
  4. `irq->hw` is already set
- `vgic_supports_direct_msis()`: also false on a host where
  `system_supports_direct_sgis()` is true and the VM's `nassgicap` is clear,
  so clearing vSGI support for a VM turns off vLPI forwarding too.
- `its_map_vlpi()` failure: returned to the caller as an error, with `irq->hw`
  left false; the comment above the call says "silently bail out", the code
  does not.
- `its->its_lock`: taken with `guard(mutex)` after `vgic_get_its()`, held to
  the end of the function.
- `irq->irq_lock`: taken with `raw_spin_lock_irqsave()` before the `irq->hw`
  test and held across `its_map_vlpi()`, so the ITS driver runs with
  interrupts off.
- `vgic_its_resolve_lpi()`: returns `ite->irq` without a reference for the
  caller; `its->its_lock` keeps the ITE and its reference alive, and
  `kvm_vgic_v4_set_forwarding()` calls no `vgic_put_irq()`.
- Pending transfer, only when `irq->pending_latch` is set:
  `irq_set_irqchip_state()` reaches `its_irq_set_irqchip_state()`, which
  sends `its_send_vint()` because the irq is now forwarded; it is an ITS
  command, not a write to the pending table.
- Pending transfer failure: `WARN_RATELIMIT()`, then the error is returned
  with `irq->hw` still true and the vLPI still mapped.
- After the transfer: `pending_latch` is cleared and the lock is dropped
  inside `vgic_queue_irq_unlock()`, not at the `out_unlock_irq` label.

**Removing a forwarded interrupt**

- Signature: `void kvm_vgic_v4_unset_forwarding(struct kvm *kvm, int
  host_irq)`; it takes no routing entry and returns nothing.
- Lookup: `__vgic_host_irq_get_vlpi()` in `arch/arm64/kvm/vgic/vgic-v4.c`
  walks `kvm->arch.vgic.lpi_xa` under `guard(rcu)` for an entry with
  `irq->hw` set and `irq->host_irq == host_irq`.
- Lookup does not call `vgic_get_its()`, `vgic_its_resolve_lpi()` or
  `its_get_vlpi()`.
- Reference: taken with `vgic_try_get_irq_ref()`; if that fails the helper
  returns NULL without looking further.
- Not forwarded: no entry matches, the helper returns NULL and the function
  returns having changed nothing; same when `vgic_supports_direct_msis()` is
  false.
- Found: under `irq->irq_lock`, re-tests `irq->hw`, then `atomic_dec()` of the
  target vPE's `vlpi_count`, `irq->hw = false`, `its_unmap_vlpi()`.
- `irq->host_irq`: not cleared.
- `its_unmap_vlpi()`: returns `void`; a failing `irq_set_vcpu_affinity()` only
  hits `WARN_ON_ONCE()`.
- `its->its_lock`: not taken; `kvm_irq_routing_update()` in
  `virt/kvm/eventfd.c` reaches this function through
  `kvm_arch_update_irqfd_routing()` with `kvm->irqfds.lock` held, so nothing
  on this path may sleep.
- `kvm_arch_update_irqfd_routing()`: on a changed MSI route it only unmaps;
  it does not map the new route.

**Virtual SGIs**

- Driver side: `its_init()` passes `its_sgi_domain_ops` to `its_init_v4()`
  when any ITS is `is_v4_1()`, inside its `has_v4 & rdists->has_vlpis`
  branch; `its_alloc_vcpu_sgis()` in `drivers/irqchip/irq-gic-v4.c` creates
  `sgi_domain` and allocates the 16 irqs only if `has_v4_1_sgi()`, which adds
  `gic_cpuif_has_vsgi()`.
- KVM side: `system_supports_direct_sgis()` is `has_gicv4_1` and
  `gic_cpuif_has_vsgi()`; `has_gicv4_1` comes from
  `gic_data.rdists.has_rvpeid` and `gicv4_enable`, and `vgic_v3_probe()`
  assigns it only when `gic_data.rdists.has_vlpis` was set.
- `GICD_TYPER2_nASSGIcap` of the host: tested by neither; in
  `drivers/irqchip/irq-gic-v3.c` it only decides whether `gic_dist_init()`
  sets `GICD_CTLR_nASSGIreq` in the host's `GICD_CTLR`.
- `find_4_1_its()`: returns this CPU's `local_4_1_its` when set; the first
  `is_v4_1()` entry of `its_nodes` is only the fallback.
- `local_4_1_its`: set in `inherit_vpe_l1_table_from_its()` and copied in
  `inherit_vpe_l1_table_from_rd()`.
- Set pending: `its_sgi_set_irqchip_state()` does a `writeq_relaxed()` of
  vPE ID and `d->hwirq` to `GITS_SGIR` through `its->sgir_base`; no command
  is queued.
- Clear pending and all configuration: VSGI commands on the same
  `find_4_1_its()`, through `its_configure_sgi()`.
- Read back: goes to the redistributor of the vPE's CPU, not to an ITS; see
  `its_sgi_get_irqchip_state()`, which returns `-ENXIO` if
  `GICR_VSGIPENDR_BUSY` never clears.

**Switching SGIs to hardware**

- `vgic_supports_direct_sgis()`: returns the per-VM `nassgicap`, not the host
  capability; without it `GICD_CTLR_nASSGIreq` is masked off in both the
  guest and the userspace write.
- Guest `GICD_CTLR` write: `nassgireq` is read-only only when the distributor
  was enabled and stays enabled; the write that enables or disables the
  distributor can change it.
- Userspace `GICD_CTLR` write: `vgic_mmio_uaccess_write_v3_misc()` stores
  `enabled` and `nassgireq` and does not call `vgic_v4_configure_vsgis()`.
- `vgic_v4_configure_vsgis()`: called from two places only,
  `vgic_mmio_write_v3_misc()` and `vgic_v3_map_resources()`; the second calls
  it only when `kvm_vgic_global_state.has_gicv4_1`, runs once, from
  `kvm_vgic_map_resources()` on first vCPU run, and applies a restored
  `nassgireq`.
- Host irqs: already allocated by `its_alloc_vcpu_sgis()` when
  `vgic_v4_init()` ran; `vgic_v4_enable_vsgis()` only looks them up with
  `irq_find_mapping()`.
- To hardware: enabled, group and priority through
  `vgic_v4_sync_sgi_config()` and `irq_domain_activate_irq()`, then pending.
- To hardware, pending: `irq_set_irqchip_state()` is called with
  `irq->pending_latch` whether set or not; a false latch sends the clearing
  VSGI.
- To software: pending only, read with `irq_get_irqchip_state()` into
  `irq->pending_latch` before `irq_domain_deactivate_irq()`.
- Active state: transferred in neither direction; `vgic_mmio_change_active()`
  forces `irq->active = false` for a hardware SGI.
- While hardware-backed: guest priority and group writes go through
  `its_prop_update_vsgi()`; enable writes go through `enable_irq()` in
  `vgic_mmio_write_senable()` and `disable_irq_nosync()` in
  `vgic_mmio_write_cenable()`, on `irq->host_irq`; both are in
  `arch/arm64/kvm/vgic/vgic-mmio.c`.

## vPE scheduling

**Making a vPE resident**

- GICv4.0 doorbell: `its_make_vpe_resident()` calls
  `disable_irq_nosync(vpe->irq)` before sending `SCHEDULE_VPE`, and does so
  even if the command then fails.
- GICv4.1 doorbell: not touched; `its_vpe_4_1_schedule()` writes
  `GICR_VPENDBASER_4_1_DB` as 0.
- `its_vpe_4_1_schedule()`: the value is exactly `GICR_VPENDBASER_Valid`,
  `GICR_VPENDBASER_4_1_VGRP0EN` from `info->g0en`,
  `GICR_VPENDBASER_4_1_VGRP1EN` from `info->g1en`, and
  `GICR_VPENDBASER_4_1_VPEID`; no address, no attributes.
- `info->req_db`: shares a union with `g0en` and `g1en` in
  `struct its_cmd_info`; only `its_vpe_4_1_deschedule()` reads it.
- `its_vpe_schedule()` on GICv4.0: the `GICR_VPENDBASER` value carries
  `GICR_VPENDBASER_PendingLast`, `GICR_VPENDBASER_IDAI` from `vpe->idai`, and
  `GICR_VPENDBASER_Valid`.
- Cacheability and shareability bits in `its_vpe_schedule()`: set in both
  `GICR_VPROPBASER` and `GICR_VPENDBASER` only when
  `rdists_support_shareable()` is true.
- `its_wait_vpt_parse_complete()`: returns without reading the register
  unless `gic_rdists->has_vpend_valid_dirty` is set; that flag is the AND of
  `GICR_TYPER_DIRTY` over the redistributors, in
  `__gic_update_rdist_properties()`.
- Timeout in `its_wait_vpt_parse_complete()`: only `WARN_ON_ONCE()`;
  `COMMIT_VPE` still returns 0, so `its_commit_vpe()` sets `vpe->ready`.

**Making a vPE non-resident**

- `its_clear_vpend_valid()`: returns the `u64` value of `GICR_VPENDBASER`
  last read, never a boolean or an error code.
- Not settled in time: the returned value has `GICR_VPENDBASER_Dirty` still
  set and `GICR_VPENDBASER_PendingLast` forced to 1 by the helper itself.
- `read_vpend_dirty_clear()`: called twice by the helper, before the write
  and after it; each call polls for up to about one second.
- `its_vpe_deschedule()` and `its_vpe_4_1_deschedule()`: neither tests
  Dirty in the result; both are void, so `DESCHEDULE_VPE` returns 0 and
  `its_make_vpe_non_resident()` clears `vpe->resident` after a timeout too.
- GICv4.1 with `info->req_db` false: the helper is called with
  `set = GICR_VPENDBASER_PendingLast`, the result is discarded, and
  `vpe->pending_last` is set to true.
- `info->req_db`: the `db` argument of `its_make_vpe_non_resident()`, which
  KVM takes from `vgic_v4_want_doorbell()`; WFI is not the only case, see
  "vPE residency from KVM".

**The pending-last hint**

- `its_vpe_schedule()`: sets `GICR_VPENDBASER_PendingLast` to 1 on every
  call, whatever `vpe->pending_last` holds.
- `its_vpe_4_1_schedule()`: writes the whole register with PendingLast 0.
- `pending_last` is not cleared when the vPE becomes resident; a true value
  stays until the next deschedule that stores the read-back, in
  `its_vpe_deschedule()` or in `its_vpe_4_1_deschedule()` with `req_db`.
- Writers of `pending_last`: `its_vpe_deschedule()` and
  `its_vpe_4_1_deschedule()` with `req_db` (both store the read-back),
  `its_vpe_4_1_deschedule()` without `req_db` (always true), and
  `vgic_v4_doorbell_handler()` (always true).
- `kvm_vgic_vcpu_pending_irq()`: reads `pending_last` without
  `vpe->vpe_lock`, after the `vgic.enabled` test and before the priority
  test; a true value is ignored while the distributor is disabled.

**Doorbell interrupts**

- Chip selection: `its_vpe_irq_domain_alloc()` picks `its_vpe_4_1_irq_chip`
  when `gic_rdists->has_rvpeid`, else `its_vpe_irq_chip`.
- The test for GICv4.1 differs by file: `gic_rdists->has_rvpeid` picks the
  chip in `drivers/irqchip/irq-gic-v3-its.c`, `has_v4_1()` is used in
  `drivers/irqchip/irq-gic-v4.c`, and `kvm_vgic_global_state.has_gicv4_1` in
  KVM.
- `its_vpe_4_1_mask_irq()` and `its_vpe_4_1_unmask_irq()`: real operations,
  `lpi_write_config()` then `its_send_invdb()`; on GICv4.1
  `its_make_vpe_resident()`, `its_make_vpe_non_resident()` and
  `vgic_v4_doorbell_handler()` skip their `enable_irq()` and
  `disable_irq_nosync()` calls.
- GICv4.1 enable: `vgic_v4_init()` removes `IRQ_NOAUTOEN` from
  `DB_IRQ_FLAGS`, so `request_irq()` enables the doorbell;
  `its_vpe_4_1_deschedule()` sets `GICR_VPENDBASER_4_1_DB` only with
  `req_db`.
- GICv4.0 enable: the `enable_irq()` loop in `its_make_vpe_non_resident()`
  runs only when `db` is true; with `db` false the doorbell stays disabled.
- GICv4.0 disable: `disable_irq_nosync()` in `its_make_vpe_resident()`, and
  in `vgic_v4_doorbell_handler()` when the interrupt is not already disabled.
- `pending_last` at deschedule: assigned, not ORed; on GICv4.1 with `req_db`
  the write to the register and the assignment are both inside
  `vpe->vpe_lock`, which the handler also takes.

**vPE residency from KVM**

- First test in `vgic_v4_load()` and `vgic_v4_put()`:
  `vgic_supports_direct_irqs()`, not `vgic_supports_direct_msis()`; it is
  true when either `vgic_supports_direct_msis()` or
  `vgic_supports_direct_sgis()` is.
- `vgic_v4_load()`: also returns 0 with the vPE left non-resident when
  `IN_WFI` is set.
- `vgic_v3_load()` and `vgic_v3_put()`: return through
  `vgic_v3_load_nested()` or `vgic_v3_put_nested()` when
  `vgic_state_is_nested()`, and then do not call `vgic_v4_load()` or
  `vgic_v4_put()`.
- `vgic_v4_want_doorbell()`: true when `IN_WFI` is set; otherwise false
  unless `vcpu_has_nv()`, and then the value of `IN_NESTED_ERET`.
- `IN_NESTED_ERET`: set in `kvm_emulate_nested_eret()` around
  `kvm_arch_vcpu_put()` and `kvm_arch_vcpu_load()`.
- `KVM_REQ_RELOAD_GICv4`: raised only in `vgic_mmio_write_v3_misc()`, on a
  guest write to `GICD_CTLR` that changes `dist->enabled` while
  `vgic_supports_direct_sgis()` is true.
- A change of `nassgireq` alone: calls `vgic_v4_configure_vsgis()` and
  raises no request.
- `vgic_mmio_uaccess_write_v3_misc()`: sets `dist->enabled` from userspace
  and raises no request.
- `vgic_v4_request_vpe_irq()`: is `request_irq()` for the doorbell, unrelated
  to `KVM_REQ_RELOAD_GICv4`.

**Blocking in WFI**

- `kvm_vcpu_wfi()`: defined in `arch/arm64/kvm/arm.c`.
- Calls made: `kvm_vgic_put()` before the halt and `kvm_vgic_load()` after
  it; it does not call `vgic_v4_put()` or `vgic_v4_load()` directly.
- `IN_WFI` is also tested by `vgic_v5_put()`, which calls
  `vgic_v5_sync_ppi_priorities()` only when it is set.
- `kvm_vgic_vcpu_pending_irq()`: does not test `IN_WFI`.

**Virtual pending base register writes**

- Helper: `its_clear_vpend_valid()` in `drivers/irqchip/irq-gic-v3-its.c`.
- `gicr_write_vpendbaser()`: the raw accessor, not the helper; on arm64 it is
  `writeq_relaxed()` with no polling and no erratum handling.
- `gicr_write_vpendbaser()` on 32-bit Arm
  (`arch/arm/include/asm/arch_gicv3.h`): if Valid reads set in the register
  it first clears Valid with a 32-bit write, then writes the low word, then
  the high word.
- The helper changes other bits in the same write that clears Valid: it
  applies `clr` and `set` to the value, as `its_vpe_4_1_deschedule()` uses
  for `GICR_VPENDBASER_4_1_DB`.
- `its_cpu_init_lpis()`: calls the helper only when `gic_rdists->has_vlpis`
  is set and `gic_rdists->has_rvpeid` is not.
- Writes that do not use the helper: `its_vpe_schedule()`,
  `its_vpe_4_1_schedule()`, `allocate_vpe_l1_table()`, and
  `__gic_update_rdist_properties()` in `drivers/irqchip/irq-gic-v3.c`.
- `allocate_vpe_l1_table()` and `__gic_update_rdist_properties()`: only when
  Valid reads 1, write the constant `GICR_VPENDBASER_PendingLast`; neither
  polls Dirty and neither reads a result back.
- `__gic_update_rdist_properties()`: runs from `gic_init_bases()` before
  `its_init()`, for each redistributor with `GICR_TYPER_VLPIS` and
  `GICR_TYPER_RVPEID`; it is the one write that also reaches the
  redistributors of other CPUs.
- `its_vpe_schedule()` and `its_vpe_4_1_schedule()`: neither reads the
  register nor tests Valid first; `vgic_v4_load()` calls in only when
  `vpe->resident` is false.
- **Unsafe usage**: using PendingLast read from `GICR_VPENDBASER` after
  clearing Valid, without waiting for `GICR_VPENDBASER_Dirty` to read 0.
  - Safe: take the value returned by `its_clear_vpend_valid()`, as
    `its_vpe_deschedule()` does; `read_vpend_dirty_clear()` does the wait
    and the helper forces PendingLast to 1 when Dirty never clears.
- **Unsafe usage**: calling `its_make_vpe_resident()`,
  `its_make_vpe_non_resident()` or `its_commit_vpe()` from preemptible
  context.
  - Safe: with preemption disabled, as `check_vcpu_requests()` and
    `kvm_vcpu_wfi()` do; each of the three has `WARN_ON(preemptible())`, and
    `gic_data_rdist_vlpi_base()` resolves to the current CPU's
    redistributor.

**What the architecture specification says**

From the Arm Generic Interrupt Controller Architecture Specification, GICv3
and GICv4 (ARM IHI 0069), and what each statement means for this code. A
kernel tree cannot supply these, so they are kept by hand and inserted as
they are.

*   **Wait for `GICR_VPENDBASER.Dirty` to clear before descheduling.** The
    redistributor sets Dirty while it is parsing the virtual pending table
    after a schedule, and the code path between making a vPE resident and
    entering the guest is preemptible, so a deschedule can arrive mid-scan. On
    GICv4.1 the architecture is explicit in both directions: with `Valid == 0`,
    "Writing 1 to GICR_VPENDBASER.Valid is UNPREDICTABLE while
    GICR_VPENDBASER.Dirty == 1"; with `Valid == 1`, "Writing 0 to
    GICR_VPENDBASER.Valid is UNPREDICTABLE while GICR_VPENDBASER.Dirty == 1".
    Do not quote that pairing at a GICv4.0 implementation: `GICR_VPENDBASER`
    has two full field-description variants, and in the GICv4.0 one the
    `Valid == 1` sub-case reads "Writing **1**", additionally gated on
    `GICR_TYPER.Dirty == 1`. The rule in the next bullet is the
    variant-independent one and is the safer thing to cite.
    `its_clear_vpend_valid()` opens by
    waiting for Dirty to clear, under the comment "Make sure we wait until the
    RD is done with the initial scan", which makes it a full residency barrier
    rather than just a Valid-clearing helper.

*   **The whole-register rule is stricter than the Dirty rule alone.** "Writing
    a new value to any bit of GICR_VPENDBASER, other than
    GICR_VPENDBASER.Valid, when GICR_VPENDBASER.Valid==1 is UNPREDICTABLE." A
    patch that adjusts any other field of a live `GICR_VPENDBASER` — even one
    that looks advisory — is outside the architecture.

## Virtual interrupts and their lifetime

**One virtual interrupt**

- `vcpu` of an SGI or PPI: NULL unless queued, exactly as for SPIs and LPIs;
  `vgic_allocate_private_irqs_locked()` sets `vcpu = NULL` and puts the owner
  in `target_vcpu`. The comment on the field in `include/kvm/arm_vgic.h` says
  otherwise.
- `target_vcpu` can be NULL: `vgic_add_lpi()` gets NULL for an unmapped
  collection, and `vgic_mmio_write_irouter()` stores whatever
  `kvm_mpidr_to_vcpu()` returns.
- `refcount`: a plain `refcount_t`, not a `struct kref`; changed without
  `irq_lock`.
- `private_irqs` in `struct vgic_cpu`: a pointer to a separately allocated
  array, made by `vgic_allocate_private_irqs_locked()`, which runs from
  `kvm_vgic_create()` for vCPUs that already exist and from
  `kvm_vgic_vcpu_init()` for later ones.
- `private_irqs` is freed in `__kvm_vgic_vcpu_destroy()`, and on the error path
  of `kvm_vgic_create()`.

**vGIC lock order**

- Documented order, outermost first: `kvm->lock`, `vcpu->mutex`,
  `kvm->arch.config_lock`, `its->cmd_lock`, `its->its_lock`,
  `lpi_xa.xa_lock`, `ap_list_lock`, `irq_lock`.
- `config_lock` has a second documented chain: `kvm->slots_lock`, then
  `kvm->srcu`, then `config_lock`.
- "IRQs disabled" does not mean every acquisition is an `_irqsave` call:
  `vgic_prune_ap_list()` takes `ap_list_lock` with plain `raw_spin_lock()` and
  `vgic_flush_state()` with `scoped_guard(raw_spinlock)`; both rely on the
  caller having IRQs off.
- That reliance is checked by `DEBUG_SPINLOCK_BUG_ON(!irqs_disabled())` in
  `vgic_prune_ap_list()` and `kvm_vgic_flush_hwstate()`, which is empty
  without `CONFIG_DEBUG_SPINLOCK`.
- `irq_lock` nested inside an `ap_list_lock` taken with IRQs off is likewise
  taken with plain `raw_spin_lock()`, for example in
  `vgic_queue_irq_unlock()`.
- `lpi_xa`: initialised with `XA_FLAGS_LOCK_IRQ` in `kvm_vgic_early_init()`.
- Reason given by the comment: `ap_list_lock` may be taken from the timer
  interrupt handler, so it and every lock below it need IRQs off; injection
  from ISRs is the second reason given.
- Two `ap_list_lock`s are taken only in `vgic_prune_ap_list()`;
  `vgic_queue_irq_unlock()` takes one.

**Looking up a virtual interrupt**

- `vgic_get_irq()` on a private ID: returns NULL with no warning.
- `vgic_get_irq()` on a GICv5 VM: returns NULL for every ID; the
  `vgic_is_v5()` test is its first statement.
- SPI index: `VGIC_NR_PRIVATE_IRQS` is subtracted first, then the result is
  clamped with `array_index_nospec(intid, nr_spis)`.
- `vgic_get_vcpu_irq()` with a NULL `vcpu`: `WARN_ON()` and NULL.
- `vgic_get_vcpu_irq()` picks the private branch with `__irq_is_sgi()` and
  `__irq_is_ppi()` on the VM's model; the GICv5 branch indexes by
  `vgic_v5_get_hwirq_id()` and bounds and clamps against
  `VGIC_V5_NR_PRIVATE_IRQS`.
- Neither function tests `private_irqs` or `spis` for NULL; `nr_spis` can be
  non-zero (set through `KVM_DEV_ARM_VGIC_GRP_NR_IRQS`) before
  `kvm_vgic_dist_init()` allocates `spis`. Callers such as
  `kvm_vgic_inject_irq()` test `vgic_initialized()` first.
- Only an LPI result carries a reference. A missing `vgic_put_irq()` is a leak
  only where the ID can be an LPI; `kvm_vgic_set_owner()` omits the put after
  rejecting everything but PPIs and SPIs.

**References on an LPI**

- `lpi_xa` itself holds no reference. A new LPI starts at count 1, and that one
  reference is the one `vgic_add_lpi()` returns and the caller stores in
  `ite->irq`.
- `vgic_add_lpi()` produces the returned reference in one of three ways:
  `vgic_get_irq()` at entry, `vgic_try_get_irq_ref()` on an object found under
  the xarray lock, or `refcount_set()` on a new object.
- There is no vgic_irq_get_ref() here; the unconditional get is
  `vgic_get_irq_ref()` in `arch/arm64/kvm/vgic/vgic.h`.
- `vgic_get_irq_ref()`: only for callers that already hold a reference; at
  count zero it warns once and takes nothing.
- `ap_list` reference: dropped with `vgic_put_irq_norelease()` in
  `vgic_prune_ap_list()` and `vgic_flush_pending_lpis()`; vCPU teardown goes
  through the latter from `__kvm_vgic_vcpu_destroy()`.

**Dropping a reference**

- `vgic_put_irq()` uses `refcount_dec_and_lock_irqsave()` on
  `lpi_xa.xa_lock`: the lock is taken only for the drop from one to zero, and
  the final decrement happens under it.
- `vgic_put_irq()` does not call `__vgic_put_irq()`; only
  `vgic_put_irq_norelease()` does.
- `vgic_release_lpi_locked()`: does both `__xa_erase()` and `kfree_rcu()` while
  the xarray lock is still held.
- A lookup under the xarray lock never sees a zero-count object left by
  `vgic_put_irq()`. A lookup under RCU can still load the pointer, and
  `vgic_put_irq_norelease()` does leave zero-count objects in `lpi_xa`.
- Lock debugging: the test is `IS_ENABLED(CONFIG_LOCKDEP)` and the ID being an
  LPI; it really takes and releases `lpi_xa.xa_lock` through
  `guard(spinlock_irqsave)`, before the decrement. It does not call
  `might_lock()`.

**Deferred release**

- `vgic_put_irq_norelease()` and `vgic_release_deleted_lpis()`: both `static`
  in `arch/arm64/kvm/vgic/vgic.c`, so only code in that file can use them.
- `vgic_put_irq_norelease()`: for an LPI returns the result of
  `refcount_dec_and_test()`, for any other interrupt false; it records nothing
  else; there is no pending_release field and no xarray mark.
- `vgic_release_deleted_lpis()`: walks all of `lpi_xa` under
  `xa_lock_irqsave()` and releases every entry whose `refcount_read()` is zero,
  including entries another vCPU's put left behind.
- Between the put and the sweep `vgic_add_lpi()` may already have evicted and
  freed the object, so the sweep can release nothing for that ID.

**Registering an LPI**

- At entry: `vgic_get_irq()`; an LPI that already exists is returned at once
  with that reference, skipping everything below.
- Before the lock, besides allocating and initialising the object:
  `xa_reserve_irq()` with `GFP_KERNEL_ACCOUNT`; on failure the object is freed
  and `ERR_PTR()` returned.
- Store under the lock: `__xa_store()` with `GFP_NOWAIT | __GFP_ACCOUNT`.
- Slot holds a zero-count object: `__xa_store()` replaces it, and the old
  object is freed with `kfree_rcu()` under the lock.
- If the displaced object's count is not zero, `WARN_ON_ONCE()` fires and it is
  not freed.
- `__xa_store()` failure: unlock, `kfree()` the new object, `ERR_PTR()`. It
  does not call `xa_release()`.
- Later failures are `update_lpi_config()` and
  `vgic_v3_lpi_sync_pending_status()`; each is undone with `vgic_put_irq()`,
  which removes a new object from `lpi_xa` and frees it when that was the last
  reference.
- Those two steps also run when a live object was found under the lock; the put
  on failure then drops only the reference just taken.
- Callers allocate the ITE before the call. On `IS_ERR()` they call
  `its_free_ite()`, whose `irq` is still NULL so no put happens;
  `vgic_its_cmd_handle_mapi()` also frees a collection it created.

**Disabling LPIs on a redistributor**

- `vgic_mmio_write_v3r_ctlr()`: does nothing without an ITS, and flushes only
  if `atomic_cmpxchg_acquire()` moves `ctlr` from `GICR_CTLR_ENABLE_LPIS` to
  `GICR_CTLR_RWP`.
- `vgic_flush_pending_lpis()` clears `pending_latch` on each LPI it removes, in
  addition to `list_del()` and `vcpu = NULL`.
- Only LPIs on this vCPU's `ap_list` are touched; an LPI that is latched
  pending but not queued keeps its `pending_latch`.
- After releasing `ap_list_lock` the function itself calls
  `vgic_release_deleted_lpis()` if any put returned true.

**The translation cache**

- `translation_cache` in `struct vgic_its`: an xarray whose entries are the
  `struct vgic_irq` pointers themselves, keyed by `vgic_its_cache_key()`. There
  is no vgic_translation_cache_entry structure, no list and no lock besides
  the xarray's own.
- **Unsafe usage**: dropping the cache's reference on the pointer the walk
  yielded.
  - Safe: put only the non-NULL value `xa_erase()` returned, as
    `vgic_its_invalidate_cache()` does; two walkers can race, and only the one
    whose erase succeeds owns the reference.
- `vgic_its_invalidate_cache()` must not sleep:
  `vgic_its_invalidate_all_caches()` calls it inside `rcu_read_lock()`.
- Invalidating paths hold different locks. ITS command handlers hold
  `its_lock`; `vgic_mmio_write_its_ctlr()` holds `cmd_lock` but not
  `its_lock`; `vgic_its_invalidate_all_caches()` holds neither.
- `vgic_its_invalidate_all_caches()` has one caller,
  `vgic_mmio_write_v3r_ctlr()`.
- Order against `its_free_ite()` is free: `vgic_its_cmd_handle_discard()`
  invalidates first, `vgic_its_free_device()` frees the ITEs first. The cache's
  own reference keeps the object alive either way.

**Storing a cached translation**

- `vgic_its_cache_translation()` makes one test of its own: `irq->hw`, which
  returns before the reference is taken.
- Its caller is `vgic_its_resolve_lpi()`, which returns before the call when
  the ITS is disabled, the ITE or a mapped collection is missing, the vCPU does
  not exist, or `vgic_lpis_enabled()` is false.
- The cache has no size limit and no eviction; `xa_store()` displaces an entry
  only when the same key is already present.

**The debugfs state file**

- There is no marking scheme here: no iter_mark_lpis(), no
  LPI_XA_MARK_DEBUG_ITER, and no reference held across the iteration.
- Next LPI: `iter_next()` calls `xa_find_after()` on `lpi_xa` with
  `XA_PRESENT`, under `rcu_read_lock()`, and keeps only the ID in `intid`.
- End of the LPIs: `intid` is set to `VGIC_LPI_MAX_INTID + 1`.
- `struct vgic_state_iter` has no LPI index or count field.
- Interrupt gone: `vgic_debug_show()` returns 0 and prints nothing when
  `vgic_get_irq()` returns NULL; no warning and no error.

**References taken by lookups**

- **Unsafe usage**: taking the reference on a pointer just loaded from `lpi_xa`
  with `vgic_get_irq_ref()`.
  - Unsafe: at count zero `vgic_get_irq_ref()` warns once and takes nothing, so
    the caller's later put underflows a freed or dying object.
  - Safe: `vgic_try_get_irq_ref()` and return NULL on false, as
    `vgic_get_lpi()` does.
- **Potentially unsafe usage**: reading fields of an entry of `lpi_xa` before
  holding a reference.
  - Unsafe: outside both `rcu_read_lock()` and `lpi_xa.xa_lock`; the object is
    freed by `kfree_rcu()` in `vgic_release_lpi_locked()`.
  - Safe: inside the RCU section, before the try-get, as
    `__vgic_host_irq_get_vlpi()` in `arch/arm64/kvm/vgic/vgic-v4.c` does with
    `hw` and `host_irq`.
  - Safe: under `lpi_xa.xa_lock`, as `vgic_release_deleted_lpis()` does.
- Walkers of `lpi_xa` outside RCU, for example `vgic_its_invall()` and
  `vgic_v3_save_pending_tables()`, discard the pointer `xa_for_each()` yields
  and call `vgic_get_irq()` on the index.
- Lookups that take a reference from `lpi_xa`: `vgic_get_lpi()`,
  `vgic_add_lpi()` and `__vgic_host_irq_get_vlpi()`; `vgic_its_check_cache()`
  does the same on `translation_cache`.
- The debugfs iterator is not one of them; it takes no reference from `lpi_xa`.

## List registers

**Queueing an interrupt**

- `irq->ops->queue_irq_unlock`: tested first; if set,
  `vgic_queue_irq_unlock()` returns its result and does nothing else.
- `vgic_v5_ppi_queue_irq_unlock()` in `arch/arm64/kvm/vgic/vgic-v5.c` is the
  only implementation: drops `irq_lock`, kicks `irq->target_vcpu`, returns
  true, never touches an ap_list or a reference.
- Reference: taken with `vgic_get_irq_ref()` from
  `arch/arm64/kvm/vgic/vgic.h`; there is no vgic_get_irq_kref() here.
- `vgic_get_irq_ref()` on an SGI, PPI or SPI of a GICv2 or GICv3 guest:
  no-op; `irq->refcount` changes only for `intid >= VGIC_MIN_LPI`.
- Caller's own reference: required; `vgic_get_irq_ref()` uses
  `refcount_inc_not_zero()` and only does `WARN_ON_ONCE()` on failure, then
  the interrupt is queued anyway.

**Kick after queueing**

- Kick of all vCPUs: `kvm_make_all_cpus_request(kvm, KVM_REQ_IRQ_PENDING)`
  when `bcast` is true; otherwise only the vCPU the interrupt was queued on.
- `bcast` needs all three, tested in this order with `&&`:
  - `vgic_model_needs_bcst_kick()`: host has `ARM64_HAS_ICH_HCR_EL2_TDIR` and
    the guest model is `KVM_DEV_TYPE_ARM_VGIC_V3`;
  - `vgic_valid_spi()` for the INTID;
  - `atomic_fetch_inc(&kvm->arch.vgic.active_spis)` returned 0.
- `active_spis`: incremented only when the first two hold, so it stays 0 for
  a GICv2 guest model and on hosts without the capability.
- `bcast` is computed under both locks; the kick is made after both are
  dropped.
- Purpose of the broadcast: each vCPU re-runs `vgic_v3_configure_hcr()`, which
  sets `ICH_HCR_EL2_TDIR` when `active_spis` is non-zero.
- Not-queued return (`irq->vcpu` set, oracle non-NULL): the oracle's vCPU
  alone is kicked; never a broadcast.

**ap_list pruning and migration**

- Kept alive by an extra reference: `vgic_get_irq_ref()` is called under
  `irq_lock`, before `irq_lock` and `ap_list_lock` are dropped.
- Extra reference dropped with `vgic_put_irq_norelease()`, not
  `vgic_put_irq()`, after all three locks are released.
- A dropped-to-zero LPI is freed later by `vgic_release_deleted_lpis()`, which
  takes `lpi_xa.xa_lock`, after the walk has released `ap_list_lock`.
- Check before the move: `irq->vcpu == vcpu && target_vcpu ==
  vgic_target_oracle(irq)`; `target_vcpu` is the value from before the unlock.
- `goto retry` runs after the move and after a failed check alike.
- `active_spis`: not touched by `vgic_prune_ap_list()`.
- **Unsafe usage**: moving the interrupt after the relock on the oracle
  comparison alone.
  - Unsafe: the entry may have left this list in the window
    (`vgic_flush_pending_lpis()` does `list_del()` and clears `irq->vcpu`), so
    `list_del()` runs on an entry that is not on `vcpu`'s list.
  - Safe: test `irq->vcpu == vcpu` as well, with both `ap_list_lock`s and
    `irq_lock` held, as `vgic_prune_ap_list()` does; `vgic_target_oracle()`
    asserts `irq_lock`.
- **Unsafe usage**: continuing the `list_for_each_entry_safe()` walk after
  `ap_list_lock` was dropped.
  - Unsafe: `tmp` was read before the unlock and may be off the list.
  - Safe: restart from the head, as `vgic_prune_ap_list()` does with
    `goto retry`.

**Filling the list registers**

- There is no compute_ap_list_depth() or multi_sgi flag here;
  `summarize_ap_list()` fills `struct ap_list_summary` (`nr_pend`, `nr_act`,
  `nr_sgi`) from entries whose oracle is this vCPU.
- `summarize_ap_list()`: one count per entry; a multi-source SGI counts once;
  pending+active goes to `nr_act`.
- Sort condition: only `irqs_outside_lrs()`, i.e. `nr_pend + nr_act >
  kvm_vgic_global_state.nr_lr`; multi-source SGIs do not trigger it.
- Sort keys of `vgic_irq_cmp()`, in order:
  1. oracle is this vCPU, before others;
  2. group enabled in the VMCR (`grpen0`/`grpen1`), before disabled;
  3. enabled, pending and not active, before the rest (pending+active sorts
     with active);
  4. lower `priority` value first;
  5. `irq->hw` set, before clear.
- `last_lr_irq`: a pointer in per-CPU `struct kvm_host_data`, accessed as
  `*host_data_ptr(last_lr_irq)`; not a field of `struct vgic_cpu`.
- `last_lr_irq` is set to NULL at each flush, then to each populated
  interrupt in turn.
- `last_lr_irq` NULL at exit: `vgic_fold_state()` returns without calling
  `vgic_v3_fold_lr_state()`.
- `vgic_v3_configure_hcr()`: returns at once without `irqchip_in_kernel()`;
  otherwise restarts `vgic_hcr` from `ICH_HCR_EL2_En`.

| Bit | Condition |
|---|---|
| `ICH_HCR_EL2_NPIE` | `irqs_pending_outside_lrs()`: `nr_pend > nr_lr` |
| `ICH_HCR_EL2_LRENPIE` | `irqs_active_outside_lrs()`: `nr_act` non-zero and `irqs_outside_lrs()` |
| `ICH_HCR_EL2_UIE` | `irqs_outside_lrs()` |
| `ICH_HCR_EL2_vSGIEOICount` | `nr_sgi == 0` |
| `ICH_HCR_EL2_VGrp0DIE` / `ICH_HCR_EL2_VGrp0EIE` | group 0 enabled / disabled in `vgic_vmcr` |
| `ICH_HCR_EL2_VGrp1DIE` / `ICH_HCR_EL2_VGrp1EIE` | group 1 enabled / disabled in `vgic_vmcr` |
| `ICH_HCR_EL2_TDIR` | see "Deactivations by trap" |

**Encoding a list register**

- `ICH_LR_HW`: set when `irq->hw && !vgic_irq_needs_resampling(irq)`; GICv2
  SGI handling plays no part.
- `vgic_irq_needs_resampling()` interrupt: takes the non-HW branch, so a level
  one gets `ICH_LR_EOI`.
- Pending withheld only when `irq->active` and one of:
  - `vgic_irq_is_multi_sgi()`;
  - the `ICH_LR_HW` case;
  - non-HW branch with `VGIC_CONFIG_LEVEL`.
- `line_level` being low does not withhold pending by a test of its own; it
  only enters through `irq_is_pending()`.
- `on_lr` in `vgic_v3_compute_lr()`: `WARN_ON(irq->on_lr)` only; the value is
  still computed and returned.
- `vgic_flush_lr_state()` has no `on_lr` test besides that `WARN_ON()`; it
  relies on each interrupt being one ap_list entry and on fold having cleared
  `on_lr`.
- `vgic_v3_compute_lr()` callers that build a pseudo-LR:
  `vgic_v3_fold_lr_state()` and `vgic_v3_deactivate()`.
- **Unsafe usage**: building a pseudo-LR for an interrupt whose `on_lr` is
  set.
  - Unsafe: the real LR holds the state; folding the pseudo-LR overwrites
    `irq->active` and clears `on_lr` while the LR is live.
  - Safe: test `irq->on_lr` under `irq_lock` first, as `vgic_v3_deactivate()`
    does.
  - Safe: walk only entries after `last_lr_irq`, after every used LR was
    folded, as `vgic_v3_fold_lr_state()` does.

**GICv2 SGI sources**

- Exit for the next source: `ICH_LR_EOI` in the LR, set by
  `vgic_v3_compute_lr()` when `irq->source` has bits besides the chosen one;
  `ICH_HCR_EL2_NPIE` is not used for this.
- `vgic_flush_lr_state()`: no special case; the SGI takes one LR, is counted
  once, and lower-priority entries behind it are still loaded.
- SGI active with sources pending: the LR carries active state with
  `irq->active_source` in the CPUID field, `ICH_LR_EOI`, and no pending bit.
- Next source is loaded by a later flush, once `irq->active` is clear.
- `vgic_v3_fold_lr()` on a v2 SGI: active LR writes CPUID to
  `irq->active_source`; pending LR sets the CPUID bit back in `irq->source`.
- Pending with `irq->source == 0`: `WARN_RATELIMIT()`, `vgic_v3_compute_lr()`
  returns 0; `vgic_v3_populate_lr()` stores that 0 in the LR and still sets
  `on_lr`.

**Reading the list registers back**

- Lookup: `vgic_get_vcpu_irq()` returns the interrupt or NULL; on NULL
  `vgic_v3_fold_lr()` returns at once.
- Lookup reference: dropped by `vgic_put_irq()` at the end.

| Kind | Taken from the LR |
|---|---|
| LPI (`intid >= VGIC_MIN_LPI`) | active bit discarded, `irq->active` = false |
| others | `irq->active` = `ICH_LR_ACTIVE_BIT` |
| edge | pending bit set: `pending_latch = true`; fold never clears it |
| level | both `ICH_LR_STATE` bits clear: `pending_latch = false`; `line_level` not taken from the LR |
| mapped level | `vgic_irq_handle_resampling()`, below |

- `vgic_irq_handle_resampling()`, ordinary mapped level: re-reads the
  physical line when the LR is still pending, or when deactivated with
  `irq->line_level` set; clears physical active if the line is low.
- `deactivated`: `irq->active` was set before the fold and the LR's active
  bit is clear.
- `kvm_notify_acked_irq()` in `vgic_v3_fold_lr()`: called when `deactivated`,
  `lr_signals_eoi_mi()` and `vgic_valid_spi()` all hold.
- The notification runs after `irq_lock` is released and before
  `vgic_put_irq()`.
- `vgic_v2_fold_lr()` in `arch/arm64/kvm/vgic/vgic-v2.c`: notifies on
  `lr_signals_eoi_mi()` and `vgic_valid_spi()` alone, before its lookup.

**Deactivations outside the list registers**

- `ICH_HCR_EL2_EOIcount` in `cpuif->vgic_hcr`: `__vgic_v3_save_state()` in
  `arch/arm64/kvm/hyp/vgic-v3-sr.c` copies it from hardware only when
  `ICH_HCR_EL2_LRENPIE` is set in `vgic_hcr`.
- Count starts at 0 on each entry: `vgic_v3_configure_hcr()` rewrites
  `vgic_hcr`.
- Walk start: `list_for_each_entry_continue()` from `last_lr_irq`, so the
  first entry looked at is the one after it.
- Why there: every entry that was in an LR is at or before `last_lr_irq`, and
  was folded from the real LR value just before the walk.
- Per matched entry: `vgic_v3_compute_lr()` with `ICH_LR_ACTIVE_BIT` cleared
  is passed to `vgic_v3_fold_lr()`; `irq->active` is not cleared directly, so
  fold's notification and resampling apply.
- Hardware-backed entry: `vgic_v3_deactivate_phys()` when the pseudo-LR has
  `ICH_LR_HW`; it uses `gic_write_dir()`, or the GICv5 CDDI instruction with
  `ARM64_HAS_GICV5_LEGACY`.
- `vgic_v3_fold_lr_state()` does not call `irq_set_irqchip_state()` or
  `vgic_irq_set_phys_active()` itself.
- Mapped level `vgic_irq_needs_resampling()` interrupt: pseudo-LR has no
  `ICH_LR_HW`; physical active is cleared inside fold by
  `vgic_irq_handle_resampling()`.

**Deactivations by trap**

- `ICH_HCR_EL2_TDIR` in `vgic_hcr`: set by `vgic_v3_configure_hcr()` when any
  of these holds, whatever the guest's EOImode:
  - host lacks `ARM64_HAS_ICH_HCR_EL2_TDIR`;
  - `irqs_active_outside_lrs()`;
  - `active_spis` is non-zero.
- With `vgic_v3_cpuif_trap` enabled, `__vgic_v3_perform_cpuif_access()`
  handles the trapped write first:
  - `ICH_HCR_EL2_TDIR` set in `vgic_hcr`: `___vgic_v3_write_dir()` finishes
    at hyp for EOImode 0, an LPI, or an INTID active in this vCPU's LRs;
    anything else exits to `access_gic_dir()` in `arch/arm64/kvm/sys_regs.c`;
  - bit clear in `vgic_hcr`: `__vgic_v3_write_dir()` finishes at hyp, and
    bumps EOIcount in the case that would exit with the bit set.
- `active_spis` (`atomic_t` in `struct vgic_dist`): not an exact count of
  active SPIs.
  - Incremented in `vgic_queue_irq_unlock()` per SPI queued, only when
    `vgic_model_needs_bcst_kick()`.
  - Decremented only in `vgic_v3_fold_lr()`, with `atomic_dec_if_positive()`,
    on the irqfd condition in "Reading the list registers back".
  - Readers test it against zero only.
- `vgic_v3_deactivate()` returns at once for EOImode 0 in `vgic_vmcr`, or an
  INTID at or above `nr_spis + VGIC_NR_PRIVATE_IRQS`.

| Interrupt | Physical deactivation |
|---|---|
| `irq->vcpu` NULL | none |
| `on_lr` set | via `vgic_mmio_write_cactive()`: `vgic_irq_set_phys_active()` for `irq->hw` non-SGI |
| v2 SGI, `active_source` != CPUID | none |
| pseudo-LR has `ICH_LR_HW`, vCPU not nested | `vgic_v3_deactivate_phys()` |
| pseudo-LR has `ICH_LR_HW`, `vgic_state_is_nested()` | none |
| pseudo-LR without `ICH_LR_HW` | none by `vgic_v3_deactivate()`; fold only |

**What the architecture specification says**

From the Arm Generic Interrupt Controller Architecture Specification, GICv3
and GICv4 (ARM IHI 0069), and what each statement means for this code. A
kernel tree cannot supply these, so they are kept by hand and inserted as
they are.

*   **Two list registers must not hold the same virtual INTID unless both are
    Invalid.** The architecture states that "Behavior is UNPREDICTABLE if two or
    more List Registers specify the same vINTID when: • ICH_LR<n>_EL2.State ==
    0b01. • ICH_LR<n>_EL2.State == 0b10. • ICH_LR<n>_EL2.State == 0b11." Only
    the Invalid state is exempt. This is what makes multi-source software
    interrupts awkward: distinct sources are architecturally distinct interrupt
    events but must not occupy several list registers at once, so the emulation
    injects one per entry and arranges a maintenance interrupt to deliver the
    rest.

*   **The physical INTID rule is a different rule.** In the separate list of
    programming errors that result in UNPREDICTABLE behaviour, the architecture
    names "Having two or more interrupts with the same pINTID in the List
    registers for a single virtual CPU interface." Two list registers may carry
    the same *physical* INTID in some other arrangement no more than they may
    carry the same virtual one, but the two statements are in different
    sections, constrain different fields, and cannot be cited for each other.
    If a patch or review comment cites one section for the other's claim, the
    citation is wrong even if the conclusion happens to hold.

*   **Special INTIDs and the LPI range have their own constraints.** A virtual
    INTID in 1020-1023 in a list register whose state is not Inactive is
    UNPREDICTABLE, and specifying a virtual INTID in the LPI range while
    `ICC_SRE_EL1.SRE == 0` is UNPREDICTABLE.

## World switch

**Deliverable interrupt check**

- `vgic_is_v5()`: tested first; a GICv5 VM returns
  `vgic_v5_has_pending_ppi()` and none of the checks below run.
- `its_vpe.pending_last`: read directly, with no
  `vgic_supports_direct_irqs()` test and no helper call.
- `its_vpe_4_1_deschedule()` without a doorbell request: sets `pending_last`
  to true unconditionally, so true does not imply a pending VLPI.
- Nothing under `arch/arm64/kvm` clears `pending_last`.
- Per-interrupt test: `irq_is_pending(irq) && irq->enabled && !irq->active &&
  irq->priority < vmcr.pmr`; an active interrupt never counts.
- Group enables: decoded by `vgic_get_vmcr()` but not used; only `pmr` is.
- `pmr` freshness: `vgic_vmcr` is rewritten at every guest exit (see "The
  virtual machine control register"); `kvm_vgic_put()` in `kvm_vcpu_wfi()`
  does not read the VMCR on a GICv3 host.
- Callers besides `kvm_arch_vcpu_runnable()`: `vgic_kick_vcpus()` calls it for
  every vCPU of the VM, running or not, and only kicks on true;
  `kvm_vgic_flush_hwstate()` calls it in nested state.

**The virtual machine control register**

- There is no vgic_v3_vmcr_sync() and no __vgic_v3_save_vmcr_aprs() here; no
  code reads `ICH_VMCR_EL2` at put.

| Direction | GICv3 guest (`vgic_sre` set) | GICv2 guest (`vgic_sre` clear) |
|---|---|---|
| hardware to `vgic_vmcr` | every exit, `__vgic_v3_save_state()` | every exit, same function |
| `vgic_vmcr` to hardware | load, `__vgic_v3_restore_vmcr_aprs()` | `__vgic_v3_activate_traps()`: load with VHE, every entry without |

- `__vgic_v3_save_state()`: reads `ICH_VMCR_EL2` unconditionally; with VHE it
  runs from `kvm_vgic_sync_hwstate()`, without VHE from
  `__hyp_vgic_save_state()`.
- `__vgic_v3_restore_vmcr_aprs()`: skips the VMCR write when `vgic_sre` is
  clear, and still restores the APRs.
- `__vgic_v3_activate_traps()`: writes the VMCR only when `vgic_sre` is clear
  and `vgic_hcr` has `ICH_HCR_EL2_En`.
- `__vgic_v3_deactivate_traps()`: does not read or write the VMCR.
- `vgic_get_vmcr()` in `arch/arm64/kvm/vgic/vgic-mmio.c`: switches on
  `vgic_model`, not on `kvm_vgic_global_state.type`.
- GICv2 model on a GICv3 CPU interface: `vgic_get_vmcr()` calls
  `vgic_v3_get_vmcr()`, which decodes `vgic_v3.vgic_vmcr`; `vgic_v2_get_vmcr()`
  is used only on GICv2 hardware.
- `vgic_vmcr` outside the guest: equals the hardware value as of the last
  exit; no extra sync is needed before `vgic_get_vmcr()`.
- pKVM, write to hardware: `kvm_arch_vcpu_load()` issues the
  `__vgic_v3_restore_vmcr_aprs` hypercall; `handle___vgic_v3_restore_vmcr_aprs()`
  copies the host `vgic_vmcr` into the hyp vCPU first.
- pKVM, save: `__vgic_v3_save_state()` fills the hyp copy at each exit;
  `sync_hyp_vgic_state()` copies it to the host after each run.
- Nested state: `vgic_v3_sync_nested()` reads `ICH_VMCR_EL2` into the vCPU's
  `ICH_VMCR_EL2` sysreg at each exit; `vgic_v3_load_nested()` loads the
  shadow built from that sysreg; `vgic_vmcr` of the vCPU is not touched.

**Loading and putting a vCPU**

- `vgic_v3_put()`: saves only the APRs, through `__vgic_v3_save_aprs()`; the
  VMCR is covered in "The virtual machine control register".
- vgic_fold_lr_state is not a function here; `kvm_vgic_sync_hwstate()` calls
  `vgic_fold_state()`, which calls `vgic_v3_fold_lr_state()`.
- `kvm_vgic_flush_hwstate()`: does not prune; `vgic_prune_ap_list()` runs from
  `kvm_vgic_sync_hwstate()` and `kvm_vgic_process_async_update()`.
- `kvm_vgic_flush_hwstate()`: has no empty-list short-cut; outside nested
  state and for a VM that is not GICv5 it always runs
  `vgic_flush_lr_state()`, which rewrites `used_lrs` and the first
  `kvm_vgic_global_state.nr_lr` slots of `vgic_lr[]`, and `vgic_hcr` when
  `irqchip_in_kernel()`.
- pKVM condition: `is_protected_kvm_enabled()`, so it covers every guest on a
  pKVM host, protected or not.
- pKVM load: `vgic_v3_load()` skips the hypercall; `kvm_arch_vcpu_load()`
  issues `__vgic_v3_restore_vmcr_aprs` after `__pkvm_vcpu_load`.
- pKVM put: `vgic_v3_put()` skips the hypercall; `kvm_arch_vcpu_put()` issues
  `__vgic_v3_save_aprs` before `__pkvm_vcpu_put`.
- pKVM and `kvm_vcpu_wfi()`: its `kvm_vgic_put()`/`kvm_vgic_load()` pair
  therefore saves and restores no APRs.
- `flush_hyp_vgic_state()` (each run, host to hyp): copies `vgic_hcr`,
  `used_lrs` clamped to `hyp_gicv3_nr_lr`, and the used `vgic_lr[]`; forces
  `vgic_sre`.
- `sync_hyp_vgic_state()` (each run, hyp to host): copies `vgic_hcr`,
  `vgic_vmcr` and the used `vgic_lr[]`.
- pKVM APRs: host to hyp in `handle___vgic_v3_restore_vmcr_aprs()`, hyp to
  host in `handle___vgic_v3_save_aprs()`; never per run.
- Nested state, entry and exit: `kvm_vgic_flush_hwstate()` and
  `kvm_vgic_sync_hwstate()` return early after `vgic_v3_flush_nested()` and
  `vgic_v3_sync_nested()`; `vgic_flush_state()` and `vgic_fold_state()` do
  not run.

**Trapping the CPU interface**

- Group enables in the VMCR do not select any trap bit.

| Condition | Bits | Held in |
|---|---|---|
| `ARM64_WORKAROUND_CAVIUM_30115` | `ICH_HCR_EL2_TALL0`, `ICH_HCR_EL2_TALL1` | patched constant |
| `ARM64_WORKAROUND_GICv3_BROKEN_SEIS` | `ICH_HCR_EL2_TALL0`, `ICH_HCR_EL2_TALL1`, `ICH_HCR_EL2_TDIR` | patched constant |
| no `ARM64_HAS_ICH_HCR_EL2_TDIR` | `ICH_HCR_EL2_TC` | patched constant |
| `kvm-arm.vgic_v3_group0_trap`, `kvm-arm.vgic_v3_group1_trap`, `kvm-arm.vgic_v3_common_trap` | the matching bit | patched constant |
| no in-kernel irqchip | `ICH_HCR_EL2_TALL0`, `ICH_HCR_EL2_TALL1`, `ICH_HCR_EL2_TC` | `vgic_hcr`, by `vcpu_set_ich_hcr()` |
| no `ARM64_HAS_ICH_HCR_EL2_TDIR`, or `irqs_active_outside_lrs()`, or `active_spis` non-zero | `ICH_HCR_EL2_TDIR` | `vgic_hcr`, by `vgic_v3_configure_hcr()` |

- `dir_trap`: has no early parameter; only the broken-SEIS case sets it.
- Patched constant: `kvm_compute_ich_hcr_trap_bits()` is the `ALTERNATIVE_CB()`
  callback of `vgic_ich_hcr_trap_bits()` in `arch/arm64/kvm/vgic/vgic.h`; the
  value is never stored in `vgic_hcr`.
- `vgic_v3_probe()`: computes no trap bits; it calls
  `vgic_v3_enable_cpuif_traps()`, which enables `vgic_v3_cpuif_trap` when the
  constant is non-zero. There is no vgic_v3_enable() here.
- `vcpu_set_ich_hcr()`: called only from `kvm_calculate_traps()`, which
  `kvm_arch_vcpu_run_pid_change()` runs before the vCPU's first run.
- `vgic_v3_configure_hcr()`: assigns `vgic_hcr` from `ICH_HCR_EL2_En` at every
  flush when `irqchip_in_kernel()`; bits ORed in elsewhere do not survive it.
- `__vgic_v3_restore_state()`: writes `compute_ich_hcr()`, which is `vgic_hcr`
  ORed with the constant, to `ICH_HCR_EL2` at every entry, with or without the
  static key.
- `__vgic_v3_activate_traps()`: writes the constant ORed with
  `ICH_HCR_EL2_En`, not `vgic_hcr`, and only if `vgic_v3_cpuif_trap` is on,
  `its_vpe.its_vm` is set or `vgic_sre` is clear.
- `vgic_hcr` without `ICH_HCR_EL2_En` (no vgic): `__vgic_v3_activate_traps()`
  sets `ICC_SRE_EL1.SRE` so that the trap bits take effect.
- `__vgic_v3_save_state()`: writes 0 to `ICH_HCR_EL2` at every exit.
- `vgic_v3_cpuif_trap`: gates only the hyp handler in
  `arch/arm64/kvm/hyp/include/hyp/switch.h` and the `ICH_HCR_EL2` writes in
  `__vgic_v3_activate_traps()` and `__vgic_v3_deactivate_traps()`; per-vCPU
  bits in `vgic_hcr` do not enable it.
- Key off: every trapped access exits to `arch/arm64/kvm/sys_regs.c`; there
  `ICC_DIR_EL1` goes to `access_gic_dir()`, and the group and common
  registers are `undef_access`.
- `access_gic_dir()`: calls `vgic_v3_deactivate()` for a write when
  `kvm_has_gicv3()`; with the key off it handles the trap that
  `ICH_HCR_EL2_TDIR` in `vgic_hcr` causes.
- `__vgic_v3_perform_cpuif_access()`: returns 0 or 1 only; it never returns
  -1 and never injects an exception itself.
- `__vgic_v3_perform_cpuif_access()`: returns 0 at once unless `vgic_model`
  is `KVM_DEV_TYPE_ARM_VGIC_V3`.
- Nested guest: `__vgic_v3_perform_cpuif_access()` returns 0 to the host when
  `__vgic_v3_check_trap_forwarding()` finds that the L1 `ICH_HCR_EL2` or, for
  `ICC_IGRPEN0_EL1` and `ICC_IGRPEN1_EL1`, the L1 `HFGRTR_EL2`/`HFGWTR_EL2`
  asks for the trap.

## Mapped hardware interrupts

**Mapping a hardware interrupt**

- `kvm_vgic_map_phys_irq()`: takes three arguments (vcpu, host irq, virtual
  INTID); there is no `struct irq_ops` argument.
- `kvm_vgic_map_irq()`: besides `irq->hw`, `irq->host_irq` and
  `irq->hwintid`, it calls `irq->ops->set_direct_injection(vcpu, irq, true)`
  when the installed ops has that callback.
- Already mapped interrupt: not rejected; the three fields are overwritten.
- `-EINVAL` from the map: only when `irq_to_desc(host_irq)` returns NULL.
- INTID type: `kvm_vgic_map_phys_irq()` makes no PPI/SPI test, only
  `BUG_ON(!irq)`; the PPI/SPI test is in `kvm_vgic_set_owner()`.
- Reset: `kvm_timer_vcpu_reset()` calls `kvm_vgic_reset_mapped_irq()` only
  when `timer->enabled` and `irqchip_in_kernel()`; it first calls
  `kvm_timer_update_irq(vcpu, false, ...)` for every timer.
- Injection is gated by `irq->owner`, not by `irq->hw`:
  `vgic_validate_injection()` never looks at `irq->hw`, and the map sets no
  owner.
- Owner mismatch: `kvm_vgic_inject_irq()` drops the request and returns 0,
  not an error; `KVM_IRQ_LINE` and irqfd pass `NULL` and get that 0.
- GICv5 VM: `kvm_timer_update_irq()` returns before `kvm_vgic_inject_irq()`
  for `map.direct_vtimer` and `map.direct_ptimer`; the timer does not inject
  those in software.

**Physical interrupt lookup and unmap**

- Physical ID: `kvm_vgic_map_irq()` walks `data->parent_data` from
  `irq_desc_get_irq_data()` to the root and stores that root `hwirq`; it does
  not call `irq_get_irq_data()` or `irqd_to_hwirq()`.
- `kvm_vgic_unmap_irq()`: writes only `irq->hw = false` and
  `irq->hwintid = 0`.
- `irq->host_irq`: left at its old value by the unmap.
- `irq->ops`: not cleared by the unmap.
- Before clearing, the unmap calls
  `irq->ops->set_direct_injection(irq->target_vcpu, irq, false)` when the ops
  has that callback.
- `kvm_vgic_unmap_phys_irq()`: returns `-EAGAIN` and changes nothing when
  `!vgic_initialized()`; `kvm_vgic_map_phys_irq()` has no such test.

**Per-interrupt callbacks**

- `struct irq_ops` has no `flags` field; software resampling is reported by
  the `get_flags()` callback returning `VGIC_IRQ_SW_RESAMPLE`.
- `vgic_irq_needs_resampling()`: defined in `include/kvm/arm_vgic.h`; false
  when `irq->ops` or `irq->ops->get_flags` is NULL.
- The timer's `arch_timer_irq_ops` is `const`;
  `kvm_arch_timer_get_irq_flags()` reads
  `kvm_vgic_global_state.no_hw_deactivation` on every call.
- `get_input_level()`: independent of resampling; an ops may have it and
  still return 0 from `get_flags()`.
- Other callbacks in `struct irq_ops`: `queue_irq_unlock` (replaces the body
  of `vgic_queue_irq_unlock()`) and `set_direct_injection`.
- Installers of `irq->ops`:
  - `kvm_timer_enable()`, for every timer of the vcpu, emulated ones too, and
    before its `kvm_vgic_map_phys_irq()` calls.
  - `vgic_v5_set_ppi_ops()`, from `vgic_v5_setup_private_irq()`, for every
    private interrupt of a GICv5 VM; the timer later replaces it on its own
    interrupts with `arch_timer_irq_ops_vgic_v5`.
- `kvm_vgic_clear_irq_ops()`: installs NULL through
  `kvm_vgic_set_irq_ops()`; nothing in this tree calls it.
- Map and unmap never write `irq->ops`, but both read it for
  `set_direct_injection`; an ops installed after the map misses the
  enable call.
- `irq->ops` set does not imply `irq->hw`: users test `irq->hw` separately,
  for example `vgic_v3_compute_lr()`.

**Resampling a mapped level interrupt**

- Callers of `vgic_irq_handle_resampling()`: `vgic_v3_fold_lr()` and
  `vgic_v2_fold_lr()`, not the fold-state functions directly.
- Those two are also reached from `vgic_v3_deactivate()`,
  `vgic_v2_deactivate()` and the `eoicount` replay loop, with an LR value
  built by `vgic_v3_compute_lr()` or `vgic_v2_compute_lr()`.
- GICv5 VM: `vgic_fold_state()` calls `vgic_v5_fold_ppi_state()` and never
  reaches `vgic_irq_handle_resampling()`.
- Re-read condition without software resampling: only when
  `lr_pending || (lr_deactivated && irq->line_level)`, not on every EOI.
- `vgic_get_phys_line_level()` without `get_input_level()`: reads
  `IRQCHIP_STATE_PENDING` of `irq->host_irq`; it does not fall back to
  `irq->line_level`.
- `irq->line_level`: set to false by `vgic_v3_populate_lr()` and
  `vgic_v2_populate_lr()` when a mapped level interrupt goes into the LR
  as pending; that is why a still-pending LR forces a re-read.
- Software resampling in `vgic_irq_handle_resampling()`: the line is not read
  and `lr_deactivated` and `lr_pending` are ignored; physical active is
  cleared whenever `!(irq->active || irq->pending_latch)`.
- `ICH_LR_HW` and `GICH_LR_HW`: left out for a software-resampled interrupt
  by `vgic_v3_compute_lr()` and `vgic_v2_compute_lr()`.
- Second re-read site: `vgic_mmio_write_senable()` re-reads a mapped level
  line on guest enable and clears physical active if
  `!irq->active && was_high && !irq->line_level`.

**Pending state by accessor**

- hw SGI below means `irq->hw && vgic_irq_is_sgi(irq->intid)`; it is tested
  before the other `irq->hw` tests in all three helpers and ignores
  `is_user`.

| Access | Interrupt | Guest | Userspace |
|---|---|---|---|
| read | hw SGI | physical `IRQCHIP_STATE_PENDING` | same |
| read | mapped level | `vgic_get_phys_line_level()`, latch ignored | as other |
| read | other | `irq_is_pending()` | vGICv3 `irq->pending_latch`; vGICv2 `irq_is_pending()` |
| set | hw SGI | physical pending set, latch untouched | same |
| set | other `irq->hw` | latch set, physical active set | latch set only |
| clear | hw SGI | physical pending cleared | same |
| clear | other `irq->hw` | `vgic_hw_irq_cpending()` | latch cleared only |

- `__read_pending()` on a hw SGI: calls `irq_get_irqchip_state()`; it does
  not call `vgic_v4_get_vlpi_state()`.
- `__set_pending()` from the guest on a mapped interrupt: sets physical
  active with `vgic_irq_set_phys_active()`, not physical pending.
- `vgic_hw_irq_cpending()`: clears the latch and physical pending always,
  physical active only when `!irq->active`.
- Mapped edge interrupt: read as "other"; the write rows test `irq->hw`
  only, so they apply to it.
- vGICv3 userspace write of `GICD_ISPENDR` or `GICR_ISPENDR0`:
  `vgic_v3_uaccess_write_pending()` calls `vgic_uaccess_write_spending()`
  with `val`, then `vgic_uaccess_write_cpending()` with `~val`; both helpers
  run with `is_user` true.
- A vGICv3 userspace write of `GICR_ISPENDR0` therefore clears physical
  pending of every hw SGI whose bit is 0.
- vGICv2 userspace: `vgic_uaccess_write_spending()` and
  `vgic_uaccess_write_cpending()` are the register handlers themselves; see
  `arch/arm64/kvm/vgic/vgic-mmio-v2.c`.

## Virtual ITS

**Virtual ITS objects**

- `struct its_device`, `struct its_collection`, `struct its_ite`: defined in
  `arch/arm64/kvm/vgic/vgic.h`, next to `COLLECTION_NOT_MAPPED` and
  `its_is_collection_mapped()`; `struct vgic_its` is in
  `include/kvm/arm_vgic.h`.
- `struct vgic_its` list heads: `device_list` and `collection_list`;
  `dev_list` and `coll_list` are the link fields inside the objects.
- Unmapped collection, form 1: the object exists and `target_addr` is
  `COLLECTION_NOT_MAPPED`, as `vgic_its_alloc_collection()` leaves it.
- Unmapped collection, form 2: `ite->collection` is NULL, set by
  `vgic_its_free_collection()` for every ITE that used the freed collection.
- `its_is_collection_mapped()`: false for both forms; code that reads
  `ite->collection->collection_id` without that test needs its own NULL
  test.
- `its_lock`: also keeps the reference an ITE holds on `ite->irq`;
  `vgic_its_cache_translation()` asserts the lock for that reason.

**Processing guest commands**

- Failed read of a command: the command is skipped and `creadr` still
  advances; the loop does not stop.
- `vgic_its_handle_command()`: takes `its_lock` around the whole dispatch, so
  every handler runs under `cmd_lock` then `its_lock`.
- `vgic_its_process_commands()`: tests only `its->enabled`;
  `GITS_CBASER_VALID` is tested in `vgic_mmio_write_its_ctlr()` when the
  enable bit is set.
- `cwriter` on a disabled ITS: stored after the range test against
  `ITS_CMD_BUFFER_SIZE(its->cbaser)`, as on an enabled one; the commands run
  when `vgic_mmio_write_its_ctlr()` enables the ITS.
- Loop termination: `creadr` wraps only when it equals
  `ITS_CMD_BUFFER_SIZE(its->cbaser)`, so both offsets must be multiples of
  `ITS_CMD_SIZE` below that size.
- That invariant is kept by `vgic_mmio_write_its_cwriter()`,
  `vgic_mmio_uaccess_write_its_creadr()`, and by
  `vgic_mmio_write_its_cbaser()` and `vgic_its_reset()`, which zero both
  offsets.

**Mapping an event**

- Collection: need not exist or be mapped; a missing one is created unmapped
  by `vgic_its_alloc_collection()`.
- Collection ID of a missing collection: must pass `vgic_its_check_id()`
  against `its->baser_coll_table`, else `E_ITS_MAPC_COLLECTION_OOR`.
- Event ID: `vgic_its_check_event_id()` also requires the ITT slot of the
  event to be in a visible memslot, not only the range.
- LPI number: rejected when `lpi_nr < GIC_LPI_OFFSET` or
  `lpi_nr >= max_lpis_propbaser(kvm->arch.vgic.propbaser)`; there is no other
  case.
- Unwind: a collection created by this command is freed with
  `vgic_its_free_collection()` when `vgic_its_alloc_ite()` or
  `vgic_add_lpi()` fails; a collection that already existed is kept.

**Unmapping devices and events**

- `its_unmap_vlpi()`: returns `void` in this tree
  (`drivers/irqchip/irq-gic-v4.c`); `its_free_ite()` does not wrap it in
  `WARN_ON()`.
- Hardware-forwarded interrupt in `its_free_ite()`: under `irq->irq_lock`,
  `its_unmap_vlpi(irq->host_irq)` if `irq->hw`, then `irq->hw = false`, all
  before `vgic_put_irq()`.
- `its_free_ite()`: does not touch `pending_latch` or `enabled` of the
  `struct vgic_irq`.
- `its_free_ite()` with `ite->irq` NULL: allowed, the unmap and put are
  skipped; `vgic_its_cmd_handle_mapi()` relies on it in its unwind.
- `vgic_its_cmd_handle_discard()`: needs `find_ite()` to succeed and
  `its_is_collection_mapped(ite->collection)`.
- DISCARD of an event whose collection is unmapped in either form: returns
  `E_ITS_DISCARD_UNMAPPED_INTERRUPT` and the ITE stays.
- DISCARD besides freeing: `vgic_its_invalidate_cache()`, then a zero ITE is
  written to the guest's ITT with `vgic_its_write_entry_lock()`.
- MAPD with V=0: writes a zero DTE to guest memory even when no device was
  mapped.
- `E_ITS_MAPD_ITTSIZE_OOR`: tested only when V=1.
- `vgic_its_free_device()`: calls `vgic_its_invalidate_cache()` after freeing
  the ITEs.

**Table format revisions**

- `struct vgic_its_abi`: has no revision field; the revision is the index
  into `its_table_abi_versions[]`.
- `vgic_mmio_uaccess_write_its_iidr()`: returns `-EINVAL` when
  `rev >= NR_ITS_ABIS`; it reads only `GITS_IIDR_REV(val)` and ignores the
  other fields.
- Entry size check in `vgic_its_read_entry_lock()` and
  `vgic_its_write_entry_lock()`: a `BUILD_BUG_ON()` that the `sizeof` of the
  object passed equals `ABI_0_ESZ`, while `NR_ITS_ABIS == 1`.
- Run-time `KVM_BUG_ON()` returning `-EINVAL`: guarded by `NR_ITS_ABIS > 1`,
  so it never runs in this tree.
- Checked object: `*valp` for a read, `val` for a write, so a zero entry is
  written as `0ULL`; a plain `0` fails the build.

**Saving the tables**

- Device whose ID fails `vgic_its_check_id()`: skipped by
  `vgic_its_save_device_tables()`; the save does not fail.
- `compute_next_devid_offset()`: skips such devices, so the next offset of an
  earlier DTE points at the next device that is saved.
- Event with `ite->collection` NULL: `vgic_its_save_ite()` writes an all-zero
  ITE, which restore reads as invalid.
- `compute_next_eventid_offset()`: skips ITEs with a NULL collection.
- Event whose collection exists with `COLLECTION_NOT_MAPPED`: saved normally
  with its ICID.
- `vgic_its_save_cte()`: sets the valid bit for every collection on the list,
  and stores `COLLECTION_NOT_MAPPED` as the target of an unmapped one.
- Saving fails with `-EACCES` in `vgic_its_save_itt()` for an ITE with
  `ite->irq->hw` set when `kvm_vgic_global_state.has_gicv4_1` is false.

**Restoring the tables**

| Function | Rejects | Does not test |
|---|---|---|
| `vgic_its_restore_dte()` | `num_eventid_bits > VITS_TYPER_IDBITS`, then `vgic_its_check_id()` failure; both `-EINVAL` | an existing device with that ID; the ITT address |
| `vgic_its_restore_ite()` | non-zero `lpi_id < VGIC_MIN_LPI`; `event_id + offset` out of range; missing collection; `vgic_its_check_event_id()` failure; all `-EINVAL` | `find_ite()`; the upper LPI bound of `max_lpis_propbaser()` |

- Collection in `vgic_its_restore_ite()`: must exist; it may be unmapped, and
  then `vgic_add_lpi()` gets a NULL vCPU.
- ITT address: tested only indirectly, by the read in `scan_its_table()` and
  by `vgic_its_check_event_id()` for each valid ITE.
- `vgic_its_free_device_list()` on a failed device restore: frees every
  device on `its->device_list`, not only those this restore created.

**Restore and command handler checks**

- **Unsafe usage**: a restore function that creates a device, event or
  collection without the device ID, event ID, collection ID and event ID
  size checks of its command handler.
  - Unsafe: `num_eventid_bits` above `VITS_TYPER_IDBITS`;
    `vgic_its_restore_itt()` passes `BIT_ULL(dev->num_eventid_bits) * ite_esz`
    to the `int size` of `scan_its_table()`.
  - Unsafe: an event ID above `VITS_MAX_EVENTID`; `vgic_its_cache_key()` packs
    the event ID into `VITS_TYPER_IDBITS` bits below the device ID.
  - Safe: `vgic_its_restore_dte()` makes the `VITS_TYPER_IDBITS` and
    `vgic_its_check_id()` tests of `vgic_its_cmd_handle_mapd()`.
  - Safe: `vgic_its_restore_ite()` calls `vgic_its_check_event_id()`, as
    `vgic_its_cmd_handle_mapi()` does.
  - Safe: `vgic_its_restore_cte()` calls `vgic_its_check_id()` and
    `kvm_get_vcpu_by_id()`, as `vgic_its_cmd_handle_mapc()` does.
- **Potentially unsafe usage**: restoring an object without looking for one
  that already has its ID.
  - Unsafe: for the collection table, which is walked entry by entry and
    carries the ID inside each entry, so two entries can name one collection.
  - Safe: `vgic_its_restore_cte()` calls `find_collection()` first and returns
    `-EEXIST`.
  - Safe: `vgic_its_restore_ite()` adds to a device that
    `vgic_its_restore_dte()` has just allocated, and `scan_its_table()` gives
    each event ID once.
- Restore-only check: the next-offset field; `vgic_its_restore_ite()` rejects
  `event_id + offset >= BIT_ULL(dev->num_eventid_bits)`.
- Checks the handler makes and restore does not: see "Restoring the tables".

**Guest table walks**

- Step: `gpa` advances by the callback's return value times `esz`, not by one
  entry; `id` advances by the same return value.
- Return values of `scan_its_table()`: `< 0` read or callback error; 0 the
  callback found the last element; 1 the next step would leave the table.
- First read: happens before any bound test, so `size` must cover at least
  one entry.
- `next_offset * esz`: a 32-bit multiply, widened afterwards; it is bounded
  because the offsets come from a 14-bit DTE field or a 16-bit ITE field.
- Bound: in bytes, not IDs; `vgic_its_restore_dte()` does not test
  `id + offset`, and an offset past the table ends the scan with 1.
- ID after a step: tested by `vgic_its_restore_dte()` with
  `vgic_its_check_id()`, or by `vgic_its_restore_ite()` with
  `vgic_its_check_event_id()`, only when the new entry is valid;
  `handle_l1_dte()` does not test it.

**Locks for user requests**

- `vgic_its_ctrl()` order: `kvm->lock`, all vCPU mutexes through
  `kvm_trylock_all_vcpus()`, `kvm->arch.config_lock`, `its->its_lock`.
- `vgic_its_attr_regs_access()`: the same first three; it takes no ITS mutex
  itself, the register handlers take `cmd_lock` or `its_lock` themselves, for
  example `vgic_mmio_write_its_cbaser()`.
- `-EBUSY`: a literal in both functions; `kvm_trylock_all_vcpus()` itself
  returns `-EINTR`.
- There is no save_its_tables_in_progress flag; `vgic_write_guest_lock()` in
  `arch/arm64/kvm/vgic/vgic.h` sets `dist->table_write_in_progress` around
  each write.
- Documented sequence in `Documentation/virt/kvm/devices/arm-vgic-its.rst`:
  1. guest memory and vCPUs
  2. redistributors
  3. ITS base address
  4. GITS_CBASER
  5. all other GITS registers except GITS_CTLR
  6. `KVM_DEV_ARM_ITS_RESTORE_TABLES`
  7. GITS_CTLR
  8. KVM_IRQFD assignments for MSIs
- GITS_IIDR: not a step of its own; the documentation requires it only before
  `KVM_DEV_ARM_ITS_RESTORE_TABLES`.
- `vgic_mmio_write_its_cbaser()`: zeroes `creadr` and `cwriter`, which is why
  GITS_CREADR follows GITS_CBASER.
- Enabled ITS: writes to GITS_CBASER and GITS_BASER are ignored, and
  `vgic_mmio_uaccess_write_its_creadr()` returns `-EBUSY`, which is why
  GITS_CTLR is the last register restored.
- `vgic_mmio_write_its_baser()`: a changed value frees the device or
  collection list, so GITS_BASER precedes the table restore.
- GITS_CWRITER from userspace: uses `vgic_mmio_write_its_cwriter()`, the
  guest's handler, which processes commands if the ITS is enabled.

## Emulated distributor and redistributor registers

**The register emulation framework**

- Guest entry points: `dispatch_mmio_read()` and `dispatch_mmio_write()` in
  `arch/arm64/kvm/vgic/vgic-mmio.c`, installed in `kvm_io_gic_ops`; there is
  no vgic_mmio_read() or vgic_mmio_write() in this tree.
- `IODEV_REDIST` guest access: the handler gets `iodev->redist_vcpu`, the
  owner of the frame, not the vCPU that trapped.
- Redistributor access through `vgic_uaccess()`: the on-stack device built by
  `vgic_v3_redist_uaccess()` leaves `redist_vcpu` NULL, so the handler gets
  the vCPU chosen by the attribute.
- Userspace slots: `REGISTER_DESC_WITH_BITS_PER_IRQ()` (in
  `arch/arm64/kvm/vgic/vgic-mmio.h`) and
  `REGISTER_DESC_WITH_BITS_PER_IRQ_SHARED()` (in
  `arch/arm64/kvm/vgic/vgic-mmio-v3.c`) also take `uaccess_read` and
  `uaccess_write` arguments; passing NULL selects the guest handler.
- `REGISTER_DESC_WITH_BITS_PER_IRQ_SHARED()`: expands to two regions; the
  first, covering the private IRQs, is hard-wired to `vgic_mmio_read_raz()` and
  `vgic_mmio_write_wi()` for guest and userspace alike.
- Userspace access with no region, or one that fails `check_region()`:
  `vgic_uaccess_read()` stores 0 and returns 0, `vgic_uaccess_write()` returns
  0; neither returns `-ENXIO`.
- `-ENXIO` for an unknown offset: comes from `vgic_v3_has_attr_regs()`, which
  serves only `vgic_v3_has_attr()`, and from the ITS path.
- Userspace width: `vgic_uaccess_read()` and `vgic_uaccess_write()` always
  pass `sizeof(u32)`, so an offset that is not 4-byte aligned is RAZ/WI with
  return 0.
- `uaccess_write` return value: becomes the result of `vgic_uaccess()`; the
  fallback to `write` returns 0.
- ITS userspace access: `vgic_its_attr_regs_access()` in
  `arch/arm64/kvm/vgic/vgic-its.c` calls neither `vgic_uaccess()` nor
  `check_region()`; it calls `vgic_find_mmio_region()` directly.
- ITS access length: 8 if the region has `VGIC_ACCESS_64bit`, else 4.
- ITS errors: misaligned offset gives `-EINVAL`; no region, or ITS base not
  set, gives `-ENXIO`.
- ITS callbacks: writes use `uaccess_its_write` if set, else `its_write`;
  reads always use `its_read`, `uaccess_read` is not consulted.

**Invalidate registers of the redistributor**

- Checks in both handlers, in order: `addr & 4` set, then
  `!vgic_lpis_enabled()`; either one drops the write.
- `vgic_has_its()`: not called by either handler.
- `vgic_lpis_enabled()`: tests `ctlr == GICR_CTLR_ENABLE_LPIS`, so a write
  that arrives while `ctlr` holds `GICR_CTLR_RWP` (disable in progress) is
  dropped too.
- `vgic_mmio_write_invlpi()` extra check: `lower_32_bits(val) < VGIC_MIN_LPI`
  drops the write before the busy counter is touched; without it
  `vgic_get_irq()` could return an SPI.
- `vgic_set_rdist_busy()`: brackets the work in both handlers; `syncr_busy`
  in `struct vgic_cpu` is an `atomic_t` counter, not a flag.
- `vgic_mmio_write_invlpi()` work: `vgic_its_inv_lpi()`, which is
  `update_lpi_config()` with no vCPU filter; `priority` and `enabled` of the
  LPI are reloaded whichever vCPU it targets.
- `vgic_mmio_write_invall()` work: `vgic_its_invall()` passes the vCPU as
  filter; `priority` and `enabled` change only for LPIs whose `target_vcpu` is
  this redistributor's vCPU.
- ITS translation cache: not touched; neither path calls
  `vgic_its_invalidate_cache()`.

**Guest-generated SGIs**

- Targeted mode: `vgic_v3_dispatch_sgi()` itself does not walk the vCPUs and
  there is no match_mpidr() in this tree; each set bit of the 16-bit list is
  one `kvm_mpidr_to_vcpu()` lookup, and a NULL result is skipped.
- RS field: not read; `ICC_SGI1R_RS_MASK` is not referenced under
  `arch/arm64/kvm`, so only Aff0 values 0 to 15 can be targeted.
- Group argument: set by `access_gic_sgi()` in `arch/arm64/kvm/sys_regs.c`,
  from `Op2` for AArch64 and `Op1` for AArch32.

| Register | `allow_group1` | May raise |
|---|---|---|
| `SYS_ICC_SGI1R_EL1` | true | Group 0 or Group 1 |
| `SYS_ICC_ASGI1R_EL1` | false | Group 0 only |
| `SYS_ICC_SGI0R_EL1` | false | Group 0 only |

- Group test in `vgic_v3_queue_sgi()`: `!irq->group || allow_group1`; it is
  not a match between the register and `irq->group`.
- Group test and broadcast: `vgic_v3_queue_sgi()` applies it per target in
  both modes, and before the `irq->hw` branch.
- IRQ lookup: `vgic_get_vcpu_irq()`, not `vgic_get_irq()`.
- Hardware-backed SGI (`irq->hw`): `vgic_v3_queue_sgi()` calls
  `irq_set_irqchip_state()` on `irq->host_irq` with `IRQCHIP_STATE_PENDING`;
  no function of `arch/arm64/kvm/vgic/vgic-v4.c` is on this path.
- Hardware-backed SGI: `pending_latch` is not set and
  `vgic_queue_irq_unlock()` is not called; a failure only gives
  `WARN_RATELIMIT()`.

**Identification registers from userspace**

- Pre-init precondition: vCPU 0 must exist; `vgic_v3_parse_attr()` returns
  `-EINVAL` for `KVM_DEV_ARM_VGIC_GRP_DIST_REGS` otherwise.
- `reg_allowed_pre_init()`: does not look at the direction, so the read
  handler `vgic_mmio_read_v3_misc()` also runs before init for `GICD_IIDR`
  and `GICD_TYPER2`.
- There is no vgic_uaccess_write_iidr() here; the `GICD_IIDR` case is inside
  `vgic_mmio_uaccess_write_v3_misc()`.
- `GICD_IIDR` write: any difference from the current value outside
  `GICD_IIDR_REVISION_MASK` gives `-EINVAL`.
- `GICD_IIDR` write after init: accepted; that case has no
  `vgic_initialized()` test.
- `GICD_TYPER2` write, in order: same value as read back returns 0; a changed
  value after init gives `-EBUSY`; a change outside `GICD_TYPER2_nASSGIcap`
  gives `-EINVAL`; a non-zero value without `system_supports_direct_sgis()`
  gives `-EINVAL`.
- `GICD_TYPER2` write stores `nassgicap` in `struct vgic_dist`, not
  `nassgireq`; clearing it is allowed on any host.
- `spis` before init: NULL until `kvm_vgic_dist_init()` runs from
  `vgic_init()`, while `nr_spis` may already be non-zero from
  `KVM_DEV_ARM_VGIC_GRP_NR_IRQS`.
- **Unsafe usage**: allowing in `reg_allowed_pre_init()` an offset whose read
  or write handler reaches `spis` of `struct vgic_dist`; `vgic_get_irq()`
  indexes it for any SPI INTID below `nr_spis + VGIC_NR_PRIVATE_IRQS`.
  - Safe: a handler that touches only scalar fields of `struct vgic_dist`, as
    the `GICD_IIDR` and `GICD_TYPER2` cases of
    `vgic_mmio_uaccess_write_v3_misc()` do.
- **Unsafe usage**: a userspace write handler that takes `config_lock`, or
  falls through to a guest handler that takes it; `vgic_v3_attr_regs_access()`
  calls the handler with `kvm->lock`, every vCPU mutex and `config_lock` held.
  - Safe: `vgic_mmio_uaccess_write_v3_misc()` has its own `GICD_CTLR` case
    and reaches `vgic_mmio_write_v3_misc()` only for `GICD_TYPER`, which
    returns without locking.
  - Safe: `vgic_mmio_uaccess_write_cactive()` calls
    `__vgic_mmio_write_cactive()` directly, where the guest handler
    `vgic_mmio_write_cactive()` takes the lock first.
- **Unsafe usage**: a userspace write handler changing, once
  `vgic_initialized()` is true, a field that `vgic_init()` has read.
  - Safe: the `GICD_TYPER2` case returns `-EBUSY` for a changed value;
    `vgic_init()` reads `nassgicap` through `vgic_supports_direct_irqs()` to
    decide whether `vgic_v4_init()` runs.
  - Safe: `implementation_rev` after init; it is read only when a register is
    read, for GICv3 in `vgic_mmio_read_v3_misc()` and
    `vgic_mmio_read_v3r_ctlr()`.

**The redistributor type register**

- Flag bits: `vgic_mmio_read_v3r_typer()` sets only `GICR_TYPER_PLPIS` (when
  `vgic_has_its()`) and `GICR_TYPER_LAST`; `GICR_TYPER_VLPIS` is not set, on
  any host.
- Affinity field: `kvm_vcpu_get_mpidr_aff()` masked with `GENMASK(23, 0)`,
  so Aff3 reads as zero.
- Region pointer: `rdreg` in `struct vgic_cpu`, with `rdreg_index`; there is
  no rdist_region field.
- `vgic_mmio_vcpu_rdist_is_last()` does not look at `kvm->online_vcpus`.
- Last, first test: `rdreg` NULL gives false.
- Last, step 1: `rdreg_index < rdreg->free_index - 1` gives false.
- Last, step 2: for `count != 0` and `rdreg_index == count - 1`, the walk over
  `rd_regions` gives false if a region has `base` equal to the end of this
  one and `free_index > 0`.
- Last, step 3: true otherwise, including the highest registered index of a
  region that is not full.
- `rdreg` NULL again: `vgic_v3_free_redist_region()` clears it for every vCPU
  of the freed region, so Last reads clear from then on.
- Userspace read: the `GICR_TYPER` region has `uaccess_read` NULL, so
  `vgic_mmio_read_v3r_typer()` serves userspace too and Last is computed at
  read time.
- Userspace write: `vgic_mmio_uaccess_write_wi()`.

## vGIC lifecycle

**Creating the vGIC**

- `-EBUSY` has three sources in `kvm_vgic_create()`
  (`arch/arm64/kvm/vgic/vgic-init.c`): `kvm_trylock_all_vcpus()` fails;
  `kvm->created_vcpus != atomic_read(&kvm->online_vcpus)` (a vCPU is
  mid-creation); any vCPU has `vcpu_has_run_once()`.
- `kvm_vm_has_ran_once()` is not called by `kvm_vgic_create()`.
- `-EEXIST`: the test is `irqchip_in_kernel()`, which reads `vgic.in_kernel`,
  not `vgic_model`.
- Type validation: `kvm_vgic_create()` has none and returns no `-EINVAL`; the
  only `-ENODEV` is GICv2 without
  `kvm_vgic_global_state.can_emulate_gicv2`. It has no host check for GICv3.
- Limit field: `kvm->max_vcpus`, not a field of `kvm->arch`.
- Order: `in_kernel`, `vgic_model`, `implementation_rev` and the bases are
  written before the per-vCPU allocation, then `kvm_vgic_finalize_idregs()`
  rewrites the VM's GIC ID register fields, then the allocation loop runs.
- `vgic_allocate_private_irqs_locked()` relies on that order: it picks the
  array size with `vgic_is_v5()`, which reads `vgic_model`.
- Existing vCPUs: only `vgic_allocate_private_irqs_locked()` is called;
  `kvm_vgic_vcpu_init()` is not. No redistributor frame is registered here.
- `KVM_DEV_TYPE_ARM_VGIC_V5` is a third model: `kvm->max_vcpus` is
  `min(VGIC_V5_MAX_CPUS, kvm_vgic_global_state.max_gic_vcpus)`, the private
  array has `VGIC_V5_NR_PRIVATE_IRQS` entries, and after success
  `kvm_timer_init_vm()` is run again.
- GICv3 only, after the allocation succeeded: `vgic.nassgicap` is set from
  `system_supports_direct_sgis()`.

**Failure of vGIC creation**

- Failure that reaches the cleanup: only `-ENOMEM` from
  `vgic_allocate_private_irqs_locked()`; the `-E2BIG` exit is before any vGIC
  field is written.
- Private IRQs: freed by an open-coded `kfree()` plus NULL store for every
  vCPU; `kvm_vgic_vcpu_destroy()` is not called.
- `vgic.vgic_model` and `vgic.in_kernel`: were written before the loop, and
  are reset to 0 and `false`.
- Resulting state: `irqchip_in_kernel()` is false, so a retry does not get
  `-EEXIST`.
- Not restored: `kvm->max_vcpus`, `vgic.implementation_rev`, the base
  addresses, and the ID register fields written by
  `kvm_vgic_finalize_idregs()`.
- ID registers: `kvm_finalize_sys_regs()` in `arch/arm64/kvm/sys_regs.c`
  rewrites the GIC fields at first run, clearing them when
  `irqchip_in_kernel()` is false.
- `kvm->max_vcpus`: the stale model limit keeps bounding later vCPU creation;
  see `kvm_arch_vcpu_precreate()` in `arch/arm64/kvm/arm.c`.

**Initialising the vGIC**

- `kvm_vgic_inject_irq()` (`arch/arm64/kvm/vgic/vgic.c`): does not call
  `vgic_lazy_init()`. When `vgic_initialized()` is false it returns 0 and the
  injection is dropped silently.
- `vgic_lazy_init()` is called only by the userspace entry points, before
  they call `kvm_vgic_inject_irq()`: `kvm_vm_ioctl_irq_line()` in
  `arch/arm64/kvm/arm.c` and `vgic_irqfd_set_irq()` in
  `arch/arm64/kvm/vgic/vgic-irqfd.c`. Both pass up its `-EBUSY` for an
  uninitialised model other than GICv2; `vgic_irqfd_set_irq()` tests
  `vgic_valid_spi()` first and returns `-EINVAL` if that fails.
- In-kernel injectors, for example the timer in
  `arch/arm64/kvm/arch_timer.c`, call `kvm_vgic_inject_irq()` directly: before
  init they get 0, no error and no lazy init, also on GICv2.
- `kvm_arch_set_irq_inatomic()`: before init returns `-EWOULDBLOCK` for
  `KVM_IRQ_ROUTING_IRQCHIP`.
- `vgic_init()`: returns 0 when already initialised. Its only own refusal is
  `-EBUSY` while `kvm->created_vcpus != atomic_read(&kvm->online_vcpus)`.
  Other errors are passed up from what it calls.
- `vgic_init()` itself rejects nothing on the model, the base addresses or
  `nr_spis`. Bases are checked in `vgic_v2_map_resources()` and
  `vgic_v3_map_resources()`; the `nr_spis` range is checked in
  `vgic_set_common_attr()`.
- Per-vCPU step in `vgic_init()`: `kvm_vgic_vcpu_reset()`. There is no
  kvm_vgic_vcpu_enable() in this tree.
- `vgic_v4_init()` gate in `vgic_init()`: `vgic_supports_direct_irqs()`, true
  for direct MSIs or direct SGIs, not `vgic_supports_direct_msis()` alone.
- GICv5 in `vgic_init()`: `vgic_v5_init()` replaces the SPI and GICv4 setup;
  it returns `-EINVAL` if any vCPU has `vcpu_has_nv()`.
- `vgic_v3_attr_regs_access()` before init: `-EBUSY`, except when
  `reg_allowed_pre_init()` is true, which is `GICD_IIDR` and `GICD_TYPER2` in
  `KVM_DEV_ARM_VGIC_GRP_DIST_REGS`.

**Resource mapping and ready flag**

- Distributor registration: `vgic_register_dist_iodev()` runs with
  `kvm->slots_lock` held and `kvm->arch.config_lock` dropped; the caller's
  `vcpu->mutex` is held too. `config_lock` is dropped after
  `dist->vgic_dist_base` has been copied to a local.
- There is no vgic_ready() accessor in this tree; `dist->ready` is read
  directly, and only inside `kvm_vgic_map_resources()`.
- Reads of `dist->ready`: `smp_load_acquire()` with no lock on the fast path,
  then a plain read under both locks.
- Publication: `smp_store_release(&dist->ready, true)` after the distributor
  frame is registered, with `slots_lock` held and `config_lock` already
  dropped.
- GICv5: `vgic_v5_map_resources()` registers no distributor frame; `ready` is
  still set.
- Clearing: `kvm_vgic_dist_destroy()` stores `false` with a plain store under
  `config_lock`.
- Failure: every non-zero return ends in `kvm_vm_dead()`. That includes
  userspace configuration errors such as `-ENXIO` for an unset base and
  `-EBUSY` for an uninitialised GICv3.
- Failure does not call `kvm_vgic_destroy()`; nothing already registered is
  unregistered and `ready` stays false. Teardown happens only in
  `kvm_arch_destroy_vm()`.
- After `kvm_vm_dead()`: VM, vCPU and device ioctls return `-EIO`; see the
  `vm_dead` tests in `virt/kvm/kvm_main.c`.

**Registering redistributors**

- Locks: the caller holds `kvm->slots_lock` (asserted).
  `kvm->arch.config_lock` is taken inside and dropped before
  `kvm_io_bus_register_dev()`, so the bus call runs under `slots_lock` only.
- Rollback in `vgic_register_all_redist_iodevs()`: unregisters the vCPUs
  before the failing one. The failing vCPU itself was never put on the bus.
- Rollback in `vgic_v3_set_redist_base()`: retakes `config_lock` and calls
  `vgic_v3_free_redist_region()`, which clears `vgic_cpu.rdreg` of every vCPU
  that points to the region and frees it.
- `vgic_unregister_redist_iodev()`: only removes the device from the bus. It
  does not reset `rd_iodev.base_addr`, and nothing in the rollback resets
  `rdreg_index`.
- `rd_iodev.base_addr` is set back to `VGIC_ADDR_UNDEF` only in
  `kvm_vgic_vcpu_init()` and `__kvm_vgic_vcpu_destroy()`.
- Successfully created vCPU: the `vgic_unregister_redist_iodev()` call is in
  `kvm_vgic_destroy()`, in the loop after `config_lock` is dropped.
  `__kvm_vgic_vcpu_destroy()` skips it, because `kvm_get_vcpu_by_id()`
  returns that vCPU.
- That call in `kvm_vgic_destroy()` finds no bus: `kvm_destroy_vm()` has
  already destroyed the buses and set `kvm->buses[]` to NULL, so
  `kvm_io_bus_unregister_dev()` returns 0 at its `!bus` test.
- vCPU whose creation failed: unregistered in `__kvm_vgic_vcpu_destroy()`,
  reached through `kvm_vgic_vcpu_destroy()` with `slots_lock` only.
- Paths that reach it for a failed vCPU: the two error exits of
  `kvm_arch_vcpu_create()`, and `kvm_arch_vcpu_destroy()` from the error
  labels of `kvm_vm_ioctl_create_vcpu()` in `virt/kvm/kvm_main.c`.

**Scope of the configuration lock**

- `kvm_io_bus_unregister_dev()`: waits in
  `synchronize_srcu_expedited(&kvm->srcu)`.
- `kvm_io_bus_register_dev()`: does not wait; it frees the old bus with
  `call_srcu()`.
- Both bus calls assert `kvm->slots_lock`.
- SRCU readers take `config_lock`: `kvm_handle_guest_abort()` holds
  `kvm->srcu` across `io_mem_abort()`, and MMIO handlers such as
  `vgic_mmio_write_v3_misc()` and `vgic_mmio_read_active()` lock it.
- Locks taken before `config_lock`: `kvm->lock`, `vcpu->mutex`,
  `kvm->slots_lock`, and the `kvm->srcu` read side. `slots_lock` is outside
  `config_lock`, never inside.
- **Unsafe usage**: calling `kvm_io_bus_unregister_dev()`, or
  `vgic_unregister_redist_iodev()`, with `config_lock` held.
  - Unsafe: `synchronize_srcu_expedited()` in `kvm_io_bus_unregister_dev()`
    waits for SRCU readers, and a reader such as `vgic_mmio_read_active()`
    blocks on `config_lock`.
  - Safe: after `config_lock` is dropped and with `slots_lock` still held, as
    the last loop of `kvm_vgic_destroy()` does.
  - Safe: under `slots_lock` only, as `kvm_vgic_vcpu_destroy()` and
    `vgic_register_all_redist_iodevs()` do.
  - Safe: `__kvm_vgic_vcpu_destroy()` called under `config_lock` from
    `kvm_vgic_destroy()`; its `kvm_get_vcpu_by_id()` test is false for every
    vCPU in `kvm->vcpu_array`, so the unregister is not reached.
- **Unsafe usage**: taking `slots_lock` while `config_lock` is held, in order
  to reach a bus call.
  - Safe: `slots_lock` first, then `config_lock`, as `kvm_vgic_addr()`,
    `kvm_vgic_map_resources()` and `kvm_vgic_destroy()` do.
- Registration with `config_lock` held: does not wait for SRCU in this tree.
  `vgic_v2_map_resources()` registers `cpuif_iodev` with both locks held; the
  GICv3 redistributor and the distributor paths drop `config_lock` first.
- `kvm_vgic_destroy()` under both locks: `vgic_debug_destroy()`,
  `__kvm_vgic_vcpu_destroy()` per vCPU, and `kvm_vgic_dist_destroy()`. The
  last one includes `xa_destroy()` of `lpi_xa` and, when
  `vgic_supports_direct_irqs()`, `vgic_v4_teardown()`.
- `kvm_vgic_destroy()` after `config_lock` is dropped: only
  `vgic_unregister_redist_iodev()` per vCPU, for GICv3.
- Distributor, ITS and GICv2 CPU interface frames: no code in
  `arch/arm64/kvm/vgic/` unregisters them. `kvm_destroy_vm()` destroys the
  buses with `kvm_io_bus_destroy()` before it calls `kvm_arch_destroy_vm()`.

## Host handoff, nested guests and GICv5 hosts

**Host GIC information in KVM**

- `struct gic_kvm_info`: there is no gicv_base field; the GICV region is
  `vcpu` (a `struct resource`), and `type` can also be `GIC_V5`.
- `vgic_set_kvm_info()`: allocates a private copy and `BUG_ON()`s on a
  second call; if the allocation fails the pointer stays NULL and
  `kvm_vgic_hyp_init()` later returns `-ENODEV`.
- GICv3 driver precondition: `gic_of_setup_kvm_info()` and
  `gic_acpi_setup_kvm_info()` in `drivers/irqchip/irq-gic-v3.c` run only
  while `supports_deactivate_key` is enabled; `gic_init_bases()` disables it
  when `!is_hyp_mode_available()`.
- ACPI mismatch: if the maintenance interrupt, its trigger mode or the GICV
  base differ between GICC entries, `gic_acpi_parse_virt_madt_gicc()` returns
  `-EINVAL` and nothing is handed to KVM at all.
- Missing maintenance interrupt: `kvm_vgic_hyp_init()` returns `-ENXIO` only
  when `no_maint_irq_mask` is clear; the GICv3 driver never gets that far, it
  returns before `vgic_set_kvm_info()`, so KVM sees `-ENODEV`.
- `-ENODEV` or `-ENXIO` from `kvm_vgic_hyp_init()`: `init_subsystems()` in
  `arch/arm64/kvm/arm.c` continues with `vgic_present` false (userspace
  irqchip only); it fails instead under `is_protected_kvm_enabled()`, and
  with `-EINVAL` when `kvm_mode` is `KVM_MODE_NV`.
- `vgic_v3_probe()`: has no SRE check and no `-ENODEV` return; its only
  errors come from `kvm_register_vgic_device()`.
- `__vgic_v3_get_gic_config()`: returns a bool, true if the CPU interface
  can do GICv2 MMIO; it does not return `ICH_VTR_EL2`.
- `ICH_VTR_EL2` value: comes from `vgic_ich_vtr()` in
  `arch/arm64/kvm/vgic/vgic.h`, a constant patched in by
  `kvm_patch_ich_vtr_el2()`, which also clears `ICH_VTR_EL2_SEIS` on broken
  SEIS hardware; `kvm_vgic_global_state` holds no copy of the register.
- `no_hw_deactivation`: handled in `kvm_vgic_hyp_init()` before the probe
  switch (taint, then `kvm_vgic_global_state.no_hw_deactivation`), not in
  `vgic_v3_probe()`.
- GICv2 emulation on a GICv3 host: see the if-chain in `vgic_v3_probe()`;
  the easy-to-miss cases are a GICV base that is not page aligned and
  `KVM_MODE_PROTECTED`, which both leave `can_emulate_gicv2` false while
  `KVM_DEV_TYPE_ARM_VGIC_V3` is still registered.
- `kvm-arm.vgic_v4_enable`: defaults to off (`gicv4_enable` in
  `arch/arm64/kvm/vgic/vgic-v3.c`); without it `has_gicv4` and `has_gicv4_1`
  stay false on GICv4 hardware and the log says "GICv4 support disabled".
- `has_gicv4` and `has_gicv4_1`: `vgic_v3_probe()` assigns them only inside
  `if (info->has_v4)`; `has_gicv4_1` is `info->has_v4_1 && gicv4_enable`.

**A guest hypervisor's list registers**

- `vgic_state_is_nested()`: true when `is_nested_ctxt()` and the virtual
  `HCR_EL2` has `HCR_IMO` or `HCR_FMO` set (`WARN_ONCE()` if only one of
  them); it does not look at `ICH_HCR_EL2`.
- LR load point: `vgic_v3_load_nested()` writes the shadow LRs to hardware
  once, at vCPU load; they stay there across entries until
  `vgic_v3_put_nested()` zeroes them.
- On each entry: the only hardware write `kvm_vgic_flush_hwstate()` makes is
  in `vgic_v3_flush_nested()`, which writes L1's in-memory `ICH_HCR_EL2` OR
  `vgic_ich_hcr_trap_bits()` to hardware.
- Shadow `vgic_hcr`: the raw L1 value, nothing masked or merged in
  `vgic_v3_create_shadow_state()`.
- Compaction: `vgic_v3_create_shadow_lr()` skips L1 LRs with no
  `ICH_LR_STATE` and packs the rest from hardware index 0, so a hardware
  index is not the L1 index; convert with `lr_map_idx_to_shadow_idx()`.
- Translation: done by `translate_lr_pintid()`, with `vgic_get_vcpu_irq()`
  only; there is no lr_map_vintid() here.
- `translate_lr_pintid()` clears `ICH_LR_HW` when the lookup finds no irq,
  the irq is not `hw`, or `irq->intid > VGIC_MAX_SPI`; it does not set
  `ICH_LR_EOI`.
- `translate_lr_pintid()` overwrites the pINTID field with `irq->hwintid`
  whenever the lookup finds an irq, including when it has just cleared
  `ICH_LR_HW`.
- Write-back on every exit: `vgic_v3_sync_nested()`, called from
  `kvm_vgic_sync_hwstate()`, reads the hardware LRs and merges only
  `ICH_LR_STATE` into L1's in-memory LRs (`ICH_LR0_EL2` onwards); it also
  copies back `ICH_VMCR_EL2` and the EOIcount field of `ICH_HCR_EL2`.
- Write-back on put: `vgic_v3_put_nested()` copies back only the APRs; it
  does not call `vgic_v3_sync_nested()` or
  `vgic_v3_handle_nested_maint_irq()`.

**Nested deactivation and maintenance interrupt**

- Deactivation call: `vgic_v3_sync_nested()` passes the pINTID field of
  L1's LR to `vgic_v3_deactivate()` in `arch/arm64/kvm/vgic/vgic-v3.c`, the
  same function that handles a trapped `ICC_DIR_EL1` write.
- Which HW bit is tested: `ICH_LR_HW` and a non-zero state in L1's
  in-memory LR as it was before the write-back, plus a zero state in the
  hardware LR; so it also runs for an entry whose shadow LR had `ICH_LR_HW`
  cleared by `translate_lr_pintid()`.
- `vgic_v3_deactivate()` returns without touching the interrupt unless L1's
  own `vgic_vmcr` (in `vcpu->arch.vgic_cpu.vgic_v3`) has
  `ICH_VMCR_EL2_VEOIM_MASK` set and the INTID is below
  `nr_spis + VGIC_NR_PRIVATE_IRQS`.
- Physical side: when `vgic_state_is_nested()`, `vgic_v3_deactivate()` skips
  `vgic_v3_deactivate_phys()`, because the HW bit of the shadow LR has
  already deactivated the host interrupt.
- After clearing the active state: `vgic_v3_deactivate()` folds a pseudo-LR
  with `vgic_v3_fold_lr()` and raises `KVM_REQ_VGIC_PROCESS_UPDATE` on the
  vCPU that holds the interrupt; it does not re-queue it itself.
- Host maintenance interrupt while L2 runs: `vgic_maintenance_handler()`
  calls `vgic_v3_handle_nested_maint_irq()`, which injects `mi_intid` into L1
  with level taken from the hardware `ICH_MISR_EL2` (not the computed one),
  then clears `ICH_HCR_EL2_En` in hardware.
- Every exit from L2: `vgic_v3_sync_nested()` writes 0 to hardware
  `ICH_HCR_EL2` and then calls `vgic_v3_nested_update_mi()`, which sets the
  level again from L1's in-memory registers.

**GICv3 guests on GICv5 hosts**

- Legacy support is not in `struct gic_kvm_info`: `vgic_v5_probe()` tests
  `cpus_have_final_cap(ARM64_HAS_GICV5_LEGACY)` and records it in
  `kvm_vgic_global_state.has_gcie_v3_compat`; the capability comes from
  `ICC_IDR0_EL1_GCIE_LEGACY` in `test_has_gicv5_legacy()`.
- Handoff from `drivers/irqchip/irq-gic-v5.c`: only `gicv5_of_init()` calls
  `gic_of_setup_kvm_info()`, which needs `gicv5_global_data.virt_capable`
  and a maintenance interrupt; the ACPI `gic_acpi_init()` in that file hands
  nothing to KVM.
- Host without legacy support: `vgic_v5_probe()` returns 0 if it registered
  `KVM_DEV_TYPE_ARM_VGIC_V5`, and `-ENODEV` only if it did not (pKVM, or
  registration failed).
- Host with legacy support: `vgic_v5_probe()` registers both
  `KVM_DEV_TYPE_ARM_VGIC_V5` and `KVM_DEV_TYPE_ARM_VGIC_V3`; under pKVM only
  the GICv3 one.
- `max_gic_vcpus` with legacy support: `min(VGIC_V3_MAX_CPUS,
  VGIC_V5_MAX_CPUS)`.
- `nr_lr`: taken from `vgic_ich_vtr()`; `vgic_v5_probe()` does not call
  `__vgic_v3_get_gic_config()`.
- Maintenance interrupt: set up by `kvm_vgic_hyp_init()` after the probe,
  not by `vgic_v5_probe()`.
- `vgic_host_has_gicv3()`: defined in `arch/arm64/kvm/vgic/vgic.h`; the
  per-VM test is `vgic_is_v3()`; there is no vgic_is_v3_compat() here.
- `__vgic_v3_compat_mode_enable()`: called from
  `__vgic_v3_restore_vmcr_aprs()`, so on vCPU load, not from
  `__vgic_v3_activate_traps()`.
- Clearing `ICH_VCTLR_EL2_V3`: there is no __vgic_v3_compat_mode_disable();
  nothing on the put path writes `ICH_VCTLR_EL2`, so the bit stays set after
  a GICv3 guest is put; `__vgic_v5_compat_mode_disable()` in
  `arch/arm64/kvm/hyp/vgic-v5-sr.c` clears it, called from
  `__vgic_v5_restore_vmcr_apr()` when a GICv5 guest is loaded.
- HW-mode LRs are still used: `no_hw_deactivation` is not set on a GICv5
  host, so `vgic_v3_compute_lr()` sets `ICH_LR_HW` for mapped interrupts.
- `vgic_v3_deactivate_phys()` in `arch/arm64/kvm/vgic/vgic-v3.c`: used only
  where KVM emulates the deactivation in software, in the EOIcount replay of
  `vgic_v3_fold_lr_state()` and in `vgic_v3_deactivate()`.
- With `ARM64_HAS_GICV5_LEGACY`, `vgic_v3_deactivate_phys()` issues
  `gic_insn()` CDDI instead of `gic_write_dir()`, with the type field
  hard-coded to 1, the value of `GICV5_HWIRQ_TYPE_PPI`.

## Model gaps

### Other mistakes models make

- Models take the GICv4 calls from KVM into the ITS driver to run in process
  context. `update_lpi_config()` and `update_affinity()` call
  `its_prop_update_vlpi()` and `its_get_vlpi()` with `irq->irq_lock` held, so
  `its_irq_set_vcpu_affinity()` and its callees may only spin.
- Models take `arch/arm64/kvm/vgic/vgic-v5.c` to be only the compat layer for
  GICv3 guests. For a `KVM_DEV_TYPE_ARM_VGIC_V5` VM the private interrupts
  get their INTIDs from `vgic_v5_make_ppi()`, and `kvm_vgic_sync_hwstate()`
  skips `vgic_prune_ap_list()`.
- Models take `kvm_vgic_global_state.type` to be `VGIC_V3` whenever a GICv3
  guest can run. `vgic_v5_probe()` sets it to `VGIC_V5` and enables the
  `gicv3_cpuif` static key under `ARM64_HAS_GICV5_LEGACY`; the host test is
  `vgic_host_has_gicv3()`.
- Models take `irq_is_ppi()`, `irq_is_sgi()`, `irq_is_spi()`, `irq_is_lpi()`
  and `irq_is_private()` to take an INTID only. In `include/kvm/arm_vgic.h`
  they take the `struct kvm *` first and decode by `vgic_model`.
- Models take every field of `struct its_vpe` to be valid on any GICv4. In
  `include/linux/irqchip/arm-gic-v4.h` a union overlays the GICv4.0 fields
  `vpe_proxy_event` and `idai` with the GICv4.1 fields `fwnode`,
  `sgi_domain` and `sgi_config`.
- Models take partitioned PPIs to be backed by irq-partition-percpu.c. There
  is no such file in this tree.
- Models take `its_msi_teardown()` to be one function.
  `drivers/irqchip/irq-gic-its-msi-parent.c` has its own static
  `its_msi_teardown()`, separate from the one in
  `drivers/irqchip/irq-gic-v3-its.c`.
- Models know one vGIC debugfs file. `vgic_its_debug_init()` adds one per
  vITS, and `vgic_its_debug_start()` takes `its->its_lock`, released only in
  `vgic_its_debug_stop()`.
- Models expect `kzalloc()` and `kcalloc()` in
  `drivers/irqchip/irq-gic-v3-its.c` and under `arch/arm64/kvm/vgic/`. Most
  allocations there use `kzalloc_obj()`, `kzalloc_objs()` and `kmalloc_obj()`
  from `include/linux/slab.h`.
