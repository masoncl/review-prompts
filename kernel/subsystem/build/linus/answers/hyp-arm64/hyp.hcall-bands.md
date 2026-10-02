- Three bands, bounded by `hcall_min` and `hcall_max` in `handle_host_hcall()`:

| Band | Entries | Key clear | Key set |
|---|---|---|---|
| early | `__pkvm_init` up to the entry before `__KVM_HOST_SMCCC_FUNC_MIN_PKVM` | allowed | rejected |
| common | from `__KVM_HOST_SMCCC_FUNC_MIN_PKVM` up to the entry before `__KVM_HOST_SMCCC_FUNC_PKVM_ONLY` | allowed | allowed |
| pKVM-only | from `__KVM_HOST_SMCCC_FUNC_PKVM_ONLY` up to the entry before `__KVM_HOST_SMCCC_FUNC_MAX` | rejected | allowed |

- Key: the static key `kvm_protected_mode_initialized`, not
  `is_protected_kvm_enabled()`.
- Key clear: `hcall_max = __KVM_HOST_SMCCC_FUNC_PKVM_ONLY`; key set:
  `hcall_min = __KVM_HOST_SMCCC_FUNC_MIN_PKVM`.
- Non-protected nVHE: only `pkvm_drop_host_privileges()` in
  `arch/arm64/kvm/pkvm.c` enables the key, so the pKVM-only band is rejected for
  good.
- Marker names: there is no MAX_NO_PKVM marker; the three are
  `__KVM_HOST_SMCCC_FUNC_MIN_PKVM`, `__KVM_HOST_SMCCC_FUNC_PKVM_ONLY` and
  `__KVM_HOST_SMCCC_FUNC_MAX`.
- `MARKER()` in `arch/arm64/include/asm/kvm_asm.h`: a marker uses up no number;
  it has the value of the entry written after it.
- New entry: it joins the band of the marker it is written after; an entry
  written directly after a marker becomes that band's first value.
- Only exception: `__pkvm_prot_finalize`, listed under the comment "unavailable
  once pKVM has finalised" yet written after `__KVM_HOST_SMCCC_FUNC_MIN_PKVM`,
  so it stays callable.
- Reason, from the comment in `handle_host_hcall()`: the key must be enabled
  before finalisation, and finalisation runs per CPU.
- VM and vCPU lifecycle calls: all in the pKVM-only band, none placed against
  the rule.
