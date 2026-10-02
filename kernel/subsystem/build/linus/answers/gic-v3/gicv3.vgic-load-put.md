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
