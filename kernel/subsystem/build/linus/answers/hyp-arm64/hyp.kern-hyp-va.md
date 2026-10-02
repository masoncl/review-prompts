- `__kern_hyp_va()`: five instructions, `and`, `ror`, `add`, `add ... lsl 12`,
  `ror`. `kvm_update_va_mask()` has `BUG_ON(nr_inst != 5)`.
- Assembly: there is no kern_hyp_va assembler macro here. The `__ASSEMBLER__`
  part of `arch/arm64/include/asm/kvm_mmu.h` has only `hyp_pa` and
  `hyp_kimg_va`.
- Region bit of the tag: bit `hyp_va_bits - 1`, the complement of that bit in
  `__pa_symbol(__hyp_idmap_text_start)`. `hyp_va_bits` is `kvm_hyp_va_bits()`,
  `max(IDMAP_VA_BITS, vabits_actual)`, not `vabits_actual`.
- Random tag bits: only with `CONFIG_RANDOMIZE_BASE` and
  `tag_lsb != hyp_va_bits - 1`; they fill
  `GENMASK_ULL(hyp_va_bits - 2, tag_lsb)`.
- Call site: `hyp_mode_check()` in `arch/arm64/kernel/smp.c` calls
  `kvm_compute_layout()`, then `kvm_apply_hyp_relocations()`.
- Condition: both run only if `IS_ENABLED(CONFIG_KVM)` and
  `!is_kernel_in_hyp_mode()`. Under VHE neither runs, and `va_mask`,
  `tag_val` stay zero.
- Order: `smp_cpus_done()` calls `hyp_mode_check()` before
  `setup_system_features()`, which reaches `apply_alternatives_all()`.
- Zero tag: when `tag_val` is 0, `kvm_update_va_mask()` keeps the `and` and
  writes NOPs over the other four instructions.
- VHE hyp objects: the asm is inside `#ifndef __KVM_VHE_HYPERVISOR__`, so
  `__kern_hyp_va()` compiles to nothing there. Elsewhere under VHE the five
  instructions are patched to NOPs.
- `__early_kern_hyp_va()` in `arch/arm64/kvm/va_layout.c`: the same
  computation in C. `init_hyp_physvirt_offset()`,
  `kvm_apply_hyp_relocations()` and `kvm_patch_vector_branch()` use it.
- `compute_instruction()` and `__early_kern_hyp_va()` must give the same
  result; `hyp_physvirt_offset` is derived from the C form.
