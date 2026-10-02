- Names absent from this tree: sr_forward_xarray, forward_traps,
  kvm_check_forward_trap, check_cgt, BEHAVE_FORWARD_ANY. The tree has
  `sr_forward_xa`, `__forward_traps()`, `compute_trap_behaviour()` and
  `BEHAVE_FORWARD_RW`.
- `struct trap_bits`: holds `index`, `behaviour`, `value`, `mask` only.
  Complex conditions are callbacks in `ccc[]`.
- `union trap_config`: `sri` is the index into `sys_reg_descs[]` or
  `sys_insn_descs[]` plus one; `fgf` is the fine-grained filter. `line` is
  a field of `struct encoding_to_trap_config`.
- `encoding_to_cgt[]`, `encoding_to_fgt[]`, `non_0x18_fgt[]`: `__initconst`;
  after init only `sr_forward_xa` holds the encoding data.
- `kvm_sys_reg_table_init()`: called from `kvm_arm_init()` on every host;
  an error return makes KVM fail to initialise.
- Init checks by outcome:

| Check | Where | Outcome |
|---|---|---|
| MBZ bit, duplicate CGT, invalid or duplicate FGT | `populate_nv_trap_config()` | `-EINVAL` |
| FGT bit is generated RES0/RES1 in the read register and, if the group has one, in the write register | `aggregate_fgt()` | `-EINVAL` |
| FGT bit has both polarities | `check_fgt_masks()` | `-EINVAL` |
| recursive combination | `populate_nv_trap_config()` | `-EINVAL` |
| descriptor index too large or duplicate | `populate_sysreg_config()` | `-EINVAL` |
| masks do not cover all 64 bits | `check_fgt_masks()` | `kvm_info()`, `res0` recomputed |
| feature map does not cover the register | `check_feature_map()` | `kvm_err()` only |

- `populate_nv_trap_config()`: stores `encoding_to_fgt[]` entries in the
  xarray only when the host has `ARM64_HAS_FGT`; `aggregate_fgt()` runs
  either way.
- `check_fgt_bit()`: does not test the VM's FEAT_FGT or any enable bit in
  `HCR_EL2` or `HCRX_EL2`. It reads the guest register through
  `__vcpu_sys_reg()`, and for negative polarity also requires the bit not
  to be RES0.
- `HCRX_FGTnXS`: the only filter; it drops the FGT check when the guest
  set `HCRX_EL2_FGTnXS`.
- Missing entry, by kind:

| What is missing | Result |
|---|---|
| encoding not in `sr_forward_xa` at all | UNDEF, or FEAT_IDST handling in the feature ID space; message unless IMPDEF range |
| descriptor exists, no CGT or FGT entry | KVM handles it; the guest hypervisor's trap is ignored, no warning |
| CGT or FGT entry, no descriptor (`tc.sri == 0`) | forwarded if the guest traps it, else as in the first row |
| FGT register bit in neither `encoding_to_fgt[]` nor `non_0x18_fgt[]` | `check_fgt_masks()` makes it RES0; `get_reg_fixed_bits()` then makes it RES0 in the guest's register |

- Traps with an EC other than `ESR_ELx_EC_SYS64` do not use the tables, for
  example:
  - `forward_smc_trap()` and `forward_debug_exception()` in
    `arch/arm64/kvm/emulate-nested.c`: forward when `is_nested_ctxt()` and
    the bit is set in `HCR_EL2` or `MDCR_EL2`.
  - `handle_hvc()`: for any NV vCPU, in either context, forwards, or
    injects UNDEF if `HCR_HCD` is set.
  - `handle_svc()`: forwards unconditionally.
  - `kvm_handle_eret()`: forwards whenever `is_hyp_ctxt()` is false, except
    an ERETAx on a vCPU without ptrauth, which goes to
    `kvm_handle_ptrauth()` and gets UNDEF.
  - FP, SVE and WFx: helpers in `arch/arm64/include/asm/kvm_emulate.h`.
