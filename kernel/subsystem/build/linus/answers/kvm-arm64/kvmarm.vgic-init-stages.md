- Stage flags: `in_kernel`, `initialized`, `ready` in `struct vgic_dist`; there
  is no vgic_ready() macro.
- `dist->ready`: read only by `kvm_vgic_map_resources()`; no configuration
  path tests it.
- `kvm_vgic_create()` errors, in the order tested:

  | Error | Case |
  |---|---|
  | `-ENODEV` | GICv2 asked for, `can_emulate_gicv2` false |
  | `-EBUSY` | `kvm_trylock_all_vcpus()` failed |
  | `-EBUSY` | `created_vcpus` differs from `online_vcpus` |
  | `-EEXIST` | irqchip already in kernel |
  | `-EBUSY` | a vCPU has run |
  | `-E2BIG` | more online vCPUs than the model's maximum |

- Private interrupts: allocated by `kvm_vgic_create()` for existing vCPUs and
  by `kvm_vgic_vcpu_init()` for later ones; `vgic_init()` does not allocate
  them.
- `vgic_init()` on GICv5: calls `vgic_v5_init()` and allocates no SPIs.
- Explicit init: required for GICv3 and GICv5; `vgic_lazy_init()`,
  `vgic_v3_map_resources()` and `vgic_v5_map_resources()` return `-EBUSY`
  without it.
- GICv2 lazy init runs from:
  - `vgic_lazy_init()`, on the `KVM_IRQ_LINE` path in `arch/arm64/kvm/arm.c`
    and in `arch/arm64/kvm/vgic/vgic-irqfd.c`;
  - `vgic_v2_attr_regs_access()`;
  - `vgic_v2_map_resources()`, on the first run.
- Base addresses: refused with `-EEXIST` by `vgic_check_iorange()` when
  already set; there is no test of `initialized` or `ready`.
- Redistributor regions: checked by `vgic_v3_alloc_redist_region()`, also
  with no stage test.
- Refused once `initialized`:
  - new vCPU: `-EBUSY` from `kvm_arch_vcpu_precreate()`;
  - `KVM_DEV_ARM_VGIC_GRP_MAINT_IRQ`: `-EBUSY`;
  - a changed `GICD_TYPER2`: `-EBUSY` in `vgic_mmio_uaccess_write_v3_misc()`.
- `KVM_DEV_ARM_VGIC_GRP_NR_IRQS`: `-EBUSY` once `nr_spis` is non-zero, so a
  second write before init is refused too.
- `GICD_IIDR` revision write: no stage test.
- Refused before `initialized`, GICv3: register access returns `-EBUSY`,
  except what `reg_allowed_pre_init()` lets through.
- `kvm_vgic_inject_irq()` before `initialized`: returns 0 and injects nothing.
- `kvm_vgic_map_resources()` failure: calls `kvm_vm_dead()`; an unset address
  gives `-ENXIO`.
