# Questions: MM Folios

- guide: mm-folio.md
- title: MM Folios
- min-relevance: 3

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/mm-folio-measurement.md` is the
wider set the readers were measured on and `catalogue/mm-folio-measurement-results.md` says what
they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## folio.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## folio.core-files: Core files

- section: Finding your way
- relevance: 4 - several well-known files have moved

A table and nothing else, job to file: the folio structure; the flag accessors; reference
counting; the release path and the per-CPU LRU batches; the batch type they use; the page cache;
truncation and invalidation; writeback; GUP; the page-based wrappers. Where a job has no file of
its own in this tree, or its code is split between files, say so in the row.

## folio.entry-points: Entry points

- section: Finding your way
- relevance: 4 - turns a search into a lookup

A table and nothing else, job to the function this tree defines to start reading from: look a
folio up in the page cache; add one; remove one; lock it; take and drop a reference; put it on the
LRU; mark it dirty; start and end writeback; truncate; invalidate.

# Pages, heads and tails

## folio.not-folios: Non-folio compound pages

- section: Pages, heads and tails
- relevance: 4 - calling folio helpers on them reads the wrong fields

Which memory described by `struct page` is not a folio, and how does code tell whether a page it
found by PFN or by address belongs to a folio? What are the requirements for calling
`page_folio()` and the folio helpers on such a page in order to assure safe usage? Start from
`struct slab`, `struct ptdesc` and `folio_test_large()`.

## folio.page-types: Page types

- section: Pages, heads and tails
- relevance: 3 - a typed page has no mapcount

What does giving a page a type do to its mapcount, how does code tell a typed page from a mapped
one, and which typed pages are nevertheless folios that user space maps? Start from
`enum pagetype` in `include/linux/page-flags.h`.

## folio.tail-overlays: Tail page overlays

- section: Pages, heads and tails
- relevance: 4 - decides which orders a field exists for

From which folio order does each group of fields that `struct folio` keeps in the memory of its
tail pages exist? What are the requirements for reading or writing one of those fields in order to
assure safe usage, and which test do in-tree callers make first? Start from `FOLIO_MATCH`.

## folio.layout-change: Changing the folio layout

- section: Pages, heads and tails
- relevance: 4 - the structure is overlaid on another in four places

What must a change that adds or moves a field in `struct folio` keep true about `struct page`,
the tail-page overlays and the other descriptors that share the memory, and what fails to
compile if it does not? Start from `FOLIO_MATCH` and `struct ptdesc`.

# Converting between pages and folios

## folio.page-to-folio: Page to folio

- section: Converting between pages and folios
- relevance: 4 - the conversion has preconditions that are easy to break

How does `page_folio()` find the folio for a page, and what are the requirements for the page
pointer it is given? What must a caller that holds no reference on the page recheck before it uses
the result? Start from `page_folio()` and `compound_head()`.

## folio.folio-page: Folio to page

- section: Converting between pages and folios
- relevance: 3 - unchecked arithmetic

What are the requirements for the index passed to `folio_page()` in order to assure safe usage,
and what does it do with an index beyond the folio? Which page of a large folio does a page table
entry that maps part of it refer to? Start from `folio_page()`.

## folio.stat-accounting: Folio statistics helpers

- section: Converting between pages and folios
- relevance: 3 - converting a caller to folios changes the unit

In what unit do `lruvec_stat_mod_folio()`, `node_stat_mod_folio()` and the other statistics
helpers that take a folio count? Which of them scale the value by the number of pages in the folio
themselves? What are the requirements for the value a caller passes to each in order to assure
safe usage? Start from `lruvec_stat_mod_folio()` and `node_stat_mod_folio()`.

## folio.kmap: kmap of a folio

- section: Converting between pages and folios
- relevance: 2 - only matters with high memory

How much of a folio does `kmap_local_folio()` map? What are the requirements for using the address
it returns on a large folio, where there is high memory, in order to assure safe usage, and what
must code that touches a whole large folio do? Start from `include/linux/highmem.h`.

## folio.compat-wrappers: Page-based wrappers

- section: Converting between pages and folios
- relevance: 2 - they hide a conversion

What do the page-based wrappers in `mm/folio-compat.c` do when handed a tail page? What are the
requirements for converting a caller from the page form to the folio form in order to keep its
behaviour the same? Start from `mm/folio-compat.c`.

# References and mapcounts

## folio.refcount-holders: Reference holders

- section: References and mapcounts
- relevance: 5 - every "is it safe to free or migrate" decision rests on this

A table of what holds references on a folio: how many each holder has on a small folio and on a
large one. Then what the table cannot show: does being on the LRU, or waiting in a per-CPU batch,
hold one? Start from `folio_expected_ref_count()`.

## folio.mapcount-vs-refcount: Mapcount and reference count

- section: References and mapcounts
- relevance: 4 - the relation is relied on everywhere

What relation holds between `folio_mapcount()` and `folio_ref_count()`, and in which order do
callers change the two when they add a mapping and when they remove one? What may code conclude
from the two values when it reads them while mappings can still be added or removed? Start from
the callers of `folio_add_file_rmap_ptes()` and `folio_remove_rmap_ptes()` in `mm/memory.c`.

## folio.try-get: Taking a reference

- section: References and mapcounts
- relevance: 4 - the wrong variant on a possibly-free folio corrupts the count

What are the requirements for calling `folio_get()` and for calling `folio_try_get()` in order to
assure safe usage: which of them may be used on a folio the caller holds no reference on? What
must be rechecked after `folio_try_get()` succeeds on such a folio? Start from `folio_get()` and
`folio_try_get()`.

## folio.expected-ref-count: Expected reference count

- section: References and mapcounts
- relevance: 4 - migration, splitting and reclaim all compare against it

What does `folio_expected_ref_count()` add up, what does it leave out that the caller must add,
and what must be held or excluded for a comparison of the folio's count against it to mean
anything? Start from `include/linux/mm.h`.

## folio.ref-freeze-exact: Freezing and exact counts

- section: References and mapcounts
- relevance: 4 - the only way to get exclusive ownership of a live folio

What does `folio_ref_freeze()` do to the reference count, and what does `folio_try_get()` return
while the count is frozen? What can raise the reference count of a folio for a short time while a
caller that has not frozen it compares the count against an exact value? Start from
`folio_ref_freeze()` in `include/linux/page_ref.h`.

## folio.pincount: Recording a pin

- section: References and mapcounts
- relevance: 3 - the test for a pin can be wrong in one direction

How is a pin from `pin_user_pages()` recorded on a folio that has a separate pin count and on
one that does not, which folios have one, and in which direction can `folio_maybe_dma_pinned()`
be wrong? Start from `folio_has_pincount()` and `mm/gup.c`.

## folio.mapcount-fields: Mapcount fields

- section: References and mapcounts
- relevance: 4 - the fields differ by folio size and by configuration

Which counters does this tree keep to say how often a small folio and a large folio are mapped,
and what stored value means not mapped? What does `CONFIG_NO_PAGE_MAPCOUNT` change for code that
reads the mapcount of one page? Start from `folio_mapcount()` and `folio_entire_mapcount()`.

## folio.mapped-tests: Mapped tests

- section: References and mapcounts
- relevance: 3 - several similar helpers

Which helpers answer whether a folio is mapped, how many times it is mapped, and whether one page
of it is mapped? Which of them are exact for a large folio? Start from `folio_mapped()`.

## folio.mm-id-tracking: Per-mm mapcount tracking

- section: References and mapcounts
- relevance: 3 - replaces a test people remember

What does a large folio record about which address spaces map it? What does
`folio_maybe_mapped_shared()` guarantee: when can it return true for a folio that one address
space maps, and when false for a folio that several map? Start from `folio_maybe_mapped_shared()`
and `_mm_id_mapcount`.

# The mapping and private fields

## folio.mapping-field: The mapping field

- section: The mapping and private fields
- relevance: 4 - its low bits are flags, and NULL has a meaning

What can `folio->mapping` contain besides a pointer to an address space, and what does NULL mean
for a folio that was found in the page cache? What are the requirements for reading
`folio->mapping` directly, without `folio_mapping()`, in order to assure safe usage? Start from
`FOLIO_MAPPING_ANON` and `folio_mapping()`.

## folio.private: The private field

- section: The mapping and private fields
- relevance: 3 - it shares storage, and its validity depends on a flag

Who owns `folio->private`, and what does `folio_attach_private()` change on the folio besides the
field? What are the requirements for reading the field of a folio that a page-cache lookup
returned, in order to assure safe usage? Start from `folio_attach_private()`.

# The folio lock

## folio.lock: Scope and lock order

- section: The folio lock
- relevance: 4 - what it protects is not written on it

What does the folio lock protect and what does it not, may taking it sleep, and where does it
come in the mm lock order relative to the mmap lock and the page cache's own lock? Start from
`folio_lock()`, `folio_trylock()` and the comment at the top of `mm/filemap.c`.

## folio.recheck-after-lock: Rechecking after locking

- section: The folio lock
- relevance: 4 - the classic truncate race

Between a page-cache lookup that returns a folio and `folio_lock()` on it, what can change about
the folio? What are the requirements for using the folio once the lock is held in order to assure
safe usage, and what do in-tree callers recheck? Name a function that shows it. Start from
`filemap_fault()` or `truncate_inode_pages_range()`.

## folio.uptodate: Completing a read

- section: The folio lock
- relevance: 3 - one helper does two flag changes at once

What does `folio_end_read()` do to the flags of the folio? What are the requirements for the state
of a folio passed to it, and for what the caller does with the folio afterwards, in order to
assure safe usage? Start from `mm/filemap.c`.

## folio.lock-after-gup: Locking several folios

- section: The folio lock
- relevance: 3 - trylock versus lock

What are the requirements for holding the folio lock on more than one folio at a time, in order to
assure safe usage? When may code that took references on several folios through GUP call
`folio_lock()` on each of them? Name in-tree code that shows it.

## folio.lock-at-error-labels: Lock state on error paths

- section: The folio lock
- relevance: 2 - generic, but the labels in mm are long

Which of the folio lock functions can return without holding the lock, and what does each return
then? What are the requirements for calling `folio_unlock()` on an error path that follows one of
them, in order to assure safe usage? Start from `folio_lock_killable()`.

# Flags

## folio.flags-word: The flags word

- section: Flags
- relevance: 3 - more than flags live there

What type is the flags word of a folio in this tree, and what besides flags is packed into it?
When a flag accessor is handed a tail page, what decides which page's word it touches? Start from
`enum pageflags` and the comment on the flag policies in `include/linux/page-flags.h`.

## folio.second-page-flags: Flags on the second page

- section: Flags
- relevance: 3 - the accessor touches a page that not every folio has

How is a flag that is kept on the second page of a large folio declared, and what are the
requirements for a folio passed to its accessors, in order to assure safe usage? Start from
`PF_SECOND` and `FOLIO_SECOND_PAGE`.

## folio.flag-ownership: Flag ownership

- section: Flags
- relevance: 4 - flags have owners and different locking

A table of the folio flags whose changes have an owner (locked, uptodate, dirty, writeback, lru,
active, referenced, private, swapbacked, swapcache, mlocked, unevictable): who sets and clears
each, and under which lock or atomicity rule. Then what the table cannot show: when the
non-atomic accessors are safe to use.

## folio.flag-tests-need-ref: Flag tests without a reference

- section: Flags
- relevance: 4 - the result describes whatever the memory is now

What are the requirements for testing a flag of a folio, or reading `folio->mapping`, in order to
assure safe usage: what must the caller hold for the result to describe the folio it meant? What
may a caller that holds no reference do with the result? Which debugging checks fire when the
pointer is a tail page or freed memory? Start from `PF_POISONED_CHECK` and `folio_flags()`.

## folio.adding-a-flag: Adding a page flag

- section: Flags
- relevance: 3 - the bits are scarce and the accessors are generated

What must a change that adds a page flag update besides the enumeration so that the accessors,
the debug output and the tracing tables keep working, what limits the number of bits and where
does the build check it, and how is a flag confined to the configurations that need it? Start
from `PAGEFLAG` and `include/trace/events/mmflags.h`.

# The LRU

## folio.lru-batching: Per-CPU LRU batching

- section: The LRU
- relevance: 4 - a folio is often not where its flags say

While a folio sits in one of the per-CPU batches of `struct cpu_fbatches`, is its LRU flag set,
and does the batch hold a reference on it? What makes `folio_batch_move_lru()` run before a batch
is full? Start from `struct cpu_fbatches` and `folio_batch_move_lru()` in `mm/folio.c`.

## folio.lru-drain: Draining LRU batches

- section: The LRU
- relevance: 3 - callers that need an exact LRU state must drain

What do `lru_add_drain()`, `lru_add_drain_all()` and `lru_cache_disable()` each guarantee about
folios that this CPU and other CPUs have queued, and for how long? What are the requirements for
code that needs every folio it examines to be on an LRU list, in order to assure safe usage? Name
in-tree code that shows it. Start from `lru_add_drain()`, `lru_add_drain_all()` and
`lru_cache_disable()`.

## folio.lru-flags: LRU placement flags

- section: The LRU
- relevance: 3 - they are changed under a different lock from the rest

Under which lock are a folio's LRU list and its placement flags changed, what does isolating a
folio do to those flags and to its reference count, and what must a caller hold or have tested
before it isolates one? Start from `folio_isolate_lru()` and `lruvec_add_folio()`.

## folio.lazyfree: Lazyfree folios

- section: The LRU
- relevance: 4 - a state encoded in two flags and changed from three places

How is a lazily freed anonymous folio encoded in its flags, and what puts it in that state? What
do reclaim and a later write each do to such a folio and to its flags? Start from
`folio_mark_lazyfree()`, `lru_lazyfree()` and `try_to_unmap_one()`.

## folio.mark-accessed: Recording an access

- section: The LRU
- relevance: 2 - behaviour differs with the multi-generation LRU

What does `folio_mark_accessed()` do on a first and on a second access, and how does that change
when the multi-generation LRU is enabled? Start from `mm/folio.c`.

# PFN scanners

## folio.speculative-access: Speculative access from a PFN

- section: PFN scanners
- relevance: 5 - the scanner holds nothing that keeps the memory a folio

What are the requirements for code that finds a page by PFN and holds no reference on it, in order
to assure safe usage: what may it read before it takes a reference, and how must it take one? What
must it recheck after the reference is taken? Name a scanner that shows it. Start from
`mm/compaction.c` and `mm/page_idle.c`.

## folio.order-reads: Order, size and stepping

- section: PFN scanners
- relevance: 3 - the read can be torn, and the step is computed from a folio that may have changed

Where does a folio keep its order and its number of pages? What do `compound_order()`,
`folio_order()` and `folio_nr_pages()` guarantee when the caller holds no reference on the folio?
What are the requirements for a PFN walker that uses one of them to step past a large folio, in
order to assure safe usage? Start from `compound_order()`, `folio_order()` and `folio_nr_pages()`.

## folio.pfn-validity: PFN validity

- section: PFN scanners
- relevance: 3 - PFN walkers hit holes and offline sections

What does `pfn_valid()` guarantee, and what does `pfn_to_online_page()` add? What are the
requirements for a PFN passed to `pfn_to_page()` in order to assure safe usage? Start from
`include/linux/mmzone.h` and `mm/memory_hotplug.c`.

## folio.sections: Memmap contiguity across sections

- section: PFN scanners
- relevance: 2 - one memory model

Under which memory model are the pages of a physically contiguous range not contiguous in the
`struct page` array or in per-section side tables? What are the requirements for arithmetic on
`struct page` pointers there in order to assure safe usage, and what keeps code that steps from
one page of a folio to the next correct in this tree? Start from
`include/asm-generic/memory_model.h`.

# Page cache lookup

## folio.pagecache-structure: Page cache storage

- section: Page cache lookup
- relevance: 4 - the entries are not always folios

What can a slot of `i_pages` hold besides a folio, and how is a large folio represented across the
indices it covers? What are the requirements for using an entry loaded from `i_pages` as a folio
in order to assure safe usage? Start from `i_pages` and `xa_is_value()`.

## folio.lookup-api: Lookup functions and FGP flags

- section: Page cache lookup
- relevance: 4 - the return convention changed from what people remember

A table of the page cache lookup functions to choose from: what each returns when there is no
folio, and whether it can create, lock or wait. Which `fgf_t` flags change what failure looks like
or whether the call may sleep? Start from `__filemap_get_folio()` and `filemap_get_folio()`.

## folio.lockless-lookup: Lockless lookup protocol

- section: Page cache lookup
- relevance: 5 - every step is there for a race

What are the requirements for a lockless page-cache lookup between loading the slot and returning
a referenced folio, in order to assure safe usage: what does `filemap_get_entry()` recheck, and
what race does each recheck close? Start from `filemap_get_entry()`.

## folio.batch-lookups: Batch lookups

- section: Page cache lookup
- relevance: 4 - the variants differ in what they return and lock

A table to choose from, for `find_get_entries()`, `find_lock_entries()`, `filemap_get_folios()`
and its tagged and contiguous forms: which return value entries, which lock the folios, and how
each treats a large folio that straddles the start or the end of the range.

## folio.xas-multi-index: Multi-index entries

- section: Page cache lookup
- relevance: 3 - the walk can visit one entry many times

What does `xas_next()` return for each index that a multi-index entry covers? What are the
requirements for a loop over a range of `i_pages` that must handle each folio once, in order to
assure safe usage? Under what lock is the value of `xa_get_order()` stable? Start from
`xas_next()` and `xa_get_order()`.

## folio.info-disclosure: Cache residency disclosure

- section: Page cache lookup
- relevance: 2 - a side channel

What permission check limits the system calls that report whether file data is cached, and what
must a new interface that exposes cache residency do? Start from `can_do_mincore()` and
`can_do_cachestat()`.

# Page cache insertion and removal

## folio.add-to-cache: Adding to the page cache

- section: Page cache insertion and removal
- relevance: 4 - references, charge and lock all change hands here

What are the requirements for the folio passed to `filemap_add_folio()`, and for what its caller
holds, in order to assure safe usage? What does the function hold or change on the folio when it
succeeds, and what when it fails? Start from `filemap_add_folio()` and `__filemap_add_folio()`.

## folio.shadow-entry-on-add: Shadow entries at insertion

- section: Page cache insertion and removal
- relevance: 4 - the slot a folio goes into may already hold an entry

What does `__filemap_add_folio()` do with a shadow entry that is already in the slot, and with one
that covers more indices than the folio? Start from `__filemap_add_folio()`.

## folio.remove-from-cache: Removing from the page cache

- section: Page cache insertion and removal
- relevance: 3 - who drops the cache's references

Of the functions that remove a folio from the page cache, which is used when, what must the
caller hold, and who drops the references the cache held? Start from `filemap_remove_folio()`
and `__filemap_remove_folio()`.

## folio.large-folio-support: Large folio support

- section: Page cache insertion and removal
- relevance: 3 - a filesystem opts in and sets bounds

How does a filesystem say that a mapping may hold large folios and bound their order, what does
each setter do to the bound it does not name, and what must code that allocates a folio for the
cache respect? Start from `mapping_set_large_folios()` and `mapping_set_folio_order_range()`.

## folio.truncate-vs-invalidate: Truncation and invalidation

- section: Page cache insertion and removal
- relevance: 4 - the two look alike and promise different things

Which folios may `truncate_inode_pages_range()` and `invalidate_inode_pages2_range()` each leave
in the cache, and how does each report that? What does `mapping_evict_folio()` check before it
removes a folio? Start from `mm/truncate.c`.

## folio.mapping-set-update: Workingset hook on cache nodes

- section: Page cache insertion and removal
- relevance: 2 - every modifier of the tree must set it

What does `mapping_set_update()` install on an XArray cursor, and what does the installed function
keep up to date? What are the requirements for code that stores to or erases from `i_pages` in
order to assure safe usage? Start from `mm/internal.h`.

## folio.dropbehind: Uncached buffered I/O

- section: Page cache insertion and removal
- relevance: 2 - a newer path through the cache

What does the drop-behind flag on a folio mean, who sets and clears it, and when is such a folio
removed from the cache and when is it kept? Start from `PG_dropbehind` and `FGP_DONTCACHE`.

# Allocating and freeing

## folio.alloc: Allocating a folio

- section: Allocating and freeing
- relevance: 3 - the entry points and what state they hand back

Of `folio_alloc()`, `filemap_alloc_folio()` and `vma_alloc_folio()`, which is used when, and what
does each apply that the others do not? In what state is a fresh folio handed back? Start from
`folio_alloc()`, `filemap_alloc_folio()` and `vma_alloc_folio()`.

## folio.free: Freeing a folio

- section: Allocating and freeing
- relevance: 3 - what runs when the last reference goes

What does `__folio_put()` undo when the last reference on a folio is dropped, and in what order?
What does it do differently for a large, a hugetlb and a zone-device folio? From which contexts
may `folio_put()` drop the last reference? Start from `folio_put()` and `__folio_put()` in
`mm/folio.c`.

## folio.zone-device: Zone-device folios

- section: Allocating and freeing
- relevance: 2 - a few drivers

What does `free_zone_device_folio()` do with a zone-device folio whose last reference is dropped?
What must be set again before such a folio is handed out again, and does `zone_device_page_init()`
or its caller set it? Start from `mm/memremap.c` and `zone_device_page_init()`.

# Model gaps

## folio.model-gaps: Other mistakes models make

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
