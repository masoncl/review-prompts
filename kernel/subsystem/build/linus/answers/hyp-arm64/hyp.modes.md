- `enum kvm_mode` in `arch/arm64/include/asm/kvm_host.h`: four values,
  `KVM_MODE_DEFAULT`, `KVM_MODE_PROTECTED`, `KVM_MODE_NV`, `KVM_MODE_NONE`.
- VHE, nVHE and hVHE: not values of `enum kvm_mode`; `has_vhe()` and
  `has_hvhe()` tell them apart.
- `has_vhe()` in hyp objects: a compile-time constant, true in VHE hyp code and
  false in nVHE hyp code; it reads the cap only in kernel-proper code.
- `has_vhe()` false in nVHE hyp code although that code runs at EL2:
  `has_vhe()` tells whether the kernel runs at EL2, not whether the calling
  code does.
- Hyp code that needs to know it is at EL2: `is_hyp_code()`,
  `is_nvhe_hyp_code()`, `is_vhe_hyp_code()` in
  `arch/arm64/include/asm/cpufeature.h`, all compile-time.
- `is_kernel_in_hyp_mode()`: kernel-proper only; it has a `BUILD_BUG_ON()` that
  fails the build in a hyp object.
- `is_protected_kvm_enabled()` and `has_hvhe()` in VHE hyp code: constant
  false.
- All three predicates outside hyp objects: go through `cpus_have_final_cap()`,
  which calls `BUG()` before `setup_system_features()` has run; earlier code
  uses `kvm_get_mode()` and `is_kernel_in_hyp_mode()`.
