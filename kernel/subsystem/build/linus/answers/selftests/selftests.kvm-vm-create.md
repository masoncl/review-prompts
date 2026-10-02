- Hook names: the library has no hook named kvm_arch_vm_create() and no helper
  named vm_create_shape(). `kvm_arch_vm_post_create()` is the last call in
  `__vm_create()`; `kvm_arch_vm_finalize_vcpus()` is the last call in
  `__vm_create_with_vcpus()`; both in
  `tools/testing/selftests/kvm/lib/kvm_util.c`.
- `____vm_create()`, `vm_create_barebones()`, `vm_create_barebones_type()`:
  run neither hook.
- `vm_recreate_with_one_vcpu()`: runs neither hook; it calls
  `kvm_vm_restart()` and `vm_vcpu_recreate()`.
- `nr_runnable_vcpus` of `__vm_create()`: on arm64 it is also the
  redistributor count of the default GICv3, through
  `kvm_arch_vm_post_create()` and `__vgic_v3_setup()`.
- `vm_create(0)`: fails the assertion in `vm_nr_pages_required()`.
- Comment above `____vm_create()` in
  `tools/testing/selftests/kvm/include/kvm_util.h`: says the irqchip is
  "x86 only"; arm64 `kvm_arch_vm_post_create()` creates one too.
- **Potentially unsafe usage**: `vm_create()` or `__vm_create()`, then
  `vm_vcpu_add()` or `aarch64_vcpu_add()`, with no call to
  `kvm_arch_vm_finalize_vcpus()`.
  - Unsafe: on arm64 while the default vGIC is enabled. The first `KVM_RUN`
    returns `-EBUSY` from `vgic_v3_map_resources()`, and
    `kvm_vgic_map_resources()` then calls `kvm_vm_dead()`. The test need not
    use interrupts for this to fail.
  - Safe: call `kvm_arch_vm_finalize_vcpus()` after the last vCPU, as
    `setup_vm()` in `tools/testing/selftests/kvm/arm64/psci_test.c` and
    `create_vm()` in `tools/testing/selftests/kvm/dirty_log_test.c` do.
  - Safe: the test called `test_disable_default_vgic()` before creating the
    VM, as `main()` in `tools/testing/selftests/kvm/arm64/vgic_init.c` does;
    `vm->arch.has_gic` stays false and the hook does nothing.
  - Safe: the VM comes from `____vm_create()`, as in
    `tools/testing/selftests/kvm/arm64/page_fault_test.c`; no default vGIC
    exists.
  - Safe: the test is built only for architectures that use the weak empty
    hook, as `hardware_disable_test` is in
    `tools/testing/selftests/kvm/Makefile.kvm`. Only arm64 overrides
    `kvm_arch_vm_finalize_vcpus()`.
- **Potentially unsafe usage**: on arm64, adding a vCPU after
  `kvm_arch_vm_finalize_vcpus()` has run.
  - Unsafe: when the VM has the default vGIC; the hook initialised it, and
    `kvm_arch_vcpu_precreate()` in `arch/arm64/kvm/arm.c` returns `-EBUSY`
    once the vGIC is initialised.
  - Safe: add every vCPU first, then finalize once, as
    `__vm_create_with_vcpus()` does.
  - Safe: the test called `test_disable_default_vgic()` and has not yet
    initialised a vGIC of its own, as `test_vgic_then_vcpus()` in
    `tools/testing/selftests/kvm/arm64/vgic_init.c` does; the hook did
    nothing, so `vgic_initialized()` is still false.
