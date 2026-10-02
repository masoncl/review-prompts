- There is no kvm_hyp_handle_ptrauth() in this tree, and none of the three
  hyp tables has an `ESR_ELx_EC_PAC` entry.
- `__fixup_guest_exit()` dispatches only when the raw `*exit_code` equals
  `ARM_EXCEPTION_TRAP`. A trap with `ARM_EXIT_WITH_SERROR_BIT` set goes to
  the host unhandled and is replayed after the SError is injected.
- `__fixup_guest_exit()` does nothing for an IRQ exit, and for SError or
  illegal-return exits it only stores `ESR_EL2`; it emulates no vGIC or
  erratum trap itself.
- Table selection: VHE `fixup_guest_exit()` passes its `hyp_exit_handlers`
  directly. `kvm_get_exit_handler_array()` exists only in
  `arch/arm64/kvm/hyp/nvhe/switch.c` and tests `vcpu_is_protected()`.
- A non-protected guest under pKVM uses `hyp_exit_handlers`, not
  `pvm_exit_handlers`.
- Entries that differ from the nVHE `hyp_exit_handlers`:

| Table | EC | Handler |
|---|---|---|
| VHE | `ESR_ELx_EC_SYS64` | `kvm_hyp_handle_sysreg_vhe()` |
| VHE | `ESR_ELx_EC_ERET` | `kvm_hyp_handle_eret()` |
| VHE | `0x3F` | `kvm_hyp_handle_impdef()` |
| pVM | `ESR_ELx_EC_HVC64` | `kvm_handle_pvm_hvc64()` |
| pVM | `ESR_ELx_EC_SYS64` | `kvm_handle_pvm_sys64()` |
| pVM | `ESR_ELx_EC_SVE` | `kvm_handle_pvm_restricted()` |
| pVM | `ESR_ELx_EC_CP15_32` | none |

- `kvm_hyp_handle_iabt_low` and `kvm_hyp_handle_watchpt_low`: macros for
  `kvm_hyp_handle_memory_fault()`; a change to it affects three ECs.
- Handlers that return false after changing state, so the host sees the
  changed state:
  - `kvm_hyp_handle_dabt_low()` may set `*exit_code` to
    `ARM_EXCEPTION_EL1_SERROR`;
  - `kvm_hyp_handle_impdef()` always returns false; with
    `ARM64_WORKAROUND_PMUV3_IMPDEF_TRAPS` it first rewrites
    `vcpu->arch.fault.esr_el2` to a synthetic `ESR_ELx_EC_SYS64`;
  - `kvm_hyp_handle_zcr_el2()` always returns false, and may first load
    guest FP state through `kvm_hyp_handle_fpsimd()`;
  - `pkvm_memshare_call()` in `arch/arm64/kvm/hyp/nvhe/pkvm.c`, when
    `__pkvm_guest_share_host()` returns `-ENOENT`, fakes a data abort in
    `vcpu->arch.fault` so the host maps the page.
- `kvm_handle_pvm_sysreg()`: injects an undefined exception and returns true
  when no descriptor matches; returns false when the descriptor has a NULL
  `access`.
- `kvm_handle_pvm_hvc64()`: handles the vendor-hyp features, meminfo, share
  and unshare calls; every other function ID returns false to the host.
- **Potentially unsafe usage**: a handler returning true without calling
  `__kvm_skip_instr()`.
  - Unsafe: when nothing else changed that would stop the same trap; the
    `do`/`while` loop around `__guest_enter()` re-enters the guest on the
    same instruction, which traps again.
  - Safe: the trap cause was removed, as `kvm_hyp_handle_fpsimd()` does by
    making the guest the FP owner before `__activate_cptr_traps()`.
  - Safe: the handler wrote `ELR_EL2` itself, as `kvm_hyp_handle_mops()` and
    `kvm_hyp_handle_eret()` do.
  - Safe: an exception was injected, as `kvm_handle_pvm_restricted()` does
    with `inject_undef64()`.
  - Safe: a retry is intended, as `kvm_hyp_handle_memory_fault()` does when
    `__populate_fault_info()` fails.
  - Safe: an HVC exit, as in `kvm_handle_pvm_hvc64()`; `ELR_EL2` already
    points past the HVC, and `__pkvm_memshare_page_req()` subtracts 4 to
    replay it.
