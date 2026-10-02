- There is no kvm_pgtable_stage2_set_owner(), kvm_init_invalid_leaf_owner(),
  KVM_INVALID_PTE_OWNER_MASK or pkvm_host_invalid_pte_type here;
  `kvm_pgtable_stage2_annotate()` in `arch/arm64/kvm/hyp/pgtable.c` writes the
  entry, and the types are `enum kvm_invalid_pte_type` in
  `arch/arm64/include/asm/kvm_pgtable.h`.

| PTE bits | Field | Mask |
|---|---|---|
| 63:60 | type | `KVM_INVALID_PTE_TYPE_MASK` |
| 59:4 | extra metadata | `KVM_HOST_DONATION_PTE_EXTRA_MASK` |
| 3:1 | owner (`enum pkvm_component_id`) | `KVM_HOST_DONATION_PTE_OWNER_MASK` |
| 0 | valid, clear | `KVM_PTE_VALID` |

- Owner and extra masks: defined in `arch/arm64/kvm/hyp/nvhe/mem_protect.c`,
  not in a header.

| Type | Where it appears | Meaning |
|---|---|---|
| `KVM_INVALID_PTE_TYPE_LOCKED` | any stage-2, transient | break-before-make in progress |
| `KVM_HOST_INVALID_PTE_TYPE_DONATION` | host stage-2 | page owned by hyp or a guest |
| `KVM_GUEST_INVALID_PTE_TYPE_POISONED` | guest stage-2 | page forcibly reclaimed by the host |

- `kvm_pgtable_stage2_annotate()`: returns `-EINVAL` for type 0, for
  `KVM_INVALID_PTE_TYPE_LOCKED`, and for an annotation that touches bit 0 or
  bits 63:60.
- `host_stage2_set_owner_metadata_locked()`: returns `-EINVAL` for
  `PKVM_ID_HOST`; on success always sets the host state to `PKVM_NOPAGE`.
- `host_stage2_set_owner_locked()`: accepts only `PKVM_ID_HYP` (annotation with
  zero metadata) and `PKVM_ID_HOST`; `PKVM_ID_GUEST` gets `-EINVAL`.
- `host_stage2_set_owner_locked()` with `PKVM_ID_HOST`: installs a valid
  `PKVM_HOST_MEM_PROT` idmap in place of the annotation and sets
  `PKVM_PAGE_OWNED`; it does not leave a zero entry.
- Guest-owned page: extra metadata from `host_stage2_encode_gfn_meta()`; VM
  handle in metadata bits 15:0 (`KVM_HOST_PTE_OWNER_GUEST_HANDLE_MASK`), gfn in
  bits 55:16 (`KVM_HOST_PTE_OWNER_GUEST_GFN_MASK`).
- `host_stage2_decode_gfn_meta()`: `-EINVAL` for a valid PTE or another type,
  `-EPERM` when the owner is not `PKVM_ID_GUEST`, `-EAGAIN` when
  `get_vm_by_handle()` no longer finds the VM.
- Only `__pkvm_host_force_reclaim_page_guest()` decodes the metadata, through
  `host_stage2_get_guest_info()`; `__pkvm_host_reclaim_page_guest()` takes the
  VM and gfn from its caller.
- Guest page shared back to the host: `__pkvm_guest_share_host()` replaces the
  annotation with a valid mapping, so owner and gfn are in the host stage-2
  only while the host state is `PKVM_NOPAGE`;
  `__pkvm_guest_unshare_host()` writes the annotation again.
