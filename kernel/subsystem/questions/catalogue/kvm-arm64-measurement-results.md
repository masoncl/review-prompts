# What the kvm-arm64 measurement found

Three models were asked the 82 questions in `kvm-arm64-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against a
mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C. Reader C
is the most current (it answered for kernels up to 7.0), reader A is a few
releases behind it, and reader B is older still; which models they were does not
matter here. The hand-written guide was never checked against current sources,
so differences between it and the built guide are expected and are noted below.

## What all three readers got wrong

- **Names every reader offered that are not in the tree.** An
  AA32_ID_SANITISED() descriptor macro (it is `AA32_ID_WRITABLE()`, with
  `val = GENMASK(31, 0)`); a KVM_PGTABLE_WALK_HANDLE_FAULT walker flag (the
  flag is `KVM_PGTABLE_WALK_IGNORE_EAGAIN`, with the opposite sense: `-EAGAIN`
  ends a walk unless it is set); a __pkvm_teardown_vm hypercall;
  kvm_inject_dabt() and kvm_inject_pabt() (the abort handler calls
  `kvm_inject_sea_dabt()`, `kvm_inject_sea_iabt()` and
  `kvm_inject_size_fault()`). Two of three also offered
  kvm_pgtable_stage2_set_owner() for `kvm_pgtable_stage2_annotate()`,
  KVM_INVALID_PTE_LOCKED for `KVM_INVALID_PTE_TYPE_LOCKED`, a fpsimd.S under
  `arch/arm64/kvm/hyp/`, and kvm_reset_id_regs() for `kvm_reset_sys_regs()` and
  `reset_vm_ftr_id_reg()`.
- **The pKVM VM life cycle.** The handle is reserved at VM creation
  (`__pkvm_reserve_vm` from `pkvm_init_host_vm()`), the hypervisor VM and each
  hypervisor vCPU are created at that vCPU's first run, and teardown is two
  calls: `__pkvm_start_teardown_vm` from the stage-2 destroy path and
  `__pkvm_finalize_teardown_vm` from `pkvm_destroy_hyp_vm()`.
  `pkvm_create_hyp_vm()` takes `kvm->slots_lock` and then `config_lock`; no
  reader had the locks right.
- **What is copied between the host's and the hypervisor's vCPU.** One reader
  had the whole context copied every time, one had it copied at load and put,
  one said there is no dirty marker and no sync hypercall. There is a
  `PKVM_HOST_STATE_DIRTY` flag and a `__pkvm_vcpu_sync_state` hypercall; a
  non-protected guest is copied in only when dirty and only PC and PSTATE come
  back; only the TWI, TWE and VSE bits of `hcr_el2` flow from the host.
- **Restrictions under pKVM.** MTE, eager splitting and the block-size
  capability are refused for every VM once pKVM is on, not only for protected
  ones. SVE and the PMU are refused for a protected VM. Features are not
  rejected at `KVM_ARM_VCPU_INIT`; the hypervisor masks them in
  `pkvm_init_features_from_host()`.
- **The GICv3 trap bits.** The bits common to all guests are computed by an
  alternatives callback, `kvm_compute_ich_hcr_trap_bits()`, and read with
  `vgic_ich_hcr_trap_bits()`. Two readers had them decided in
  `vgic_v3_probe()` and cached in the global state. `vcpu_set_ich_hcr()` adds
  the per-vCPU ones from `kvm_calculate_traps()`.
- **The VMCR is saved on every exit** by `__vgic_v3_save_state()`; only the
  active priority registers are load and put state. All three said both are.
- **Direct injection.** `its_unmap_vlpi()` and `kvm_vgic_v4_unset_forwarding()`
  return void, and the unset path finds the interrupt by scanning the LPI
  xarray for the host interrupt number, not through the ITS.
- **`VCPU_INITIALIZED` can be cleared again**, by the run loop when it catches
  a guest in an unsupported 32-bit mode and by the nVHE switch for a protected
  vCPU. Two readers said never.
- **`config_lock` sits in two chains**, `kvm->lock` then `vcpu->mutex` then
  `config_lock`, and `slots_lock` then `srcu` then `config_lock`. One reader
  had it outside `vcpu->mutex`, one gave a single chain, one had it protect the
  timer offsets, which `kvm->lock` and `kvm_trylock_all_vcpus()` do.
- **VM destruction order**: all three had the vCPUs or the stage-2 in the wrong
  place. The vgic goes first, then the hypervisor VM, then stage-2, then the
  vCPUs.
- **Fine-grained traps**: `kvm->arch.fgu[]` is per VM and computed once;
  `vcpu->arch.fgt[]` is a read and write pair per group, computed at load by
  `kvm_vcpu_load_fgt()` and written by `__activate_traps_hfgxtr()`, at load on
  VHE and at every entry on nVHE.
- **Sanitised registers of a nested guest** are not only the VNCR-backed ones;
  `HCR_EL2`, `MDCR_EL2` and the others after `__SANITISED_REG_START__` are
  masked too, by the read, assign and modify accessors alike.
- **PMU**: setting the number of counters has no has-run check; only the
  filter and the PMU selection do. Every attribute is refused once the PMU is
  initialised.
- **MTE**: `HCR_TID5` is set when the VM has no MTE, and enabling MTE is refused
  if a guest_memfd slot exists.

## What readers A and B got wrong as well

- **The stage-2 fault handler is no longer one function.** Both described
  `user_mem_abort()` with a force_pte local. It is a driver over
  `kvm_s2_fault_pin_pfn()` (which calls `kvm_s2_fault_get_vma_info()`),
  `kvm_s2_fault_compute_prot()` and `kvm_s2_fault_map()`, passing
  `struct kvm_s2_fault_desc` and `struct kvm_s2_fault_vma_info`. Reader C knew
  the helpers and invented a third structure.
- **First run.** Both listed a kvm_arch_vcpu_run_map_fp() step and a debug
  init step that do not exist, and left out `kvm_finalize_sys_regs()`, the
  nested allocations, `vgic_v5_finalize_ppi_state()` and
  `pkvm_create_hyp_vcpu()`.
- **Debug.** Both had kvm_arm_setup_debug() and kvm_arm_clear_debug() in the
  run loop. Debug state is decided at load by `kvm_vcpu_load_debug()` through
  `vcpu->arch.debug_owner`.
- **Which register is where while loaded.** Both described an older scheme;
  reader B named __vcpu_read_sys_reg_from_cpu(). The code is
  `locate_register()` and `struct sr_loc` in `sys_regs.c`.
- **Trapped system register flow.** Reader A had a vCPU in virtual EL2 forward
  to the guest hypervisor, which is the opposite of the code, and both had a
  binary search of the table; the descriptor index comes from the forwarding
  xarray, and the fine-grained UNDEF check comes first.
- **HCR_EL2** is written at every entry on VHE as well as nVHE, by
  `___activate_traps()`; both had it as load state on VHE.
- **GICv5.** Reader A did not know whether the tree has it and reader B said it
  does not. It does: `arch/arm64/kvm/vgic/vgic-v5.c`, its own interrupt ID encoding, and a
  step at first run.

## What reader B got wrong as well

Reader B answered for a kernel about a dozen releases back and had whole
mechanisms out of date: `__vcpu_sys_reg()` as an lvalue (assignment is
`__vcpu_assign_sys_reg()` and `__vcpu_rmw_sys_reg()`); pending exceptions as
KVM_ARM64_ flags in a single vcpu->arch.flags word (they are `PENDING_EXCEPTION`,
`EXCEPT_MASK` and `INCREMENT_PC` in `iflags`, one of three flag sets); FP
ownership in the vCPU (it is the per-CPU `fp_owner` in `struct kvm_host_data`);
LPIs on a list with a list lock (they are in the `lpi_xa` xarray, found under
RCU); the dependency tables in an id_regs.c (they are in `config.c`);
`config_lock` outside `vcpu->mutex`; two groups of host hypercalls, not three;
no ioctl for the writable ID masks (`KVM_ARM_GET_REG_WRITABLE_MASKS`).

## What the readers already knew

The file for each job and the entry points (all three); the selftests (A and
C); `KVM_ARM_VCPU_INIT` and finalising (A and C); how ID register writes are
checked, how the register enum is numbered and the accessor family (C); the MMU
lock mode per operation, the vgic lock order and the vgic reference rules (A and
C, each with one correction); the shadow stage-2 structure and the trap
forwarding tables (C).

## Where the hand-written guide is stale

- `vcpu_has_run_once()` reads `vcpu->pid`, but generic `kvm_vcpu_ioctl()` sets
  that after `kvm_arch_vcpu_run_pid_change()` returns; the arch hook does not.
  The guide tells every gate to use it, while almost every in-tree gate (ID
  registers, the PMU, the hypercall bitmaps, the SMCCC filter) uses the per-VM
  `kvm_vm_has_ran_once()`; `vcpu_has_run_once()` has three users.
- It says `kvm_vcpu_initialized()` stays true for ever. The flag is cleared in
  two places.
- It cites "Fix clobbered ELR in sync abort/SError" as a guest exception
  injection bug. That commit is about the hypervisor's own `ELR_EL2` on its
  panic path.
- It says unmapping a vLPI must be checked and warned on. The function returns
  void.
- Its example of a numeric range over `enum vcpu_sysreg` is code that has been
  fixed; `__copy_vcpu_state()` now skips the timer registers by name and says
  why in a comment.
- It describes `user_mem_abort()` as one function with a `vma_shift` to
  re-check under the lock and a memory cache pointer that may be
  uninitialised. The handler is staged, staleness is caught by
  `mmu_invalidate_retry()`, and `get_mmu_memcache()` always returns a cache.
- Its GIC sections (active priority register write rules, self-synchronising
  reads, memory-mapped interface gating) restate the architecture manual and
  name nothing in the tree. They are left to the manual.
- It says nothing about nested virtualisation, the feature dependency tables,
  the per-VM ID registers or GICv5, which is where most recent change is.

## What was left out of the build set and why

The guide may be 1,851 words and every question found at least one weak reader,
so the build set was chosen by importance to someone reviewing a patch, not by
dropping what readers know. Kept: the first-run order and its predicates, the
register enum and accessors, the ID register descriptors and checks, the
dependency tables, exception injection, the staged fault handler and its
release and lock rules, teardown, the vgic locks and LPI references, direct
injection, the GICv3 traps, and the pKVM life cycle, state copy and
restrictions. Left out: nested virtualisation beyond what the register
questions say (five questions; it needs a guide of its own), the timer and PMU,
vCPU requests, load and put, reset, MPIDR, the descriptor fields and trap flow,
the hypervisor exit handlers, hypercalls, the page-table library's entry points
and walker flags, mapping size and retry in the fault path, the pKVM page
states and transitions, the pending list, GICv5, debug and the flag sets.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader A          182        44%      8     50   6.12 to 6.18
reader B          232        78%      2     79   6.9 to 6.13
reader C          182        23%     26     12   6.15 to 7.0

question                           reader A      reader B      reader C
kvmarm.core-files                   3% ( 1)       6% ( 5)       3% ( 3)
kvmarm.hyp-dirs                     6% ( 1)      75% ( 2)       5% ( 3)
kvmarm.entry-points                 5% ( 1)       7% ( 1)       2% ( 1)
kvmarm.docs                        15% ( 1)      53% ( 2)      15% ( 1)
kvmarm.selftests                    2% ( 1)      20% ( 1)       0% ( 0)
kvmarm.modes                       43% ( 1)      68% ( 3)      26% ( 2)
kvmarm.vm-destroy-order            64% ( 5)      88% ( 5)      50% ( 5)
kvmarm.vcpu-init-ioctl             17% ( 2)      79% ( 5)       0% ( 2)
kvmarm.vcpu-features               18% ( 1)      87% ( 3)      28% ( 2)
kvmarm.finalize                    10% ( 1)      53% ( 1)       0% ( 0)
kvmarm.first-run                   35% ( 1)      87% ( 2)      16% ( 3)
kvmarm.has-run-predicates          43% ( 1)      74% ( 3)      30% ( 1)
kvmarm.arch-flags                  30% ( 2)      70% ( 7)       3% ( 1)
kvmarm.vcpu-flags                  67% ( 4)      83% ( 4)      36% ( 4)
kvmarm.config-lock                 56% ( 2)      82% ( 6)      35% ( 4)
kvmarm.vcpu-requests               39% ( 3)      98% ( 5)      21% ( 5)
kvmarm.run-loop                    46% ( 1)      83% ( 1)       5% ( 2)
kvmarm.vcpu-load-put               19% ( 2)      92% ( 1)       3% ( 1)
kvmarm.reset                       32% ( 1)      80% ( 1)      13% ( 2)
kvmarm.mpidr                       34% ( 2)      88% ( 1)       5% ( 1)
kvmarm.vpidr-vmpidr                44% ( 1)      86% ( 1)      28% ( 1)
kvmarm.sysreg-storage              44% ( 3)      77% ( 3)       0% ( 2)
kvmarm.sysreg-enum-usage           33% ( 2)      89% ( 2)      11% ( 3)
kvmarm.sysreg-accessors            26% ( 1)      86% ( 2)       1% ( 1)
kvmarm.sysreg-location             71% ( 4)      86% ( 1)      14% ( 2)
kvmarm.sysreg-desc                 51% ( 6)      81% ( 4)      30% ( 2)
kvmarm.sysreg-trap-flow            77% ( 4)      84% ( 2)      22% ( 3)
kvmarm.idreg-storage               22% ( 2)      86% ( 4)      20% ( 1)
kvmarm.idreg-desc-kinds            20% ( 1)      73% ( 1)      25% ( 3)
kvmarm.idreg-write-check           45% ( 1)      80% ( 2)       6% ( 1)
kvmarm.idreg-after-run             17% ( 1)      82% ( 1)      12% ( 1)
kvmarm.idreg-expose-usage          25% ( 1)      82% ( 2)      16% ( 1)
kvmarm.feat-map                    32% ( 5)      90% ( 4)      19% ( 3)
kvmarm.trap-calc                   63% ( 1)      89% ( 3)      25% ( 1)
kvmarm.fgt                         51% ( 1)      82% ( 2)      41% ( 1)
kvmarm.hcr-el2                     64% ( 3)      83% ( 5)      24% ( 1)
kvmarm.trap-sync                   68% ( 1)      85% ( 2)      39% ( 4)
kvmarm.hyp-exit-fixup              70% ( 3)      71% ( 3)      39% ( 4)
kvmarm.pending-exception           12% ( 1)      87% ( 4)      30% ( 3)
kvmarm.inject-usage                43% ( 3)      90% ( 4)      30% ( 3)
kvmarm.hypercalls                  77% ( 4)      92% ( 5)      41% ( 5)
kvmarm.s2-mmu-struct               23% ( 3)      68% ( 5)       0% ( 0)
kvmarm.pgtable-api                 28% ( 3)      80% ( 3)      11% ( 3)
kvmarm.walker-flags                17% ( 1)      54% ( 3)      29% ( 2)
kvmarm.shared-walk                 35% ( 3)      79% ( 2)      18% ( 4)
kvmarm.mmu-lock-mode               22% ( 1)      66% ( 3)      20% ( 1)
kvmarm.fault-entry                 52% ( 4)      84% ( 5)      27% ( 5)
kvmarm.fault-stages                80% ( 2)      91% ( 6)      31% ( 2)
kvmarm.fault-release-usage         47% ( 2)      78% ( 4)      19% ( 1)
kvmarm.fault-memcache              62% ( 1)      93% ( 5)      39% ( 1)
kvmarm.fault-mapping-size          44% ( 1)      80% ( 3)       4% ( 1)
kvmarm.fault-retry                 51% ( 1)      68% ( 3)      22% ( 1)
kvmarm.s2-teardown                 61% ( 4)      90% ( 4)      23% ( 2)
kvmarm.s2-teardown-usage           46% ( 2)      72% ( 1)      27% ( 2)
kvmarm.mte                         58% ( 4)      92% ( 3)      46% ( 3)
kvmarm.vhe-nvhe-split              71% ( 4)      89% ( 2)      17% ( 6)
kvmarm.nvhe-build                  64% ( 3)      90% ( 1)      22% ( 2)
kvmarm.hyp-call                    55% ( 2)      78% ( 1)      26% ( 2)
kvmarm.fp-ownership                45% ( 2)      84% ( 1)      17% ( 1)
kvmarm.debug-ownership             59% ( 1)      84% ( 1)      19% ( 1)
kvmarm.pkvm-objects                33% ( 2)      69% ( 1)      14% ( 4)
kvmarm.pkvm-vm-lifecycle           64% ( 4)      90% ( 2)      51% ( 3)
kvmarm.pkvm-before-first-run       48% ( 2)      58% ( 1)      28% ( 1)
kvmarm.pkvm-state-sync             73% ( 3)      81% ( 2)      66% ( 1)
kvmarm.pkvm-page-states            67% ( 5)      75% ( 4)      26% ( 3)
kvmarm.pkvm-transitions            65% ( 2)      95% ( 3)      38% ( 1)
kvmarm.pkvm-restrictions           70% ( 5)      76% ( 3)      64% ( 3)
kvmarm.vgic-lock-order             29% ( 1)      73% ( 2)       8% ( 1)
kvmarm.vgic-irq-refs               11% ( 1)      73% ( 2)       9% ( 1)
kvmarm.vgic-lpi-release-usage      40% ( 1)      73% ( 2)      16% ( 1)
kvmarm.vgic-init-stages            27% ( 2)      84% ( 3)      14% ( 1)
kvmarm.vgic-ap-list                49% ( 4)      78% ( 4)      51% ( 5)
kvmarm.vgic-v4-forwarding          72% ( 2)      86% ( 3)      38% ( 3)
kvmarm.vgic-cpuif-traps            70% ( 2)      85% ( 4)      43% ( 2)
kvmarm.vgic-apr-vmcr               55% ( 2)      85% ( 3)      44% ( 3)
kvmarm.vgic-v5                     75% ( 1)      97% ( 1)      37% ( 5)
kvmarm.timer-contexts              24% ( 2)      74% ( 2)      32% ( 1)
kvmarm.pmu                         56% ( 4)      78% ( 4)      60% ( 5)
kvmarm.nv-state                    59% ( 6)      86% (11)      25% ( 3)
kvmarm.nv-shadow-s2                75% ( 2)      92% ( 1)      33% ( 3)
kvmarm.nv-trap-forwarding          57% ( 1)      88% ( 1)       0% ( 0)
kvmarm.nv-resx                     58% ( 1)      89% ( 1)      44% ( 3)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `kvmarm.vm-destroy-order`, `kvmarm.vcpu-flags`, `kvmarm.sysreg-location`, `kvmarm.sysreg-desc`, `kvmarm.sysreg-trap-flow`, `kvmarm.trap-calc`, `kvmarm.fgt`, `kvmarm.hyp-exit-fixup`, `kvmarm.fault-entry`, `kvmarm.fault-memcache`, `kvmarm.fault-retry`, `kvmarm.vhe-nvhe-split`, `kvmarm.pkvm-page-states`, `kvmarm.pkvm-transitions`, `kvmarm.vgic-ap-list`, `kvmarm.nv-state`, `kvmarm.nv-shadow-s2`, `kvmarm.nv-trap-forwarding`, `kvmarm.nv-resx`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `kvmarm.vcpu-init-ioctl`, `kvmarm.vcpu-features`, `kvmarm.finalize`, `kvmarm.vcpu-requests`, `kvmarm.vcpu-load-put`, `kvmarm.reset`, `kvmarm.idreg-storage`, `kvmarm.idreg-after-run`, `kvmarm.s2-mmu-struct`, `kvmarm.pgtable-api`, `kvmarm.walker-flags`, `kvmarm.fault-mapping-size`, `kvmarm.pkvm-objects`, `kvmarm.vgic-irq-refs`, `kvmarm.vgic-init-stages`, `kvmarm.timer-contexts`.

## Questions reorganised

- 73 questions became 67, grouped by subject: modes and the hypervisor, first run and
  configuration, running a vCPU, guest system registers, ID registers and traps, stage-2 page
  tables, stage-2 faults, interrupt controller and timer, protected mode, nested virtualisation.
- Merged: `kvmarm.vcpu-init-ioctl` + `kvmarm.vcpu-features` to `kvmarm.vcpu-init`;
  `kvmarm.sysreg-accessors` + `kvmarm.sysreg-location` to `kvmarm.sysreg-access`;
  `kvmarm.idreg-write-check` + `kvmarm.idreg-after-run` to `kvmarm.idreg-writes`;
  `kvmarm.fault-retry` + `kvmarm.fault-mapping-size` to `kvmarm.fault-stale-inputs`;
  `kvmarm.pkvm-page-states` + `kvmarm.pkvm-transitions` to `kvmarm.pkvm-ownership`.
- Dropped: `kvmarm.selftests`, a list of which test covers what that a directory listing gives and
  that no reader was far off on.
- Questions that asked for steps in order or for a structure's fields (`kvmarm.first-run`,
  `kvmarm.run-loop`, `kvmarm.vcpu-load-put`, `kvmarm.reset`, `kvmarm.sysreg-desc`,
  `kvmarm.s2-mmu-struct`, `kvmarm.pgtable-api`, `kvmarm.vcpu-requests`) now ask where the order
  matters, what is final when, and what a reviewer adding to them would get wrong.
