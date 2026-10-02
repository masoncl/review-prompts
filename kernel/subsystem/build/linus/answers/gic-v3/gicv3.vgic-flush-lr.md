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
