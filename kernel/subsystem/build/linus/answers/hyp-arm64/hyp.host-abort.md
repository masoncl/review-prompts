- Faulting address: `FIELD_GET(HPFAR_EL2_FIPA, fault.hpfar_el2) << 12`;
  `HPFAR_MASK` is not used here, and the page offset from `FAR_EL2` is not
  merged in.
- `__get_fault_info()` returns `false` (AT on `FAR_EL2` failed):
  `handle_host_mem_abort()` returns without mapping and the host retries.
- `__get_fault_info()` returns `true` with `HPFAR_EL2_NS` clear, which
  happens when `__fault_safe_to_translate()` is false: `BUG_ON()`.
- `ARM64_WORKAROUND_834220`: `__hpfar_valid()` is false for translation
  faults, so the address comes from `__translate_far_to_hpfar()`.

| `host_stage2_idmap()` result | Handling |
|---|---|
| `0` | return to host |
| `-EEXIST` (leaf already valid) | return to host |
| `-EPERM` (annotated entry) | `host_inject_mem_abort()`, then return |
| anything else, `-EAGAIN` and `-ENOMEM` included | `BUG()` |

- `-EAGAIN` from the map walker never reaches the switch:
  `__host_stage2_idmap()` passes `KVM_PGTABLE_WALK_IGNORE_EAGAIN`.
- There is no __inject_host_exception(); `host_inject_mem_abort()` in
  `arch/arm64/kvm/hyp/nvhe/mem_protect.c` calls `inject_host_exception()` in
  `arch/arm64/kvm/hyp/nvhe/hyp-main.c`.
- Injected `ESR_EL1`: the `ESR_EL2` value with `ESR_ELx_S1PTW` set and, unless
  the fault came from `PSR_MODE_EL0t`, the EC repainted to
  `ESR_ELx_EC_DABT_CUR` or `ESR_ELx_EC_IABT_CUR`; the FSC is unchanged, so it
  is not a synchronous external abort.
- `inject_host_exception()`: writes `FAR_EL1` only when the FSC is a
  translation fault.
- `is_pkvm_stage2_abort()` in `arch/arm64/mm/fault.c`: tests only
  `is_pkvm_initialized()` and `ESR_ELx_S1PTW`; it does not test the FSC.
- User-mode fault: `do_page_fault()` sends `SIGSEGV` with `SEGV_ACCERR` before
  any VMA lookup.
