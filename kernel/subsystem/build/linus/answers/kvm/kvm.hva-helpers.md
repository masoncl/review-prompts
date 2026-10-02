- `gfn_to_hva_memslot_prot()`, `gfn_to_hva_prot()`,
  `kvm_vcpu_gfn_to_hva_prot()`: global in `virt/kvm/kvm_main.c` but carry no
  export macro, so a module listed in `KVM_SUB_MODULES` cannot call them.
- `gfn_to_hva_memslot()`, `gfn_to_hva()`, `kvm_vcpu_gfn_to_hva()`: carry
  `EXPORT_SYMBOL_FOR_KVM_INTERNAL()`.
