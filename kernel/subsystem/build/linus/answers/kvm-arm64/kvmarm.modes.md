- `kvm-arm.mode=protected`: `aliases[]` in
  `arch/arm64/kernel/pi/idreg-override.c`, which spells it
  `kvm_arm.mode=protected`, maps it to `arm64_sw.hvhe=1`, not
  to `id_aa64mmfr1.vh=0`. On a VHE-capable CPU booted at EL2 pKVM therefore
  runs as hVHE; `__finalise_el2` in `arch/arm64/kernel/hyp-stub.S` keeps the
  kernel at EL1 when the hVHE override is set.
- `kvm-arm.mode=nvhe` (`kvm_arm.mode=nvhe` in `aliases[]`): maps to
  `arm64_sw.hvhe=0 id_aa64mmfr1.vh=0`, so it also turns hVHE off.
- `hvhe_filter()`: accepts the override only for value 1, boot at EL2 and a
  non-zero VH field in `id_aa64mmfr1_el1`. `hvhe_possible()`, the `.matches`
  test of `ARM64_KVM_HVHE`, then reads the override. There is no
  kvm_arm.hvhe alias.
- `kvm_mode`: the static in `arch/arm64/kvm/arm.c`; written only by
  `early_kvm_mode_cfg()`, and nothing changes it afterwards.
- `early_kvm_mode_cfg()` at the wrong exception level, with
  `is_hyp_mode_available()` true: `protected` with the kernel at EL2 does
  `pr_warn_once()`, returns 0 and leaves `kvm_mode` unchanged; `nvhe` at EL2
  and `nested` at EL1 hit `WARN_ON()` and return `-EINVAL`.
- `is_protected_kvm_enabled()`: true whenever `kvm_get_mode()` was
  `KVM_MODE_PROTECTED` at cap finalisation (`is_kvm_protected_mode()` in
  `arch/arm64/kernel/cpufeature.c`). It does not say KVM initialised;
  `is_pkvm_initialized()` says the host has been deprivileged.
- Predicates inside the hypervisor objects (`arch/arm64/include/asm/virt.h`):

| Predicate | VHE object | nVHE object | Host code |
|---|---|---|---|
| `has_vhe()` | constant true | constant false | final cap |
| `has_hvhe()` | constant false | final cap | final cap |
| `is_protected_kvm_enabled()` | constant false | final cap | final cap |
| `is_kernel_in_hyp_mode()` | `BUILD_BUG_ON()` | `BUILD_BUG_ON()` | reads `CurrentEL` |

- `is_hyp_nvhe()`: calls `is_kernel_in_hyp_mode()`, so host code only.
- **Potentially unsafe usage**: testing `has_vhe()`, `has_hvhe()` or
  `is_protected_kvm_enabled()` in host code.
  - Unsafe: before system capabilities are finalised; `cpus_have_final_cap()`
    in `arch/arm64/include/asm/cpufeature.h` does `BUG()`.
  - Safe: once `system_capabilities_finalized()` is true, as `kvm_arm_init()`
    and `finalize_pkvm()` do from initcalls.
  - Safe: early code tests `is_kernel_in_hyp_mode()` or `kvm_get_mode()`
    instead, as `early_kvm_mode_cfg()`, `CHOOSE_HYP_SYM()` in
    `arch/arm64/include/asm/kvm_asm.h` and `is_kvm_protected_mode()` do.
- Register layout at EL2: test `has_vhe() || has_hvhe()`, as
  `__activate_cptr_traps()` in `arch/arm64/kvm/hyp/include/hyp/switch.h`
  does; `!has_vhe()` alone picks the wrong layout under hVHE.
