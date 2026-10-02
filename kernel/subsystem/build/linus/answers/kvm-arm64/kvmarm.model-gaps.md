- Models take GICv5 support to be absent, or limited to GICv3 guests on a
  GICv5 host. `vgic_is_v5()`, a macro in `include/kvm/arm_vgic.h`, is tested
  outside the vgic too, for example in `arch/arm64/kvm/arch_timer.c` and in
  `__hyp_vgic_restore_state()` in `arch/arm64/kvm/hyp/nvhe/switch.c`.
- Models take `vcpu_el2_e2h_is_set()` to read only the guest's `HCR_EL2`. It
  is always true without `ARM64_HAS_HCR_NV1`; see
  `arch/arm64/include/asm/kvm_emulate.h`.
- Models take an injected external abort to be always pended as a synchronous
  exception. `inject_abt64()` in `arch/arm64/kvm/inject_fault.c` calls
  `pend_serror_exception()` instead of `pend_sync_exception()` when
  `effective_sctlr2_ease()` is true.
- Models take GICv4 direct injection to be used whenever the host has it, and
  GICv2 emulation to be offered whenever the hardware allows. `vgic_v3_probe()`
  sets `has_gicv4` from `kvm-arm.vgic_v4_enable`, which defaults to off. It
  does not register the GICv2 device when the mode is `KVM_MODE_PROTECTED`.
- Models take the host never to take back a guest page by force.
  `is_spurious_el1_translation_fault()` in `arch/arm64/mm/fault.c` calls
  `pkvm_force_reclaim_guest_page()`.
- Models take a CFI failure at EL2 to go unreported. The host reports it in
  `kvm_nvhe_report_cfi_failure()` in `arch/arm64/kvm/handle_exit.c`, called
  from `nvhe_hyp_panic_handler()` under `CONFIG_CFI`.
- Models take the nVHE hypervisor to have no tracing. The host side is
  `arch/arm64/kvm/hyp_trace.c`, built under `CONFIG_NVHE_EL2_TRACING`.
  `__tracing_load` and the other tracing hypercalls sit in the range that is
  always available.
- Models take guest debug state to be chosen through a debug pointer in the
  vCPU. `kvm_vcpu_load_debug()` sets `vcpu->arch.debug_owner` at load, and
  pKVM copies debug state by that owner in `flush_debug_state()` and
  `sync_debug_state()`.
- Models take `KVM_ARM_VCPU_PMU_V3` to be the only PMU feature bit.
  `KVM_ARM_VCPU_PMU_V3_STRICT` is bit 9 and `KVM_VCPU_MAX_FEATURES` is 10.
  With it set, `kvm_setup_vcpu()` creates no default PMU.
- Models take host exit handling to cover only aborts from lower exception
  levels. `arm_exit_handlers[]` routes `ESR_ELx_EC_DABT_CUR` to
  `kvm_handle_vncr_abort()`, for faults on a guest hypervisor's VNCR page.
