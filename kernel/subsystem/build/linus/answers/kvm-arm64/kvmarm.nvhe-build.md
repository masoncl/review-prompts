- Section renaming is done only by `hyp.lds.S` through `HYP_SECTION()` and
  `BEGIN_HYP_SECTION()`; `objcopy` only prefixes symbols and `gen-hyprel`
  renames nothing.
- Sections the script renames: `.idmap.text`, `.text`,
  `.data..ro_after_init`, `.rodata`, `.data..percpu`, `.bss`, `.data`.
  Writable initialised data is therefore allowed.
- Under `CONFIG_NVHE_EL2_TRACING` the script also builds `.hyp.event_ids`,
  from inputs that `define_events.h` already names `.hyp.event_ids.*`.
- Other input sections, for example `__kvm_ex_table`, are not named in
  `hyp.lds.S`; `arch/arm64/kernel/vmlinux.lds.S` places `__kvm_ex_table`
  inside the hyp text range.
- No step in `nvhe/Makefile` checks for stray sections or undefined symbols.
  A reference to an unaliased kernel symbol fails only at the `vmlinux` link,
  as an undefined `__kvm_nvhe_` symbol.
- `gen-hyprel` fails the build on an unexpected RELA type in a `.hyp`
  section and on any `SHT_REL` section.
- `gen-hyprel` picks relocations by the section that holds them, not by
  target: every `R_AARCH64_ABS64` in a `.hyp` section is converted by
  `kvm_apply_hyp_relocations()`, including a pointer to an aliased kernel
  symbol.
- kCFI is not removed: only `CC_FLAGS_FTRACE`, `CC_FLAGS_SCS` and the
  profile-use flags are filtered, and `gen-hyprel` accepts
  `R_AARCH64_ABS32` for the type hashes.
- UBSAN: on in trap mode when `CONFIG_UBSAN_KVM_EL2` is set
  (`UBSAN_SANITIZE := y`, `CFLAGS_UBSAN_TRAP`).
- Other sanitizers: the Makefile has no per-sanitizer disable lines. The
  `.nvhe.o` files are not in `obj-y`, so `is-kernel-object` in
  `scripts/Makefile.lib` is empty and the flags are not added.
- `-fno-stack-protector` and `-DDISABLE_BRANCH_PROFILING`: set in
  `nvhe/Makefile` itself.
- `memcpy()`, `memset()`, `clear_page()`, `copy_page()`: compiled into the
  object from `arch/arm64/lib/` and bound with `KVM_NVHE_ALIAS_HYP()` to the
  hyp copy of the `__pi_` symbol. `KVM_NVHE_ALIAS()` is for kernel symbols.
- Hyp globals that mirror host values are separate variables; the host
  assigns each one through `kvm_nvhe_sym()`, most of them in
  `kvm_hyp_init_symbols()` in `arch/arm64/kvm/arm.c`. A new one needs such an
  assignment.
- `is_kernel_in_hyp_mode()`: does not compile in hyp code
  (`BUILD_BUG_ON()`). `CHOOSE_VHE_SYM()` expands to
  `__nvhe_undefined_symbol`, so it fails at link.
- **Potentially unsafe usage**: dereferencing `vcpu->kvm` or
  `vcpu->arch.hw_mmu` in nVHE code without `kern_hyp_va()`.
  - Unsafe: when the vCPU can be the host's `struct kvm_vcpu`, which holds
    kernel addresses; that is every guest when pKVM is off.
  - Safe: after `is_protected_kvm_enabled()` has tested true, as in
    `vcpu_is_protected()`; `handle___kvm_vcpu_run()` then passes only the
    hyp copy, whose `kvm` pointer `nvhe/pkvm.c` set to `&hyp_vm->kvm`.
  - Safe: `kern_hyp_va(vcpu->kvm)` in code shared with VHE; `__kern_hyp_va()`
    in `arch/arm64/include/asm/kvm_mmu.h` is empty in the VHE object.
  - Safe: behind a `vcpu_has_nv()` test, which is constant false in the nVHE
    object, as in `__activate_cptr_traps_vhe()`.
