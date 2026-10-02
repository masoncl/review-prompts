- `hyp_ffa_init()`: offers `FFA_VERSION_1_2` to EL3 and caps
  `hyp_ffa_version` at it.
- Higher or equal minor, not yet negotiated: not refused for its version; if
  `hyp_ffa_post_init()` succeeds the host gets `hyp_ffa_version` and
  negotiation is complete, otherwise it gets `FFA_RET_NOT_SUPPORTED`.
- Lower minor, not yet negotiated: `do_ffa_version()` forwards `FFA_VERSION`
  to EL3; only `FFA_RET_NOT_SUPPORTED` counts as refusal, and the value then
  stored is the host's request, not EL3's answer.
- `hyp_ffa_version`: lowered before `hyp_ffa_post_init()` runs and not
  restored when that fails; the flag stays clear and the host may call again.
- After negotiation: a lower minor gets `FFA_RET_NOT_SUPPORTED`; equal or
  higher gets `hyp_ffa_version`.
- `has_version_negotiated`: written only in `do_ffa_version()`; no other FF-A
  call sets it, they are refused by the gate in `kvm_host_ffa_handler()`.
- `has_version_negotiated` reads: plain read under `version_lock` in
  `do_ffa_version()`; the `smp_load_acquire()` is in
  `kvm_host_ffa_handler()`, with no lock.
- `do_ffa_version()` results: written straight into `a0` (version or
  `FFA_RET_NOT_SUPPORTED`), not through `ffa_to_smccc_error()`.
- `hyp_ffa_init()` returning 0 early (SMCCC older than 1.2, or EL3 answers
  `FFA_RET_NOT_SUPPORTED`): leaves `hyp_ffa_version` 0 and the flag clear;
  `kvm_host_ffa_handler()` has no "FF-A absent" test, so the gate still
  applies.
- **Potentially unsafe usage**: writing `hyp_ffa_version`.
  - Unsafe: once `has_version_negotiated` is set; `__do_ffa_mem_xfer()`,
    `do_ffa_mem_reclaim()` and `do_ffa_part_get()` read it without
    `version_lock`.
  - Safe: under `version_lock` while the flag is clear, before the
    `smp_store_release()`, as `do_ffa_version()` does.
  - Safe: in `hyp_ffa_init()`, while the flag is clear; it runs inside the
    `__pkvm_init` hypercall, before `init_subsystems()` installs EL2 on the
    other CPUs.
