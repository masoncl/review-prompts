# What the gic-v3 measurement found

Three models were asked the 139 questions in `gic-v3-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A and C (both
current; A assumed kernels from 6.8 to 6.19, C from 6.12 to 7.0) and B (older,
6.6 to 6.13, and wrong about fundamentals as well as names); which models they
were does not matter here. The hand-written guide was never checked against
current sources, so differences between it and the built guide are expected
and are noted below. One group of four answers from reader B came back from
the checker empty and was run again on its own; the numbers include the second
run.

## What all three readers got wrong

- **Pseudo-NMI set-up.** All three had SGIs and PPIs take a per-interrupt
  reference count and switch to handle_percpu_devid_fasteoi_nmi(). Neither
  exists. `gic_irq_nmi_setup()` swaps the flow handler to
  `handle_fasteoi_nmi()` only for interrupts outside the redistributor and
  writes `dist_prio_nmi`; SGIs, PPIs and EPPIs keep
  `handle_percpu_devid_irq()`. Readers A and C put a MediaTek quirk flag in the
  GIC driver; the only thing there that forbids NMIs is
  `nmi_support_forbidden`, set in `gic_prio_init()` for the RK3399
  `FLAGS_WORKAROUND_INSECURE` quirk. Reader B used GICv2 priority macros.
- **PPI partitions.** All three listed a `ppi_descs` field and a partition
  domain. `struct gic_chip_data` holds `parts` and `nr_parts`, there is no
  partition interrupt type in `gic_irq_domain_translate()`, and the affinity
  of a partitioned PPI is returned by `gic_irq_get_fwspec_info()`.
- **Waiting for a register write.** `gic_do_wait_for_rwp()` is void, uses
  `readl_relaxed_poll_timeout_atomic()` and only logs; `gic_dist_config()` and
  `gic_cpu_config()` take no sync callback and their callers wait;
  `gic_set_affinity()` does not wait after the router write although its
  comment says so. Reader B also put the redistributor's write-pending bit at
  bit 31; `GICR_CTLR_RWP` is bit 3.
- **Shareability read-back.** For the command queue, the property table and
  the pending table all three said the flush flag follows a read-back of zero.
  `its_probe_one()` and `its_cpu_init_lpis()` set the flag on any mismatch and
  rewrite the register as non-cacheable only when it reads back zero; the
  forced non-shareable flags mask the read-back for those registers but make
  `its_alloc_tables()` start non-cacheable instead.
- **The virtual machine control register.** Readers A and B said it is saved
  when the vCPU is put, by functions that do not exist; reader C repeated the
  comment in `kvm_vcpu_wfi()`. `__vgic_v3_save_state()` reads it back at every
  guest exit, `vgic_v3_put()` saves only the active priority registers, and
  where it is written depends on the guest's `vgic_sre` and on the hypervisor
  mode.
- **Per-interrupt callbacks.** `struct irq_ops` has no flags field. It has
  `get_flags()`, `get_input_level()`, `queue_irq_unlock()` and
  `set_direct_injection()`; `kvm_vgic_map_irq()` does not install it and the
  unmap does not clear it; the timer's `get_flags()` reports
  `VGIC_IRQ_SW_RESAMPLE` from `no_hw_deactivation`.
- **Registering an LPI.** All three said the store under the xarray lock
  passes no allocation flags and that a failed store calls xa_release().
  `vgic_add_lpi()` reserves with `xa_reserve_irq()` before the lock, stores
  with `GFP_NOWAIT | __GFP_ACCOUNT`, evicts an entry whose count is zero and
  hands it to `kfree_rcu()`, and on failure only unlocks and frees. There is no
  xa_release() in the vGIC.
- **Disabling LPIs on a redistributor.** All three said
  `vgic_flush_pending_lpis()` leaves the pending state alone and drops the
  reference with `vgic_put_irq()`. It clears `pending_latch`, clears `vcpu`,
  uses `vgic_put_irq_norelease()` and then `vgic_release_deleted_lpis()`.
- **Deactivation by trap.** All three tied the deactivate-register trap to the
  guest's EOI mode. `vgic_v3_configure_hcr()` sets it whatever the mode: when
  the CPU lacks the trap capability, when active interrupts are outside the
  list registers, or when `active_spis` is non-zero. That counter is
  incremented in `vgic_queue_irq_unlock()` when an SPI is queued and
  decremented only in `vgic_v3_fold_lr()`; the broadcast on its first
  increment is `KVM_REQ_IRQ_PENDING`. The cases in `vgic_v3_deactivate()` and
  the AmpereOne errata behind the nested-state skip were unknown to all.
- **Initialising the vGIC.** `vgic_init()` does not allocate private
  interrupts, `kvm_vgic_inject_irq()` returns 0 and drops the injection before
  initialisation, and only `GICD_IIDR` and `GICD_TYPER2` may be accessed by
  userspace before it.
- **Boot-time writes of the virtual pending base register.** No reader could
  name `__gic_update_rdist_properties()` and `allocate_vpe_l1_table()`, which
  write `GICR_VPENDBASER_PendingLast` without the dirty-bit poll that
  `its_clear_vpend_valid()` does before and after its write.
- **A GICv3 guest on a GICv5 host.** `vgic_v5_probe()` keys on the
  `ARM64_HAS_GICV5_LEGACY` capability, registers both device types, and the
  only change on the GICv3 paths is that `vgic_v3_deactivate_phys()` issues a
  GICv5 deactivate instruction.
- **Smaller things all missed**: the MSI parent file is
  `irq-gic-its-msi-parent.c`; `MSI_ALLOC_FLAGS_PROXY_DEVICE` is what marks a
  new device shared; the table entry helpers of the virtual ITS are macros in
  `vgic-its.c` whose size check is a `BUILD_BUG_ON()` while there is one ABI;
  `kvm_io_bus_register_dev()` uses `call_srcu()` and only the unregister
  waits for readers; the debugfs walk finds LPIs with `xa_find_after()` under
  RCU and takes no lock; `vpe_table_mask` only prefers a target and never
  skips the move command; nothing in the tree says a VSYNC after a GICv4.1 vPE
  unmap would be an error, only that it is not needed.

## What only some got wrong

- Reader A: the LPI xarray lock placed below the list lock (the comment in
  `vgic.c` puts it above); `vlpi_lock` called a mutex (it is a raw spinlock and
  sits outside `vmapp_lock`); the list sort order and a compute_ap_list_depth()
  that does not exist (`summarize_ap_list()` and `irqs_outside_lrs()`);
  `vgic_state_is_nested()` keyed on the virtual interface enable (it tests the
  virtual IMO and FMO bits); the redistributor walk ending at the first region;
  `its_msi_teardown()` order.
- Reader C: a pending_release bit in `struct vgic_irq` and xarray marks for
  deferred release (neither exists; a zero `refcount` is the marker);
  `vgic_put_irq()` described as two steps (it is
  `refcount_dec_and_lock_irqsave()`); `vcpu` as the owner of SGIs and PPIs,
  following a stale header comment; `cmd_lock` said to serialise save and
  restore.
- Readers A and C: the irqs-on entry path calling gic_arch_enable_irqs() (it
  is `gic_unmask_pnmis()`); invdb and vsgi builders always returning a vPE
  (they return NULL with a warning on an ITS that is not GICv4.1).
- Reader B, besides the above: the completion wait run under the ITS lock and
  its origin sampled after the write pointer; eight to ten send functions
  (there are two); a VSYNC after every vPE unmap; eager and lazy vPE mapping
  the wrong way round; an invented GICv4 lock order with `vmovp_lock`
  outermost; every GICv4 request routed through one callback; the priority
  shift condition backwards; `gic_complete_ack()` always writing the EOI
  register; set-pending of a virtual SGI by command (it is a write to
  `GITS_SGIR`); the translation cache as a fixed LRU list; kref in place of
  `refcount_t`; `vgic_get_irq()` indexing private interrupts; the restore order
  of the ITS tables; MAPTI replacing an existing mapping; the SGI number and
  target list bit positions.

## What the readers already knew

Readers A and C: the entry points, the interrupt ID ranges, the command queue
sequence with its wrap arithmetic and endianness fix-up, `compute_common_aff()`,
the LPI range allocator and its sort invariant, the move-command serialisation,
eager against lazy mapping and `vmapp_count`, the GICv4 structures and
interface, the fields of `struct vgic_irq`, the target oracle, the invalidate
register checks, SGI sending and per-CPU initialisation (reader C), the ITS
structures. Reader B knew the file layout and little else in detail.

## Where the hand-written guide is stale

- It says the virtual machine control register stays in hardware until the vCPU
  is put and that `vgic_v3_get_vmcr()` therefore reads a stale copy. In this
  tree it is read back at every exit. The put in `kvm_vcpu_wfi()` is still
  there and still matters for the doorbell request, which is keyed on `IN_WFI`;
  the comment above it gives the old reason.
- It says the pending-LPI flush leaves pending state untouched.
  `vgic_flush_pending_lpis()` clears `pending_latch`. The ownership re-check in
  `vgic_prune_ap_list()` that the paragraph argues for is there.
- "`xa_release()` belongs outside the xarray lock": the vGIC calls it nowhere.
- It says the ready flag's ordering used to be borrowed from a
  `synchronize_srcu()` inside register-frame registration. Registration uses
  `call_srcu()`; the flag is published with `smp_store_release()`.
- It gives the GICv4 lock order as three deep. The comment it quotes is still
  in `arm-gic-v4.h`, but `vlpi_lock` is taken outside `vmapp_lock`, and
  `vpe_proxy.lock` and `rd_lock` inside `vpe_lock`.
- It says any path that reads `col_idx` must take the vPE lock.
  `its_vpe_set_irqchip_state()` reads it under the doorbell's descriptor lock
  alone, correctly, because `its_vpe_set_affinity()` is a callback of the same
  interrupt.
- It names VSYNC_VCPU_INVALID, which is not in the tree, and about a fifth of
  it is quotation from the architecture specification: what RWP tracks, the
  UNPREDICTABLE cases for list registers and the pending base register, the
  CommonLPIAff sharing rules, the stall and retry bits. A build from a kernel
  tree reproduces what the code and its comments say about these and nothing
  more. The emulated ITS in this tree has no stalled state at all: a command
  that cannot be read or that fails is skipped.
- It has no map of the files and nothing on: the deactivate trap and
  `active_spis`, `struct irq_ops`, `on_lr`, PPI affinity through
  `gic_irq_get_fwspec_info()`, nested guests, the GICv5 device type that now
  shares `vgic_init()` and `kvm_vgic_map_resources()`, or protected mode.
- The checker noted one thing the guide's rule about not caching directly
  injected interrupts does not cover: `kvm_vgic_v4_set_forwarding()` calls
  `vgic_its_resolve_lpi()`, which caches the translation before `hw` is set,
  and nothing invalidates that entry afterwards.

## What was left out of the build set

Reader B is wrong nearly everywhere, so the set was chosen by importance and
trimmed where readers A and C are both right, not by dropping what readers
know. Of the 139 questions 115 are kept, with budgets adding to 9,590 words.
Left out:

- Probe and boot sequences a reviewer reads once: `gicv3.its-probe`,
  `gicv3.dist-init`, `gicv3.rdist-discovery`, `gicv3.lpi-cpu-init`,
  `gicv3.its-collections`, `gicv3.options`, `gicv3.chip-data`.
- Paths with one or two call sites: `gicv3.mask-forwarded`,
  `gicv3.set-affinity`, `gicv3.lpi-affinity`, `gicv3.lpi-activate`,
  `gicv3.msi-parent`, `gicv3.its-vpe-table`, `gicv3.v4-proxy-device`,
  `gicv3.v4-vlpi-doorbell`, `gicv3.v4-vpe-init`, `gicv3.v4-boot-cleanup` (the
  boot-time writes are kept in `gicv3.v4-vpend-usage`).
- KVM paths covered well enough by a neighbour that is kept:
  `gicv3.vgic-maint-irq`, `gicv3.vgic-active-access`, `gicv3.vgic-v4-init`,
  `gicv3.vgic-pending-tables`, `gicv3.vits-handlers`, `gicv3.vits-inject`,
  `gicv3.vgic-propbaser`.
- Shrunk to a pointer because readers A and C answer them:
  `gicv3.entry-points`, `gicv3.intid-ranges`, `gicv3.common-aff`,
  `gicv3.vgic-target-oracle`, `gicv3.v4-vmovp`, `gicv3.cmdq-layout`.
- The architecture specification's own rules, which no question run against a
  kernel tree can answer.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 322 corrections, 28% rewritten on average, 33 answers rewritten 15% or less, 36 rewritten 40% or more
reader B: 440 corrections, 81% rewritten on average, 1 answers rewritten 15% or less, 136 rewritten 40% or more
reader C: 243 corrections, 19% rewritten on average, 65 answers rewritten 15% or less, 9 rewritten 40% or more

question                            reader A      reader B      reader C
gicv3.files                         10% ( 3)      23% ( 4)       6% ( 2)
gicv3.entry-points                   0% ( 0)       6% ( 3)       1% ( 1)
gicv3.docs-tests                     2% ( 1)      16% ( 1)      17% ( 2)
gicv3.options                       32% ( 3)      82% ( 2)      34% ( 3)
gicv3.chip-data                     11% ( 1)      62% ( 5)       3% ( 1)
gicv3.intid-ranges                   1% ( 1)      50% ( 2)       0% ( 0)
gicv3.rdist-discovery               54% ( 4)      78% ( 1)       9% ( 1)
gicv3.rdist-capabilities            33% ( 4)      80% ( 4)      22% ( 2)
gicv3.irq-chips                     28% ( 5)      85% ( 3)       6% ( 3)
gicv3.eoi-mode                      28% ( 1)      80% ( 5)       7% ( 1)
gicv3.fwspec                        52% ( 2)      92% ( 3)      32% ( 2)
gicv3.quirks                        41% ( 2)      78% ( 2)      17% ( 5)
gicv3.rwp-wait                      58% ( 3)      82% ( 3)      39% ( 2)
gicv3.rwp-usage                     15% ( 1)      73% ( 2)      39% ( 1)
gicv3.mask-forwarded                11% ( 1)      78% ( 2)      18% ( 1)
gicv3.irqchip-state                 28% ( 1)      91% ( 2)      21% ( 1)
gicv3.set-affinity                  18% ( 1)      88% ( 1)      13% ( 0)
gicv3.prio-constants                17% ( 4)      86% ( 2)       0% ( 0)
gicv3.prio-views                    24% ( 1)      84% ( 2)       8% ( 2)
gicv3.prio-usage                    23% ( 2)      79% ( 3)      31% ( 1)
gicv3.nmi-setup                     39% ( 3)      83% ( 3)      34% ( 5)
gicv3.nmi-entry                     27% ( 2)      95% ( 3)       3% ( 1)
gicv3.ack-sync                      21% ( 1)      77% ( 2)       9% ( 1)
gicv3.sgi-send                      13% ( 3)      57% ( 4)       0% ( 0)
gicv3.cpu-init                      33% ( 2)      79% ( 2)       0% ( 0)
gicv3.sre-enable                    29% ( 1)      71% ( 2)       5% ( 1)
gicv3.dist-init                     36% ( 1)      82% ( 4)       5% ( 1)
gicv3.hotplug-states                22% ( 1)      79% ( 4)      18% ( 1)
gicv3.its-node                       3% ( 2)      80% ( 6)       1% ( 1)
gicv3.its-device                    45% ( 4)      76% ( 2)      20% ( 3)
gicv3.its-collections               24% ( 1)      75% ( 2)      20% ( 2)
gicv3.its-probe                     43% ( 4)      86% ( 5)      19% ( 4)
gicv3.its-quiesce                   39% ( 2)      80% ( 3)       0% ( 0)
gicv3.its-memory                    30% ( 1)      86% ( 4)      24% ( 3)
gicv3.cmdq-layout                    1% ( 1)      68% ( 3)      18% ( 1)
gicv3.cmdq-send                      3% ( 1)      93% ( 6)      17% ( 1)
gicv3.cmdq-flush                    21% ( 1)      87% ( 4)      37% ( 2)
gicv3.cmdq-wait                      4% ( 1)      92% ( 4)      24% ( 0)
gicv3.cmdq-builders                 25% ( 2)      74% ( 7)       6% ( 1)
gicv3.cmdq-sync                     24% ( 1)      91% ( 2)       5% ( 1)
gicv3.cmdq-vmapp-sync               41% ( 1)      86% ( 1)      16% ( 1)
gicv3.cmdq-usage                    47% ( 2)      83% ( 2)      26% ( 3)
gicv3.its-tables                    23% ( 3)      87% ( 6)      20% ( 1)
gicv3.its-l2-alloc                  17% ( 1)      69% ( 1)       4% ( 0)
gicv3.its-vpe-table                 13% ( 1)      88% ( 1)      37% ( 3)
gicv3.common-aff                     0% ( 0)      93% ( 1)       0% ( 0)
gicv3.noncoherent                   22% ( 3)      70% ( 2)      22% ( 4)
gicv3.lpi-tables                    33% ( 4)      84% ( 6)      30% ( 3)
gicv3.lpi-idbits                    38% ( 2)      78% ( 1)      17% ( 1)
gicv3.lpi-prealloc                   5% ( 1)      89% ( 3)      28% ( 2)
gicv3.lpi-cpu-init                  18% ( 2)      86% ( 3)      17% ( 1)
gicv3.lpi-config                    12% ( 1)      85% ( 1)      10% ( 1)
gicv3.lpi-direct-inv                 5% ( 1)      77% ( 1)      29% ( 1)
gicv3.lpi-allocator                  7% ( 1)      75% ( 1)       5% ( 1)
gicv3.lpi-affinity                  29% ( 3)      88% ( 2)      12% ( 1)
gicv3.msi-prepare                   31% ( 3)      85% ( 8)       4% ( 1)
gicv3.msi-parent                    55% ( 4)      85% ( 3)      12% ( 1)
gicv3.lpi-activate                  24% ( 1)      87% ( 4)      14% ( 1)
gicv3.v4-structs                    11% ( 2)      72% ( 6)       2% ( 1)
gicv3.v4-api                         7% ( 1)      55% ( 4)       4% ( 2)
gicv3.v4-irqchips                   16% ( 3)      90% ( 3)      10% ( 1)
gicv3.v4-locks                      54% ( 8)      89% ( 4)       6% ( 2)
gicv3.v4-col-idx                    40% ( 5)      81% ( 2)      14% ( 3)
gicv3.v4-vpe-affinity                7% ( 1)      92% ( 6)      11% ( 1)
gicv3.v4-vmovp                       3% ( 1)      84% ( 4)       0% ( 0)
gicv3.v4-mapping-policy              5% ( 1)      84% ( 3)       0% ( 0)
gicv3.v4-schedule                   14% ( 1)      85% ( 3)      10% ( 2)
gicv3.v4-deschedule                 23% ( 1)      90% ( 5)      17% ( 2)
gicv3.v4-vpend-usage                70% ( 5)      84% ( 4)      41% ( 2)
gicv3.v4-pending-last               41% ( 1)      84% ( 1)      30% ( 1)
gicv3.v4-doorbells                  30% ( 3)      87% ( 1)       6% ( 1)
gicv3.v4-proxy-device               24% ( 3)      78% ( 1)      13% ( 1)
gicv3.v4-vlpi-map                   17% ( 6)      87% ( 5)       3% ( 2)
gicv3.v4-vlpi-doorbell              33% ( 2)      82% ( 1)      38% ( 1)
gicv3.v4-vsgi                       19% ( 4)      91% ( 4)      11% ( 1)
gicv3.v4-vpe-init                    5% ( 1)      88% ( 3)      12% ( 3)
gicv3.v4-boot-cleanup               16% ( 1)      91% ( 2)      28% ( 1)
gicv3.vgic-global                   37% ( 5)      83% ( 4)       8% ( 7)
gicv3.vgic-irq                       3% ( 1)      76% ( 2)      18% ( 3)
gicv3.vgic-irq-ops                  59% ( 3)      85% ( 4)      56% ( 4)
gicv3.vgic-lookup                   38% ( 5)      89% ( 7)      53% ( 3)
gicv3.vgic-lock-order               16% ( 1)      85% ( 3)      13% ( 1)
gicv3.vgic-dist-cpu                 31% ( 1)      80% ( 5)      31% ( 2)
gicv3.vgic-lpi-refs                 18% ( 6)      74% ( 2)      13% ( 2)
gicv3.vgic-lpi-get                  44% ( 1)      83% ( 2)      10% ( 1)
gicv3.vgic-lpi-put                  20% ( 1)      86% ( 2)      37% ( 2)
gicv3.vgic-lpi-norelease            25% ( 1)      85% ( 2)      35% ( 4)
gicv3.vgic-lpi-add                  18% ( 4)      69% ( 5)      16% ( 3)
gicv3.vgic-lpi-flush                19% ( 2)      74% ( 2)      17% ( 2)
gicv3.vgic-translation-cache        18% ( 3)      79% ( 2)      22% ( 2)
gicv3.vgic-queue                    40% ( 3)      86% ( 6)      17% ( 2)
gicv3.vgic-target-oracle             0% ( 0)      62% ( 1)       0% ( 0)
gicv3.vgic-prune                    21% ( 2)      74% ( 4)      25% ( 2)
gicv3.vgic-flush-lr                 71% ( 4)      89% ( 3)      20% ( 2)
gicv3.vgic-compute-lr               41% ( 2)      82% ( 5)      15% ( 1)
gicv3.vgic-fold-lr                  25% ( 5)      78% ( 6)      12% ( 3)
gicv3.vgic-eoicount                 44% ( 2)      83% ( 2)      30% ( 2)
gicv3.vgic-dir-trap                 71% ( 4)      87% ( 3)      42% ( 5)
gicv3.vgic-pending-check            28% ( 1)      89% ( 3)      21% ( 2)
gicv3.vgic-vmcr                     64% ( 6)      85% ( 4)      13% ( 3)
gicv3.vgic-wfi                      22% ( 2)      88% ( 2)      26% ( 3)
gicv3.vgic-load-put                 62% ( 3)      92% ( 3)      25% ( 1)
gicv3.vgic-traps                    74% ( 3)      88% ( 2)      28% ( 3)
gicv3.vgic-maint-irq                54% ( 1)      88% ( 1)      17% ( 0)
gicv3.vgic-mapped                   40% ( 4)      92% ( 5)      44% ( 4)
gicv3.vgic-resample                 37% ( 3)      82% ( 1)       9% ( 1)
gicv3.vgic-pending-access           20% ( 1)      90% ( 3)      15% ( 1)
gicv3.vgic-active-access            36% ( 1)      87% ( 3)      36% ( 1)
gicv3.vgic-v4-forwarding            47% ( 2)      91% ( 2)       6% ( 1)
gicv3.vgic-v4-load-put              12% ( 3)      87% ( 5)      12% ( 2)
gicv3.vgic-v4-vsgi                  45% ( 3)      87% ( 3)       3% ( 1)
gicv3.vgic-v4-init                  11% ( 2)      64% ( 2)       0% ( 0)
gicv3.vgic-pending-tables           35% ( 3)      81% ( 2)      22% ( 2)
gicv3.vits-structs                  22% ( 5)      72% ( 7)      47% ( 4)
gicv3.vits-cmdq                      8% ( 1)      77% ( 4)      15% ( 1)
gicv3.vits-handlers                 13% ( 4)      58% ( 3)       8% ( 1)
gicv3.vits-mapti                    22% ( 3)      87% ( 4)      13% ( 1)
gicv3.vits-mapd-discard             22% ( 2)      84% ( 5)      36% ( 2)
gicv3.vits-inject                   33% ( 3)      91% ( 4)      37% ( 2)
gicv3.vits-abi                      34% ( 3)      94% ( 4)      44% ( 1)
gicv3.vits-save                     22% ( 2)      79% ( 4)      33% ( 1)
gicv3.vits-restore                  25% ( 4)      96% ( 4)      39% ( 3)
gicv3.vits-scan                     40% ( 1)      84% ( 2)      31% ( 1)
gicv3.vits-ctrl-locking             44% ( 2)      85% ( 4)      22% ( 2)
gicv3.vgic-mmio                     25% ( 3)      84% ( 1)      14% ( 2)
gicv3.vgic-rd-inv                    8% ( 1)      92% ( 1)       6% ( 1)
gicv3.vgic-rd-typer                 12% ( 1)      86% ( 1)      19% ( 1)
gicv3.vgic-propbaser                39% ( 2)      86% ( 3)      11% ( 1)
gicv3.vgic-sgi-dispatch             30% ( 1)      78% ( 3)       0% ( 0)
gicv3.vgic-id-regs                  36% ( 3)      88% ( 3)      32% ( 2)
gicv3.vgic-create                   39% ( 3)      79% ( 6)      38% ( 2)
gicv3.vgic-init                     43% ( 4)      75% ( 2)      51% ( 5)
gicv3.vgic-map-resources            52% ( 2)      79% ( 4)      29% ( 4)
gicv3.vgic-redist-iodev             43% ( 2)      77% ( 3)      14% ( 1)
gicv3.vgic-destroy                  29% ( 3)      87% ( 6)       9% ( 2)
gicv3.vgic-config-lock              44% ( 1)      72% ( 3)      31% ( 1)
gicv3.vgic-debugfs                  62% ( 1)      77% ( 3)      25% ( 1)
gicv3.vgic-nested                   48% ( 6)      90% ( 6)      26% ( 5)
gicv3.vgic-v5-host                  48% ( 5)      95% ( 4)      47% ( 5)
```

## Questions reorganised

- The build set went from 117 questions to 109, one part and one `- section:` per subject: the distributor, redistributors and interrupt chips; register writes and priorities; CPU bring-up and IPIs; the ITS command queue; ITS tables and memory; LPIs; vPE mapping and movement; virtual LPIs and SGIs; vPE scheduling; virtual interrupts and their lifetime; list registers; world switch; mapped hardware interrupts; the virtual ITS; emulated distributor and redistributor registers; vGIC lifecycle; host handoff, nested guests and GICv5 hosts. The five verbatim items are untouched, so the five subjects that hold one kept the section name it carries.
- Merged: `gicv3.rwp-wait` and `gicv3.rwp-usage` into `gicv3.rwp-completion`; `gicv3.prio-constants` into `gicv3.prio-usage`; `gicv3.cmdq-layout` into `gicv3.cmdq-send`; `gicv3.v4-irqchips` into `gicv3.v4-doorbells`, with the virtual SGI chip left as a starting point of `gicv3.v4-vsgi`; `gicv3.vgic-destroy` into `gicv3.vgic-config-lock`.
- Dropped: `gicv3.docs-tests`, an inventory whose one useful part, the ABI documents, is now a row of the `gicv3.files` table; `gicv3.v4-structs` and `gicv3.vgic-dist-cpu`, which asked for the members of structures. What each object stands for is the overview's job, and the set-up flags and `active_spis` are asked about by `gicv3.vgic-init`, `gicv3.vgic-map-resources` and `gicv3.vgic-dir-trap`.
- Reworded, same id: questions that asked what a structure holds (`gicv3.its-node`, `gicv3.its-device`, `gicv3.vgic-irq`, `gicv3.vits-structs`, `gicv3.vgic-global`) now ask for its locks, its lifetime and what it is confused with; questions that asked for every step in order (`gicv3.cpu-init`, `gicv3.cmdq-send`, `gicv3.v4-vpe-affinity`, `gicv3.vgic-lpi-add`) ask which step depends on which and what the caller learns. None asks more than three or four things.
- Moved: KVM's GICv4 questions now sit beside the host driver's (`gicv3.vgic-v4-forwarding` and `gicv3.vgic-v4-vsgi` with virtual LPIs and SGIs, `gicv3.vgic-v4-load-put` and `gicv3.vgic-wfi` with vPE scheduling); `gicv3.vgic-lpi-get`, `gicv3.vgic-translation-cache` and `gicv3.vgic-debugfs` sit with the LPI lifetime, `gicv3.vgic-prune` with the list registers, `gicv3.vgic-irq-ops` with mapped interrupts, `gicv3.hotplug-states` with CPU bring-up.
