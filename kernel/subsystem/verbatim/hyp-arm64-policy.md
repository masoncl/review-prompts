These are rules for judging a finding against the hypervisor at EL2 (nVHE
and pKVM, `arch/arm64/kvm/hyp/`), written by a KVM/arm64 reviewer listed in
MAINTAINERS. A kernel tree cannot supply them, so they are kept by hand and
inserted as they are. They say how to judge. The facts about the code are in
the built guide. Where a rule here and the code under review disagree, the
rule decides the verdict.

- A fatal path at EL2 (`BUG()`, `BUG_ON()`, `WARN_ON()`, `hyp_panic()`) is
  judged by who can reach it. Reachable from a guest (through a hypercall's
  side effects, shared memory or DMA), or from host userspace through a
  syscall or ioctl that ends in a hypercall, it is a bug. Reachable only from
  the host kernel's own privileged code, it is not a bug, and fixing it is a
  hardening improvement if the fix is cheap. pKVM does not defend the host
  against the host. Reachable only through a firmware or hardware fault (EL3,
  the SMMU, the GIC misbehaving), it is out of scope, since pKVM does not
  recover from those. One reached because EL2's own invariant broke is a bug
  in EL2, separate from the panic. Reachability is checked, not read off the
  path's shape. List every writer of the value the fatal path reads: host
  userspace through an ioctl, the guest (including guest state that EL2
  copies out to the host and reads back on a later entry), and the host
  kernel alone. The path is host-kernel-only when neither userspace nor the
  guest can put a bad value there.
- Whether an assertion is the right check and whether triggering it is a bug
  are separate questions. A `WARN_ON()` whose condition can be met through a
  contracted input is the wrong tool, and the function should return an
  error instead. Contracted inputs are host-supplied values after
  de-privilege, an allocation from a pool the host feeds, a lookup result, a
  firmware or hardware return, a race, and anything timed. An allocation that
  a reserve sized at init guarantees may assert, but the reserve is per tree,
  so check its sizing in the tree under review. An assertion that can only
  fire when EL2's own just-written state is inconsistent is correct. Do not
  demote such an assertion because a different bug elsewhere could break the
  invariant. Report that bug.
- `WARN_ON()` and `BUG_ON()` are both fatal at EL2 in nVHE and pKVM. The code
  after a triggered `WARN_ON()` never runs, so `if (WARN_ON(err)) goto out;`
  has a dead error path. Report that. Do not use `CONFIG_BUG=n` to turn a
  defensive `WARN_ON()` into a NULL-dereference finding.
- `BUG()` and a direct `hyp_panic()` call end the same way at EL2. Do not
  report a change from one to the other as a regression.
- A hypercall or trap handler at EL2 runs to completion on the trapping CPU
  with interrupts masked. There is no scheduler, no preemption and no
  deferred work. Do not report a race that needs one handler to be
  interrupted or its tail deferred on the same CPU. Concurrency between two
  CPUs each running a handler against shared EL2 state is real and is judged
  under the kernel memory model as usual.
- For a protected vCPU, `HCR_EL2` is set by the hypervisor at vCPU init, and
  what it takes from the host's value is an allowlist. Sort each bit the code
  touches into one of two classes. Configuration bits define the guest's
  translation, execution state, interrupt routing and feature traps, and the
  host must not be able to set or clear them. Host-owned runtime signals are
  a benign policy or an event the host applies at runtime and that is
  meaningless unless it reaches the vCPU that runs, such as the WFI/WFE trap
  policy and virtual SError injection. They are copied in from the host's
  value. A signal the guest consumes must also reach the host again: the PE
  clears `HCR_EL2.VSE` when the guest takes the virtual SError, and a host
  that never sees the cleared bit injects the same SError on the next entry.
  The virtual IRQ and FIQ pending bits are injection signals too, but a
  guest's interrupts arrive through the vGIC, so for a protected vCPU the
  host does not get to raise one around the vGIC, and they stay out of the
  allowlist. Over-inclusion and under-inclusion are both bugs. A
  configuration bit taken from the host lets the host change the guest's
  environment. A host-owned signal left out means the host can no longer
  apply that policy or deliver that event. Copying only the allowlisted
  signals is correct, not a partial sync.
- Whether a field belongs to vCPU load or to every entry is decided by the
  requirement, not by where the code puts it today. State the host changes
  between entries (a pending virtual SError, a WFI/WFE policy change) belongs
  on the per-entry path, and state fixed for the life of the load (the
  fine-grained trap block) belongs at load. Report state at the wrong
  cadence. Do not report per-load state as missing from the per-entry path
  when its requirement places it at load.
- Converting a pointer with `kern_hyp_va()` more than once is harmless on a
  linear-map pointer. It is not corruption, at most a cleanup note.
- Whether EL2 saves the host's FP/SIMD state before loading a guest's
  differs between nVHE and pKVM, and the gate is per tree. Do not report the
  save as missing where the host's own lazy FP machinery covers it, nor as
  wasted where pKVM saves eagerly for a non-protected guest. Read the gate
  in the tree under review before reporting either.
