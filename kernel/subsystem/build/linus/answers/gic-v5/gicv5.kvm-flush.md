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
