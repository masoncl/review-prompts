# KVM Subsystem Details

## Quick Checks

- If a patch introduces a guest-visible feature, it must default off and
  must be enumerable (via KVM_GET_SUPPORTED_CPUID2 or other architecture-
  specific mechanisms).

- Is a new configuration flag being added to a memslot or VCPU? Should it
  be immutable after creation? If so, reject modifications.

- Is there a loop over memory sizes or page tables? Does it have a
  cond_resched() or does it periodically release any locks it holds?
  Otherwise you may see soft lockups or lock contention.

- Do not use WARN_ON/BUG_ON for guest- or userspace-reachable states.
  KVM allows userspace (e.g., QEMU) to set almost any vCPU state via
  ioctls (KVM_SET_SREGS, KVM_SET_NESTED_STATE, etc.). Userspace can set
  this state in unusual orders or inject architecturally impossible states.

- Ensure kvm->srcu is held when accessing guest memory.

- Do not assume that the guest memory containing an instruction remains
  static between the time the CPU faults on it and the time KVM software
  decodes it.

- Concurrency during VM teardown or modifications to VM state while vCPUs
  are running may cause Use-After-Frees or NULL dereferences.

  Ensure vCPUs and their nested state are completely halted and freed
  before the backing VM assets (like APIC/PIC state or memory) are
  destroyed.
