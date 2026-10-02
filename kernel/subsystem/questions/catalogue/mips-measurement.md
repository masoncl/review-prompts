# Questions: MIPS (measurement set)

- guide: mips.md
- title: MIPS Subsystem Details

A wide set of questions about `arch/mips`, used to measure what a model
already knows before deciding what the built guide should spend its words on.
The hand-written guide it will replace is 480 words and is entirely about one
hazard: duplicate entries in the translation lookaside buffer during early
initialisation. So most questions here are about the TLB code, and the rest
sample the other parts of the architecture a patch under `arch/mips/` is
likely to touch. Format: `../../../docs/subsystem-questions.md`.

# The architecture directory

## mips.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup
- words: 110

Which files hold the TLB maintenance code, the generator of the TLB exception
handlers and the assembler it uses, the cache maintenance code, address space
id allocation, CPU probing and the feature test macros, the coprocessor 0
accessors, the hazard barriers, the exception entry code and the trap
handlers, the system call tables, the SMP back ends and KVM? A table. Start
from `arch/mips/mm/` and `arch/mips/kernel/`.

## mips.platform-layout: Platform selection

- section: Finding your way
- relevance: 3 - decides which board code and which header overrides a build gets
- words: 70

How does a build choose its platform code and its per-platform header
overrides, and how does the device-tree based multi-board kernel differ from
the older board directories? Start from `arch/mips/Kbuild.platforms`,
`arch/mips/generic/Platform` and the `mach-generic` headers.

# The TLB

## mips.tlb-wrappers: TLB instruction wrappers

- section: TLB primitives
- relevance: 4 - every TLB routine is written in these
- words: 70

Which C wrappers does this tree provide for the TLB instructions, including
any invalidate and guest variants, which header defines them, and do they
contain any hazard handling themselves? Start from `tlb_probe()`.

## mips.hazard-barriers: Coprocessor 0 hazard barriers

- section: TLB primitives
- relevance: 4 - a missing barrier works on one core and fails on another
- words: 90

List the hazard barrier macros used around TLB operations, say which one goes
between which coprocessor 0 access and which TLB instruction or later use, and
which header defines them. What do they expand to on the different ISA levels
the kernel can be built for? Start from `mtc0_tlbw_hazard()`.

## mips.unique-entryhi: Invalidated entry values

- section: TLB primitives
- relevance: 5 - the value written into an invalidated entry decides whether two entries can match
- words: 70

What value does the kernel write into the EntryHi of a TLB entry it
invalidates, why is it computed from the entry's index, which address segment
is it taken from for the host and for a KVM guest, and what extra bit is set
on hardware that supports it? Start from `UNIQUE_ENTRYHI()`.

## mips.machine-check: Duplicate entry machine check

- section: TLB primitives
- relevance: 5 - the failure the whole init sequence is built to avoid
- words: 80

What happens on MIPS hardware when two TLB entries match the same address:
which exception is raised, which status bit identifies the cause, which
operations can raise it, what does the kernel's handler do, and can the
kernel continue afterwards? Start from `do_mcheck()`.

## mips.tlb-init-sequence: TLB initialisation order

- section: Initialisation
- relevance: 4 - the order is what makes the first flush safe
- words: 80

In what order does the kernel set up the TLB on the boot CPU, on a secondary
CPU, and on a CPU returning from a power state that lost it? Name the
functions and say what each step writes. Start from `tlb_init()` and
`per_cpu_trap_init()`.

## mips.uniquify: Uniquifying inherited entries

- section: Initialisation
- relevance: 5 - rewritten recently, and the algorithm is the subject of the old guide
- words: 120

How does this tree deal with whatever entries firmware or a previous kernel
left in the TLB before its first flush: which TLB instructions does it use and
which does it avoid, what does it record about each entry, in what order does
it process them, how does it choose replacement values, and what memory does
it use for its table? If the tree has no such step, say so and stop. Start
from `r4k_tlb_uniquify()`.

## mips.uniquify-gating: Skipping uniquification

- section: Initialisation
- relevance: 4 - the step does not run everywhere and cannot
- words: 60

On which hardware is the step that uniquifies inherited TLB entries skipped,
what is relied on instead, and which TLB features is the step's algorithm
unable to handle? Start from `r4k_tlb_configure()`.

## mips.init-tlb-usage: TLB operations before initialisation

- section: Initialisation
- relevance: 5 - the rule the old guide exists for
- words: 100

In code that runs while the TLB may still hold entries the kernel did not
write, what usage of the probe, indexed write and random write operations is
unsafe, and what that looks similar is correct? Does reading an entry and
writing it back unchanged count as safe? Name in-tree code that shows each.

## mips.tlbinv: Hardware invalidate support

- section: Initialisation
- relevance: 4 - changes both the flush path and what an invalid entry looks like
- words: 70

How does the kernel detect that a CPU can invalidate TLB entries in hardware,
which feature macro reports it, and what does `local_flush_tlb_all()` do
differently when it is present and when wired entries exist? Start from
`cpu_has_tlbinv`.

## mips.vtlb-ftlb: Variable and fixed TLBs

- section: TLB layout
- relevance: 3 - loops over the TLB use these sizes
- words: 70

Which fields of `struct cpuinfo_mips` describe the size of the TLB and its
parts, how are they filled in, and how do the flush routines use them to
decide between flushing entries one at a time and dropping everything? Start
from `tlbsizevtlb` and `tlbsizeftlbsets`.

## mips.wired-entries: Wired entries

- section: TLB layout
- relevance: 4 - wired entries survive flushes and restrict every index loop
- words: 80

How are wired TLB entries added and removed, who uses them, how is the number
of wired entries read on the different ISA revisions, and which address space
id is used for them when ids are global? Start from `add_wired_entry()`,
`num_wired_entries()` and `kmap_coherent()`.

## mips.pagemask: PageMask invariants

- section: TLB layout
- relevance: 4 - the rest of the mm code assumes one value
- words: 60

What value must the PageMask register hold outside the routines that change
it, which routines change it temporarily and for what, and what goes wrong on
which CPU if it is left changed? Start from `PM_DEFAULT_MASK`.

## mips.local-flush-pattern: Flushing one entry

- section: Maintenance
- relevance: 4 - the template every new TLB routine copies
- words: 90

Give the sequence the local flush routines follow to remove the entry for one
address: what is saved and restored, what is disabled, how the entry is found,
what is written over it, and which barriers sit between the steps. Start from
`local_flush_tlb_page()` and `local_flush_tlb_one()`.

## mips.htw: Hardware page table walker

- section: Maintenance
- relevance: 4 - a walker that runs mid-sequence rewrites the registers being used
- words: 70

What do `htw_stop()` and `htw_start()` do, do they nest, which code must
bracket its TLB register accesses with them, and what usage is unsafe when
they are left out? Start from `cpu_has_htw`.

## mips.asid-mmid: Address space identifiers

- section: Maintenance
- relevance: 4 - two schemes with different scope share one set of helpers
- words: 100

How are address space identifiers allocated and recycled when they are per
CPU and when they are global to the system, where is each kept, which register
carries the identifier in each scheme, and what does `drop_mmu_context()` do
in each case? Start from `cpu_context()` and `arch/mips/mm/context.c`.

## mips.update-tlb: Loading an entry after a fault

- section: Maintenance
- relevance: 3 - the one place C code chooses between an indexed and a random write
- words: 80

How does `__update_tlb()` decide between an indexed and a random write, how
does it fill the two halves of an entry, what does it do for a huge page, and
under which configurations does the page table entry have a different layout?

## mips.r3k-tlb: R3000-class TLB code

- section: Maintenance
- relevance: 2 - a second implementation that a change to the first can forget
- words: 60

How does the TLB code for R3000-class CPUs differ from the R4000-class code in
entry format, index encoding, hazard handling and the entries it leaves alone
on a full flush? Start from `arch/mips/mm/tlb-r3k.c`.

## mips.tlbex-generator: Generated exception handlers

- section: Exception handlers
- relevance: 4 - the fast paths are not in any source file as written
- words: 90

How are the TLB refill, load, store and modify handlers produced, when and on
which CPUs does that happen, where do they end up in memory, what limits their
size, and how can the generated code be inspected? Start from
`build_tlb_refill_handler()`.

## mips.tlbex-probe-race: Probe results in handlers

- section: Exception handlers
- relevance: 3 - a probe that misses inside a handler is not always a bug
- words: 60

Under what hardware conditions can the probe inside a generated TLB exception
handler fail to find the entry that faulted, how does the generator handle
that, and is every path covered? Start from `cpu_has_tlbex_tlbp_race()`.

## mips.kvm-tlb: KVM and the TLB

- section: Exception handlers
- relevance: 3 - a second set of TLB routines that must follow the same rules
- words: 70

Which virtualisation modes does MIPS KVM support in this tree, where are its
root and guest TLB routines, which of them mirror routines in
`arch/mips/mm/tlb-r4k.c`, and what else in KVM duplicates code from the
handler generator? Start from `arch/mips/kvm/tlb.c`.

# The rest of the architecture

## mips.cpu-features: Feature tests

- section: CPU and memory model
- relevance: 4 - the wrong test compiles and silently picks the wrong path
- words: 90

How are the feature macros whose names begin with cpu_has_ defined, how can a
platform turn one into a compile-time constant, where are the option bits set,
and what usage of per-CPU data such as `current_cpu_data` is unsafe while a
similar-looking use is correct? Start from
`arch/mips/include/asm/cpu-features.h`.

## mips.cache-aliases: Data cache aliases

- section: CPU and memory model
- relevance: 4 - stale data with no crash
- words: 90

How does the kernel cope with virtually indexed data caches whose aliases can
hold different data for one physical page: which feature macro reports it,
which page flag defers the flush, where is the deferred flush done, and when
is a temporary mapping at a matching colour used instead? Start from
`cpu_has_dc_aliases` and `__update_cache()`.

## mips.address-segments: Address segments

- section: CPU and memory model
- relevance: 3 - address arithmetic that is right on one platform and wrong on the next
- words: 80

What are the unmapped kernel address segments on 32-bit and 64-bit kernels,
which macros convert between them and physical addresses, what changes under
the enhanced virtual addressing option, and what usage of those macros is
unsafe where a similar use is correct?

## mips.abis-syscalls: ABIs and system call tables

- section: Kernel entry
- relevance: 3 - a new system call has to be added in more than one place
- words: 80

Which user ABIs does a 64-bit MIPS kernel support, where is the system call
table for each and how is it generated, where do the numbers start, and which
entry file dispatches each? Start from `arch/mips/kernel/syscalls/`.

## mips.fpu-context: Floating point ownership

- section: Kernel entry
- relevance: 3 - the register file may or may not be live
- words: 80

How does the kernel track whether a task's floating point and vector state is
live in the registers, which helpers take and give up ownership, what must be
disabled around them, and what happens on a CPU with no floating point unit?
Start from `lose_fpu()` and `own_fpu()`.

## mips.delay-slots: Branch delay slots

- section: Kernel entry
- relevance: 3 - skipping an instruction is not adding four to the program counter
- words: 70

When an exception handler needs to skip or emulate the faulting instruction,
how does it work out the address to resume at if the instruction was in a
branch delay slot, and how are instructions in the delay slot of an emulated
branch executed? Start from `compute_return_epc()` and `mips_dsemul()`.

## mips.llsc-barriers: Atomics and barriers

- section: Kernel entry
- relevance: 3 - errata turn a plain loop into a broken one
- words: 80

How are the memory barrier and load-linked, store-conditional sequences
parameterised for CPUs with errata or without the instructions, which macro
emits a barrier of a named kind, and which build-time tool checks the result?
Start from `arch/mips/include/asm/sync.h`.

## mips.cm-access: Coherence manager access

- section: Kernel entry
- relevance: 3 - the redirect registers are shared state
- words: 70

When code needs to read or write the registers of another core through the
coherence manager, what usage is unsafe and what is correct, what may and may
not be done while the redirect is held, and how do SMP back ends register
themselves? Start from `mips_cm_lock_other()` and `struct plat_smp_ops`.

## mips.workarounds: Errata configuration

- section: Kernel entry
- relevance: 2 - where a workaround is switched on has moved
- words: 60

Where are CPU errata workarounds selected in this tree, how does code test for
them, and is there a header that collects them per platform?

# Changing the implementation

## mips.change-checklist: Changing TLB code

- section: What a change must preserve
- relevance: 4 - several copies and several builds share the rules
- words: 90

What must a change to the TLB maintenance or initialisation code keep working
besides the function it edits: the other implementations of the same
routines, the copies in KVM, the power management path, 32-bit and 64-bit
builds, CPUs with and without the optional TLB features? Are there any tests
or debug aids in the tree for it?
