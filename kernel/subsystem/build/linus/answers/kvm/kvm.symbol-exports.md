- `EXPORT_SYMBOL_FOR_KVM_INTERNAL()`: usable only by the modules named in
  `KVM_SUB_MODULES`; `kvm` itself is not in that list.
- `KVM_SUB_MODULES` on x86: whichever of `kvm-amd` and `kvm-intel` is built as
  a module; see `arch/x86/include/asm/kvm_types.h`.
- `EXPORT_SYMBOL_GPL()`: allowed only on lines that contain one of the seven
  names in `exports_grep_trailer` in `arch/x86/kvm/Makefile`; any GPL module
  can use those symbols.
- The seven names: `kvm_get_kvm()`, `kvm_get_kvm_safe()`, `kvm_put_kvm()`, and
  the four page-track exports in `arch/x86/kvm/mmu/page_track.c`.
- `EXPORT_SYMBOL_FOR_KVM()`: not used under `virt/kvm/` or `arch/x86/kvm/`; it
  is for kernel code outside the KVM modules and exports to `kvm` plus
  `KVM_SUB_MODULES`.
- `EXPORT_SYMBOL_FOR_KVM()` with `KVM_SUB_MODULES` defined: exports even when
  `kvm` is built in.
- `EXPORT_SYMBOL_FOR_KVM()` without `KVM_SUB_MODULES`: empty on x86, and
  elsewhere empty unless `CONFIG_KVM` is a module.
- There is no EXPORT_SYMBOL_GPL_FOR_KVM_INTERNAL macro in this tree.
- Build check: `check_kvm_exports` in `arch/x86/kvm/Makefile` stops the build
  with `$(error ...)` when make reads that Makefile.
- Build check scope: runs only under `ifdef CONFIG_KVM_X86`, and scans `*.c`
  and `*.h` under both `virt/kvm` and `arch/x86/kvm`.
- Build check method: a whole-word text grep for `EXPORT_SYMBOL_GPL` and
  `EXPORT_SYMBOL`, so a comment that contains either word also fails the build.
- Not caught by the check: `.S` files, and any other macro, for example
  `EXPORT_SYMBOL_NS_GPL()` or a direct `EXPORT_SYMBOL_FOR_MODULES()`.
- A new `EXPORT_SYMBOL_GPL()` export for a non-KVM module needs its name added
  to `exports_grep_trailer` in the same patch.
