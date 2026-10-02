- Models take a selftest to include `"../kselftest.h"`. Here `lib.mk` adds
  `-I${top_srcdir}/tools/testing/selftests` to `CFLAGS`, and tests include
  `"kselftest.h"` and `"kselftest_harness.h"` from any depth; both spellings
  are in the tree.
- Models know KVM selftests with the types vm_vaddr_t and vm_paddr_t and with
  vm_vaddr_alloc(). None is in this tree: the types are `gva_t` and `gpa_t` in
  `tools/testing/selftests/kvm/include/kvm_util_types.h`, the allocator is
  `vm_alloc()`, and the library uses `u64` and `u32`.
- Models take `tools/testing/selftests/net/forwarding/lib.sh` to install an
  `EXIT` trap when sourced. Here it sets no trap.
