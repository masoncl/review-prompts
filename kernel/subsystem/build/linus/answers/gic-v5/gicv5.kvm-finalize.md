- Caller: `kvm_arch_vcpu_run_pid_change()` in `arch/arm64/kvm/arm.c`, on each
  vCPU's first run, after `kvm_timer_enable()` and
  `kvm_arm_pmu_v3_enable()`; not from `kvm_vgic_map_resources()`.
- Lock: the function takes `kvm->arch.config_lock` itself; the caller must
  not hold it.
- Done-once guard: the `GICV5_ARCH_PPI_SW_PPI` bit of `vgic_ppi_mask`, tested
  under the lock; there is no separate flag.
- Exposed set: each PPI in `impl_ppi_mask` whose `struct vgic_irq` on vCPU 0
  has `owner` set, plus `GICV5_ARCH_PPI_SW_PPI`.
- `config`: only read, to fill `vgic_ppi_hmr`; not written.
- Timer `owner`: set per vCPU by `timer_irqs_are_valid()`, on that vCPU's own
  first run.
- PMU `owner`: set by `kvm_arm_pmu_v3_init()`, at
  `KVM_ARM_VCPU_PMU_V3_INIT`.
- Readers of `vgic_ppi_mask` (`for_each_visible_v5_ppi()` users) take no
  lock; each vCPU passes through the function, and so through the lock,
  before it first enters the guest.
- **Potentially unsafe usage**: deriving VM-wide state from one vCPU's
  `struct vgic_irq` fields on the first-run path.
  - Unsafe: when the field is set on each vCPU's own first run and the vCPU
    read is not the one running; the mask is computed once and a PPI whose
    field is set later stays hidden.
  - Safe: a field set for every vCPU before any run, such as `config`, which
    `vgic_v5_setup_private_irq()` sets at allocation.
- **Unsafe usage**: writing `vgic_ppi_mask` after the guard bit is set;
  vCPUs that have passed the guard walk it with no lock.
  - Safe: write only before the guard bit, under `config_lock`, as
    `vgic_v5_finalize_ppi_state()` does.
