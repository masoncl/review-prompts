# What the gic-v5 measurement found

Three models were asked the 138 questions in `gic-v5-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against a
mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. The hand-written guide was never checked
against current sources, so differences between it and the built guide are
expected and are noted below.

The three readers are out of date in three different ways. Reader C is the most
current overall and knows KVM's native GICv5 device, but it carries an earlier
version of a handful of host functions that have since been reworked. Reader A
describes the host driver as it is now, with some names wrong, and does not know
that a native GICv5 guest exists: it says a GICv5 host only runs GICv3 guests.
Reader B knows the architecture in outline, guesses at most names, and answered
"I do not know" to nearly every KVM question. No question was answered correctly
by all three, so the build set was chosen by importance to a reviewer and not by
dropping what readers know.

## What all three readers got wrong

- **Where the priority drop is.** `gicv5_handle_irq()` issues `CDEOI`, with an
  operand of zero, itself: straight after `gsb_ack()` and `isb()` and before it
  calls `handle_irq_per_domain()`. The comment gives the reason (a long-running
  handler, or entering a guest directly). `gicv5_hwirq_eoi()` issues `CDDI` and
  nothing else. Reader C put `CDEOI` in `gicv5_hwirq_eoi()` after the `CDDI`,
  which is the code before it was reworked, and carried that into several other
  answers. Reader B put it in `irq_eoi` after the handler, tied to an interrupt
  ID. Reader A had the place and left the step out of the acknowledge sequence,
  and guessed at the reason.
- **Who allocates LPIs.** There is no gicv5_alloc_lpi() or gicv5_free_lpi().
  `alloc_lpi()` and `release_lpi()` are static in `irq-gic-v5.c` and only the
  LPI domain's alloc and free call them; `gicv5_irq_lpi_domain_alloc()` loops
  over `nr_irqs`. `gicv5_its_irq_domain_alloc()` makes one
  `irq_domain_alloc_irqs_parent()` call for the whole range with a NULL
  argument, its loop cannot fail, and on failure it releases only the event
  IDs. Readers A and C described a per-interrupt LPI allocation in the ITS
  domain with a reverse unwind; reader B had LPI numbers start at 8192.
- **Unregistering a device frees the translation table before the
  invalidation.** `gicv5_its_device_unregister()` zeroes the entry, calls
  `gicv5_its_free_itt()` and only then `gicv5_its_device_cache_inv()`. All three
  said the memory is freed after the invalidation completes, and one offered
  the function as the model of correct ordering.
- **The ITS ignores the ACPI non-coherent flag.** `gicv5_its_init_bases()`
  takes a `noncoherent` argument and never reads it; it tests the device tree
  property on a node that is NULL under ACPI. Reader C said the function tests
  only its argument, reader B said `of_dma_is_coherent()`.
- **What serialises the ITS invalidation registers.** `dev_alloc_lock` covers
  only the device invalidation reached from `gicv5_its_msi_prepare()` and
  `gicv5_its_msi_teardown()`. The event invalidation reached from
  `gicv5_its_irq_domain_activate()` and `gicv5_its_irq_domain_deactivate()`
  writes the same device ID register with no ITS lock held. The readers offered
  `dev_alloc_lock`, the domain mutex and the descriptor lock; none of them is
  held on every path.
- **The interrupt state table.** Software does write level 1 entries (the level
  2 address, valid bit clear) in `gicv5_irs_iste_alloc()`; the IRS used for the
  mapping register is `per_cpu(per_cpu_irs_data, 0)`, not the current CPU's and
  not the first on the list. The wait helper is `gicv5_irs_ist_synchronise()`,
  which only polls; one reader had it write the sync register and two used
  names that do not exist.
- **The probe order and its unwinding.** `gicv5_init_domains()` creates the PPI,
  SPI and IPI domains; the LPI domain comes from `gicv5_irs_init()` on the first
  IRS. `gicv5_irs_remove()` is run by `gicv5_of_init()` and `gic_acpi_init()`,
  not by `gicv5_init_common()`. `pri_bits` is `min_not_zero()` of the two
  widths. No reader had all of it.
- **CPU interface bring-up has one barrier.** `gicv5_cpu_enable_interrupts()`
  has no barrier after the priority mask or enable writes; the only `isb()` is
  at the end of `gicv5_ppi_priority_init()`. `gicv5_cpu_disable_interrupts()`
  does end in `isb()`. Two readers added a barrier to the enable, one removed it
  from the disable.
- **The PPI set-type callback.** It exists, writes nothing, and returns
  `-EINVAL` only when the requested sense disagrees with the handling mode
  register. One reader said the PPI chip has no such callback.
- **A fresh LPI is not disabled or routed at allocation.**
  `gicv5_lpi_config_reset()` issues `CDHM` and `CDPEND`; `gicv5_hwirq_init()`
  issues `CDPRI` only. Readers offered `CDDIS` and `CDAFF`.
- **`gic_v5_get_gsi_domain_id()` returns `iort_iwb_handle_fwnode()`** for an IWB
  interrupt and the single `gsi_domain_handle` for everything else;
  `iort_iwb_handle()` belongs to `gic_v5_get_gsi_handle()`.
- **Which capability test is used where.** The only `cpus_have_cap()` user is
  `kvm_patch_ich_vtr_el2()`; `vgic_v5_probe()` uses `cpus_have_final_cap()`.
  Readers named helpers that do not exist.
- **KVM names.** `vgic_v5_make_ppi()`, `vgic_v5_get_hwirq_id()`,
  `get_vgic_ppi()` and `KVM_ARMV8_PMU_GICV5_IRQ` are what build an interrupt ID;
  the timer and PMU do not use the architected PPI macros. The iterator is
  `for_each_visible_v5_ppi()`. Nothing reads `vgic_ppi_hmr`. A guest write to
  the second bank of the PPI enable register returns at once in
  `access_gicv5_ppi_enabler()`.

## What readers A and B got wrong as well

- Native GICv5 guests exist. `vgic_v5_probe()` registers
  `KVM_DEV_TYPE_ARM_VGIC_V5` unless protected KVM is on, and returns `-ENODEV`
  when that was not registered and the host has no GICv3-compatible mode either;
  it does not bail out first on a host without the compatible mode.
  `has_gcie_v3_compat` is a field of `struct vgic_global`, set from the
  `ARM64_HAS_GICV5_LEGACY` capability; `struct gic_kvm_info` has no such field
  and the list register count comes from `vgic_ich_vtr()`.
- The control register is saved on every exit by `__vgic_v5_save_state()`; only
  the active priorities register is saved at put, by `__vgic_v5_save_apr()`, and
  both are restored at load. Priorities are synced into the shadow state from
  `vgic_v5_put()` and only when the vCPU is in WFI.
- `gsb_sys()` and `gsb_ack()` are in `arch/arm64/include/asm/barrier.h`;
  `gsb_sys()` has one caller, `gicv5_iri_irq_mask()`. The state query is
  `CDRCFG`, `isb()`, then a read of `ICC_ICSR_EL1`; reader B had a gsb_sync()
  there.
- ACPI: `gic_acpi_init()`, `gicv5_irs_acpi_probe()`, the MADT entry types and
  the GICC `iaffid` and `irs_id` fields. Both doubted it existed.
- The LPI and IPI domains carry no bus token; `DOMAIN_BUS_NEXUS` belongs to the
  ITS domains. The PPI domain is `PPI_NR` (128) wide.
- `irqd_set_resend_when_in_progress()` is not called anywhere in the GICv5
  files.
- `gicv5_irs_register_cpu()` turns any selector wait failure into `-ENXIO`.
  `gicv5_irs_syncr()` returns nothing and addresses only the first IRS.
- Two-level device tables: the level 2 table is never cleaned separately and
  never freed.

## What only reader B got wrong

Reader B reasons from GICv3: interrupt types picked by ID range, a memory
pending table for LPIs, an IPI sent by writing a system register, software
setting the level 1 valid bit, an SPI count summed over the IRSs, a header at
drivers/irqchip/irq-gic-v5.h, MSI parent code in the MSI library file, the
device tree type cell as 0 and 1. Every one of these is wrong for this driver.

## What only reader C got wrong

The first two match what the hand-written guide says or says was changed, so
they are probably the code as it was a little earlier:

- `__irq_is_ppi()` for a GICv5 guest tests the type and also that the ID is
  below `VGIC_V5_NR_PRIVATE_IRQS`. Reader C said no predicate bounds the ID and
  that `vgic_get_vcpu_irq()` clamps an oversized ID to zero; it returns NULL.
- A malformed CPU phandle gets a `pr_warn()` marked `FW_BUG` and a CPU node with
  no logical CPU is skipped silently. Reader C had a `WARN_ON()` for each.
- 64 PPIs per vCPU, not 128.
- The ITS structures are defined in `irq-gic-v5-its.c`; there is no
  gicv5_its_free_device(), teardown is open-coded in
  `gicv5_its_msi_teardown()`.
- The poll timeout is 10 ms.

## What the readers already knew

Readers A and C: the component model (IRS, ITS, IWB, no distributor), the typed
interrupt ID layout, the asymmetry between masking and unmasking an SPI or LPI
and the symmetric `isb()` for PPIs, the query sequence, the select, program and
poll discipline for SPIs, that the ITS has no command queue and software owns
its valid bits, the table sizing arithmetic, the IWB's fixed event IDs and empty
message callback. Reader C also: the edge and level asymmetry in the KVM flush
and fold, the direct-injection mask on the pending write, the userspace PPI
rules. Reader B: that GSB is not DSB, and that enabling needs no completion
where disabling does, both offered as guesses.

## Where the hand-written guide is stale

Most of its code anchors still exist. What does not match the tree:

- It says the GICv5 arm of `__irq_is_ppi()` tests the type field and nothing
  else, and tells reviewers to demand a separate bound from every caller. The
  macro now bounds the ID.
- It describes `gicv5_its_irq_domain_alloc()` allocating LPIs per iteration with
  an unwind that once missed earlier iterations. The function allocates nothing
  per iteration.
- It says the kernel learns whether the maintenance interrupt exists from
  `ICC_IDR0_EL1` and not from firmware, and that a missing one is tolerated.
  `gic_of_setup_kvm_info()` takes it from the device tree node and publishes
  nothing to KVM without it.
- It never mentions ACPI. The tree probes the IRS, ITS and IWB from ACPI, and
  the ACPI path never hands the GIC to KVM.
- Its section on userspace register overrides is about the vgic MMIO framework;
  the GICv5 device has no register save and restore at all (every such
  attribute group returns `-ENXIO`).
- Its sections on VM and VPE tables, valid bits of those tables, migration of
  interrupt state, doorbells, the self-synchronising register list, legacy EOI
  mode and the ranges of ID register fields are architecture with no code in the
  tree behind them (`struct gicv5_vpe` is one `bool`). A guide built from a tree
  cannot state them, and the build set does not ask.
- It has no map of the subsystem: nothing on CPU registration and affinity IDs,
  IPIs, the domains and chips, event IDs, the MSI parent code, the device
  lifetime in the ITS, or the KVM entry points.

## What was left out of the build set

Fourteen of the 138 questions. `docs`, `global-data`, `irs-chip-data`,
`ppi-numbers`, `insn-operands` and `its-table-formats` ask for what one open of
the header shows, and the core files table points there. `irs-dt-probe`,
`irs-acpi-probe` and `its-acpi-probe` are init-only and their one hazard each is
carried by the probe order, affinity and ACPI model questions. `wait-helpers` is
folded into the status register table and the timeout rule,
`ist-alignment` into the sizing question, `component-capabilities` into the
priority and LPI ID bit questions. `lpi-reset` and `kmemleak` are narrow. The
rest were kept with budgets cut by about forty percent, tables least.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader-A          341        48%     18     90   6.17 to 7.0
reader-B          305        85%      1    136   6.12 to 6.17
reader-C          271        22%     59     29   6.17 to 7.1

question                           reader-A      reader-B      reader-C   verdict
gicv5.core-files                   25% ( 2)      52% ( 7)       3% ( 3)   weak: reader-B
gicv5.entry-points                 14% ( 5)      35% ( 1)      10% ( 4)   middling
gicv5.docs                         48% ( 2)      86% ( 1)       0% ( 0)   weak: reader-A, reader-B
gicv5.components                   10% ( 2)      73% ( 1)      50% ( 2)   weak: reader-B, reader-C
gicv5.global-data                  52% ( 4)      90% ( 1)       7% ( 1)   weak: reader-A, reader-B
gicv5.irs-chip-data                29% ( 2)      95% ( 1)      29% ( 1)   weak: reader-B
gicv5.intid-encoding               41% ( 3)      82% ( 4)      12% ( 1)   weak: reader-A, reader-B
gicv5.typed-id-usage               53% ( 1)      82% ( 1)      18% ( 4)   weak: reader-A, reader-B
gicv5.hwirq-meaning                35% ( 1)      77% ( 3)       6% ( 2)   weak: reader-B
gicv5.ppi-numbers                  15% ( 1)      80% ( 1)      10% ( 1)   weak: reader-B
gicv5.irq-domains                  40% ( 5)      74% ( 6)      10% ( 3)   weak: reader-A, reader-B
gicv5.fwspec-translate             58% ( 2)      89% ( 4)       0% ( 0)   weak: reader-A, reader-B
gicv5.irq-dispatch                 26% ( 1)      79% ( 3)      20% ( 3)   weak: reader-B
gicv5.ipis                         34% ( 2)      92% ( 2)       5% ( 1)   weak: reader-B
gicv5.lpi-allocation               63% ( 5)      93% ( 6)      37% ( 4)   weak: reader-A, reader-B
gicv5.irq-chips                    19% ( 3)      76% ( 1)      27% ( 4)   weak: reader-B
gicv5.domain-alloc-unwind          35% ( 2)      85% ( 1)      66% ( 1)   weak: reader-B, reader-C
gicv5.gic-instructions              9% ( 4)      95% ( 5)      14% ( 8)   weak: reader-B
gicv5.insn-operands                12% ( 1)      93% ( 1)      23% ( 1)   weak: reader-B
gicv5.gsb-barriers                 56% ( 1)      95% ( 1)      20% ( 1)   weak: reader-A, reader-B
gicv5.mask-unmask-sync             63% ( 1)      90% ( 1)      16% ( 0)   weak: reader-A, reader-B
gicv5.ppi-mask-sync                 1% ( 2)      68% ( 3)       0% ( 3)   weak: reader-B
gicv5.barrier-usage                 9% ( 1)      86% ( 1)      38% ( 4)   weak: reader-B
gicv5.state-query                   0% ( 0)      71% ( 1)       0% ( 0)   weak: reader-B
gicv5.icsr-sharing                 53% ( 2)      87% ( 1)      18% ( 1)   weak: reader-A, reader-B
gicv5.ack-sequence                 20% ( 1)      94% ( 5)      20% ( 5)   weak: reader-B
gicv5.priority-drop                52% ( 1)      87% ( 1)      72% ( 1)   all weak
gicv5.eoi-usage                     0% ( 0)      89% ( 1)      45% ( 1)   weak: reader-B, reader-C
gicv5.forwarded-ppi-eoi            29% ( 1)      90% ( 1)      70% ( 1)   weak: reader-B, reader-C
gicv5.lpi-retrigger                71% ( 3)      92% ( 1)      20% ( 1)   weak: reader-A, reader-B
gicv5.set-affinity                 30% ( 1)      92% ( 1)      38% ( 1)   weak: reader-B
gicv5.priorities                   66% ( 8)      91% ( 1)       9% ( 1)   weak: reader-A, reader-B
gicv5.cpuif-enable                 45% ( 3)      87% ( 1)      41% ( 5)   all weak
gicv5.ppi-trigger                  49% ( 3)      87% ( 2)      58% ( 2)   all weak
gicv5.ppi-register-banks           43% ( 3)      93% ( 3)      15% ( 1)   weak: reader-A, reader-B
gicv5.lpi-reset                    73% ( 3)      91% ( 1)      40% ( 3)   all weak
gicv5.init-order                   71% ( 7)      97% ( 8)      40% ( 9)   all weak
gicv5.irs-dt-probe                 46% ( 1)      89% ( 2)       8% ( 1)   weak: reader-A, reader-B
gicv5.irs-acpi-probe               85% ( 1)      90% ( 1)       2% ( 1)   weak: reader-A, reader-B
gicv5.iaffid-mapping               57% ( 1)      76% ( 2)      20% ( 1)   weak: reader-A, reader-B
gicv5.firmware-value-handling      50% ( 3)      76% ( 3)      47% ( 5)   all weak
gicv5.cpu-registration             62% ( 4)      87% ( 3)       5% ( 1)   weak: reader-A, reader-B
gicv5.spi-ownership                32% ( 1)      81% ( 2)       0% ( 0)   weak: reader-B
gicv5.irs-id-registers             31% ( 5)      81% ( 2)      10% ( 0)   weak: reader-B
gicv5.spi-set-type                  0% ( 4)      83% ( 4)       7% ( 3)   weak: reader-B
gicv5.select-program-usage         44% ( 3)      79% ( 2)      47% ( 1)   all weak
gicv5.status-registers             36% ( 4)      82% ( 1)      10% ( 1)   weak: reader-B
gicv5.wait-helpers                 14% ( 1)      89% ( 1)      39% ( 1)   weak: reader-B
gicv5.idle-and-valid               37% ( 5)      80% ( 5)      22% ( 4)   weak: reader-B
gicv5.timeout-handling             63% ( 6)      82% ( 1)      11% ( 1)   weak: reader-A, reader-B
gicv5.irs-sync                     46% ( 2)      90% ( 1)      13% ( 0)   weak: reader-A, reader-B
gicv5.ist-overview                 55% ( 4)      80% ( 8)      50% ( 4)   all weak
gicv5.ist-structure-choice         19% ( 1)      87% ( 3)      14% ( 1)   weak: reader-B
gicv5.lpi-id-bits                  77% ( 2)      88% ( 2)      26% ( 1)   weak: reader-A, reader-B
gicv5.ist-sizing                   46% ( 2)      89% ( 2)       8% ( 1)   weak: reader-A, reader-B
gicv5.ist-alignment                39% ( 1)      87% ( 2)      35% ( 2)   weak: reader-B
gicv5.ist-publish                  52% ( 6)      85% ( 6)       1% ( 2)   weak: reader-A, reader-B
gicv5.iste-alloc                   36% ( 1)      93% ( 3)       3% ( 2)   weak: reader-B
gicv5.ist-valid-bit                33% ( 1)      78% ( 2)       1% ( 2)   weak: reader-B
gicv5.iste-serialisation           74% ( 1)      90% ( 1)       0% ( 0)   weak: reader-A, reader-B
gicv5.kmemleak                     34% ( 1)      78% ( 3)      14% ( 1)   weak: reader-B
gicv5.irs-memory-attributes        55% ( 3)      84% ( 6)      29% ( 1)   weak: reader-A, reader-B
gicv5.noncoherent-maintenance      57% ( 3)      75% ( 5)      42% ( 3)   all weak
gicv5.hw-written-readback          70% ( 3)      87% ( 1)      43% ( 2)   all weak
gicv5.id-decode-fallbacks           9% ( 1)      89% ( 3)       0% ( 0)   weak: reader-B
gicv5.component-capabilities       31% ( 1)      89% ( 2)       4% ( 1)   weak: reader-B
gicv5.virt-capable                 55% ( 3)      89% ( 3)      21% ( 2)   weak: reader-A, reader-B
gicv5.its-structures               44% ( 6)      93% ( 6)      38% ( 3)   weak: reader-A, reader-B
gicv5.its-config-model              8% ( 1)      93% ( 1)       8% ( 1)   weak: reader-B
gicv5.its-table-write              36% ( 1)      96% ( 1)      39% ( 1)   weak: reader-B
gicv5.its-invalidate               27% ( 1)      94% ( 1)      45% ( 5)   weak: reader-B, reader-C
gicv5.its-sync                     65% ( 3)      87% ( 1)      23% ( 1)   weak: reader-A, reader-B
gicv5.its-valid-bits               26% ( 3)      89% ( 2)       0% ( 0)   weak: reader-B
gicv5.its-publish-usage             1% ( 3)      86% ( 3)      16% ( 3)   weak: reader-B
gicv5.its-entry-endianness         16% ( 1)      82% ( 1)      13% ( 0)   weak: reader-B
gicv5.its-table-formats            28% ( 6)      96% ( 5)       0% ( 0)   weak: reader-B
gicv5.its-devtab-choice            68% ( 5)      87% ( 1)       2% ( 1)   weak: reader-A, reader-B
gicv5.its-devtab-l2                60% ( 3)      91% ( 1)       0% ( 1)   weak: reader-A, reader-B
gicv5.its-itt-choice               58% ( 3)      87% ( 1)      12% ( 2)   weak: reader-A, reader-B
gicv5.its-device-register          65% ( 3)      94% ( 1)      11% ( 2)   weak: reader-A, reader-B
gicv5.its-device-unregister        49% ( 2)      82% ( 2)      56% ( 5)   all weak
gicv5.its-device-lifetime          13% ( 1)      90% ( 2)      11% ( 1)   weak: reader-B
gicv5.its-scratchpad                3% ( 1)      79% ( 1)       0% ( 0)   weak: reader-B
gicv5.its-msi-parent               65% ( 4)      85% ( 2)      20% ( 1)   weak: reader-A, reader-B
gicv5.its-eventid-alloc            19% ( 4)      72% ( 2)      11% ( 3)   weak: reader-B
gicv5.its-domain-alloc             64% ( 6)      84% ( 5)      39% ( 1)   weak: reader-A, reader-B
gicv5.its-domain-free              55% ( 1)      82% ( 5)      24% ( 1)   weak: reader-A, reader-B
gicv5.its-activate                  8% ( 0)      82% ( 3)      12% ( 1)   weak: reader-B
gicv5.its-init                     41% ( 2)      88% ( 3)       9% ( 3)   weak: reader-A, reader-B
gicv5.its-noncoherent-flag         53% ( 2)      94% ( 2)      60% ( 1)   all weak
gicv5.its-acpi-probe               79% ( 2)      89% ( 1)      23% ( 1)   weak: reader-A, reader-B
gicv5.its-locking                  81% ( 3)      93% ( 1)      48% ( 1)   all weak
gicv5.iwb-overview                 11% ( 1)      85% ( 2)      19% ( 1)   weak: reader-B
gicv5.iwb-msi-template             34% ( 3)      84% ( 1)      19% ( 1)   weak: reader-B
gicv5.iwb-enable                   50% ( 4)      94% ( 1)      22% ( 1)   weak: reader-A, reader-B
gicv5.iwb-probe                    23% ( 1)      89% ( 2)      13% ( 0)   weak: reader-B
gicv5.iwb-translate                54% ( 3)      92% ( 1)      47% ( 3)   all weak
gicv5.dt-binding                   69% ( 1)      87% ( 1)       2% ( 1)   weak: reader-A, reader-B
gicv5.acpi-model                   72% ( 2)      90% ( 1)      14% ( 3)   weak: reader-A, reader-B
gicv5.boot-requirements            65% ( 2)      88% ( 1)      24% ( 1)   weak: reader-A, reader-B
gicv5.cpucaps                      56% ( 1)      91% ( 1)       0% ( 0)   weak: reader-A, reader-B
gicv5.cap-check-usage              74% ( 2)      80% ( 2)      42% ( 1)   all weak
gicv5.kvm-scope                    89% ( 4)      93% ( 2)       5% ( 1)   weak: reader-A, reader-B
gicv5.kvm-entry-points             47% ( 1)      95% ( 1)       9% ( 3)   weak: reader-A, reader-B
gicv5.kvm-info-handoff             69% ( 1)      89% ( 1)       8% ( 3)   weak: reader-A, reader-B
gicv5.vgic-probe                   81% ( 1)      94% ( 2)      19% ( 2)   weak: reader-A, reader-B
gicv5.compat-mode                  47% ( 7)      82% ( 6)      21% ( 4)   weak: reader-A, reader-B
gicv5.compat-mode-switch           37% ( 1)      89% ( 1)      46% ( 2)   weak: reader-B, reader-C
gicv5.kvm-not-implemented          43% ( 1)      76% ( 1)      21% ( 2)   weak: reader-A, reader-B
gicv5.kvm-intid-helpers            86% ( 4)      90% ( 5)      66% ( 3)   all weak
gicv5.kvm-type-predicates          79% ( 1)      89% ( 1)      59% ( 1)   all weak
gicv5.kvm-private-lookup           66% ( 1)      93% ( 1)      48% ( 1)   all weak
gicv5.kvm-ppi-count                78% ( 1)       0% ( 1)      27% ( 2)   weak: reader-A
gicv5.kvm-irq-ops                  86% ( 1)      89% ( 1)      36% ( 2)   weak: reader-A, reader-B
gicv5.kvm-ppi-masks                70% ( 4)      93% ( 3)      20% ( 5)   weak: reader-A, reader-B
gicv5.kvm-finalize                 85% ( 3)      90% ( 1)      50% ( 3)   all weak
gicv5.kvm-visible-iteration        78% ( 1)      89% ( 1)      45% ( 1)   all weak
gicv5.kvm-userspace-ppis           74% ( 7)      94% ( 1)       0% ( 0)   weak: reader-A, reader-B
gicv5.kvm-device-attrs             88% ( 2)      96% ( 1)      25% ( 3)   weak: reader-A, reader-B
gicv5.kvm-state-placement          87% ( 2)      95% ( 4)      20% ( 3)   weak: reader-A, reader-B
gicv5.kvm-flush                    51% ( 3)      86% ( 6)      17% ( 6)   weak: reader-A, reader-B
gicv5.kvm-fold                     51% ( 1)      92% ( 1)       5% ( 1)   weak: reader-A, reader-B
gicv5.kvm-edge-level-usage         25% ( 1)      83% ( 1)       0% ( 0)   weak: reader-B
gicv5.kvm-hyp-ppi-switch           77% ( 1)      91% ( 1)      36% ( 4)   weak: reader-A, reader-B
gicv5.kvm-dvi                      77% ( 1)      92% ( 1)      36% ( 4)   weak: reader-A, reader-B
gicv5.kvm-bitmap-atomicity         53% ( 3)      85% ( 3)      22% ( 3)   weak: reader-A, reader-B
gicv5.kvm-load-put                 53% ( 1)      90% ( 1)      19% ( 3)   weak: reader-A, reader-B
gicv5.kvm-vmcr-apr                 79% ( 1)      88% ( 1)      11% ( 1)   weak: reader-A, reader-B
gicv5.kvm-pending-check            66% ( 1)      87% ( 1)      20% ( 2)   weak: reader-A, reader-B
gicv5.kvm-priority-sync            66% ( 1)      81% ( 1)      24% ( 1)   weak: reader-A, reader-B
gicv5.kvm-enable-trap              76% ( 5)      89% ( 1)      43% ( 4)   all weak
gicv5.kvm-fgt                      56% ( 3)      92% ( 3)      20% ( 2)   weak: reader-A, reader-B
gicv5.kvm-id-emulation             58% ( 3)      82% ( 3)       7% ( 1)   weak: reader-A, reader-B
gicv5.kvm-timers                   77% ( 6)      94% ( 5)      16% ( 5)   weak: reader-A, reader-B
gicv5.kvm-pmu                      81% ( 1)      90% ( 1)       0% ( 0)   weak: reader-A, reader-B
gicv5.kvm-create                   69% ( 4)      90% ( 1)      35% ( 4)   weak: reader-A, reader-B
gicv5.kvm-selftests                79% ( 2)      93% ( 1)      60% ( 2)   all weak
gicv5.change-checklist             71% ( 9)      80% ( 6)      60% ( 7)   all weak
```

## Questions reorganised

- The build set went from 126 questions to 99, one part and one `- section:` per subject: interrupt IDs, domains and chips; instructions, barriers and the interrupt path; CPU interface and PPIs; IRS probing and registers; the interrupt state table; ITS entries and publishing; ITS devices and tables; ITS interrupts and MSIs; the interrupt wire bridge; firmware, boot and CPU capabilities; KVM scope and probing; KVM interrupt IDs and PPI state; KVM entry and exit; KVM traps and emulated registers.
- Merged on the host side, old id to new: `intid-encoding` to `typed-id-usage`; `irq-chips` and `lpi-retrigger` to `chip-operations`; `gsb-barriers` to `barrier-usage`; `irq-dispatch` to `ack-sequence`; `mask-unmask-sync` and `ppi-mask-sync` to `mask-sync`; `icsr-sharing` to `state-query`; `virt-capable` to `id-decode-fallbacks`; `spi-set-type` to `select-program-usage`; `status-registers` to `idle-and-valid`; `ist-structure-choice` to `lpi-id-bits`; `iste-serialisation` to `iste-alloc`; `its-table-write` to `its-publish-usage`; `its-sync` to `its-invalidate`; `its-structures` to `its-device-lifetime`; `its-devtab-l2` to `its-devtab-choice`; `its-scratchpad` to `its-msi-parent`; `iwb-msi-template` to `iwb-overview`; `cap-check-usage` to `cpucaps`.
- Merged on the KVM side: `kvm-not-implemented` to `kvm-scope`; `kvm-ppi-count` to `kvm-private-lookup`; `kvm-visible-iteration` to `kvm-ppi-masks`; `kvm-device-attrs` to `kvm-userspace-ppis`; `kvm-edge-level-usage` to `kvm-fold`; `kvm-priority-sync` to `kvm-load-put`.
- Dropped: `dt-binding`, an inventory of compatible strings and properties (the binding file is a row of `core-files`, and the cell layout is asked by `fwspec-translate`); `kvm-selftests`, an inventory scored 2 (the selftests are a row of `core-files`); `change-checklist`, a six-item checklist that handed over its own answer and whose every item has a question: `init-order` and `acpi-model`, `noncoherent-maintenance`, `lpi-id-bits` and `its-devtab-choice`, `its-entry-endianness`, `forwarded-ppi-eoi`, `compat-mode`.
- Kept with a narrower ask: `irs-id-registers` no longer wants a table of ID fields, only which system-wide properties are read from the first IRS and on what assumption; `irq-domains` asks for parentage, who creates the LPI domain and which domains carry a bus token; `lpi-allocation` gained what `lpi-reset` found every reader wrong on, what is not done to a fresh LPI.
- Every "list in order what X does" question (`init-order`, `cpuif-enable`, `ist-publish`, `iste-alloc`, `its-device-register`, `its-init`, `its-domain-alloc`, `vgic-probe`) now asks what must precede what, what can fail and what is undone.
