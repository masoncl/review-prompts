- `kvm_call_hyp_nvhe()` on a refused call: after the `WARN_ON()` it sets
  `res.a1 = -EOPNOTSUPP` and returns that, not what the hypervisor left in
  x1.
- `kvm_call_hyp()` on VHE: direct call followed by `isb()`.
  `kvm_call_hyp_ret()` on VHE: direct call with no `isb()`.
- Inside the nVHE object all three macros are plain calls `f(...)`; see the
  `__KVM_NVHE_HYPERVISOR__` branch in `arch/arm64/include/asm/kvm_host.h`.
- `enum __kvm_host_smccc_func` has three regions, split by `MARKER()`
  entries. A `MARKER()` takes no slot; it has the value of the next entry.

| Region | Ends before | Callable |
|---|---|---|
| early | `__KVM_HOST_SMCCC_FUNC_MIN_PKVM` | until pKVM is finalised |
| common, starts at `__pkvm_prot_finalize` | `__KVM_HOST_SMCCC_FUNC_PKVM_ONLY` | always |
| pKVM only | `__KVM_HOST_SMCCC_FUNC_MAX` | once pKVM is finalised |

- `host_hcall[]` uses designated initialisers, so the order of
  `HANDLE_FUNC()` lines does not matter; the enum position does.
- Missing `HANDLE_FUNC()`: for the last enum value the
  `BUILD_BUG_ON(ARRAY_SIZE(host_hcall) != __KVM_HOST_SMCCC_FUNC_MAX)` in
  `handle_host_hcall()` fails; anywhere else the slot is NULL and the call is
  refused at run time.
- `DECLARE_REG()` in `arch/arm64/kvm/hyp/include/nvhe/trap_handler.h`:
  declares `___check_reg_` plus the register number, so two `DECLARE_REG()`
  of one register in the same scope do not compile.
- Handler that never writes `cpu_reg(host_ctxt, 1)`: the host gets back the
  x1 it passed, so the caller must not use the value of
  `kvm_call_hyp_nvhe()`.
- vCPU pointer argument under pKVM: `__get_host_hyp_vcpus()` in
  `arch/arm64/kvm/hyp/nvhe/hyp-main.c` accepts it only if it equals
  `host_vcpu` of the loaded hyp vCPU, else yields NULL; for example
  `handle___kvm_vcpu_run()` uses it through `get_host_hyp_vcpus()`.
