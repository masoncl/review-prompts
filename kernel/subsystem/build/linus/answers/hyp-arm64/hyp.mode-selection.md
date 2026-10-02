- Aliases for `kvm-arm.mode`: in `aliases[]` in
  `arch/arm64/kernel/pi/idreg-override.c`; there is no
  arch/arm64/kernel/idreg-override.c.
- `kvm_arm.mode=protected` alias: expands to `arm64_sw.hvhe=1`.
- hVHE: `early_kvm_mode_cfg()` has no value for it; `arm64_sw.hvhe=1` selects
  it, given directly or through the `protected` alias.
- `hvhe_filter()`: accepts `arm64_sw.hvhe=1` only when the CPU booted at EL2 and
  has VHE.
- `__finalise_el2` in `arch/arm64/kernel/hyp-stub.S`: with the hvhe override
  set it refuses the upgrade to VHE, so the kernel stays at EL1 and
  `early_kvm_mode_cfg()` then accepts `protected` on a VHE-capable CPU.
- `is_kvm_protected_mode()` in `arch/arm64/kernel/cpufeature.c`: tests only
  `kvm_get_mode() == KVM_MODE_PROTECTED`; the exception-level test that the
  cap relies on is in `early_kvm_mode_cfg()`.
- Requests `early_kvm_mode_cfg()` refuses, in the order it tests them; every
  refusal leaves `kvm_mode` unchanged, none resets it to `KVM_MODE_DEFAULT`:

| Request | Condition | Result |
|---|---|---|
| NULL | always | `-EINVAL` |
| any but `none` | `!is_hyp_mode_available()` | `pr_warn_once()`, returns 0 |
| `protected` | `is_kernel_in_hyp_mode()` | `pr_warn_once()`, returns 0 |
| `nvhe` | `is_kernel_in_hyp_mode()` | `WARN_ON()`, `-EINVAL` |
| `nested` | `!is_kernel_in_hyp_mode()` | `WARN_ON()`, `-EINVAL` |
| unknown | none of the rows above matched | `-EINVAL` |

- `protected`: after `is_hyp_mode_available()`, `is_kernel_in_hyp_mode()` is
  its only test; there is no CPU feature test, no override test and no
  configuration test.
