# Questions: ARM64 (measurement set)

- guide: arm64.md
- title: ARM64 Architecture Code

A wide set of questions about the arm64 architecture code (`arch/arm64/`
outside KVM), used to measure what a model already knows before deciding what
the built guide should spend its words on. The hand-written guide it will
replace is 4,420 words and was never checked against current sources. KVM, the
hypervisor code and the GIC drivers have their own guides. The answers have to
come from the tree, so a question about an architectural rule asks how the tree
encodes or relies on it, not what the architecture manual says. Format:
`../../../docs/subsystem-questions.md`.

# Finding your way

## arm64.core-files: Core files

- section: Finding your way
- relevance: 4 - files have been split, merged and moved
- words: 120

Which files hold exception entry (assembly and C), the FP/SIMD, SVE and SME
state code, MTE, CPU feature detection and errata, alternatives and instruction
patching, the page table helpers, TLB invalidation, the ASID allocator, the
contiguous-PTE code, the early position-independent boot code, and the system
register description and its generator? A table. Start from
`arch/arm64/kernel/`, `arch/arm64/mm/` and `arch/arm64/tools/`.

## arm64.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 110

For each job (a synchronous exception from EL1, one from EL0, an IRQ, a system
call, a data abort, a context switch, bringing up a secondary CPU, finalising
CPU capabilities), which function do you start reading from? A table. Start
from `arch/arm64/kernel/entry-common.c`.

## arm64.docs: Authoritative documentation

- section: Finding your way
- relevance: 3 - several ABI rules are written down only there
- words: 70

Which files under `Documentation/arch/arm64/` are the authority on the boot
protocol, ELF hwcaps, the ID registers visible to user space, SVE, SME, MTE,
tagged addresses, GCS and silicon errata?

## arm64.selftests: Selftests

- section: Finding your way
- relevance: 3 - says which test covers a change
- words: 70

What is in each directory under `tools/testing/selftests/arm64/`, and which
programs there exercise FP/SVE/SME state across context switches, ptrace and
signals?

# Exception syndromes

## arm64.esr-layout: Syndrome register layout

- section: Exception syndromes
- relevance: 4 - every decode and every synthesised syndrome rests on it
- words: 70

How is an `ESR_ELx` value divided into fields, at which bits, and which macros
name each field, including the second syndrome field above bit 31? Start from
`arch/arm64/include/asm/esr.h`.

## arm64.esr-abort-iss: Abort syndrome fields

- section: Exception syndromes
- relevance: 4 - bit positions are misremembered
- words: 100

For data and instruction aborts, which ISS and ISS2 fields does the tree define,
at which bits, and which of them are only valid when another bit is set? A
table. Start from `ESR_ELx_ISV` and `ESR_ELx_FnV`.

## arm64.esr-fsc-helpers: Fault status predicates

- section: Exception syndromes
- relevance: 3 - open-coded comparisons miss the level bits and the negative levels
- words: 80

Which helpers classify the fault status code of an abort (translation,
permission, access flag, address size, external abort on a walk), what range of
levels does each accept, and how are levels below zero encoded? Start from
`esr_fsc_is_translation_fault()`.

## arm64.esr-il-synthesis: Syndromes built in software

- section: Exception syndromes
- relevance: 4 - a wrong IL bit gives a syndrome hardware would never write
- words: 100

Where does code build or rewrite an `ESR_ELx` value in software (for an
exception injected into a guest, and for the syndrome reported to user space
with a signal), and what does each of those places do with the instruction
length bit? Start from the users of `ESR_ELx_IL` in `arch/arm64/kvm/` and
`set_thread_esr()`.

## arm64.esr-eret-fpac: ERET trap and FPAC syndromes

- section: Exception syndromes
- relevance: 3 - the two ISS layouts are confused with each other
- words: 100

What do the ISS bits of a trapped exception-return instruction mean, which
helpers test them, and how is the syndrome for a pointer authentication failure
built when an emulated authenticated exception return fails? Start from
`ESR_ELx_ERET_ISS_ERET` and `kvm_emulate_nested_eret()`.

## arm64.esr-iss-usage: Reading ISS fields

- section: Exception syndromes
- relevance: 4 - the same ISS bit means different things under different classes
- words: 90

What usage of an ISS field macro is unsafe because the exception class has not
been established, and what that looks similar is correct? Name in-tree code
that checks the class before the field, and code that reuses ISS bits across
two classes correctly.

## arm64.brk-dispatch: BRK immediates

- section: Exception syndromes
- relevance: 3 - the registration interface readers remember may be gone
- words: 90

How is a `BRK` exception taken from the kernel routed to its handler: which
immediates are reserved for which user (BUG, CFI, KASAN, UBSAN, kprobes, kgdb),
and is there a run-time registration interface for handlers? Start from
`do_el1_brk64()` and `arch/arm64/include/asm/brk-imm.h`.

# Exception entry and return

## arm64.vector-entry-asm: Assembly entry work

- section: Entry assembly
- relevance: 4 - every later assumption in C rests on what this set up
- words: 120

In order, what do the vector stub and the register-save macro do before the C
handler runs for an exception from EL0, and which steps are skipped for one
from EL1? Cover the stack check, where `current` is kept, pointer
authentication keys, MTE, the speculative store bypass state, the interrupt
priority mask and the frame record. Start from `kernel_ventry` and
`kernel_entry` in `arch/arm64/kernel/entry.S`.

## arm64.entry-isb: Synchronising entry-time register writes

- section: Entry assembly
- relevance: 3 - someone adding a register write has to put it in the right place
- words: 70

On entry from EL0, which system register writes share one context
synchronisation, under which capabilities is that barrier present, and where
must a new register write that is not self-synchronising be placed? Start from
`kernel_entry`.

## arm64.kpti-trampoline: Kernel unmapped at EL0

- section: Entry assembly
- relevance: 3 - touches vectors, ASIDs and TLB invalidation at once
- words: 100

When the kernel is unmapped while user space runs, how do exceptions get in and
out: which vectors are used, which registers are scratch, how are the two
ASIDs of a process related, and what do the TLB invalidation helpers do
differently? Start from `tramp_ventry`, `arm64_kernel_unmapped_at_el0()` and
`USER_ASID_FLAG`.

## arm64.entry-c-sequence: C entry and exit sequence

- section: Entry in C
- relevance: 5 - calling instrumentable code too early or too late is a recurring bug
- words: 120

In the C entry code, what is the order of operations on entry from kernel mode
and from user mode and on the way back out, and before and after which calls is
it unsafe to run instrumentable code or take an exception? Say which functions
an older kernel had for this that are no longer there. Start from
`arm64_enter_from_kernel_mode()` and `arm64_exit_to_user_mode()`.

## arm64.daif-helpers: Exception mask helpers

- section: Entry in C
- relevance: 4 - the helpers also touch the interrupt priority mask
- words: 100

What do `local_daif_mask()`, `local_daif_save()`, `local_daif_restore()` and
`local_daif_inherit()` each do, including to the interrupt priority mask, and
what do the `DAIF_PROCCTX`, `DAIF_PROCCTX_NOIRQ`, `DAIF_ERRCTX` and `DAIF_MASK`
constants stand for? A table.

## arm64.handler-masks: Masks set by each handler

- section: Entry in C
- relevance: 4 - decides what can interrupt a handler
- words: 90

Which exceptions does each kind of handler leave masked while it runs: a
synchronous exception from EL1, an IRQ or FIQ, an SError, a debug exception
from EL1, and entry from EL0? Start from `el1_abort()`, `el1_interrupt()` and
`el1h_64_error_handler()`.

## arm64.nmi-paths: Paths treated as NMI

- section: Entry in C
- relevance: 3 - NMI context limits what the handler may call
- words: 80

Which entry paths are accounted as NMIs rather than ordinary interrupts or
exceptions, and how is an interrupt taken with interrupts masked told apart
from a normal one? Start from the callers of `irqentry_nmi_enter()` in
`arch/arm64/kernel/entry-common.c`.

## arm64.pmr-masking: Interrupt priority masking

- section: Entry in C
- relevance: 4 - two masking schemes coexist and the flags value differs
- words: 110

When pseudo-NMIs are enabled, how are interrupts masked and unmasked, what
values does the priority mask register take and what does each mean, how is
that reflected in saved flags and in `pt_regs`, and which helper tells the two
schemes apart? Start from `arch/arm64/include/asm/irqflags.h`,
`GIC_PRIO_IRQON` and `GIC_PRIO_PSR_I_SET`.

## arm64.pmr-sync-usage: Priority mask synchronisation

- section: Entry in C
- relevance: 3 - the barrier is needed in one direction only
- words: 80

After which writes of the interrupt priority mask is `pmr_sync()` needed and
after which is it not, what instruction is it, and when is it patched out? Name
in-tree code for both cases.

## arm64.stacks: Kernel stacks

- section: Stacks
- relevance: 4 - several stacks, each with its own entry rule
- words: 110

Which stacks can kernel code run on (task, IRQ, overflow, SDEI, EFI), how big
is each and where is it allocated, which helper says whether an address is on
a given stack, and which shadow call stack goes with each? A table. Start from
`arch/arm64/include/asm/stacktrace.h` and `arch/arm64/kernel/irq.c`.

## arm64.stack-overflow: Stack overflow detection

- section: Stacks
- relevance: 3 - the check has to work with no free register
- words: 80

How is a kernel stack overflow detected on exception entry, what alignment
property of the stacks does the check rely on, and what happens after it
fires? Start from `kernel_ventry` and `handle_bad_stack()`.

## arm64.sp-switch-usage: Switching stacks

- section: Stacks
- relevance: 4 - an exception taken mid-switch finds an inconsistent stack
- words: 90

What usage when code moves the stack pointer or the shadow call stack pointer
to another stack is unsafe, and what is correct? Name the in-tree code that
switches to the IRQ stack and say what it masks, and for how long.

# System registers

## arm64.sysreg-accessors: Accessor macros

- section: Register access
- relevance: 4 - the wrong accessor assembles to the wrong thing or not at all
- words: 110

What is the difference between `read_sysreg()` and `read_sysreg_s()` and their
write forms, what does `sysreg_clear_set()` do when nothing changes, which
helpers extract or build a field from the generated definitions, and why does
the hypervisor configuration register have its own write macro? Start from the
end of `arch/arm64/include/asm/sysreg.h`.

## arm64.fixed-register-insn: Instructions with a fixed operand register

- section: Register access
- relevance: 3 - a constraint alone lets the compiler pick the wrong register
- words: 90

How does the tree emit a system instruction whose register operand must be the
zero register, or that takes no operand, and what usage of an inline assembly
constraint for such an instruction is unsafe? Start from `write_sysreg_s()`,
`__TLBI_0` and `gic_insn()`.

## arm64.sysreg-file-format: Register description file

- section: Generated definitions
- relevance: 4 - new registers must be described here, not by hand
- words: 100

What block and field kinds does the system register description file accept,
and for one register with one field of each kind, which macro names does the
generator emit? Start from the comment at the top of `arch/arm64/tools/sysreg`
and `define_field` in `arch/arm64/tools/gen-sysreg.awk`.

## arm64.sysreg-resx-masks: Reserved-bit masks

- section: Generated definitions
- relevance: 4 - the value changes silently when the description changes
- words: 90

How are the `_RES0`, `_RES1` and `_UNKN` masks of a register computed, what is
the value when the description has no line of that kind, and does the generator
know about bits that are reserved only when a feature is absent?

## arm64.sysreg-mask-consumers: Consumers of generated masks

- section: Generated definitions
- relevance: 4 - neither the compiler nor a test notices the change
- words: 100

Which C and assembly code consumes a generated `_RES1` or `_RES0` mask to build
a register value, and what does someone editing a register's description have
to check as a result? Start from `SCTLR_EL2_RES1`, `INIT_SCTLR_EL2_MMU_ON` and
the users of `_RES0` masks under `arch/arm64/kvm/`.

## arm64.sctlr-init: Initial SCTLR values

- section: Generated definitions
- relevance: 3 - decides whether exception entry and return synchronise context
- words: 80

Which bits do the initial `SCTLR_EL1` and `SCTLR_EL2` values set with the MMU on
and off, and in particular do they set the bits that make exception entry and
exception return context synchronising? Start from `INIT_SCTLR_EL1_MMU_ON`.

## arm64.conditional-resx: Bits reserved without a feature

- section: Generated definitions
- relevance: 3 - looked for in the generated masks, where it is not
- words: 70

Where does the tree record that a register bit behaves as RES0 or RES1 only
when some feature is not implemented, and how is that marked? Start from
`arch/arm64/kvm/config.c`.

## arm64.isb-after-write-usage: Context synchronisation after a write

- section: Context synchronisation
- relevance: 5 - both the missing barrier and the needless one get reported
- words: 120

What usage of a system register write with no `isb()` after it is unsafe, and
what that looks similar is correct because nothing at the current exception
level depends on the new value before an exception return? Name in-tree code on
both sides, for example around `update_sctlr_el1()`, `__mte_enable_kernel()`,
`cpu_enable_pan()` and the trap configuration in
`arch/arm64/include/asm/el2_setup.h`.

## arm64.self-sync-writes: Writes that need no barrier

- section: Context synchronisation
- relevance: 4 - reviewers ask for barriers the code deliberately omits
- words: 100

Which system register writes does the tree deliberately not follow with an
`isb()` because the register or field synchronises itself, and what comment or
code shows it? Consider the vector length fields, the FP8 mode register, the
interrupt priority mask and SSBS. Start from `task_fpsimd_load()`,
`vec_probe_vqs()` and `local_daif_restore()`.

## arm64.readback-usage: Reading a register back

- section: Context synchronisation
- relevance: 3 - a read-back says the value was stored, not that it took effect
- words: 80

Where does the tree write a system register and immediately read it back with
no barrier between, what is each such read-back used to find out, and what
would be unsafe to conclude from it?

# CPU features and errata

## arm64.cpucap-types: Capability scopes and types

- section: Capabilities
- relevance: 4 - the type decides what happens on a late or mismatched CPU
- words: 120

What scopes can a CPU capability have, what do the flags about late CPUs mean,
and which combined types does the tree define for features and for errata? A
table saying, for each type, whether a late CPU may have it when the system
does not and may lack it when the system has it. Start from
`ARM64_CPUCAP_SCOPE_LOCAL_CPU` in `arch/arm64/include/asm/cpufeature.h`.

## arm64.cap-check-helpers: Testing a capability

- section: Capabilities
- relevance: 5 - the wrong helper reads a bit that is not final yet, or patches nothing
- words: 120

What is the difference between `cpus_have_cap()`, `cpus_have_final_cap()`,
`cpus_have_final_boot_cap()`, `alternative_has_cap_likely()`,
`alternative_has_cap_unlikely()` and `this_cpu_has_cap()`: when may each be
called, what does each do before capabilities are finalised, and which one do
helpers such as `system_supports_sve()` use?

## arm64.idreg-sanitisation: ID register sanitisation

- section: Capabilities
- relevance: 4 - a new ID field that is not described is hidden or taints
- words: 110

How is a system-wide safe value of an ID register computed from the CPUs: what
do the field types, the strict flag and the visible flag mean, which function
reads the result, and how can the command line override a field? Start from
`struct arm64_ftr_bits`, `read_sanitised_ftr_reg()` and
`arch/arm64/kernel/pi/idreg-override.c`.

## arm64.add-capability: Adding a CPU feature

- section: Capabilities
- relevance: 4 - several files have to change together
- words: 100

What has to be added, and where, to detect a new architectural feature and use
it in the kernel: the capability number, the ID register field, the
capability entry and its enable callback, the helper that tests it, and any
requirement on higher exception levels recorded in the boot documentation?
Start from `arch/arm64/tools/cpucaps` and `arm64_features`.

## arm64.add-erratum: Adding an erratum workaround

- section: Capabilities
- relevance: 4 - the match type and the documentation table are often forgotten
- words: 100

What has to be added, and where, for a new CPU erratum workaround: the
configuration option, the capability, the entry that matches affected CPUs and
its type, and the documentation table? Which capability type do errata use and
what does it do to a late CPU that needs the workaround? Start from
`arm64_errata` in `arch/arm64/kernel/cpu_errata.c`.

## arm64.alternatives: Alternatives patching

- section: Capabilities
- relevance: 4 - the replacement runs from a different address than it was assembled at
- words: 110

How does an alternative sequence get patched: what forms are there in C and in
assembly, including the callback form, when are boot, system and module
alternatives applied, and what may the replacement instructions not contain?
Start from `arch/arm64/include/asm/alternative-macros.h` and
`__apply_alternatives()`.

# Patching code and cache maintenance

## arm64.insn-patching-api: Instruction patching functions

- section: Patching and caches
- relevance: 4 - the variants differ in what they synchronise
- words: 110

Which functions write instructions into kernel or module text, how do they map
the target for writing, what lock do they take, what cache maintenance do they
do, and which of them synchronise other CPUs? Say which users (jump labels,
static calls, ftrace, kprobes, the BPF JIT) call which. Start from
`arch/arm64/kernel/patching.c`.

## arm64.patching-sync-usage: Other CPUs and patched code

- section: Patching and caches
- relevance: 4 - the write is visible before other CPUs are guaranteed to fetch it
- words: 100

What usage when modifying an instruction that another CPU may be executing is
unsafe, and what is correct? Say which in-tree patching paths rely on the
patched instruction being one that may be changed while it is executed, which
stop all CPUs, and how the rest make other CPUs resynchronise.

## arm64.cache-maint-names: Cache maintenance routines

- section: Patching and caches
- relevance: 3 - the routines were renamed to say what they do
- words: 100

Which routines clean or invalidate the caches by virtual address, to which
point does each operate, and which should be used after writing instructions,
for non-coherent DMA and for persistent memory? Say which older names a reader
might look for. Start from the comment in `arch/arm64/include/asm/cacheflush.h`.

## arm64.icache-sync: Instruction cache coherency for user pages

- section: Patching and caches
- relevance: 3 - done lazily, at the time the mapping is installed
- words: 80

When does the kernel make the instruction cache coherent with a page's data,
what page flag records that it has been done and what clears it, and how do
the cache type capabilities change the work? Start from
`__sync_icache_dcache()` and `flush_dcache_folio()`.

# Page tables

## arm64.pgtable-config: Levels and folding

- section: Page table format
- relevance: 4 - levels can be folded at run time, not only at build time
- words: 100

How many page table levels can a kernel be built with, which of them can be
folded at run time and on what condition, and which helpers say whether a level
is in use? Start from `pgtable_l4_enabled()`, `pgtable_l5_enabled()` and
`lpa2_is_enabled()`.

## arm64.pte-bits: Software and hardware PTE bits

- section: Page table format
- relevance: 4 - dirty and writable are encoded across three bits
- words: 110

How are writable, dirty and young encoded in a PTE with and without hardware
management of the dirty state, which bits are software-only, how is a
present-but-inaccessible entry distinguished from a swap entry, and which bit
marks a contiguous range? Start from the table above
`__check_safe_pte_update()` and `arch/arm64/include/asm/pgtable-prot.h`.

## arm64.pte-setters: Writing an entry

- section: Page table format
- relevance: 4 - the barrier is conditional on what is being written
- words: 90

What do `__set_pte()`, `__set_pte_nosync()`, `__set_pte_complete()` and
`__set_ptes_anysz()` each do, for which new values are barriers issued after
the store and which barriers, and what else is done before a user mapping is
installed?

## arm64.pte-barrier-batching: Deferred PTE barriers

- section: Page table format
- relevance: 4 - the deferral is unsafe where it cannot be flushed
- words: 110

How are the barriers after kernel PTE updates deferred and batched, what flag
records that they are pending, when are they finally issued, what happens if
the task is preempted or interrupted in between, and which update paths issue
the barriers directly regardless? Start from `queue_pte_barriers()` and
`is_lazy_mmu_mode_active()`.

## arm64.ptep-accessors: Public and private PTE accessors

- section: Contiguous mappings
- relevance: 4 - arch code that uses the public name recurses or folds when it must not
- words: 90

What is the difference between `ptep_get()`, `set_ptes()` and the other public
accessors and their double-underscore forms, and which should code under
`arch/arm64/mm/` use for kernel mappings and inside the contiguous-PTE
implementation?

## arm64.contpte-fold: Folding and unfolding

- section: Contiguous mappings
- relevance: 4 - the sequence is a break-before-make on sixteen entries
- words: 120

When is a range of PTEs folded into a contiguous mapping and when unfolded,
what sequence of clears, invalidation and stores does the conversion perform,
how are access and dirty bits preserved, and which step is skipped on hardware
that tolerates the change? Start from `contpte_convert()` and
`__contpte_try_fold()`.

## arm64.lockless-walk: Lockless readers

- section: Contiguous mappings
- relevance: 4 - a contiguous block can change under the reader
- words: 100

How does a lockless page table walker read an entry that may be part of a
contiguous block being folded or unfolded, and how do the lockless offset
helpers cope with a level that is folded at run time? Start from
`contpte_ptep_get_lockless()` and `pud_offset_lockless()`.

## arm64.lockless-walk-usage: Reading entries without the lock

- section: Contiguous mappings
- relevance: 4 - a plain dereference can be torn or re-read
- words: 80

What usage when reading a page table entry without holding the page table lock
is unsafe, and what is correct? Name the accessors a walker should use at the
PTE level and at the higher levels.

## arm64.tlb-api: Invalidation functions

- section: TLB invalidation
- relevance: 5 - each function differs in scope, walk-cache handling and barriers
- words: 130

Which TLB invalidation functions does the tree provide, and for each: which
instruction it uses, whether it also invalidates walk-cache entries, the stride
and level hint it passes, and the barriers around it? A table. Say which
functions a reader of an older kernel would look for and not find. Start from
the comment in `arch/arm64/include/asm/tlbflush.h`.

## arm64.tlb-flags: Invalidation flags

- section: TLB invalidation
- relevance: 5 - the flags replace several older function variants
- words: 90

What flags can be passed to `__flush_tlb_range()` and `__flush_tlb_page()`,
what does each change, and which combination is refused? Name one caller of
each flag. If this tree has no such flags, say so and stop.

## arm64.tlb-barrier-template: Barriers around invalidation

- section: TLB invalidation
- relevance: 5 - a missing or misplaced barrier leaves a stale translation in use
- words: 120

What barrier goes before the invalidation instruction and what after it, when
is an `isb()` also issued, and which helpers wrap the completing barrier for
user, batched, kernel and hypervisor invalidation? Say what extra work those
helpers do for errata. Start from `__tlbi_sync_s1ish()` and
`flush_tlb_kernel_range()`.

## arm64.tlb-operands: Invalidation operands

- section: TLB invalidation
- relevance: 4 - a wrong level hint or granule means nothing is invalidated
- words: 110

How are the operands of a by-address and of a range invalidation built: the
address and ASID fields, the level hint and when it is left out, the granule,
scale and count of a range, and the alignment a range needs with 52-bit
addresses? Start from `__tlbi_level_asid()`, `__tlbi_range()` and
`__flush_tlb_range_op()`.

## arm64.tlb-batch: Batched and gathered invalidation

- section: TLB invalidation
- relevance: 3 - the barrier is separated from the invalidation
- words: 90

How does the reclaim batching interface invalidate without waiting, where is
the completing barrier, and how does the `mmu_gather` flush pick the stride,
the level hint and whether to keep walk-cache entries? What does it skip when a
whole address space is torn down? Start from `arch_tlbbatch_add_pending()` and
`tlb_flush()` in `arch/arm64/include/asm/tlb.h`.

## arm64.bbm-safe-changes: Changes allowed without break-before-make

- section: Changing live mappings
- relevance: 5 - says which live updates need the invalid step and which do not
- words: 110

Which changes to a valid entry does the tree treat as safe without going
through an invalid entry, which does it reject, and which debug checks enforce
that? Start from `pgattr_change_is_safe()` and `__check_safe_pte_update()`.

## arm64.bbm-usage: Replacing a live entry

- section: Changing live mappings
- relevance: 5 - skipping the invalidation can raise a TLB conflict abort
- words: 120

What usage when replacing a valid translation table entry with a different
valid one is unsafe, and what is correct? Name in-tree code that clears,
invalidates and then writes, code that updates access and dirty state in place
without doing so, and code that relies on a hardware capability to skip a step.

## arm64.bbm-level: Hardware tolerance of conflicting entries

- section: Changing live mappings
- relevance: 5 - the capability has been renamed and its detection is unusual
- words: 110

Which capability says that block and page sizes can be changed without an
intermediate invalid entry, how is it detected, what type is it so that a late
CPU without it is handled, what code depends on it, and what happens at boot if
a secondary CPU lacks it? Start from `arch/arm64/tools/cpucaps`,
`split_kernel_leaf_mapping()` and `force_pte_mapping()`.

## arm64.kernel-mapping-changes: Changing kernel mappings

- section: Changing live mappings
- relevance: 4 - the linear map may be mapped with blocks
- words: 110

How do `set_memory_ro()` and its relatives change permissions on kernel
memory: which address ranges are accepted, when is the linear alias changed as
well, when is the linear map mapped at page granularity, and how is a block or
contiguous mapping split first? Start from `change_memory_common()` and
`can_set_direct_map()`.

## arm64.asid-allocator: ASID allocation

- section: Address spaces
- relevance: 3 - the rollover ordering is subtle and lockless on the fast path
- words: 110

How are ASIDs allocated and recycled: the generation, what happens on
rollover, reserved and pinned ASIDs, the pairing used when the kernel is
unmapped at EL0, and what the fast path of a context switch checks without
taking the lock? Start from `check_and_switch_context()` and `flush_context()`.

## arm64.ttbr-switch: Switching translation tables

- section: Address spaces
- relevance: 3 - TTBR0 is not always the user page table
- words: 100

How is the user page table installed on a context switch, what is the reserved
table and when is it installed instead, how does that change when privileged
access never is emulated in software, and how are the identity map and a new
kernel table installed? Start from `cpu_switch_mm()`,
`cpu_set_reserved_ttbr0()`, `cpu_install_idmap()` and `cpu_replace_ttbr1()`.

## arm64.fault-handling: Page fault handling

- section: Address spaces
- relevance: 4 - permission checks are derived from the syndrome
- words: 120

How does the page fault handler turn a syndrome into the access it checks
against the VMA, how does it treat kernel faults on user addresses with and
without an exception table entry, and how are protection key, guarded control
stack and tag check faults handled? Start from `do_page_fault()`,
`is_el1_permission_fault()` and `fault_info`.

## arm64.memory-layout: Address conversion helpers

- section: Address spaces
- relevance: 3 - the kernel image is not in the linear map
- words: 90

What are the regions of the kernel virtual address space, which conversion
helper is valid for a linear map address, which for a kernel image symbol, and
what do `virt_addr_valid()` and `__is_lm_address()` check? Start from
`arch/arm64/include/asm/memory.h` and `Documentation/arch/arm64/memory.rst`.

# Tagged addresses and MTE

## arm64.untagged-addr: Tag removal helpers

- section: Tagged addresses
- relevance: 4 - the helper keeps kernel addresses intact by design
- words: 100

How does `untagged_addr()` remove a tag, what does it do to a kernel address,
how does it differ from `__tag_reset()`, and how do `access_ok()` and
`mm_untag_mask()` treat tagged user pointers depending on the task's setting?
Start from `arch/arm64/include/asm/memory.h` and
`arch/arm64/include/asm/uaccess.h`.

## arm64.untag-usage: Arithmetic on user addresses

- section: Tagged addresses
- relevance: 4 - the MMU ignores the top byte, software arithmetic does not
- words: 80

What usage of a user-supplied address in comparisons, shifts or VMA lookups is
unsafe when tags may be present, and what is correct? Name in-tree code that
untags before use and say where generic code is expected to have done it.

## arm64.mte-page-flags: Page tag state flags

- section: Memory tagging
- relevance: 5 - two racing initialisers must not both clear tags
- words: 110

Which page flags record that a page's tags have been initialised, what protocol
lets exactly one of several racing callers initialise them, what ordering do
the helpers give, is the tagged flag ever cleared, and how do hugetlb folios
differ? Start from `try_page_mte_tagging()` and `set_page_mte_tagged()`.

## arm64.mte-sync-tags: Tag initialisation at mapping time

- section: Memory tagging
- relevance: 4 - the condition is on the PTE, not the VMA
- words: 90

When an entry is installed, under what conditions on the new PTE are the
page's tags initialised, what does the initialisation do, and what orders it
before the entry becomes visible? Start from `__sync_cache_and_tags()` and
`mte_sync_tags()`.

## arm64.mte-tag-init-usage: Making a tagged page visible

- section: Memory tagging
- relevance: 5 - user space can map the page between the flag and the tags
- words: 110

What usage when initialising tags for a page that other observers can reach
(a shared zero page, a page being copied, swapped in, or compared for merging)
is unsafe, and what is correct? Name the in-tree code for each of those cases
and say in what order it writes tags, sets the flag and publishes the page.
Start from `copy_highpage()`, `arch_swap_restore()`, `tag_clear_highpages()`
and `memcmp_pages()`.

## arm64.mte-modes: Tag check modes

- section: Memory tagging
- relevance: 3 - the mode is per task, per CPU preference and per kernel
- words: 110

How is the tag check fault mode chosen for a user task and for the kernel,
where is the per-task value kept and when is it written to hardware, how are
asynchronous faults collected on entry, exit and context switch, and what does
the tag check override bit do on entry? Start from `mte_update_sctlr_user()`,
`mte_check_tfsr_el1()` and `mte_disable_tco_entry()`.

# FP/SIMD, SVE and SME

## arm64.fp-state-tracking: Lazy state tracking

- section: FP state
- relevance: 5 - decides whether registers or memory hold the truth
- words: 120

How does the kernel know whether a task's FP/SIMD state is live in this CPU's
registers: what do `TIF_FOREIGN_FPSTATE`, the per-CPU `fpsimd_last_state` and
the task's `fpsimd_cpu` record, when is the state loaded and when saved, and
how does KVM take part? Start from the comment at the top of
`arch/arm64/kernel/fpsimd.c`.

## arm64.fp-state-format: Saved state format

- section: FP state
- relevance: 5 - the wrong buffer is stale by definition
- words: 120

Where is a task's saved FP/SIMD, SVE and SME state kept, what says which of the
buffers is valid, what do `TIF_SVE` and `TIF_SME` mean beyond that, what types
are the SVE and SME buffers, and what is the `to_save` field for? Start from
`enum fp_type`, `struct cpu_fp_state` and the comment above
`task_fpsimd_load()`.

## arm64.fp-context-ownership: Owning the register file

- section: FP state
- relevance: 4 - softirqs may use the registers too
- words: 90

What must code hold while it manipulates a task's FP state or
`TIF_FOREIGN_FPSTATE`, what does that do on a preemptible-RT kernel and with
interrupts already disabled, and which functions assume the caller holds it?
Start from `get_cpu_fpsimd_context()`.

## arm64.kernel-neon: Kernel-mode SIMD

- section: FP state
- relevance: 5 - the interface takes an argument older code did not pass
- words: 120

What is the contract of `kernel_neon_begin()` and `kernel_neon_end()`: the
argument, when it may be NULL, from which contexts they may be called, what
`may_use_simd()` checks, whether the section is preemptible, and what the
scoped helper does? Start from `arch/arm64/include/asm/simd.h`.

## arm64.fp-syscall: State discarded at a system call

- section: FP state
- relevance: 4 - part of the ABI
- words: 80

Which vector state is discarded or kept when a task makes a system call, how is
that implemented without saving registers, and what resets it on the way out?
Start from `fpsimd_syscall_enter()`.

## arm64.fp-traps: Access traps

- section: FP state
- relevance: 3 - first use allocates and converts state
- words: 90

What happens when a task first uses SVE or SME: which handler runs, what it
allocates, how existing FP/SIMD state is carried over, and what it asserts
about the thread flags on entry? Start from `do_sve_acc()` and `do_sme_acc()`.

## arm64.vl-change: Changing the vector length

- section: Vector length and SME
- relevance: 5 - state sized for the old length must not survive
- words: 120

What does changing a task's SVE or SME vector length do to its saved state:
what is allocated and when, what is preserved, what is zeroed, what happens to
streaming mode and to ZA, and what is left alone when only the length for the
next exec is changed? Start from `vec_set_vector_length()` and
`change_live_vector_length()`.

## arm64.vl-change-usage: State derived from the vector length

- section: Vector length and SME
- relevance: 4 - stale data reappears in registers of the new width
- words: 80

What usage when changing a vector length or switching streaming mode on behalf
of a task is unsafe with respect to buffers, flags and live registers, and what
is correct? Name the helpers that flush or convert the state.

## arm64.sme-state: SME state

- section: Vector length and SME
- relevance: 4 - two independent enables with different lifetimes
- words: 110

What SME state does a task have (the streaming and ZA enables, ZA, ZT0, the
second thread ID register), where is each stored, what does entering or
leaving streaming mode do to the vector registers, and which helper clears
streaming mode in a saved state? Start from `thread_sm_enabled()`,
`sme_alloc()` and `task_smstop_sm()`.

## arm64.fp-signal: Signal frame records

- section: Vector length and SME
- relevance: 4 - restore must accept every layout save can produce
- words: 120

Which FP-related records can a signal frame contain, when is each present, and
on return how are the SVE and FP/SIMD records combined, what is rejected, and
what is required of a streaming-mode record? Start from
`restore_sve_fpsimd_context()` and `setup_sigframe_layout()`.

## arm64.fp-ptrace: Ptrace register sets

- section: Vector length and SME
- relevance: 3 - a write through one view must update the others
- words: 100

Which register sets expose FP/SIMD, SVE, streaming SVE, ZA, ZT0 and the FP8
mode register to a debugger, what does writing each do to the task's flags and
buffers, and which helpers keep the FP/SIMD and SVE views consistent? Start
from `sve_set_common()`, `fpsimd_sync_from_effective_state()` and
`fpsimd_sync_to_effective_state_zeropad()`.

# User access and security features

## arm64.uaccess: User access primitives

- section: Security features
- relevance: 4 - what may run between enable and disable is restricted
- words: 110

How do the user access routines reach user memory: which instructions are
used, how is privileged access never provided in hardware and how is it
emulated, what must not happen between enabling and disabling user access, and
how is a pointer sanitised against speculation? Start from
`uaccess_ttbr0_enable()`, `__uaccess_mask_ptr()` and `__raw_get_user()`.

## arm64.ptrauth: Pointer authentication

- section: Security features
- relevance: 3 - kernel and user keys share registers
- words: 100

Which pointer authentication keys do user tasks and the kernel use, when are
they switched, how is a task's per-key enable applied, and how must a function
that changes the keys be built? Start from `ptrauth_thread_switch_user()`,
`__ptrauth_keys_install_kernel_nosync` and `ptrauth_keys_init_cpu`.

## arm64.gcs: Guarded control stack

- section: Security features
- relevance: 3 - new state in context switch, signals, faults and clone
- words: 110

What per-task state does the guarded control stack add, where is it switched,
what barrier does the switch need, how is a stack allocated for a new thread,
what is pushed on signal delivery, and how are faults on such a stack
classified? Start from `gcs_thread_switch()`, `gcs_alloc_thread_stack()` and
`is_gcs_fault()`.

## arm64.poe: Permission overlays

- section: Security features
- relevance: 3 - one more register to switch and to reset around signal handlers
- words: 90

How are protection keys implemented with permission overlays: where is the
overlay register saved and switched, what value does a signal handler run
with and how is the old one restored, and how does a fault say it came from an
overlay? Start from `permission_overlay_switch()`,
`save_reset_user_access_state()` and `fault_from_pkey()`.

## arm64.spectre: Speculation mitigations

- section: Security features
- relevance: 3 - state machines spread over vectors, firmware calls and prctl
- words: 110

Which speculation vulnerabilities does the tree track, what states can each be
in, how do the branch history mitigations choose between a loop, a firmware
call and an instruction, how are the exception vectors switched per CPU, and
how is speculative store bypass controlled per task? Start from
`arch/arm64/kernel/proton-pack.c` and `this_cpu_set_vectors()`.

# Boot, power and emulation

## arm64.boot-flow: Early boot

- section: Boot and power
- relevance: 3 - early code runs before relocation and with the MMU in a special state
- words: 120

What are the steps from the image entry point to `start_kernel()`: the initial
identity map, exception level setup, enabling the MMU, mapping and relocating
the kernel, and applying command line overrides? What may the code built
under `arch/arm64/kernel/pi/` not do, and how are its symbols named? Start
from `primary_entry` and `early_map_kernel()`.

## arm64.el2-setup: Exception level setup

- section: Boot and power
- relevance: 4 - a feature that traps by default needs enabling here
- words: 110

When a CPU enters at EL2, what configures the hypervisor registers so that EL1
can use each feature, how does the kernel later move itself to EL2 where the
hardware allows, which calls does the stub hypervisor accept, and where are
the requirements on firmware written down? Start from `init_el2_state`,
`finalise_el2` and `arch/arm64/kernel/hyp-stub.S`.

## arm64.suspend-resume: Suspend and restart

- section: Boot and power
- relevance: 3 - register state is lost and must be rebuilt in the right order
- words: 100

What is saved and restored around a CPU power-down, which per-feature hooks
run on the way back up, and how do hibernation and kexec leave the running
kernel's page tables and exception level? Start from `cpu_suspend()`,
`__cpu_suspend_exit()` and `cpu_soft_restart()`.

## arm64.el0-emulation: Emulated EL0 accesses

- section: Boot and power
- relevance: 3 - user-visible behaviour that depends on traps being set
- words: 100

Which system register reads and instructions executed at EL0 does the kernel
trap and emulate, how are the handlers looked up, what is returned for an ID
register read, and how does the handler step past the instruction? Start from
`do_el0_sys()`, `sys64_hooks` and `try_emulate_mrs()`.
