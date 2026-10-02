- Section prefix: added by the partial link `ld -r -T hyp.lds` that makes
  `kvm_nvhe.tmp.o`; `cmd_hypcopy` only passes `--prefix-symbols=__kvm_nvhe_`.
- `arch/arm64/kvm/hyp/nvhe/hyp.lds.S`: prefixes only the input sections it
  lists; any other section, for example `__kvm_ex_table`, keeps its name.
- Section not listed in `hyp.lds.S`: `emit_rela_section()` in
  `arch/arm64/kvm/hyp/nvhe/gen-hyprel.c` skips it, so its pointers get no
  EL2 fix-up.
- `__ro_after_init` data in nVHE code: `HYPERVISOR_RODATA_SECTIONS` in
  `arch/arm64/kernel/vmlinux.lds.S` places it in `.hyp.rodata`, which is
  mapped `PAGE_HYP_RO` at EL2.
- Kernel symbol used at EL2: the only mechanism is `KVM_NVHE_ALIAS()` in
  `arch/arm64/kernel/image-vars.h`; there is no hyp-image.S or kvm_nvhe.h.
- Kernel code used at EL2: compiled a second time into the object, as
  `lib-objs` and `../../../kernel/smccc-call.o` in
  `arch/arm64/kvm/hyp/nvhe/Makefile`; `KVM_NVHE_ALIAS_HYP()` lines in
  `image-vars.h` alias plain names such as `memcpy` to the `__pi_` names.
- `KVM_NVHE_ALIAS()` only makes the link succeed; EL2 can dereference the
  symbol only if its page is in the EL2 stage-1, which `init_hyp_mode()` in
  `arch/arm64/kvm/arm.c` builds and, under pKVM, `recreate_hyp_mappings()`
  in `arch/arm64/kvm/hyp/nvhe/setup.c` rebuilds from its own list.
- `host_hcall[]` order: free, `HANDLE_FUNC()` is a designated initialiser.
- `kvm_call_hyp()` and `kvm_call_hyp_ret()`: call `f` directly when
  `has_vhe()`, so `f` needs a VHE definition too; an nVHE-only function
  must be called with `kvm_call_hyp_nvhe()`.
- Relocation source: the static RELA entries of `kvm_nvhe.tmp.o`; the object
  is not linked as PIE.
- hyp_symbol_addr is not in this tree; EL2 code takes the address of a
  symbol directly.
- `gen-hyprel`: emits a fix-up for `R_AARCH64_ABS64` only; an unlisted
  relocation type in a `.hyp` section or any `SHT_REL` section fails the
  build.
- `kvm_apply_hyp_relocations()`: `__init`, called once from
  `hyp_mode_check()` in `arch/arm64/kernel/smp.c`, after
  `kvm_compute_layout()`, only when `!is_kernel_in_hyp_mode()`.
- Every listed slot is rewritten whatever it points to, so a statically
  initialised pointer in hyp data holds a hyp VA afterwards, also when the
  host reads it.
