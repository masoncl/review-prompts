# Questions: ARM64 Architecture Code

- guide: arm64.md
- title: ARM64 Architecture Code

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/arm64-measurement.md` is the
wider set the readers were measured on and `catalogue/arm64-measurement-results.md` says what they
got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## arm64.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## arm64.core-files: Core files

- section: Finding your way
- relevance: 4 - files have been split, merged and moved

A table and nothing else, job to file: exception entry in assembly and in C; the FP/SIMD, SVE
and SME state code and its low-level save and restore routines; MTE; CPU feature detection and
errata; alternatives and instruction patching; the page table helpers; TLB invalidation; the
ASID allocator; the contiguous-PTE code; the early position-independent boot code; the system
register description and its generator. Where a reader is likely to look for a file that does
not exist in this tree, say so in the row. Start from `arch/arm64/kernel/`, `arch/arm64/mm/`
and `arch/arm64/tools/`.

# Exception entry

## arm64.entry-c-sequence: C entry and exit sequence

- section: Exception entry
- relevance: 5 - calling instrumentable code too early or too late is a recurring bug

What does this tree call the C helpers that bracket an exception taken from kernel mode, from user
mode and as an NMI, and which generic entry functions are they built on, where a reader's memory
offers arm64's own enter and exit helpers? What are the requirements for running instrumentable
code or taking another exception inside those sequences in order to assure safe usage? Start from
`arm64_enter_from_kernel_mode()` and `arm64_exit_to_user_mode()`.

## arm64.entry-user-mode-work: User-mode path obligations

- section: Exception entry
- relevance: 5 - a new entry or exit path that leaves a call out corrupts vector state or restartable sequences

What must a path that enters the kernel from user mode, or returns to it, call for vector state
and for restartable sequences, and how does the system call path differ? Start from
`arm64_enter_from_user_mode()` and `arm64_syscall_enter_from_user_mode()`.

## arm64.entry-asm-state: Assembly entry state

- section: Exception entry
- relevance: 4 - every later assumption in C rests on what the assembly set up

By the time a C handler runs, what has the assembly entry switched or saved for an exception
from EL0 that it leaves alone for one from EL1, so that a patch adding per-task state knows
which path needs it? Which of its system register writes share one context synchronisation,
under which capabilities is that barrier present at all, and where must a new write that does
not synchronise itself be placed? Start from `kernel_ventry` and `kernel_entry` in
`arch/arm64/kernel/entry.S`.

## arm64.stack-overflow: Stack overflow detection

- section: Exception entry
- relevance: 3 - the check has to work with no free register and rests on how stacks are aligned

What property of how every kernel stack is allocated and aligned does the overflow check on
exception entry rely on, so that a new stack has to be allocated the same way? Is the check
conditional on a configuration option or on the exception level the exception came from, and
what happens when it fires on the overflow stack itself? Start from `kernel_ventry` and
`handle_bad_stack()`.

## arm64.stacks: Kernel stacks

- section: Exception entry
- relevance: 3 - several stacks, each with its own entry rule

Besides the task stack, which stacks can kernel code find itself on, where is each allocated,
and what does this tree call the helper that says an address is on one, where a reader's memory
offers a test named after each stack? Which of them has a shadow call stack of its own? Start
from `arch/arm64/include/asm/stacktrace.h` and `arch/arm64/kernel/irq.c`.

## arm64.sp-switch-usage: Switching stacks

- section: Exception entry
- relevance: 4 - an exception taken mid-switch finds an inconsistent stack

What are the requirements for code that moves the stack pointer or the shadow call stack pointer
to another stack, in order to assure safe usage? What does `call_on_irq_stack()` mask, and over
which part of the call does it keep it masked? Start from `call_on_irq_stack` in
`arch/arm64/kernel/entry.S`.

## arm64.brk-dispatch: Kernel BRK routing

- section: Exception entry
- relevance: 3 - the registration interface readers remember may be gone

How is a BRK instruction executed by the kernel routed to the code that handles its immediate,
where a reader's memory offers a run-time registration interface, and what does a patch that
adds a new kernel user of BRK therefore have to change? Where are the immediates reserved?
Start from `do_el1_brk64()` and `arch/arm64/include/asm/brk-imm.h`.

# Exception masks

## arm64.daif-helpers: Exception mask helpers

- section: Exception masks
- relevance: 4 - the helpers also touch the interrupt priority mask

What do `local_daif_restore()` and `local_daif_inherit()` do to the interrupt priority mask as
well as to the DAIF bits, and in which order? What are the requirements for calling those two
helpers and `local_daif_mask()` when pseudo-NMIs are enabled, in order to assure safe usage? Start
from `arch/arm64/include/asm/daifflags.h`.

## arm64.handler-masks: Masks while a handler runs

- section: Exception masks
- relevance: 4 - decides what can interrupt a handler

A table of handler kind against what it leaves masked while it runs, and so what can interrupt
it: a synchronous exception from EL1, an IRQ or FIQ, an SError, a debug exception from EL1, and
entry from EL0. Then what the table cannot show: which handlers inherit the mask of the context
they interrupted and which set a fixed one. Start from `el1_abort()`, `el1_interrupt()` and
`el1h_64_error_handler()`.

## arm64.pmr-masking: Interrupt priority masking

- section: Exception masks
- relevance: 4 - two masking schemes coexist and the flags value differs

When pseudo-NMIs are enabled, what does masking and unmasking interrupts write and to which
register, and what does a saved flags value or the copy in `struct pt_regs` then hold? What are
the requirements for testing a flags value or a `struct pt_regs` for masked interrupts, in order
to assure safe usage under both masking schemes? Start from `arch/arm64/include/asm/irqflags.h`,
`GIC_PRIO_IRQON` and `GIC_PRIO_PSR_I_SET`.

## arm64.pmr-sync-usage: Priority mask synchronisation

- section: Exception masks
- relevance: 3 - the barrier is needed in one direction only

After which writes of the interrupt priority mask is `pmr_sync()` needed and after which is it
not, what is it, and what makes it disappear on some systems? Name in-tree code for both cases.

# Syndromes

## arm64.esr-fields: ESR fields and ISS2

- section: Syndromes
- relevance: 4 - every decode and every synthesised syndrome rests on the layout

Where are the fields of an exception syndrome value named, and where is the second syndrome
field that lies above bit 31? For data and instruction aborts, which ISS and ISS2 fields hold
anything only when another bit is set, and which bit? Start from
`arch/arm64/include/asm/esr.h`, `ESR_ELx_ISV` and `ESR_ELx_FnV`.

## arm64.esr-iss-usage: Reading ISS fields

- section: Syndromes
- relevance: 4 - the same ISS bit means different things under different classes

What are the requirements for reading a field of the ISS with one of the field macros of
`arch/arm64/include/asm/esr.h` in order to assure safe usage? Name in-tree code that meets them,
and code that reads the same ISS bits under two exception classes. Start from `ESR_ELx_EC()`.

## arm64.esr-il-synthesis: Syndromes built in software

- section: Syndromes
- relevance: 4 - a wrong IL bit gives a syndrome hardware would never write

What are the requirements for the `ESR_ELx_IL` bit of a syndrome that software builds or rewrites,
in order to assure safe usage, for an exception that KVM injects into a guest and for the syndrome
that `set_thread_esr()` reports to user space with a signal? Start from the users of `ESR_ELx_IL`
in `arch/arm64/kvm/` and `set_thread_esr()`.

## arm64.esr-eret-fpac: ERET trap and FPAC syndromes

- section: Syndromes
- relevance: 3 - the two ISS layouts are confused with each other

What do the ISS bits of a trapped exception-return instruction mean? When an emulated
authenticated exception return fails, what is kept from the trapped syndrome in the pointer
authentication failure syndrome that is built, and under what conditions is that exception
injected at all and what happens otherwise? Start from `ESR_ELx_ERET_ISS_ERET` and
`kvm_emulate_nested_eret()`.

# System register definitions

## arm64.sysreg-accessors: Accessor macros

- section: System register definitions
- relevance: 4 - the wrong accessor assembles to the wrong thing or not at all

When must the `read_sysreg_s()` and `write_sysreg_s()` forms be used in place of
`read_sysreg()` and `write_sysreg()`, and what goes wrong with the plain form? What does
`sysreg_clear_set()` skip, and why does that matter for a register whose write has a side
effect? Why does the hypervisor configuration register have a write macro of its own? Start
from the end of `arch/arm64/include/asm/sysreg.h`.

## arm64.fixed-register-insn: XZR and no-operand instructions

- section: System register definitions
- relevance: 3 - a constraint alone lets the compiler pick the wrong register

How does the tree emit a system instruction whose register operand must be the zero register, or
that takes no operand? What are the requirements for the inline assembly operand of such an
instruction in order to assure safe usage? Start from `write_sysreg_s()`, `__TLBI_0` and
`gic_insn()`.

## arm64.sysreg-file-format: Register description file

- section: System register definitions
- relevance: 4 - new registers must be described here, not by hand

A new register is described in `arch/arm64/tools/sysreg` and not by hand in a header. A table
of each kind of field line the file accepts against the macros the generator emits for it, so
that a reader can predict the name to use. Then: which helpers build or extract a field from
those names, and what may a description not leave undescribed? Start from the comment at the
top of the file and `define_field` in `arch/arm64/tools/gen-sysreg.awk`.

## arm64.sysreg-resx: Reserved-bit masks

- section: System register definitions
- relevance: 4 - the value changes silently when the description changes

How are the RES0, RES1 and UNKN masks of a register computed, and what is a mask's value when
the description has no line of that kind? Where does the tree record, and how does it mark, a
bit that behaves as reserved only when some feature is not implemented, which the generator
does not know about? Start from `arch/arm64/tools/gen-sysreg.awk` and `arch/arm64/kvm/config.c`.

## arm64.sysreg-mask-consumers: Consumers of generated masks

- section: System register definitions
- relevance: 4 - neither the compiler nor a test notices the change

What C and assembly code builds a register value, or the set of bits that need describing, out
of a generated RES0 or RES1 mask, so that editing a register's description changes it with no
warning? What does someone editing a description have to check as a result, and what in the
tree complains at run time about a bit nobody covered? Start from `SCTLR_EL2_RES1`,
`INIT_SCTLR_EL2_MMU_ON` and `check_feature_map()`.

# Context synchronisation

## arm64.isb-after-write-usage: Register writes needing an ISB

- section: Context synchronisation
- relevance: 5 - both the missing barrier and the needless one get reported

What are the requirements for following a system register write with an `isb()`, and for leaving
the `isb()` out, in order to assure safe usage? Name in-tree code that issues the barrier and code
that leaves it out, for example around `update_sctlr_el1()`, `__mte_enable_kernel()`,
`cpu_enable_pan()` and the trap configuration in `arch/arm64/include/asm/el2_setup.h`.

## arm64.self-sync-writes: Writes that need no barrier

- section: Context synchronisation
- relevance: 4 - reviewers ask for barriers the code deliberately omits

Which system register writes does the tree deliberately not follow with an `isb()` because it
treats the write as synchronising itself, and what comment or code shows it for each? Start from
`task_fpsimd_load()`, `vec_probe_vqs()`, `local_daif_restore()` and
`arch/arm64/kernel/proton-pack.c`.

## arm64.sctlr-init: Initial SCTLR values

- section: Context synchronisation
- relevance: 3 - decides whether exception entry and return synchronise context

Do the initial `SCTLR_EL1` and `SCTLR_EL2` values, with the MMU on and with it off, set the bits
that make exception entry and exception return context synchronising, and does each value get
them by naming them or from a generated reserved-bit mask? What may code that runs under each
value therefore assume about an exception return standing in for an `isb()`? Start from
`INIT_SCTLR_EL1_MMU_ON`.

## arm64.readback-usage: Reading a register back

- section: Context synchronisation
- relevance: 3 - a read-back says the value was stored, not that it took effect

What does reading a system register back straight after writing it, with no `isb()` between the
two, guarantee about the value that is read? What does this tree use such a read-back to find out?
Name two places that do it.

# CPU capabilities

## arm64.cap-check-helpers: Testing a capability

- section: CPU capabilities
- relevance: 5 - the wrong helper reads a bit that is not final yet, or patches nothing

Which of `cpus_have_cap()`, `cpus_have_final_cap()`, `cpus_have_final_boot_cap()`,
`alternative_has_cap_likely()`, `alternative_has_cap_unlikely()` and `this_cpu_has_cap()` is
used when: when may each be called, and what does each do or return before capabilities are
finalised? Which one do helpers such as `system_supports_sve()` use?

## arm64.cpucap-types: Capability scopes and types

- section: CPU capabilities
- relevance: 4 - the type decides what happens on a late or mismatched CPU

A table of the combined capability types the tree defines for features and for errata: for
each, its scope, whether a late CPU may have it when the system does not, and whether it may
lack it when the system has it. Then what happens to a CPU that breaks its type's rule. Start
from `ARM64_CPUCAP_SCOPE_LOCAL_CPU` in `arch/arm64/include/asm/cpufeature.h`.

## arm64.idreg-sanitisation: ID register sanitisation

- section: CPU capabilities
- relevance: 4 - a new ID field that is not described is hidden or taints

What happens to an ID register field that has no entry in the feature tables, or whose entry
is strict or not visible, when CPUs differ in it and when user space reads the register? What
must a patch that starts to use a new ID field therefore add, and where can the command line
override a field? Start from `struct arm64_ftr_bits`, `read_sanitised_ftr_reg()` and
`arch/arm64/kernel/pi/idreg-override.c`.

## arm64.add-cap-or-erratum: Adding a feature or erratum

- section: CPU capabilities
- relevance: 4 - several files have to change together and some are checked by nothing

What has to change together when a patch adds a CPU feature capability or an erratum workaround,
and which of those places does neither the compiler nor a boot test check? Start from
`arch/arm64/tools/cpucaps`, `arm64_features` in `arch/arm64/kernel/cpufeature.c` and
`arm64_errata` in `arch/arm64/kernel/cpu_errata.c`.

## arm64.alternatives: Alternatives patching

- section: CPU capabilities
- relevance: 4 - the replacement runs from a different address than it was assembled at

What may the replacement instructions of an alternative not contain, given where they are
assembled and where they end up running, and what does the patching code fix up for them? What
does `ALTERNATIVE_CB()` require of its callback? Start from
`arch/arm64/include/asm/alternative-macros.h` and `__apply_alternatives()`.

## arm64.alternatives-timing: Points of alternative patching

- section: CPU capabilities
- relevance: 4 - code that runs before its alternative is applied executes the unpatched instructions

When is each kind of alternative applied, for the boot CPU, for the whole system and for a module,
and what are the requirements for code that runs before that point, in order to assure safe usage?
Start from `apply_boot_alternatives()`, `apply_alternatives_all()` and
`apply_alternatives_module()`.

## arm64.el2-setup: Early EL2 setup

- section: CPU capabilities
- relevance: 4 - a feature that traps by default needs enabling here

A feature that traps to EL2 by default has to be enabled there before EL1 can use it. Where does a
patch add that enable so that every boot path that enters at EL2 runs it, and which registers does
`init_el2_state` leave to another step? What does `finalise_el2` require of the state it finds
when it moves the kernel to EL2? Start from `init_el2_state`, `finalise_el2` and
`arch/arm64/kernel/hyp-stub.S`.

# Patching and cache maintenance

## arm64.insn-patching-api: Instruction patching functions

- section: Patching and cache maintenance
- relevance: 4 - the variants differ in what they synchronise

A table of the functions that write instructions into kernel or module text, to choose
between: what cache maintenance each does and whether it makes other CPUs resynchronise. Then
what they share: how the target is mapped for writing and under which lock. Which of them do
kprobes arm and disarm with? Start from `arch/arm64/kernel/patching.c`.

## arm64.patching-sync-usage: Other CPUs and patched code

- section: Patching and cache maintenance
- relevance: 4 - the write is visible before other CPUs are guaranteed to fetch it

What are the requirements for modifying an instruction that another CPU may be executing, in order
to assure safe usage? How do the jump label code and the alternatives code each meet them? Start
from `arch/arm64/kernel/patching.c`.

## arm64.cache-maint-names: Cache maintenance routines

- section: Patching and cache maintenance
- relevance: 3 - the routines were renamed to say what they do

What does this tree call the routines that clean or invalidate the caches by virtual address,
where a reader's memory offers names that say less, and to which point does each operate? Which
is to be used after writing instructions, which for non-coherent DMA and which for persistent
memory? Start from the comment in `arch/arm64/include/asm/cacheflush.h`.

# Page table entries

## arm64.pte-bits: Software and hardware PTE bits

- section: Page table entries
- relevance: 4 - dirty and writable are encoded across three bits

How are writable and dirty encoded across an entry's bits with and without hardware management
of the dirty state, so that testing one bit alone gives the wrong answer? How does the tree
tell a present-but-inaccessible entry from a swap entry, and what does it call that bit and the
userfaultfd bit, where a reader's memory offers other names? Start from the table above
`__check_safe_pte_update()` and `arch/arm64/include/asm/pgtable-prot.h`.

## arm64.ptep-accessors: Public and private PTE accessors

- section: Page table entries
- relevance: 4 - arch code that uses the public name recurses or folds when it must not

What is the difference between `ptep_get()`, `set_ptes()` and the other public accessors and
their double-underscore forms, and which must code under `arch/arm64/mm/` use for kernel
mappings and inside the contiguous-PTE implementation? What goes wrong with the other one?

## arm64.pte-setters: Writing an entry

- section: Page table entries
- relevance: 4 - the barrier is conditional on what is being written

After a store to a page table entry, for which new values are barriers issued and which barriers,
and which of `__set_pte()`, `__set_pte_nosync()` and `__set_pte_complete()` is used when? What
does `__set_ptes_anysz()` do before it stores an entry that maps user memory? Start from
`__set_ptes_anysz()`.

## arm64.pte-barrier-batching: Deferred PTE barriers

- section: Page table entries
- relevance: 4 - the deferral is unsafe where it cannot be flushed

When are the barriers after a kernel page table update deferred, and what is guaranteed if the
task is preempted or interrupted before the deferred barriers are issued? What are the
requirements for code that accesses a kernel mapping it has just written, in order to assure safe
usage? Start from `queue_pte_barriers()` and `is_lazy_mmu_mode_active()`.

## arm64.pgtable-config: Levels and folding

- section: Page table entries
- relevance: 4 - levels can be folded at run time, not only at build time

Which page table levels can be folded at run time and not only at build time, and what decides it?
What does `lpa2_is_enabled()` guarantee about the levels in use? Start from `pgtable_l4_enabled()`
and `pgtable_l5_enabled()`.

## arm64.contpte-fold: Contpte folding and unfolding

- section: Page table entries
- relevance: 4 - the sequence is a break-before-make on sixteen entries

What sequence of clears, invalidation and stores does converting a range of PTEs to or from a
contiguous mapping perform, what does it preserve of the access and dirty bits of the entries,
and which step is skipped on hardware that tolerates the change? What decides that a range is
folded or unfolded at all? Start from `contpte_convert()` and `__contpte_try_fold()`.

## arm64.lockless-read: Reading entries without the lock

- section: Page table entries
- relevance: 4 - a plain dereference can be torn, and a contiguous block can change under the reader

What are the requirements for reading a page table entry without holding the page table lock, at
the PTE level and at the higher levels, in order to assure safe usage? How does
`contpte_ptep_get_lockless()` cope with an entry that is part of a contiguous block being folded
or unfolded, and how do `pud_offset_lockless()` and `p4d_offset_lockless()` cope with a level that
is folded at run time? Start from `contpte_ptep_get_lockless()` and `pud_offset_lockless()`.

# TLB invalidation

## arm64.tlb-api: Invalidation functions

- section: TLB invalidation
- relevance: 5 - each function differs in scope, walk-cache handling and barriers

A table of the TLB invalidation functions to choose between: scope, whether walk-cache entries
go too, and whether the function waits for completion. Say which functions a reader would look
for and not find, and what does their job now. What does the kernel-range function leave behind
that another function exists to drop? Start from the comment in
`arch/arm64/include/asm/tlbflush.h`.

## arm64.tlb-flags: Invalidation flags

- section: TLB invalidation
- relevance: 5 - the flags replace several older function variants

What flags can be passed to `__flush_tlb_range()` and `__flush_tlb_page()`, what does each
change, and which combination is refused and how? Name one caller of each flag. If this tree
has no such flags, say so and stop.

## arm64.tlb-barrier-template: Barriers around invalidation

- section: TLB invalidation
- relevance: 5 - a missing or misplaced barrier leaves a stale translation in use

What barrier must precede a TLB invalidation instruction and what must follow it, and when is an
`isb()` needed as well? What do the helpers that wrap the completing barrier do besides the
barrier? Start from `__tlbi_sync_s1ish()` and `flush_tlb_kernel_range()`.

## arm64.tlb-operands: Invalidation operands

- section: TLB invalidation
- relevance: 4 - a wrong level hint or granule means nothing is invalidated

What are the requirements for the operands of the invalidations that `__flush_tlb_range_op()`
issues, in order to assure safe usage? When is the level hint left out, and what limits how many
operations are issued before the whole address space is invalidated? Start from
`__tlbi_level_asid()`, `__tlbi_range()` and `__flush_tlb_range_op()`.

# Break-before-make

## arm64.bbm-usage: Replacing a live entry

- section: Break-before-make
- relevance: 5 - skipping the invalidation can raise a TLB conflict abort

What are the requirements for replacing a valid translation table entry with a different valid one
in order to assure safe usage? Name in-tree code that meets them in full, code that changes a live
entry in place, and code that relies on a CPU capability to leave a step out. Start from
`contpte_convert()` and `__ptep_set_access_flags()`.

## arm64.bbm-safe-changes: Changes allowed without break-before-make

- section: Break-before-make
- relevance: 5 - says which live updates need the invalid step and which do not

Which changes to a valid entry does the tree treat as safe without going through an invalid
entry, which does it reject, and which debug checks enforce that? Start from
`pgattr_change_is_safe()` and `__check_safe_pte_update()`.

## arm64.bbm-level: BBM level capability

- section: Break-before-make
- relevance: 5 - the capability has been renamed and its detection is unusual

What does this tree call the capability that says block and page sizes can be changed without
an intermediate invalid entry, where a reader's memory offers another name, and how is it
detected? Which changes does it cover and which not, and what happens to a secondary or late
CPU that lacks it? Start from `arch/arm64/tools/cpucaps`, `split_kernel_leaf_mapping()` and
`force_pte_mapping()`.

## arm64.kernel-mapping-changes: Changing kernel mappings

- section: Break-before-make
- relevance: 4 - the linear map may be mapped with blocks

Which address ranges do `set_memory_ro()` and its relatives accept, and what do they do when
given anything else? When is the linear alias changed as well, and what makes it safe to change
part of a block or contiguous mapping of the linear map? Start from `change_memory_common()`
and `can_set_direct_map()`.

# Tagged addresses and MTE

## arm64.untagged-addr: Tag removal helpers

- section: Tagged addresses and MTE
- relevance: 4 - the helper keeps kernel addresses intact by design

What does `untagged_addr()` do to a user address and to a kernel address, does it depend on the
task's tagged-address setting, and how does it differ from `__tag_reset()`? How do `access_ok()`
and `mm_untag_mask()` treat a tagged user pointer? Start from
`arch/arm64/include/asm/memory.h` and `arch/arm64/include/asm/uaccess.h`.

## arm64.untag-usage: Arithmetic on user addresses

- section: Tagged addresses and MTE
- relevance: 4 - the MMU ignores the top byte, software arithmetic does not

What are the requirements for using a user-supplied address in a comparison or a VMA lookup when
it may carry a tag, in order to assure safe usage? Name in-tree code that calls `untagged_addr()`
before such a use, and say where generic code is expected to have called it.

## arm64.mte-page-flags: Page tag state flags

- section: Tagged addresses and MTE
- relevance: 5 - two racing initialisers must not both clear tags

What protocol lets exactly one of several racing callers initialise a page's tags, what do the
losers do, and what ordering do the helpers give between the tag stores and the flag that says
they are done? Is that flag ever cleared, and how do hugetlb folios differ? Start from
`try_page_mte_tagging()` and `set_page_mte_tagged()`.

## arm64.mte-sync-tags: Tag initialisation at mapping time

- section: Tagged addresses and MTE
- relevance: 4 - the condition is on the PTE, not the VMA

When an entry is installed, under what conditions on the new PTE are the page's tags
initialised, and what orders that before the entry becomes visible: which barrier, and where?
Start from `__sync_cache_and_tags()` and `mte_sync_tags()`.

## arm64.mte-tag-init-usage: Making a tagged page visible

- section: Tagged addresses and MTE
- relevance: 5 - user space can map the page between the flag and the tags

What are the requirements for initialising the tags of a page that other observers can reach, in
order to assure safe usage? In what order does in-tree code write the tags, set the flag that says
the tags are valid and publish the page? Start from `copy_highpage()`, `arch_swap_restore()`,
`tag_clear_highpages()` and `memcmp_pages()`.

# FP, SVE and SME state

## arm64.fp-state-format: Saved state format

- section: FP, SVE and SME state
- relevance: 5 - the wrong buffer is stale by definition

What says which of a task's saved FP/SIMD, SVE and SME buffers is valid, and what do `TIF_SVE` and
`TIF_SME` mean beyond that? What is the `to_save` field of `struct cpu_fp_state` for? Start from
`enum fp_type`, `struct cpu_fp_state` and the comment above `task_fpsimd_load()`.

## arm64.fp-state-tracking: Lazy state tracking

- section: FP, SVE and SME state
- relevance: 5 - decides whether registers or memory hold the truth

What has to be true for a task's FP state to be live in this CPU's registers, going by
`TIF_FOREIGN_FPSTATE`, the per-CPU `fpsimd_last_state` and the task's `fpsimd_cpu`? Which of
those must code that changes a task's saved state invalidate, and how does KVM take part?
Start from the comment at the top of `arch/arm64/kernel/fpsimd.c`.

## arm64.fp-context-ownership: FPSIMD context ownership

- section: FP, SVE and SME state
- relevance: 4 - softirqs may use the registers too

What must code hold while it manipulates a task's FP state or `TIF_FOREIGN_FPSTATE`, what does
taking it do on a preemptible-RT kernel and with interrupts already disabled, and how do the
functions that assume the caller holds it say so? Start from `get_cpu_fpsimd_context()`.

## arm64.kernel-neon: Kernel-mode SIMD

- section: FP, SVE and SME state
- relevance: 5 - the interface takes an argument older code did not pass

What do `kernel_neon_begin()` and `kernel_neon_end()` require of their argument and of the context
they are called from, and what does `scoped_ksimd()` do for a caller? Start from
`arch/arm64/include/asm/simd.h`.

## arm64.kernel-neon-preemption: Preemption inside kernel-mode SIMD

- section: FP, SVE and SME state
- relevance: 5 - decides whether a long SIMD section has to yield and when a caller must fall back to scalar code

What do `kernel_neon_begin()` and `kernel_neon_end()` guarantee about preemption between the two
calls, and what does `may_use_simd()` check? Start from `kernel_neon_begin()` in
`arch/arm64/kernel/fpsimd.c`.

## arm64.fp-syscall: Vector state across system calls

- section: FP, SVE and SME state
- relevance: 4 - part of the ABI

Which vector state is discarded and which kept when a task makes a system call, how is that
done without saving registers, and what undoes it on the way out? Say what happens to `TIF_SVE`
and to streaming mode. Start from `fpsimd_syscall_enter()`.

## arm64.vl-change-state: Changing the vector length

- section: FP, SVE and SME state
- relevance: 5 - state sized for the old length must not survive, and stale data reappears at the new width

What does `vec_set_vector_length()` guarantee about a task's saved and live vector state once it
has changed the SVE or SME vector length, and what does it leave alone when only the length for
the next exec is changed? What are the requirements for code that changes a vector length or
switches streaming mode on behalf of a task, in order to assure safe usage? Start from
`vec_set_vector_length()` and `change_live_vector_length()`.

## arm64.sme-state: SME streaming mode and ZA

- section: FP, SVE and SME state
- relevance: 4 - two independent enables with different lifetimes

Which state does each of the SME enables make valid? What does entering or leaving streaming mode
do to the vector registers, and what does `task_smstop_sm()` change? Start from
`thread_sm_enabled()`, `sme_alloc()` and `task_smstop_sm()`.

## arm64.fp-signal: Signal frame records

- section: FP, SVE and SME state
- relevance: 4 - restore must accept every layout save can produce

On signal return, how are the SVE and FP/SIMD records of the frame combined, what is rejected,
and what is required of a streaming-mode record? When is each FP-related record present in a
frame that the kernel writes, so that restore accepts every layout save can produce? Start from
`restore_sve_fpsimd_context()` and `setup_sigframe_layout()`.

# Faults and user access

## arm64.fault-handling: Page fault handling

- section: Faults and user access
- relevance: 4 - permission checks are derived from the syndrome

How does the page fault handler turn a syndrome into the access it checks against the VMA, and
when does a kernel fault on a user address die at once and when does it go on to the exception
table? From what does the handler decide that a fault is a protection key fault or a guarded
control stack fault? Start from `do_page_fault()`, `is_el1_permission_fault()` and `fault_info`.

## arm64.uaccess: User access primitives

- section: Faults and user access
- relevance: 4 - what may run between enable and disable is restricted

What must not happen between enabling and disabling user access, how is user memory kept out
of reach the rest of the time on hardware with and without the privileged-access-never
feature, and how is a user pointer sanitised against speculation? Start from
`uaccess_ttbr0_enable()`, `__uaccess_mask_ptr()` and `__raw_get_user()`.

# Model gaps

## arm64.model-gaps: Other mistakes models make

- drafts: all
- relevance: 5 - a model that is told how it is wrong can correct for it

Going by what each reader said from memory for every question in this guide, which is given
below, what do models believe about this code that is wrong in this tree? One bullet per mistake:
the belief, put plainly as a model would hold it, then what is true here and where to see it.
Cover names that are gone and what does the job now, numbers and limits that have changed,
behaviour that has changed, rules the readers state more broadly than the code supports, and what
is new that none of them knew. Most consequential first: a belief that would make a reviewer
approve a bug or reject correct code comes before a file that moved. Leave out what the readers
had right, and a slip only one of them made that the others show is not a belief. One or two lines to
a bullet: the belief and the truth. Every section of this guide already corrects what models
get wrong about its subject, and what a section covers is taken out of this list afterwards, so what
matters most here is what no question above asks about.
