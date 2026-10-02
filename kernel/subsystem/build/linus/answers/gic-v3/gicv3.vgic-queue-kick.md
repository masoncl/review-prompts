- Kick of all vCPUs: `kvm_make_all_cpus_request(kvm, KVM_REQ_IRQ_PENDING)`
  when `bcast` is true; otherwise only the vCPU the interrupt was queued on.
- `bcast` needs all three, tested in this order with `&&`:
  - `vgic_model_needs_bcst_kick()`: host has `ARM64_HAS_ICH_HCR_EL2_TDIR` and
    the guest model is `KVM_DEV_TYPE_ARM_VGIC_V3`;
  - `vgic_valid_spi()` for the INTID;
  - `atomic_fetch_inc(&kvm->arch.vgic.active_spis)` returned 0.
- `active_spis`: incremented only when the first two hold, so it stays 0 for
  a GICv2 guest model and on hosts without the capability.
- `bcast` is computed under both locks; the kick is made after both are
  dropped.
- Purpose of the broadcast: each vCPU re-runs `vgic_v3_configure_hcr()`, which
  sets `ICH_HCR_EL2_TDIR` when `active_spis` is non-zero.
- Not-queued return (`irq->vcpu` set, oracle non-NULL): the oracle's vCPU
  alone is kicked; never a broadcast.
