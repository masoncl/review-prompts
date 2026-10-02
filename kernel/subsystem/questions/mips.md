# Questions: MIPS Subsystem Details

- guide: mips.md
- title: MIPS Subsystem Details

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/mips-measurement.md` is the
wider set the readers were measured on and `catalogue/mips-measurement-results.md` says what they
got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## mips.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## mips.core-files: Core files

- section: Finding your way
- relevance: 4 - turns a search into a lookup

A table and nothing else, job to file: TLB maintenance for each class of CPU; the generator of the
TLB exception handlers and the assembler it uses; address space id allocation; the TLB instruction
wrappers; the hazard barriers; the macros for invalid entry values and the wired entry count; the
TLB dump helpers; the CPU probing that sizes the TLB; KVM's TLB routines. Where the tree has no
file for a job, or one file does several jobs, say so in the row. Start from `arch/mips/mm/` and
`arch/mips/include/asm/`.

# TLB entries and primitives

## mips.hazards-and-wrappers: Hazard barriers and instruction wrappers

- section: TLB entries and primitives
- relevance: 4 - a missing barrier works on one core and fails on another

One table of which hazard barrier of `arch/mips/include/asm/hazards.h` goes between which
coprocessor 0 access and which TLB instruction or later use. Under which configuration symbols is
a barrier empty? Does any C wrapper for a TLB instruction in `arch/mips/include/asm/mipsregs.h`
put in a barrier itself, or is every barrier the caller's? Start from `mtc0_tlbw_hazard()` and
`tlb_probe()`.

## mips.unique-entryhi: Invalidated entry values

- section: TLB entries and primitives
- relevance: 5 - the value written into an invalidated entry decides whether two entries can match

What value do `UNIQUE_ENTRYHI()` and `UNIQUE_GUEST_ENTRYHI()` give for a TLB entry the kernel
invalidates, and what do they guarantee about the values for two different entries? What else does
the kernel set in EntryHi of an invalidated entry, and on which hardware? Start from
`UNIQUE_ENTRYHI()`.

## mips.pagemask: PageMask invariants

- section: TLB entries and primitives
- relevance: 4 - the rest of the mm code assumes one value

What value must the PageMask register hold outside the routines that change it, and how do the
routines that write another value put it back? What does the kernel do on a CPU whose PageMask
register does not hold `PM_DEFAULT_MASK`? Start from `PM_DEFAULT_MASK`.

## mips.wired-entries: Wired entries

- section: TLB entries and primitives
- relevance: 4 - wired entries survive flushes and restrict every index loop

What are the requirements for code that adds or removes a wired TLB entry without
`add_wired_entry()`, as `kmap_coherent()` does, in order to assure safe usage? Which code resets
the wired count, and what does `num_wired_entries()` take from the Wired register? Start from
`add_wired_entry()`, `num_wired_entries()` and `kmap_coherent()`.

# TLB initialisation

## mips.tlb-init-sequence: TLB initialisation order

- section: TLB initialisation
- relevance: 4 - the order is what makes the first flush safe

In what order does the kernel set up the TLB on the boot CPU, on a secondary CPU, and on a CPU
returning from a power state that lost it, and on the boot CPU does this happen before or
after the exception vectors are installed? Name the functions. Start from `tlb_init()` and
`per_cpu_trap_init()`.

## mips.uniquify: Uniquifying inherited entries

- section: TLB initialisation
- relevance: 5 - rewritten recently, and the algorithm is the subject of the old guide

Which TLB entries does `r4k_tlb_uniquify()` rewrite, and what does it guarantee about each value
it writes, against the entries still in the TLB and against the values `UNIQUE_ENTRYHI()` gives
later? Where does the memory it works in come from each time it runs? If this tree has no
`r4k_tlb_uniquify()`, say so and stop. Start from `r4k_tlb_uniquify()`.

## mips.uniquify-order: Order of uniquification

- section: TLB initialisation
- relevance: 5 - a change that reorders the steps can write a value that matches an entry still in the TLB

What does `r4k_tlb_uniquify()` rely on about the order in which it goes through the TLB entries it
has read? If this tree has no `r4k_tlb_uniquify()`, say so and stop. Start from
`r4k_tlb_uniquify()`.

## mips.uniquify-gating: Skipping uniquification

- section: TLB initialisation
- relevance: 4 - the step does not run everywhere and cannot

On which hardware does `r4k_tlb_configure()` not call `r4k_tlb_uniquify()`, and what does it rely
on there instead? Which TLB features can `r4k_tlb_uniquify()` not handle? If this tree has no
`r4k_tlb_uniquify()`, say so and stop. Start from `r4k_tlb_configure()`.

## mips.tlbinv: Hardware invalidate support

- section: TLB initialisation
- relevance: 4 - changes both the flush path and what an invalid entry looks like

How does the kernel detect what `cpu_has_tlbinv` reports, and what can force it off? What does
`local_flush_tlb_all()` do differently when `cpu_has_tlbinv` is true, with and without wired
entries? Start from `cpu_has_tlbinv`.

## mips.machine-check: Duplicate entry machine check

- section: TLB initialisation
- relevance: 5 - the failure the whole init sequence is built to avoid

Which exception and which status bit report that two TLB entries match one address? On which CPUs
does the kernel install a handler for that exception? Does the kernel continue after `do_mcheck()`
has run? Start from `do_mcheck()`.

## mips.init-tlb-usage: TLB operations before initialisation

- section: TLB initialisation
- relevance: 5 - the rule the old guide exists for

What are the requirements for code that calls `tlb_probe()`, `tlb_write_indexed()` or
`tlb_write_random()` while the TLB may still hold entries the kernel did not write, in order to
assure safe usage? Does the in-tree code ever write back a value it read from an inherited entry?
Name in-tree code that shows each.

# TLB maintenance

## mips.local-flush-pattern: Flushing one entry

- section: TLB maintenance
- relevance: 4 - the template every new TLB routine copies

What must a routine that removes the TLB entry for one address save and restore, and what must it
have disabled? What is different when `cpu_has_mmid` is true? Start from `local_flush_tlb_page()`
and `local_flush_tlb_one()`.

## mips.local-flush-write: Overwriting a flushed entry

- section: TLB maintenance
- relevance: 4 - a write to the wrong index or of the wrong value leaves two entries that can match

What does a routine that removes the TLB entry for one address write over the entry, and what does
it check before it writes? Start from `local_flush_tlb_page()` and `local_flush_tlb_one()`.

## mips.asid-mmid: Address space identifiers

- section: TLB maintenance
- relevance: 4 - two schemes with different scope share one set of helpers

Where is an address space identifier kept, and which register carries it, when `cpu_has_mmid` is
false and when it is true? What is flushed when the identifiers run out in each case? Start from
`cpu_context()` and `arch/mips/mm/context.c`.

## mips.drop-mmu-context: Dropping a context

- section: TLB maintenance
- relevance: 4 - the flush of a whole address space goes through it, and it does not do the same thing in every case

What does `drop_mmu_context()` guarantee about the TLB entries of the mm it is given, and how does
what it does depend on `cpu_has_mmid`? Start from `drop_mmu_context()`.

## mips.htw: Hardware page table walker

- section: TLB maintenance
- relevance: 4 - a walker that runs mid-sequence rewrites the registers being used

Do `htw_stop()` and `htw_start()` nest, and how, and must the caller have interrupts off? What are
the requirements for code that accesses the TLB registers on a CPU where `cpu_has_htw` is true? If
this tree has no `htw_stop()`, say so and stop. Start from `htw_stop()` and `cpu_has_htw`.

## mips.tlbex-generator: Generated exception handlers

- section: TLB maintenance
- relevance: 4 - the fast paths are not in any source file as written

Where in memory does the kernel put the generated refill handler and the generated load, store and
modify handlers, and what happens when generated code does not fit? What does
`build_tlb_refill_handler()` do again on every CPU, and what only on the first? Start from
`build_tlb_refill_handler()`.

## mips.change-checklist: Changing TLB code

- section: TLB maintenance
- relevance: 4 - several copies and several builds share the rules

What must a change to a routine of `arch/mips/mm/tlb-r4k.c` keep in step outside that file, and
what selects between `arch/mips/mm/tlb-r4k.c` and the other implementations of the same routines?
Which debug aids does the tree have for the TLB?

# CPU features and caches

## mips.cpu-features: cpu_has feature macros

- section: CPU features and caches
- relevance: 4 - the wrong test compiles and silently picks the wrong path

Whose data does a `cpu_has_` feature macro of `arch/mips/include/asm/cpu-features.h` read, and how
can a platform turn one into a compile-time constant? What are the requirements for code that
reads `current_cpu_data` in order to assure safe usage? Start from
`arch/mips/include/asm/cpu-features.h`.

## mips.cache-aliases: Data cache aliases

- section: CPU features and caches
- relevance: 4 - stale data with no crash

When `cpu_has_dc_aliases` is true, when is the flush of a page written through a kernel mapping
deferred, and when does the kernel use `kmap_coherent()` instead? What are the requirements for
code that writes to a page through a kernel mapping, in order to assure safe usage? Start from
`cpu_has_dc_aliases` and `__update_cache()`.

# Model gaps

## mips.model-gaps: Other mistakes models make

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
