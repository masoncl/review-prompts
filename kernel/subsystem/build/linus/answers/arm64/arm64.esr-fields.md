- `ESR_ELx_ISS2_MASK`: bits 55:32, extracted with `ESR_ELx_ISS2()`.
- ISS2 field macros (`ESR_ELx_TnD`, `ESR_ELx_TagAccess`, `ESR_ELx_GCS`,
  `ESR_ELx_Overlay`, `ESR_ELx_DirtyBit`, `ESR_ELx_Xs_MASK`,
  `ESR_ELx_HDBSSF`): bit positions inside ISS2, not inside the register.
  Apply them to `ESR_ELx_ISS2(esr)`, as `is_gcs_fault()` in
  `arch/arm64/mm/fault.c` does.
- `ESR_ELx_GCS` applied to the raw value tests bit 8, which is `ESR_ELx_CM`.
- ISS2 reaches user space: `thread.fault_code` is `unsigned long` and `esr` in
  `struct esr_context` is `__u64`; `struct pt_regs` holds no syndrome.
- `ESR_ELx_Xs_MASK` (ISS2): `data_abort_decode()` in `arch/arm64/mm/fault.c`,
  its only reader, treats it as valid only when `ESR_ELx_ISV` is set, together
  with `ESR_ELx_SAS`, `ESR_ELx_SSE`, `ESR_ELx_SRT_MASK`, `ESR_ELx_SF` and
  `ESR_ELx_AR`.
- `ESR_ELx_Overlay`, `ESR_ELx_DirtyBit`, `ESR_ELx_TnD`, `ESR_ELx_TagAccess`:
  nothing in the tree gates them on another bit or on the FSC;
  `data_abort_decode()` prints them unconditionally.
- Bits 12:11 have two meanings selected by the FSC. `ESR_ELx_SET_MASK` names
  them; `kvm_handle_guest_sea()` in `arch/arm64/kvm/mmu.c` reports them only
  under `kvm_has_ras()`. `io_mem_abort()` in `arch/arm64/kvm/mmio.c` reads the
  same bits as the load/store type with a raw `GENMASK(12, 11)`, after the
  `ESR_ELx_ISV` test and only for the FSC ranges in its `switch`.
- `ESR_ELx_FnV`: `__fault_safe_to_translate()` in
  `arch/arm64/kvm/hyp/include/hyp/fault.h` honours it only when the FSC equals
  `ESR_ELx_FSC_EXTABT`; `do_sea()` and `kvm_handle_guest_sea()` test it for
  every FSC that reaches them.
- `ESR_ELx_VNCR`: listed in `arch/arm64/include/asm/esr.h` with the fields
  shared by both abort kinds, but `host_owns_sea()` reads it only after
  `!kvm_vcpu_trap_is_iabt()`, and `kvm_handle_vncr_abort()` is the handler for
  `ESR_ELx_EC_DABT_CUR`.
