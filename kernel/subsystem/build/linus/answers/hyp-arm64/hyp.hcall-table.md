- Table guard: `BUILD_BUG_ON(ARRAY_SIZE(host_hcall) !=
  __KVM_HOST_SMCCC_FUNC_MAX)`, first statement of `handle_host_hcall()` in
  `arch/arm64/kvm/hyp/nvhe/hyp-main.c`.
- What the guard catches: a missing `HANDLE_FUNC()` line for the last entry
  before `__KVM_HOST_SMCCC_FUNC_MAX`, because the array is then too short.
- What the guard misses: a missing `HANDLE_FUNC()` line for any earlier entry.
  The slot is NULL, the array size is unchanged, the build passes, and the call
  fails at run time with `SMCCC_RET_NOT_SUPPORTED`.
- `HANDLE_FUNC(x)`: stores `handle_##x`; there is no kvm_host_hcall_ prefix.
- `array_index_nospec()`: not called by `handle_host_hcall()`; the index is used
  straight after the range test.
- Range test: `id < hcall_min || id >= hcall_max`; both bounds depend on the
  phase, see "Hypercall availability by phase".
- Invalid id: the `inval:` path writes `cpu_reg(host_ctxt, 0)` only; x1-x3 are
  not zeroed.
- Host side of an invalid id: `kvm_call_hyp_nvhe()` in
  `arch/arm64/include/asm/kvm_host.h` warns and yields `-EOPNOTSUPP` in place of
  `res.a1`.
- Stub hypercalls: `__host_hvc` in `arch/arm64/kvm/hyp/nvhe/host.S` diverts
  x0 below `HVC_STUB_HCALL_NR` to `__kvm_handle_stub_hvc` only without
  `ARM64_KVM_PROTECTED_MODE`.
- Stub ids in protected mode, once `__kvm_hyp_host_vector` is installed: every
  host HVC reaches `handle_host_hcall()`, and a stub id gets
  `SMCCC_RET_NOT_SUPPORTED`.
