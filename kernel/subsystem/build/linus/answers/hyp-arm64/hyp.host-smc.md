- Refused before any handler runs, in `handle_host_smc()`:
  - a non-zero SMC immediate (`esr & ESR_ELx_xVC_IMM_MASK`);
  - a function id with any of the upper 32 bits set after
    `ARM_SMCCC_CALL_HINTS` is cleared.
- Refused call: x0 becomes `SMCCC_RET_NOT_SUPPORTED`, nothing reaches EL3, and
  `kvm_skip_host_instr()` still runs.
- Why the upper bits are tested: `kvm_host_psci_handler()` and
  `kvm_host_ffa_handler()` take the id as `u32`.
- Hypervisor-reserved range: `handle_host_smc()` has no check for one.
- Hints: cleared in a local copy only; a call forwarded by
  `default_host_smc_handler()` or `psci_forward()` carries the host's
  original x0.
- `kvm_host_psci_handler()`: from PSCI 0.2 on it claims all 32 function numbers
  of both bases (`is_psci_0_2_call()`); an id it does not know gets
  `PSCI_RET_NOT_SUPPORTED` and is not forwarded.
- PSCI SYSTEM_OFF and SYSTEM_RESET: forwarded unchanged by `psci_forward()`;
  only CPU_ON, CPU_SUSPEND and SYSTEM_SUSPEND get a hyp entry point.
- `kvm_host_ffa_handler()`: until a version is negotiated, every FF-A call
  except `FFA_VERSION` gets `FFA_RET_INVALID_PARAMETERS`.
- Unclaimed call: `default_host_smc_handler()` forwards it whatever its owner
  field; no filter limits it to standard ids.
- Reason for forwarding: stated in the comment in `kvm_host_ffa_handler()` in
  `arch/arm64/kvm/hyp/nvhe/ffa.c`; devices rely on custom firmware calls and
  EL3 has to be trusted anyway.
