- x0 timing: `handle_host_hcall()` writes `SMCCC_RET_SUCCESS` before it calls
  the handler, not after.
- Why before: `handle___pkvm_init()` does not return on success;
  `__pkvm_init_finalise()` in `arch/arm64/kvm/hyp/nvhe/setup.c` writes x1 and
  calls `__host_enter()` itself, so x0 must already hold the status.
- Handler that writes no result: x1 is not zeroed, the host gets back the x1
  it passed (its first argument); `kvm_call_hyp()` discards it.
