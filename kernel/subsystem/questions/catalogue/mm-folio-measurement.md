# Questions: MM Folios (measurement set)

- guide: mm-folio.md
- title: MM Folios

A wide set of questions about folios, used to measure what a model already
knows before deciding what the built guide should spend its words on. Run it
with `build-guides.py --no-sources --check-memory --questions` pointed at this
directory. The trimmed set a guide is built from is `../mm-folio.md`.

# What a folio is

## folio.what-it-represents: Folios and pages

- section: The structure
- relevance: 3 - the definition everything else rests on
- words: 60

What is a folio, how does it relate to `struct page` and to a compound page's
head and tail pages, and can a single page be one? Start from `struct folio`
in `include/linux/mm_types.h`.

## folio.fields: Fields by purpose

- section: The structure
- relevance: 3 - a map of the structure
- words: 140

Group the fields of `struct folio` by what they are for (flags, list linkage,
owner and position, private data, counts, memcg, and the fields only a large
folio has) and say in a table what each group holds, including fields that
share storage in a union.

## folio.tail-overlays: Tail page overlays

- section: The structure
- relevance: 4 - decides which orders a field exists for
- words: 100

A large folio keeps extra fields in the memory of its tail pages. Which fields
live in the first, second and third tail page, from which order does each
therefore exist, and how does the build check that the layout still matches
`struct page`? Start from `FOLIO_MATCH`.

## folio.order-and-size: Order and page count

- section: The structure
- relevance: 3 - the two are confused in loops and accounting
- words: 70

Where are a folio's order and number of pages stored, which helpers read them,
and is a separate page count kept under some configuration? Start from
`folio_order()` and `folio_nr_pages()`.

## folio.flags-word: The flags word

- section: The structure
- relevance: 3 - more than flags live there
- words: 80

What type is a folio's flags word in this tree, what besides flags is packed
into it, and which flags are only meaningful on the head page and which on a
particular tail? Start from `enum pageflags` and the `PF_` policies in
`include/linux/page-flags.h`.

## folio.page-types: Page types

- section: The structure
- relevance: 3 - a typed page has no mapcount
- words: 80

What is a page type, where is it stored, which types exist, and why can a page
not have both a type and a mapcount? Start from `PGTY_` in
`include/linux/page-flags.h`.

## folio.not-folios: Non-folio compound pages

- section: The structure
- relevance: 4 - calling folio helpers on them reads the wrong fields
- words: 100

Which users of `struct page` memory are not folios (slab, page tables, zsmalloc,
large kmalloc, others), what describes each instead, and how does code tell
whether a page it found belongs to a folio? Start from `struct slab`,
`struct ptdesc` and `folio_test_large()`.

## folio.page-to-folio: Page to folio

- section: Converting between pages, folios and PFNs
- relevance: 4 - the conversion has preconditions that are easy to break
- words: 90

How does `page_folio()` find the folio for a page, what must be true of the
pointer it is given, and what can change under it if the caller holds no
reference? Start from `page_folio()` and `compound_head()`.

## folio.folio-page: Folio to page

- section: Converting between pages, folios and PFNs
- relevance: 3 - unchecked arithmetic
- words: 60

What does `folio_page()` do with an index beyond the folio, which page of a
large folio does a page table entry refer to, and which helper gives that page?
Start from `folio_page()`.

## folio.pfn-validity: PFN validity

- section: Converting between pages, folios and PFNs
- relevance: 3 - PFN walkers hit holes and offline sections
- words: 70

What does `pfn_valid()` guarantee and what does `pfn_to_online_page()` add, and
on which PFNs is `pfn_to_page()` safe to call at all? Start from
`include/linux/mmzone.h` and `mm/memory_hotplug.c`.

## folio.kmap: Mapping folio memory

- section: Converting between pages, folios and PFNs
- relevance: 2 - only matters with high memory
- words: 50

How much of a folio does `kmap_local_folio()` map, and what must code that
touches a whole large folio do? Start from `include/linux/highmem.h`.

## folio.alloc: Allocation

- section: The life of a folio
- relevance: 3 - the entry points and what state they hand back
- words: 80

Which functions allocate a folio for the page cache, for anonymous memory and
in general, and what reference count, flags and order does a fresh folio have?
Start from `folio_alloc()`, `filemap_alloc_folio()` and `vma_alloc_folio()`.

## folio.free: Freeing

- section: The life of a folio
- relevance: 3 - what runs when the last reference goes
- words: 90

What happens when a folio's last reference is dropped: which function runs,
what does it remove the folio from, and what is different for a large, a
hugetlb and a zone-device folio? Start from `folio_put()` and `__folio_put()`
in `mm/folio.c`.

## folio.zone-device: Zone-device folios

- section: The life of a folio
- relevance: 2 - a few drivers
- words: 70

How do zone-device folios differ in how their reference count and metadata are
handled, and what must be reinitialised when one is handed out again? Start
from `mm/memremap.c` and `zone_device_page_init()`.

# Counting

## folio.refcount-holders: Reference holders

- section: References
- relevance: 5 - every "is it safe to free or migrate" decision rests on this
- words: 110

List what holds references on a folio (the page cache, each mapping, private
data, the swap cache, a pin, isolation from the LRU) and how many each holds
for a large folio. Does being on the LRU hold one?

## folio.expected-ref-count: Expected reference count

- section: References
- relevance: 4 - migration, splitting and reclaim all compare against it
- words: 80

What does `folio_expected_ref_count()` add up, what does it leave out that the
caller must add, and which callers compare a folio's count against it? Start
from `include/linux/mm.h`.

## folio.ref-freeze: Freezing the reference count

- section: References
- relevance: 4 - the only way to get exclusive ownership of a live folio
- words: 80

What does freezing a folio's reference count do, what does a lockless reader
that tries to take a reference see meanwhile, and who uses it? Start from
`folio_ref_freeze()` in `include/linux/page_ref.h`.

## folio.try-get: Taking a reference

- section: References
- relevance: 4 - the wrong variant on a possibly-free folio corrupts the count
- words: 80

Which functions take a reference on a folio, which of them may be used on a
folio the caller does not already hold, and what must be rechecked after one
of those succeeds? Start from `folio_get()` and `folio_try_get()`.

## folio.pincount: Pins

- section: References
- relevance: 3 - the test for a pin can be wrong in one direction
- words: 80

How is a pin from `pin_user_pages()` recorded on a small folio and on a large
one, and in which direction can `folio_maybe_dma_pinned()` be wrong? Start from
`folio_has_pincount()` and `mm/gup.c`.

## folio.refcount-as-state: Exact reference count tests

- section: References
- relevance: 3 - transient references make any exact comparison racy
- words: 60

Why is comparing a folio's reference count against an exact value unreliable
without first excluding others, and what raises the count transiently?

## folio.mapcount-fields: Mapcount fields

- section: Mapcount
- relevance: 4 - the fields differ by folio size and by configuration
- words: 110

Which fields record how often a small folio, and a large folio, is mapped: per
page, as a whole, and in total? What value means "not mapped", and which
configuration removes the per-page counts? Start from `folio_mapcount()`,
`folio_entire_mapcount()` and `CONFIG_NO_PAGE_MAPCOUNT`.

## folio.mm-id-tracking: Per-mm mapcount tracking

- section: Mapcount
- relevance: 3 - replaces a test people remember
- words: 80

What does a large folio record about which address spaces map it, which helper
answers "may this folio be mapped by more than one", and how exact is it? Start
from `folio_maybe_mapped_shared()` and `_mm_id_mapcount`.

## folio.mapcount-vs-refcount: Mapcount and reference count

- section: Mapcount
- relevance: 4 - the relation is relied on everywhere
- words: 60

What relation holds between a folio's mapcount and its reference count, in
which order are they changed when a mapping is added or removed, and what may a
reader conclude from seeing one without the other?

## folio.mapped-tests: Mapped tests

- section: Mapcount
- relevance: 3 - several similar helpers
- words: 70

Which helpers answer "is this folio mapped", "how many times" and "is this page
of it mapped", and which of them are exact for a large folio? Start from
`folio_mapped()`.

# Locks and flags

## folio.lock: The folio lock

- section: The folio lock
- relevance: 4 - what it protects is not written on it
- words: 100

What does the folio lock protect, how is it implemented, may it sleep, and
where does it come in the mm lock order? Start from `folio_lock()`,
`folio_trylock()` and the comment at the top of `mm/filemap.c`.

## folio.recheck-after-lock: Rechecking after locking

- section: The folio lock
- relevance: 4 - the classic truncate race
- words: 70

Between finding a folio and locking it, which of its fields can change, and
what must be rechecked once the lock is held? Name a function that shows the
recheck. Start from `filemap_fault()` or `truncate_inode_pages_range()`.

## folio.lock-after-gup: Locking after GUP

- section: The folio lock
- relevance: 3 - trylock versus lock
- words: 60

When code has taken references on several folios through GUP and then needs
them locked, what locking strategy avoids deadlock, and which in-tree code does
it?

## folio.lock-at-error-labels: Lock state on error paths

- section: The folio lock
- relevance: 2 - generic, but the labels in mm are long
- words: 40

Which folio lock functions can fail or be interrupted without taking the lock,
and what must an error label therefore know? Start from `folio_lock_killable()`.

## folio.flag-ownership: Flag ownership

- section: Flags
- relevance: 4 - flags have owners and different locking
- words: 110

For the main folio flags (locked, uptodate, dirty, writeback, lru, active,
referenced, private, swapbacked, swapcache, mlocked, unevictable), who sets and
clears each and under which lock or atomicity rule? A table.

## folio.flag-tests-need-ref: Flag tests without a reference

- section: Flags
- relevance: 4 - the result describes whatever the memory is now
- words: 60

What does a flag test or a read of `folio->mapping` mean on a folio the caller
holds no reference to, and what debugging check fires on a tail page? Start
from `PF_POISONED_CHECK` and `folio_flags()`.

## folio.uptodate: Completing a read

- section: Flags
- relevance: 3 - one helper does two flag changes at once
- words: 60

How does `folio_end_read()` set uptodate and clear locked, and what goes wrong
if it is called on a folio that is already uptodate? Start from `mm/filemap.c`.

## folio.mapping-field: The mapping field

- section: Flags
- relevance: 4 - its low bits are flags, and NULL has a meaning
- words: 90

What can `folio->mapping` contain: which low bits mark anonymous, KSM or
movable, what does NULL mean for a page-cache folio, and what do tail pages
hold there? Start from `FOLIO_MAPPING_ANON` and `folio_mapping()`.

## folio.private: The private field

- section: Flags
- relevance: 3 - it shares storage, and its validity depends on a flag
- words: 80

Who owns `folio->private`, what shares its storage, how is attaching data to it
tied to a flag and a reference, and when may it be read after a page-cache
lookup? Start from `folio_attach_private()`.

# The page cache

## folio.pagecache-structure: Page cache storage

- section: Storage and lookup
- relevance: 4 - the entries are not always folios
- words: 90

What structure holds a file's cached folios, what kinds of entry can a slot
hold besides a folio, and how is a large folio represented? Start from
`i_pages` and `xa_is_value()`.

## folio.lookup-api: Page cache lookup

- section: Storage and lookup
- relevance: 4 - the return convention changed from what people remember
- words: 90

Which functions look up a folio in the page cache, what do the `FGP_` flags ask
for, and what is returned when there is none? Start from
`__filemap_get_folio()` and `filemap_get_folio()`.

## folio.lockless-lookup: Lockless lookup protocol

- section: Storage and lookup
- relevance: 5 - every step is there for a race
- words: 100

List the steps a lockless page-cache lookup takes from loading the slot to
returning a referenced folio, and say what each recheck protects against. Start
from `filemap_get_entry()`.

## folio.batch-lookups: Batch lookups

- section: Storage and lookup
- relevance: 4 - the variants differ in what they return and lock
- words: 110

For `find_get_entries()`, `find_lock_entries()`, `filemap_get_folios()` and its
tagged and contiguous forms: which return value entries, which lock the folios,
and how does each treat a large folio that straddles the range? A table.

## folio.xas-multi-index: Multi-index entries

- section: Storage and lookup
- relevance: 3 - the walk can visit one entry many times
- words: 70

What does stepping an XArray cursor over a multi-index entry return for each
index it covers, and under what lock is the order of an entry stable? Start
from `xas_next()` and `xa_get_order()`.

## folio.add-to-cache: Adding to the page cache

- section: Changing what is cached
- relevance: 4 - references, charge and lock all change hands here
- words: 100

What does adding a folio to the page cache do, in order: the memcg charge, the
lock, the references taken, what happens to a shadow entry already in the slot,
and what limits the folio's order? Start from `filemap_add_folio()` and
`__filemap_add_folio()`.

## folio.remove-from-cache: Removing from the page cache

- section: Changing what is cached
- relevance: 3 - who drops the cache's references
- words: 80

Which functions remove a folio from the page cache, what must the caller hold,
and who drops the references the cache held? Start from
`filemap_remove_folio()` and `__filemap_remove_folio()`.

## folio.large-folio-support: Large folio support

- section: Changing what is cached
- relevance: 3 - a filesystem opts in and sets bounds
- words: 70

How does a filesystem say that a mapping may hold large folios and bound their
order, and which helpers read those bounds? Start from
`mapping_set_large_folios()` and `mapping_set_folio_order_range()`.

## folio.truncate-vs-invalidate: Truncation and invalidation

- section: Changing what is cached
- relevance: 4 - the two look alike and promise different things
- words: 110

How do truncating and invalidating cached folios differ in what they do with a
dirty, a mapped or a busy folio, and which checks guard removing one? Start
from `truncate_inode_pages_range()`, `invalidate_inode_pages2_range()` and
`mapping_evict_folio()` in `mm/truncate.c`.

## folio.mapping-set-update: Workingset hook on cache nodes

- section: Changing what is cached
- relevance: 2 - every modifier of the tree must set it
- words: 60

What does `mapping_set_update()` install on an XArray cursor, why must page
cache modifications use it, and which modifiers do? Start from `mm/internal.h`.

## folio.info-disclosure: Cache residency disclosure

- section: Changing what is cached
- relevance: 2 - a side channel
- words: 60

Which system calls report whether file data is cached, and what permission
check limits them? Start from `can_do_mincore()` and `can_do_cachestat()`.

## folio.dropbehind: Uncached buffered I/O

- section: Changing what is cached
- relevance: 2 - a newer path through the cache
- words: 60

What does the drop-behind flag on a folio mean, who sets it, and when is such a
folio removed from the cache? Start from `PG_dropbehind` and `FGP_DONTCACHE`.

# The LRU

## folio.lru-batching: Per-CPU LRU batching

- section: LRU lists
- relevance: 4 - a folio is often not where its flags say
- words: 100

Which per-CPU batches sit in front of the LRU lists, what does a folio look
like while it is in one (flags, references), and what forces a batch to be
flushed early? Start from `struct cpu_fbatches` and `folio_batch_move_lru()` in
`mm/folio.c`.

## folio.lru-drain: Draining LRU batches

- section: LRU lists
- relevance: 3 - callers that need an exact LRU state must drain
- words: 70

Which functions drain the per-CPU batches for one CPU and for all, which
callers need that, and what does disabling the cache do? Start from
`lru_add_drain()`, `lru_add_drain_all()` and `lru_cache_disable()`.

## folio.lru-flags: LRU placement flags

- section: LRU lists
- relevance: 3 - they are changed under a different lock from the rest
- words: 80

Which flags say which LRU list a folio is on, under which lock are they and the
list changed, and what does isolating a folio do to them? Start from
`folio_isolate_lru()` and `lruvec_add_folio()`.

## folio.lazyfree: Lazyfree folios

- section: LRU lists
- relevance: 4 - a state encoded in two flags and changed from three places
- words: 110

How is a lazily freed anonymous folio encoded in its flags, which function puts
it in that state and onto which list, and what do reclaim and a later write each
do to it? Start from `folio_mark_lazyfree()`, `lru_lazyfree()` and
`try_to_unmap_one()`.

## folio.mark-accessed: Recording an access

- section: LRU lists
- relevance: 2 - behaviour differs with the multi-generation LRU
- words: 60

What does `folio_mark_accessed()` do on first and second access, and how does
that change when the multi-generation LRU is enabled? Start from `mm/folio.c`.

# Scanning by PFN

## folio.speculative-access: Speculative access from a PFN

- section: PFN scanners
- relevance: 5 - the scanner holds nothing that keeps the memory a folio
- words: 100

Code that walks PFNs (compaction, memory failure, page idle tracking, hotplug)
finds pages it holds no reference on. In what order must it take a reference
and test the page, and what must it recheck afterwards? Name a scanner that
does it correctly.

## folio.pfn-step: Stepping over a large folio

- section: PFN scanners
- relevance: 3 - the step is computed from a folio that may have changed
- words: 70

How should a PFN walker advance past a large folio, and what goes wrong if the
number of pages is read after the reference has been dropped or from a tail
page?

## folio.order-without-ref: Order without a reference

- section: PFN scanners
- relevance: 3 - the read can be torn by a concurrent free or split
- words: 60

What can a scanner trust about a compound page's order when it holds no
reference, and which helper exists for reading it that way? Start from
`compound_order()` and `folio_order()`.

## folio.sections: Per-section metadata

- section: PFN scanners
- relevance: 2 - one memory model
- words: 60

Under which memory model are a large folio's pages not contiguous in the
`struct page` array or in per-section side tables, and which helper steps
between them safely?

# Changing the implementation

## folio.layout-change: Changing the layout

- section: What a change must preserve
- relevance: 4 - the structure is overlaid on another in four places
- words: 80

What must a change that adds or moves a field in `struct folio` keep true about
`struct page`, the tail-page overlays and the other descriptors that share the
memory, and what fails to compile if it does not? Start from `FOLIO_MATCH` and
`struct ptdesc`.

## folio.adding-a-flag: Adding a page flag

- section: What a change must preserve
- relevance: 3 - the bits are scarce and the accessors are generated
- words: 80

What does adding a page flag involve: choosing a policy, generating the
accessors, the debug and tracing tables that list flags, and the limit on the
number of bits? Start from `PAGEFLAG` and `include/trace/events/mmflags.h`.

## folio.compat-wrappers: Page-based wrappers

- section: What a change must preserve
- relevance: 2 - they hide a conversion
- words: 60

Which page-based functions remain as thin wrappers around folio functions, where
are they, and what do they do with a tail page? Start from
`mm/folio-compat.c`.

## folio.stat-accounting: Statistics units

- section: What a change must preserve
- relevance: 3 - converting a caller to folios changes the unit
- words: 60

When a statistic is updated for a folio, in what unit is it counted, and which
helpers take a folio and do the multiplication themselves? Start from
`lruvec_stat_mod_folio()` and `node_stat_mod_folio()`.

## folio.core-files: Core files

- section: Where to look
- relevance: 4 - several well-known files have moved
- words: 90

Which files hold the folio structure and its flag accessors, reference
counting, LRU batching, the page cache, truncation, writeback and GUP? A table.

## folio.entry-points: Entry points

- section: Where to look
- relevance: 4 - turns a search into a lookup
- words: 110

For each job (look a folio up in the page cache, add one, remove one, lock it,
take and drop a reference, put it on the LRU, mark it dirty, start and end
writeback, truncate, invalidate), which function do you start reading from? A
table.
