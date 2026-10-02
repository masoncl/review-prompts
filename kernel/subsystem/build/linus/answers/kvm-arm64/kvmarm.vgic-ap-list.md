- `vgic_queue_irq_unlock()`: calls `irq->ops->queue_irq_unlock` first when
  set, and returns its result.
- First SPI queued (`active_spis` goes from 0): every vCPU gets
  `KVM_REQ_IRQ_PENDING` when `vgic_model_needs_bcst_kick()` is true.
- `kvm_vgic_flush_hwstate()`: does not call `vgic_prune_ap_list()`.
- `vgic_prune_ap_list()`: runs from `kvm_vgic_sync_hwstate()` after the fold,
  and from `kvm_vgic_process_async_update()`.
- Overflow test: `summarize_ap_list()` fills `struct ap_list_summary`;
  `irqs_outside_lrs()` decides whether to sort. There is no
  compute_ap_list_depth() and no vgic_set_underflow().
- Sort order in `vgic_irq_cmp()`:
  1. deliverable to this vCPU;
  2. group enabled in the VMCR;
  3. pending and not active;
  4. lower priority value;
  5. `hw` set.
- Maintenance bits: set by `vgic_v3_configure_hcr()` or
  `vgic_v2_configure_hcr()` at the end of `vgic_flush_lr_state()`.
- `last_lr_irq` (per-CPU host data): the last interrupt put in an LR.
- `vgic_fold_state()`: returns at once when `last_lr_irq` is NULL.
- EOIcount: `__vgic_v3_save_state()` copies it into `vgic_hcr` only when
  `ICH_HCR_EL2_LRENPIE` was set.
- EOIcount fold: `vgic_v3_fold_lr_state()` walks the `ap_list` after
  `last_lr_irq` and deactivates one active interrupt per count.
- EOIcount fold of a `hw` interrupt: also deactivates the physical one with
  `vgic_v3_deactivate_phys()`.
- LPI: `vgic_v3_fold_lr()` always clears its active state; EOIcount is not
  bumped for an LPI outside the LRs.
- DIR write, EOImode 1: `access_gic_dir()` in `arch/arm64/kvm/sys_regs.c`
  calls `vgic_v3_deactivate()`; `vgic_mmio_write_dir()` calls it too, or
  `vgic_v2_deactivate()` on a GICv2 host.
- `vgic_v3_deactivate()` cases:

  | State of the interrupt | Action |
  |---|---|
  | on no `ap_list` | nothing |
  | `on_lr` set | `vgic_mmio_write_cactive()`, then `KVM_REQ_VGIC_PROCESS_UPDATE` |
  | on an `ap_list`, not in an LR | fold a pseudo-LR, then `KVM_REQ_VGIC_PROCESS_UPDATE` |

- DIR fast path: `___vgic_v3_write_dir()` in `arch/arm64/kvm/hyp/vgic-v3-sr.c`
  handles an interrupt found active in an LR without a full exit.
- GICv2 SGI with several sources: one source per LR; `vgic_v3_populate_lr()`
  sets `pending_latch` again while sources remain.
