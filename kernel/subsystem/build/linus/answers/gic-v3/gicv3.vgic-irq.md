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
