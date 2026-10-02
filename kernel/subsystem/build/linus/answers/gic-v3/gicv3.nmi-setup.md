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
