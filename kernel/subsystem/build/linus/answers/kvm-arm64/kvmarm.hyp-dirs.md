- Files in `arch/arm64/kvm/hyp/` built into both the VHE and nVHE objects:
  `vgic-v3-sr.c`, `vgic-v5-sr.c`, `vgic-v2-cpuif-proxy.c`, `aarch32.c`,
  `entry.S`, `hyp-entry.S`, `exception.c`. The lists are the `../` entries in
  `vhe/Makefile` and `nvhe/Makefile`.
- `sysreg-sr.c`, `timer-sr.c`, `debug-sr.c`, `tlb.c`, `switch.c`: separate
  files of the same name in `vhe/` and `nvhe/`; none is shared.
- `pgtable.c`: built into the nVHE object and, by
  `arch/arm64/kvm/hyp/Makefile`, as plain kernel code with neither
  `__KVM_VHE_HYPERVISOR__` nor `__KVM_NVHE_HYPERVISOR__`. It is not in
  `vhe/Makefile`. In the host build `has_vhe()` is a runtime cap test.
- `hyp-constants.c`: in neither object; `arch/arm64/kvm/Makefile` compiles it
  to generate `hyp_constants.h`.
- nVHE also links `arch/arm64/kernel/smccc-call.o` and, from
  `arch/arm64/lib/`, `tishift.o` with the page and mem routines.
- Conditional nVHE files: `list_debug.c` under `CONFIG_LIST_HARDENED`;
  `clock.c`, `trace.c`, `events.c` under `CONFIG_NVHE_EL2_TRACING`.
- Shared source compiles to different code per object: the
  `read_sysreg_el1()` family in `arch/arm64/include/asm/kvm_hyp.h` is fixed
  VHE encodings (`_EL12` for `read_sysreg_el1()`) in the VHE object and an
  alternative keyed on `ARM64_KVM_HVHE` in the nVHE object.
- `exception.c`: `#error` unless one of the two hypervisor macros is
  defined, so it cannot be reused from host code.
