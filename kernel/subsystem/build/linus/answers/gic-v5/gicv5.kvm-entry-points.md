| Job | GICv5 function | Called from |
|---|---|---|
| Create the device | none of its own: `kvm_arm_vgic_v5_ops` uses the shared `vgic_create()`, which calls `kvm_vgic_create()` in `arch/arm64/kvm/vgic/vgic-init.c`; there is no vgic_v5_create | `.create` of `struct kvm_device_ops`, called by `kvm_ioctl_create_device()` in `virt/kvm/kvm_main.c` |
| Create: per-vCPU PPIs | `vgic_v5_setup_private_irq()`, static in `arch/arm64/kvm/vgic/vgic-init.c` | `vgic_allocate_private_irqs_locked()` |
| Initialise | `vgic_v5_init()` | `vgic_init()`, reached by `KVM_DEV_ARM_VGIC_CTRL_INIT` in `vgic_v5_set_attr()`; on a vgic that is not initialised `vgic_lazy_init()` returns `-EBUSY` for any model but `KVM_DEV_TYPE_ARM_VGIC_V2` |
| Initialise: first run | `vgic_v5_map_resources()`; `vgic_v5_finalize_ppi_state()` | `kvm_vgic_map_resources()`; `kvm_arch_vcpu_run_pid_change()` in `arch/arm64/kvm/arm.c` |
| Reset a vCPU | `vgic_v5_reset()` | static `kvm_vgic_vcpu_reset()`, whose one caller is `vgic_init()`; not `kvm_vgic_vcpu_init()` |
| Load and put a vCPU | `vgic_v5_load()`, `vgic_v5_put()` | `kvm_vgic_load()`, `kvm_vgic_put()` in `arch/arm64/kvm/vgic/vgic.c`, by `vgic_model` |
| Load and put: at hyp | `__vgic_v5_restore_vmcr_apr()`, `__vgic_v5_save_apr()` | `kvm_call_hyp()` in `vgic_v5_load()` and `vgic_v5_put()` |
| Flush state before entry | `vgic_v5_flush_ppi_state()`, then `vgic_v5_restore_state()` | `kvm_vgic_flush_hwstate()`, through static `vgic_flush_state()` and `vgic_restore_state()`; the second only if `can_access_vgic_from_kernel()` |
| Save and fold after exit | `vgic_v5_save_state()`, then `vgic_v5_fold_ppi_state()` | `kvm_vgic_sync_hwstate()`, through static `vgic_save_state()` and `vgic_fold_state()`; the first only if `can_access_vgic_from_kernel()` |
| Restore and save: nVHE | `__vgic_v5_restore_state()` with `__vgic_v5_restore_ppi_state()`; `__vgic_v5_save_state()` with `__vgic_v5_save_ppi_state()` | `__hyp_vgic_restore_state()`, `__hyp_vgic_save_state()` in `arch/arm64/kvm/hyp/nvhe/switch.c` |
| Check for a pending interrupt | `vgic_v5_has_pending_ppi()` | `kvm_vgic_vcpu_pending_irq()`, as its first test |
