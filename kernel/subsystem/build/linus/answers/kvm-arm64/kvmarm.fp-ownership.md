- Ownership: `fp_owner` in the per-CPU `struct kvm_host_data`, read through
  `host_data_ptr(fp_owner)`; nothing in `struct kvm_vcpu_arch` tracks it.
- There is no fpsimd_kvm_prepare() here; `kvm_arch_vcpu_load_fp()` calls
  `fpsimd_save_and_flush_cpu_state()` and then sets `FP_STATE_FREE`, unless
  it returned early (no FP/SIMD on the system, or a nested transition).

| State | Set by |
|---|---|
| `FP_STATE_FREE` | `kvm_arch_vcpu_load_fp()`, `kvm_arch_vcpu_ctxflush_fp()` |
| `FP_STATE_GUEST_OWNED` | `kvm_hyp_handle_fpsimd()` |
| `FP_STATE_HOST_OWNED` | pKVM hyp only: `fpsimd_sve_flush()` and `fpsimd_sve_sync()` in `arch/arm64/kvm/hyp/nvhe/hyp-main.c` |

- pKVM hyp vCPU: `fpsimd_sve_sync()` saves the guest state and restores the
  host's after a run in which the guest took the registers, so the host
  never sees `FP_STATE_GUEST_OWNED` and `kvm_arch_vcpu_ctxsync_fp()` and
  `kvm_arch_vcpu_put_fp()` bind and save nothing.
