# What the hyp-arm64 measurement found

Three models were asked the 109 questions in `hyp-arm64-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; C
carries the most recent kernel, A is a few releases behind it and B is older
still. Which models they were does not matter here. The hand-written guide was
never checked against current sources, so differences between it and the built
guide are expected and are noted below.

## What all three readers got wrong

- **Guest CPU state is not isolated.** Readers A and B said the host cannot
  read a protected guest's registers. `Documentation/virt/kvm/arm/pkvm.rst`
  marks CPU state isolation unimplemented, and `flush_hyp_vcpu()` and
  `sync_hyp_vcpu()` copy the whole `arch.ctxt` both ways for a protected vCPU.
  Reader C knew the status but left it out of the protection goals.
- **Per-entry flush and sync.** All three said protected and non-protected
  vCPUs get the same copy (reader B had them reversed). A non-protected vCPU's
  context is copied in only when `PKVM_HOST_STATE_DIRTY` is set and only PC and
  PSTATE come back; readers A and C said that flag and
  `handle___pkvm_vcpu_sync_state()` are not in the tree.
- **HCR_EL2 bits taken from the host** are `HCR_TWI | HCR_TWE | HCR_VSE` on
  every entry, for every vCPU; all three left out `HCR_VSE`, and two said
  `sync_hyp_vcpu()` copies `hcr_el2` back, which it does not.
- **Other trap registers.** The host's `mdcr_el2` replaces the value from
  `pvm_init_traps_mdcr()` on every entry, protected or not. Nothing at EL2
  writes a protected vCPU's `arch.fgt`; a non-protected one is copied at load.
- **Debug option names.** CONFIG_PROTECTED_NVHE_STACKTRACE is gone; it is
  `CONFIG_PKVM_STACKTRACE`. Relaxing the host stage-2 on panic, and with it
  file and line for a hyp `BUG()`, is `CONFIG_PKVM_DISABLE_STAGE2_ON_PANIC`,
  not `CONFIG_NVHE_EL2_DEBUG`. There is no CONFIG_PKVM_SELFTESTS. Tracing is
  `CONFIG_NVHE_EL2_TRACING`, which two readers doubted exists.
- **The panic path.** A fault at EL2 under `__kvm_hyp_host_vector` goes
  straight to `hyp_panic()` (or `hyp_panic_bad_stack()`); readers sent it
  through `__guest_exit_panic`, which only `__kvm_hyp_vector` reaches, and
  there only after `kvm_unexpected_el2_exception()` has tried the fixup table.
- **Teardown** is two hypercalls, `__pkvm_start_teardown_vm()` and
  `__pkvm_finalize_teardown_vm()`; all three described one, two of them as
  __pkvm_teardown_vm, and said a busy VM gets -EBUSY (it is -EINVAL). Pages come back through two
  memcaches, only protected VMs use `__pkvm_reclaim_dying_guest_page()`, and
  the dying flag is tested in only four places.
- **Host stage-2 faults.** An already-valid entry gives `-EEXIST`, not
  -EAGAIN, and the fatal case is the `default: BUG()` of a switch.
- **Invalid entries in the host stage-2.** Nobody had the layout: type in bits
  63:60 (`enum kvm_invalid_pte_type`), owner in 3:1, metadata in 59:4 holding
  the VM handle and the gfn. Names offered that do not exist: PKVM_ID_FFA,
  KVM_PGTABLE_S2_NOFWB, KVM_INVALID_PTE_OWNER_MASK.
- **Page states.** All left out `PKVM_POISON`; two used a mask name,
  PKVM_PAGE_STATE_MASK, that is not in the tree.
- **Transitions.** Readers A and C doubted that host-to-guest donation and
  reclaim are upstream; reader B described the removed do_share()/do_donate()
  machinery. None knew `__guest_check_pgtable_memcache()`, the check that lets
  the guest stage-2 map be asserted rather than handled.
- **Protected VM features.** PMU and SVE are refused for a protected VM and
  MTE for every VM; readers said they can be allowed.
- **Hypercall bands.** The markers are `__KVM_HOST_SMCCC_FUNC_MIN_PKVM` and
  `__KVM_HOST_SMCCC_FUNC_PKVM_ONLY`; each reader had the number of bands, a
  marker name or the reason for the `__pkvm_prot_finalize` exception wrong.
- **Sharing with the hypervisor does not map the page at EL2.**
  `hyp_pin_shared_mem()` maps it on the first pin.
- **Host locks around VM creation** are `slots_lock` then `config_lock`.
- **Rules with in-tree exceptions.** "Never return a page to another pool",
  "never write the refcount directly" and "always check `hyp_alloc_pages()`"
  each have correct code that does the opposite (`guest_s2_put_page()`,
  `reclaim_pgtable_pages()`, `host_s2_zalloc_pages_exact()`).

## What readers A and B got wrong as well

- The isolation status: both said guest CPU state isolation is implemented.
- `hpool` backs only the hypervisor's own stage-1 tables.
- The host stage-2 does not start empty: `fix_host_ownership()` maps hyp text
  read-only and annotates the other hyp-owned pages before any fault.
- The host SMC handler refuses a non-zero immediate and ids with the upper 32
  bits set; reader A knew of no such check.
- Non-protected guest operations return -EINVAL from the handlers before the
  inner functions' -EPERM, and the shared-state check is debug-only.
- Without pKVM the host saves its own FP state; `fpsimd_lazy_switch_to_host()`
  restores none and is not called under pKVM.

## What reader B got wrong as well

Reader B's picture is a generation old: `struct hyp_page` with a pool pointer,
host page state kept in stage-2 software bits, zeroed hyp metadata meaning
owned, handles equal to index plus one, a private VA range that grows
downwards, `hyp_alloc_pages()` zeroing on allocation, a per-vCPU lock for
loading, an unsupported hypercall being fatal on the host side, guest sync
traps going to `handle_trap()`. All but two of its answers were more than forty
percent rewritten.

## What the readers already knew

Which file holds what and where to start reading (all three). For readers A
and C: that a handler runs to completion with exceptions masked and that only
cross-CPU concurrency is real, the ticket lock, most of the lock inventory,
what `kern_hyp_va()` does and the shape of the EL2 address space, per-CPU
data, the de-privilege point, hypercall dispatch, the three pools, the
read-once pattern for host memory, and the FF-A feature query.

## Where the hand-written guide is stale

- It lists guest register confidentiality and integrity as guarantees; this
  tree says CPU state isolation is unimplemented.
- It places `pkvm_create_hyp_vm()` in `nvhe/pkvm.c`; that is the host-side
  function in `arch/arm64/kvm/pkvm.c`, and the EL2 one is `__pkvm_init_vm()`.
- It says `__pkvm_init()` and `__pkvm_init_finalise()` run during
  de-privilege, after `kvm_arm_init()`. They run from `init_hyp_mode()`
  inside it, several initcall levels before `finalize_pkvm()`.
- It tells EL2 to translate host addresses with AT S12E1R; the tree uses
  S1E1R, or S1E1A with POE, in `__translate_far_to_hpfar()`.
- "One global pool plus one per protected VM" misses `host_s2_pool`, and every
  hyp VM has a pool, protected or not.
- "EL2 must not allocate from a memcache whose head is in host memory" is
  contradicted by `refill_memcache()`, which is safe because it works on a
  local copy and donates each page first.
- "Reclaim must enumerate pages by ownership metadata, not by a page-table
  walk": the host picks gfns from its own interval tree and EL2 looks each up
  in the guest's stage-2.
- "Undo the mutation on the error path": the transitions check everything
  first and assert the updates; there is no rollback code outside FF-A.
- `is_dying` means teardown has started, not that a VM was marked dead after
  corruption.
- The `BUG()` route is given for the guest vector only, and its count of call
  sites (six, four in `hyp-main.c`, against two of `hyp_panic()`) is now three,
  one and one.
- It says nothing of forced reclaim and poisoned entries,
  `host_share_guest_count`, the block fixmap, hypervisor tracing, reserved VM
  handles or on-demand register sync, and it cites commits by SHA and compares
  with an out-of-tree `__kern_hyp_va()`.

## What was left out of the build set

The build set keeps 70 of the 109 questions. Left out:

- What readers A and C answer well enough and the code shows at a glance:
  `hyp.host-context`, `hyp.percpu-data`, `hyp.stack`, `hyp.spinlock`,
  `hyp.kern-hyp-va`, `hyp.hcall-dispatch`, `hyp.hcall-args`, `hyp.stage1`,
  `hyp.mm-ops`, `hyp.page-order`, `hyp.pool-locking`, `hyp.run-path`,
  `hyp.fp-switch`, `hyp.exit-handlers`.
- What another kept question already covers: `hyp.vectors` and
  `hyp.interrupts` (the panic path), `hyp.panic-report` (the debug options),
  `hyp.pkvm-init` and `hyp.init-memory` (the init sequence),
  `hyp.donated-memory` and `hyp.vm-refcount` (creation and teardown),
  `hyp.pool-foreign-pages` and `hyp.private-range` (the pool and address
  space questions), `hyp.multi-share` (the transitions table), `hyp.vmid`
  (the VM table).
- What is real but narrow, or mostly host-side: `hyp.shared-sources`,
  `hyp.symbol-sharing`, `hyp.library-code`, `hyp.hcall-host-side`,
  `hyp.host-mappings`, `hyp.share-with-hyp`, `hyp.np-guest-ops`,
  `hyp.psci-relay`, `hyp.guest-hvc`, `hyp.pvm-sysregs`, `hyp.at-translation`,
  `hyp.sve-buffers`, `hyp.debug-state`, `hyp.tracing`.

All three readers were weak on several of the last group (tracing, the
host-side mapping tree, protected guest system registers). They were left out
because they did not fit in a guide the size of the one being replaced, and
none changes a verdict as often as what was kept; they are the first to bring
back if the size limit is raised.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 257 corrections, 40% rewritten on average
reader B: 303 corrections, 78% rewritten on average
reader C: 229 corrections, 27% rewritten on average

question                    reader A      reader B      reader C
hyp.core-files               7% ( 1)     12% ( 3)      5% ( 2)
hyp.entry-points             6% ( 1)     18% ( 2)      2% ( 1)
hyp.modes                   27% ( 1)     66% ( 3)     20% ( 3)
hyp.build-namespace         29% ( 5)     80% ( 3)     18% ( 5)
hyp.shared-sources          44% ( 2)     91% ( 2)      9% ( 1)
hyp.symbol-sharing          27% ( 1)     82% ( 1)     41% ( 1)
hyp.library-code            46% ( 2)     86% ( 1)     14% ( 1)
hyp.debug-options           72% ( 4)     81% ( 2)     46% ( 1)
hyp.execution-context       17% ( 3)     66% ( 5)     27% ( 3)
hyp.interrupts              40% ( 2)     67% ( 2)     37% ( 4)
hyp.concurrency             20% ( 1)     44% ( 2)     34% ( 2)
hyp.vectors                 48% ( 1)     86% ( 4)     25% ( 2)
hyp.host-context            14% ( 1)     68% ( 2)     25% ( 2)
hyp.percpu-data             10% ( 1)     80% ( 3)      0% ( 0)
hyp.stack                   33% ( 1)     79% ( 1)     46% ( 1)
hyp.spinlock                20% ( 3)     61% ( 2)      7% ( 1)
hyp.lock-inventory          21% ( 3)     56% ( 3)      8% ( 2)
hyp.lock-order              51% ( 2)     95% ( 3)     51% ( 3)
hyp.bug-warn                26% ( 6)     64% ( 1)     16% ( 1)
hyp.panic-path              58% ( 3)     77% ( 4)     37% ( 3)
hyp.panic-report            48% ( 2)     81% ( 4)     38% ( 2)
hyp.warn-usage              19% ( 1)     93% ( 1)     33% ( 2)
hyp.threat-model            55% ( 4)     72% ( 4)     36% ( 7)
hyp.isolation-status        71% ( 4)     82% ( 5)     17% ( 1)
hyp.init-sequence           41% ( 4)     84% ( 4)      6% ( 2)
hyp.pkvm-init               37% ( 2)     79% ( 3)     15% ( 4)
hyp.deprivilege              2% ( 1)     84% ( 4)      6% ( 1)
hyp.init-predicates         53% ( 3)     83% ( 3)     24% ( 2)
hyp.init-memory             37% ( 2)     84% ( 2)     44% ( 3)
hyp.psci-relay              49% ( 2)     92% ( 3)     21% ( 2)
hyp.hcall-dispatch           5% ( 1)     83% ( 6)     18% ( 1)
hyp.hcall-bands             72% ( 2)     91% ( 3)     36% ( 2)
hyp.hcall-add               35% ( 1)     81% ( 3)     20% ( 3)
hyp.hcall-args              36% ( 1)     83% ( 2)     56% ( 2)
hyp.hcall-host-side         39% ( 1)     91% ( 3)     41% ( 2)
hyp.host-smc                64% ( 3)     81% ( 4)     20% ( 2)
hyp.host-abort              54% ( 5)     86% ( 5)     14% ( 3)
hyp.guest-hvc               29% ( 2)     81% ( 3)     18% ( 1)
hyp.host-inputs             38% ( 4)     83% ( 3)      0% ( 3)
hyp.toctou-usage            19% ( 1)     72% ( 2)     17% ( 1)
hyp.hyp-structs             20% ( 1)     73% ( 2)     35% ( 1)
hyp.pinning                 29% ( 1)     77% ( 2)     57% ( 1)
hyp.memcache                26% ( 1)     79% ( 2)     18% ( 1)
hyp.memcache-usage          36% ( 4)     74% ( 1)     11% ( 2)
hyp.donated-memory          28% ( 4)     94% ( 1)      0% ( 0)
hyp.sysreg-trust            47% ( 2)     93% ( 1)     26% ( 1)
hyp.at-translation          46% ( 1)     72% ( 2)     40% ( 2)
hyp.address-space           14% ( 1)     78% ( 7)     10% ( 1)
hyp.kern-hyp-va             24% ( 1)     84% ( 1)     16% ( 2)
hyp.kern-hyp-va-repeat      51% ( 1)     84% ( 2)     20% ( 2)
hyp.private-range           44% ( 3)     88% ( 2)     39% ( 2)
hyp.hyp-page                37% ( 1)     83% ( 6)      9% ( 1)
hyp.pools                    8% ( 1)     85% ( 1)      0% ( 0)
hyp.pool-api                40% ( 1)     64% ( 4)      9% ( 1)
hyp.pool-locking            37% ( 1)     83% ( 2)     32% ( 1)
hyp.page-order              31% ( 1)     74% ( 2)      0% ( 0)
hyp.pool-foreign-pages      40% ( 1)     88% ( 1)     41% ( 1)
hyp.pool-usage              37% ( 1)     78% ( 3)     59% ( 1)
hyp.fixmap                  40% ( 4)     64% ( 2)     19% ( 2)
hyp.fixmap-usage            48% ( 3)     75% ( 2)     23% ( 1)
hyp.stage1                   5% ( 3)     61% ( 4)     15% ( 3)
hyp.mm-ops                  29% ( 3)     60% ( 3)     10% ( 1)
hyp.page-states             32% ( 4)     85% ( 4)     66% ( 2)
hyp.state-storage            6% ( 1)     84% ( 4)     42% ( 2)
hyp.state-usage             15% ( 1)     82% ( 1)     49% ( 1)
hyp.transitions             47% ( 6)     81% ( 6)     58% ( 3)
hyp.transition-shape        56% ( 2)     87% ( 3)     56% ( 3)
hyp.transition-usage        31% ( 1)     73% ( 2)      0% ( 0)
hyp.range-validation        68% ( 2)     82% ( 3)     36% ( 3)
hyp.host-stage2             55% ( 2)     84% ( 5)     13% ( 4)
hyp.host-annotations        76% ( 5)     88% ( 4)     78% ( 5)
hyp.multi-share             51% ( 2)     74% ( 2)      0% ( 1)
hyp.guest-map-sizes         63% ( 1)     82% ( 1)     16% ( 1)
hyp.np-guest-ops            82% ( 3)     82% ( 1)     17% ( 1)
hyp.host-mappings           52% ( 2)     86% ( 1)     53% ( 3)
hyp.poison                  82% ( 3)     80% ( 2)     56% ( 1)
hyp.reclaim-clearing        56% ( 1)     86% ( 1)     18% ( 1)
hyp.share-with-hyp          48% ( 2)     89% ( 2)     37% ( 1)
hyp.vm-table                53% ( 3)     84% ( 5)      0% ( 1)
hyp.vm-create               72% ( 3)     91% ( 4)     16% ( 4)
hyp.vcpu-create             52% ( 1)     82% ( 4)     15% ( 3)
hyp.vm-refcount             47% ( 2)     84% ( 4)     37% ( 2)
hyp.vcpu-load               61% ( 5)     68% ( 4)     18% ( 5)
hyp.teardown                70% ( 4)     75% ( 4)     50% ( 3)
hyp.vm-features             82% ( 1)     84% ( 3)     43% ( 2)
hyp.run-path                37% ( 4)     85% ( 2)     44% ( 3)
hyp.flush-sync              59% ( 3)     86% ( 3)     68% ( 6)
hyp.load-vs-entry           58% ( 3)     66% ( 1)     47% ( 3)
hyp.dirty-state             83% ( 1)     86% ( 1)     80% ( 1)
hyp.hcr                     55% ( 7)     87% ( 3)     20% ( 3)
hyp.hcr-usage               19% ( 1)     67% ( 1)     22% ( 3)
hyp.trap-init               36% ( 3)     66% ( 4)     22% ( 3)
hyp.exit-handlers           27% ( 3)     89% ( 2)     26% ( 2)
hyp.pvm-sysregs             40% ( 2)     81% ( 3)     42% ( 3)
hyp.fp-switch               20% ( 5)     81% ( 2)     17% ( 5)
hyp.fp-host-state           59% ( 3)     88% ( 3)     21% ( 3)
hyp.fp-usage                24% ( 1)     79% ( 2)     14% ( 2)
hyp.sve-buffers             56% ( 2)     93% ( 3)     33% ( 1)
hyp.debug-state             54% ( 3)     84% ( 3)     39% ( 3)
hyp.switch-order            58% ( 3)     90% ( 3)     23% ( 3)
hyp.vmid                    49% ( 3)     84% ( 3)     31% ( 2)
hyp.ffa-calls               36% ( 2)     78% ( 6)     34% ( 2)
hyp.ffa-descriptor          43% ( 1)     87% ( 3)     32% ( 3)
hyp.ffa-version             32% ( 3)     94% ( 3)     43% ( 1)
hyp.ffa-features             9% ( 1)     72% ( 2)     22% ( 1)
hyp.tracing                 48% ( 5)     87% ( 6)     51% ( 4)
hyp.change-hyp-structs      57% ( 3)     68% ( 1)      0% ( 3)
hyp.change-ownership        50% ( 5)     86% ( 2)      8% ( 1)
hyp.testing                 59% ( 3)     78% ( 2)     48% ( 4)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `hyp.interrupts`, `hyp.hcall-args`, `hyp.vm-refcount`, `hyp.run-path`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `hyp.vectors`, `hyp.spinlock`, `hyp.pkvm-init`, `hyp.hcall-dispatch`, `hyp.donated-memory`, `hyp.kern-hyp-va`, `hyp.pool-locking`, `hyp.exit-handlers`, `hyp.fp-switch`.

## Questions reorganised

- 85 questions became 74, grouped by subject: modes and phases, the EL2 environment, locks, trust,
  host hypercalls and SMCs, memory from the host, hyp VMs and vCPUs, EL2 addresses, the page
  allocator, page ownership state, ownership transitions, entering a guest, floating point, the
  FF-A proxy.
- Merged: `hyp.execution-context` + `hyp.concurrency` + `hyp.interrupts` to `hyp.el2-context`;
  `hyp.vectors` + `hyp.panic-path` to `hyp.el2-exceptions`; `hyp.init-sequence` + `hyp.pkvm-init`
  to `hyp.init-phases`; `hyp.debug-options` + `hyp.testing` to `hyp.debug-and-test`;
  `hyp.hcall-dispatch` + `hyp.hcall-add` to `hyp.hcall-table`; `hyp.state-storage` +
  `hyp.state-usage` to `hyp.state-encoding`; `hyp.transition-shape` + `hyp.transition-usage` to
  `hyp.transition-order`; `hyp.flush-sync` + `hyp.dirty-state` to `hyp.entry-state-copy`;
  `hyp.hcr` + `hyp.hcr-usage` to `hyp.hcr-from-host`.
- Dropped: `hyp.change-ownership`, a checklist whose every item is asked where it belongs (lock
  order, range validation, the order of checks and updates, clearing on reclaim, the selftest).
- Questions that asked for a structure's fields, a function's steps in order or a list of options
  (`hyp.hyp-page`, `hyp.hyp-structs`, `hyp.vcpu-create`, `hyp.pool-api`, `hyp.fixmap`) now ask what
  guards, what is host-controlled and what differs from what a reader expects.
