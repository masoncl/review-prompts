- `kern_hyp_va()`: arithmetic only; it does not check that the result is mapped
  at EL2 or belongs to the host.
- EL2 mapping of host memory: created by `hyp_pin_shared_mem()` on the first pin
  and by `__pkvm_host_donate_hyp()`, both in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c`.
- `hyp_pin_shared_mem()`: fails unless the host has shared every page in the
  range; this is the check that rejects a bad pointer.
- Pinned page: stays host-writable; besides the mapping, the pin only makes
  `__pkvm_host_unshare_hyp()` fail while it is held.
- Donated page: owned by hyp, so repeated reads are stable until
  `__pkvm_hyp_donate_host()`.
- `DECLARE_REG()`: also declares an unused `int` named `___check_reg_` plus
  the register number, so two declarations of one register in a scope fail to
  build.
