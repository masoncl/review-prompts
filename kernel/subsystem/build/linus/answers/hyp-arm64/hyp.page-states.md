- `enum pkvm_page_state` is in `arch/arm64/kvm/hyp/include/nvhe/memory.h`.
- The two-bit mask is `PKVM_PAGE_STATE_VMEMMAP_MASK`; there is no
  PKVM_PAGE_STATE_MASK and no PKVM_MODULE_OWNED_PAGE in this tree.

| Value | Host and hyp (`struct hyp_page`) | Guest (stage-2 PTE) |
|---|---|---|
| `PKVM_PAGE_OWNED`, `PKVM_PAGE_SHARED_OWNED`, `PKVM_PAGE_SHARED_BORROWED` | stored | stored in SW0/SW1 of a valid PTE |
| `PKVM_NOPAGE` | stored | inferred: invalid PTE that is not poisoned |
| `PKVM_POISON` (`BIT(2)`) | not used | inferred: invalid PTE of type `KVM_GUEST_INVALID_PTE_TYPE_POISONED` |

- `PKVM_POISON`: the host forcibly reclaimed the page from the guest; only
  `guest_get_page_state()` returns it.
- `PKVM_POISON` does not fit `PKVM_PAGE_STATE_PROT_MASK` or
  `PKVM_PAGE_STATE_VMEMMAP_MASK`; no caller passes it to `pkvm_mkstate()`,
  `set_host_state()` or `set_hyp_state()`.
