- Names absent from this tree: struct kvm_pinned_page, struct kvm_vgic_dist,
  struct irq_phys_map, __kvm_call_hyp. The distributor is `struct vgic_dist`;
  `kvm_call_hyp_nvhe()` issues the HVC through `arm_smccc_1_1_hvc()`.
- pKVM scope: with `is_protected_kvm_enabled()`, EL2 owns the stage-2 of
  every guest, protected or not. `pkvm_init_host_vm()` reserves a handle for
  each VM, and the first run creates its `struct pkvm_hyp_vm`.
- `struct kvm_pgtable` on the host under pKVM: not a page table. The
  page-table fields are in a union with `pkvm_mappings`, an interval tree of
  `struct pkvm_mapping` that records what the host asked EL2 to map.
- `struct kvm_s2_mmu`: `pgt` is a pointer. The host allocates it in
  `kvm_init_stage2_mmu()`; at EL2 it points at the `pgt` embedded in
  `struct pkvm_hyp_vm`.
- `struct kvm_vmid`: `kvm_arm_vmid_update()` runs from
  `kvm_arch_vcpu_load()`, not on each guest entry. Under pKVM the load skips
  it, and EL2 sets the VMID from the handle in `init_pkvm_hyp_vm()`.
- Shadow lookup key: `tlb_vttbr` and `tlb_vtcr` hold the guest hypervisor's
  own register values. The hardware VTTBR comes from `kvm_get_vttbr()`.
- `vcpu->arch.hw_mmu` after `kvm_vcpu_put_hw_mmu()`: NULL, unless the vCPU
  was scheduled out outside WFI emulation and so kept its reference.
- Stage-2 fault targets in `kvm_handle_guest_abort()`: `io_mem_abort()` only
  when there is no memslot or the fault is a write to a read-only slot,
  `handle_access_fault()` for an access flag fault; then `pkvm_mem_abort()`
  for a protected VM, `gmem_abort()` for a guest_memfd slot,
  `user_mem_abort()` otherwise.
- `struct kvm_s2_fault_desc`: the argument of the three memory-abort
  handlers; it carries the vCPU, the memslot and the nested translation.
- `struct vgic_irq` refcount: used for LPIs only. `vgic_put_irq()` does
  nothing for a non-LPI, and `vgic_try_get_irq_ref()` takes no count for an
  INTID below `VGIC_MIN_LPI`.
- `struct vgic_irq` list membership: on an `ap_list` only while `irq->vcpu`
  is set. `irq->vcpu` is the list owner and can differ from `target_vcpu`;
  see `vgic_target_oracle()`.
- `struct irq_ops`: per-interrupt overrides hung off `irq->ops`, set with
  `kvm_vgic_set_irq_ops()`. The timer uses it; the host mapping itself is in
  the `hw`, `host_irq` and `hwintid` fields.
- GICv5 guests: PPIs only. `vgic_get_irq()` returns NULL for a v5 VM, and
  v5 INTIDs carry a type field (`vgic_v5_make_ppi()`).
- GICv5 PPIs: never queued on an `ap_list`;
  `vgic_v5_ppi_queue_irq_unlock()` only kicks the vCPU. Register state is in
  `struct vgic_v5_cpu_if`, the VM-wide PPI masks in `struct vgic_v5_vm`.
- GICv5 exclusions: `vgic_v5_probe()` does not register the device under
  pKVM, and `vgic_v5_init()` returns `-EINVAL` if a vCPU has NV.
- `struct arch_timer_context`: has no vCPU pointer and no cached CTL or
  CVAL. `timer_context_to_vcpu()` derives the vCPU from `timer_id`, and the
  values are vCPU system registers read with `__vcpu_sys_reg()`.
