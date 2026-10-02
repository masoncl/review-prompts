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
