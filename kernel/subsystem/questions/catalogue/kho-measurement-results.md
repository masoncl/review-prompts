# What the kho measurement found

Three models were asked the 48 questions in `kho-measurement.md` with no
sources, and a checker that had the sources then corrected each answer against
a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and C; which
models they were does not matter here. Reader C was the most current (it
assumed kernels from 6.19 to 7.1), reader A a few releases behind it (6.16 to
6.19), and reader B older still (6.12 to 6.17) and much weaker: more than four
fifths of what it wrote was rewritten, and for the orchestrator's file handlers
it said plainly that it had nothing to offer. Every question came back answered
and checked on the first run. After the runs two questions were reworded to
take out a clause that leaned towards an answer ("how does one key carry both an
address and an order" became "how are a block's address and its order encoded",
and "which of them is unsafe" gained "if any"); what they ask for did not
change. The hand-written guide was never checked against current sources, so
differences between it and the built guide are expected and are noted near the
end.

Kexec HandOver is young and has been reworked in almost every release since it
was merged, so each reader describes a different kernel. Reader B remembers the
first version: a notifier chain, a finalize file in debugfs, nested xarrays.
Reader A remembers the one after: no finalize step, but per-order bitmaps, the
two-argument subtree calls and an orchestrator that hands over an FDT. Reader C
has the radix tree and the three-argument calls, but still the orchestrator's
FDT, and none of the three has seen the serialization blocks or the early
memory hook. All three know what handover is for, that values in its FDTs are
in native byte order, how a range of pages is cut into chunks and which restore
call goes with which preserve call.

## What all three readers got wrong or did not know

- **Preserving when handover is off.** All three said a preserve call made
  with Kexec HandOver compiled in but not enabled quietly succeeds. The tracker
  root is allocated only by `kho_init()`, so `kho_radix_add_key()` hits
  `WARN_ON_ONCE(!tree->root)` and returns `-EINVAL`; `kho_alloc_preserve()`
  passes that on as an error pointer, `kho_preserve_vmalloc()` fails its first
  chunk with `-ENOMEM`, and the unpreserve calls warn. Reader B also had the
  danger backwards: it called `kho_add_subtree()` and `kho_remove_subtree()`
  safe and the retrieve and restore calls unsafe. The first two hand a NULL
  `kho_out.fdt` to `fdt_open_into()`; `kho_retrieve_subtree()` returns `-ENOENT`
  and the restore calls return NULL.
- **Neither check is final when first read.** All three said `is_kho_boot()`
  never changes once `kho_populate()` has run, and readers A and B said the same
  of `kho_is_enabled()` (reader B called `kho_enable` a static key).
  `kho_reserve_scratch()` and the error path of `kho_init()` clear `kho_enable`;
  `kho_memory_init_early()` and `kho_mem_retrieve()` zero `kho_in.fdt_phys`.
- **The early memory hook.** None knew `kho_memory_init_early()`, which
  `mm_core_init_early()` calls before `free_area_init()` to open the incoming
  tracker and run `kho_extend_scratch()`: readers A and C said they did not
  recognise it (nor `kho_extend_scratch()`), reader B guessed that it reserves
  scratch. Readers A and C had `kho_memory_init()` deserialize something; it
  only walks the tree and reserves each block, or reserves scratch on a cold
  boot. They also had `kho_init()` always release scratch to `MIGRATE_CMA`; on
  a handover boot it returns before that loop and `kho_scratch_migratetype()`
  does the job during memmap init.
- **Serialization blocks.** No reader recognised `struct kho_block_set` or
  `kernel/liveupdate/kho_block.c`. The file is built as part of the orchestrator,
  not of the core.
- **A file that does not exist.** All three listed a kexec_handover_debug.c.
  The debug checks are `IS_ENABLED(CONFIG_KEXEC_HANDOVER_DEBUG)` tests inside
  `kexec_handover.c`; the debugfs code is `kexec_handover_debugfs.c`.
- **The scratch check.** Readers A and C said `kho_preserve_folio()` always
  fails on memory that overlaps scratch, and then, asked directly, that
  `kho_scratch_overlap()` exists only in debug builds. The function is always
  built and `memblock_alloc_hugetlb()` and `kho_scratch_migratetype()` always
  use it; only the calls in the preserve paths are behind
  `CONFIG_KEXEC_HANDOVER_DEBUG`. Reader B had that right, but told users to
  watch `cma_alloc()`; scratch is not a CMA area, its pageblocks are only
  marked `MIGRATE_CMA`, and the allocations to watch are movable ones, which the
  memfd handler deals with through `memfd_pin_folios()`.
- **Scratch regions.** One per node with memory (`N_MEMORY`) plus two, not one
  per online node; the default size leaves out HugeTLB reservations; the
  alignment is `SCRATCH_ALIGNMENT_BYTES`, not `CMA_MIN_ALIGNMENT_BYTES`.
- **Version strings.** `KHO_FDT_COMPATIBLE` is "kho-v4"; readers A and B said
  "kho-v1" and reader C "probably kho-v3", which is what the comment above the
  definition still says. `MEMFD_LUO_FH_COMPATIBLE` is "memfd-v2" (readers A and
  B: "memfd-v1"). `LUO_ABI_COMPATIBLE` is "luo-v5".
- **The orchestrator's state is not an FDT.** Readers A and C described a
  subtree with compatible "luo-v1" and a liveupdate-number property, built by a
  luo_fdt_setup(), with LUO_FDT_ names for the strings; reader B could not name
  it. It is a packed `struct luo_ser` from `kho_alloc_preserve()`, added under
  `LUO_KHO_ENTRY_NAME` by `luo_state_setup()` and checked with `strncmp()`.
- **The reboot hook.** Readers A and C had `liveupdate_reboot()` end with a
  call to kho_finalize(), which exists nowhere (a comment in `luo_flb.c` still
  mentions it). It calls `luo_session_serialize()` and `luo_flb_serialize()`,
  and `kernel_kexec()` skips it for an image that preserves context.
- **Session locking.** All three left out the outermost lock,
  `luo_session_serialize_rwsem`, which every other path takes for read and
  which `luo_session_serialize()` keeps write-held for good when it succeeds.
- **Bad incoming state.** An incompatible or short `struct luo_ser` at early
  boot reaches `luo_restore_fail()`, which is `panic()`; reader B said boot
  carries on. A later failure in `luo_session_deserialize()` is saved, and every
  open of the device then returns `-EIO`, not the saved error.
- **Rollback direction.** `__luo_file_unfreeze()` walks a session's files
  forwards; only the sessions are walked in reverse. Readers A and C had both
  in reverse.
- **Shared objects.** All three said the get calls need no put, or that no put
  exists. `liveupdate_flb_get_incoming()` and `liveupdate_flb_get_outgoing()`
  both take a reference that `liveupdate_flb_put_incoming()` or
  `liveupdate_flb_put_outgoing()` must drop, and calling either from the
  object's own callbacks deadlocks on the mutex the callback runs under.
- **A frozen memfd.** Writes inside the current size and new seals still work;
  writes past the end, every fallocate mode and size changes get `-EPERM`.
  `memfd_luo_freeze()` refreshes only the file position.
- **Restore details.** `kho_restore_page()` has no order limit and warns only
  on a missing magic; `kho_restore_pages()` recomputes the chunks without the
  NUMA cut that `__kho_preserve_pages_order()` makes, and does not undo what it
  restored when it fails part of the way.
- **The worked unwind.** Asked which in-tree code undoes a subtree, its blob and
  its data in order, readers A and C pointed at an error path in
  `lib/test_kho.c` that does not exist (only module exit does it) and reader C
  said `prepare_kho_fdt()` needs no removal. `prepare_kho_fdt()` in
  `mm/memblock.c` is the error path that shows all three steps.

## What readers A and B got wrong as well

- **The tracker.** Both described per-order bitmaps or nested xarrays in a
  struct kho_mem_track. It is one `struct kho_radix_tree` of page-sized nodes,
  keyed by `kho_encode_radix_key()`, `KHO_TREE_MAX_DEPTH` levels deep, with its
  own mutex; both calls sleep. Reader C had the tree but not the names: it
  offered kho_radix_encode_key(), kho_radix_add_page() and kho_radix_del_page().
- **The subtree calls.** `kho_add_subtree()` takes a name, a blob and a size
  (reader A: name and FDT; reader B: a struct kho_out pointer first), the blob
  may be in any format, and the node gets `preserved-data` and `blob-size`
  properties, not one called fdt. `kho_retrieve_subtree()` has a third `size`
  argument and returns `-EINVAL` for a missing `blob-size`.
  `kho_remove_subtree()` takes the blob, matches its physical address and
  returns nothing (reader B: by name, returning an error).
- **No finalize.** Reader B described an out/finalize file, a
  register_kho_notifier() and two notifier events; reader A had the memory map
  property written as a placeholder and filled in before kexec. The root FDT is
  complete from `kho_init()` on: `kho_out_fdt_setup()` writes the tracker root
  into it, `kho_add_subtree()` edits it in place under `kho_out.lock`, and
  every debugfs file is read-only.
- **Where the root FDT comes from.** `kho_init()` allocates it with
  `kho_alloc_preserve()`; both said `kho_out_fdt_setup()` does.
- **Kexec metadata.** Neither knew `struct kho_kexec_metadata`, a packed C
  struct written and read by `kho_init()`; a failure to write it disables
  handover.
- **debugfs failures.** A failure to create the top directory or `out` disables
  handover; only `in` and single blobs are tolerated.

## What only reader B got wrong

Most of the rest, of which the parts that would change a review:
`kho_populate()` runs at kexec time and writes the outgoing FDT; `kho_init()`
is a core initcall; `kho_alloc_preserve()` returns NULL on failure;
kho_preserve_phys() and kho_restore_phys() exist; huge vmalloc areas cannot be
preserved; the scratch default is a few percent of memory and the regions are
registered CMA areas; `kho_restore_pages()` calls split_page(); the kexec
segment that is added carries the FDT; the orchestrator lives in a
liveupdate.c and the test in drivers/misc; shared-object callbacks run per file
descriptor and rebuild a struct file; a memfd must be fully sealed to be
preserved. It had nothing on the handler callbacks, their arguments,
registration, retrieve and finish, or the freeze rollback.

## What only reader C got wrong

- `CONFIG_KEXEC_HANDOVER` does not exclude deferred struct page
  initialisation; `kho_get_preserved_page()` calls `init_deferred_page()` first.
  The memmap_init_kho_scratch_pages() it named is gone.
- There is no cap on the number of sessions other than what
  `kho_block_set_grow()` can allocate, and no luo_session_quiesce().
- In `memfd_luo_preserve_folios()` a folio is preserved first and then marked
  dirty and, if need be, zeroed; reader C had the order reversed.

## What the readers already knew

All three: that property values are written and read in native byte order and
that this departs from the devicetree specification; why scratch exists; that
the caller of `kho_add_subtree()` must preserve the blob itself. Readers A and
C: which restore call goes with which preserve call and what a mismatch does,
how `kho_preserve_pages()` cuts a range, that unpreserve must repeat the
original arguments and frees nothing, vmalloc preservation, the handler
callback table (apart from `get_id`), retrieve and finish, handler registration
(reader C exactly). Reader C also had `kho_alloc_preserve()`, the root FDT
apart from the version, image loading and the ioctl list right.

## Where the hand-written guide is stale

- Its example and its prose call `kho_add_subtree()` with a name and an FDT.
  The call takes a name, a blob of any format and a size, and
  `kho_retrieve_subtree()` takes a pointer for the size as well.
- It says preserve calls made while handover is disabled "silently add tracking
  state that will never be used". They warn and return `-EINVAL`.
- It says `kho_preserve_folio()` and `kho_preserve_pages()` check for scratch
  overlap and return `-EINVAL`. They do so only with
  `CONFIG_KEXEC_HANDOVER_DEBUG`.
- It presents `kho_is_enabled()` as fixed because `kho_enable` is
  `__ro_after_init`. Two failure paths clear it during boot.
- It calls the scratch regions CMA-backed. No CMA area is registered; the
  pageblocks are only given the `MIGRATE_CMA` type. A small point, but reader
  B, believing the same, warned about `cma_alloc()`.
- It gives a whole section to native byte order in FDT properties, which every
  reader already knows, and says nothing of the tracker, the boot sequence, what
  is versioned or the orchestrator.
- The trigger table in `kernel/subsystem/subsystem.md` lists
  register_kho_notifier, which is not in the tree.

What it says about pairing restore with preserve calls, about repeating the
arguments when unpreserving, about `kho_remove_subtree()` leaving the memory to
the caller, about the vmalloc flags and about `kho_alloc_preserve()` still
holds.

## What was left out of the build set

The hand-written guide is 727 words, so the built guide is sized to 727 words
(581 to 872) with no question budgeted under 40. 15 of the 48 questions were
kept, chosen for what changes a verdict on a patch that calls or changes the
core, and they ask for 690 words, which with titles and headings comes to about
830. The first build set held the same fifteen at 585 words, eight of them with
20 to 35, and the answers to those came out as fragments that meant nothing
without the question beside them ("Zeroed folio, order `get_order(size)`.",
"Preserves: at once, in `kho_out.radix_tree`."). Fifteen questions at 40 words
or more already pass 727, so when the set was resized the room went to those
fifteen, the size moved up inside the allowed range and nothing was added from
the list below; the two guides built from it are 847 and 838 words. Dropping
one or two was the other way to make room, and was not taken because each of
the fifteen covers something a reader measured had wrong.
`kho.alloc-preserve` (readers A and C answer it; reader B expects NULL on
failure) and `kho.error-unwind` are the first to go if the guide has to come
back to 727. Three are worded a little differently from the measurement set:
`kho.enabled-state` asks for the places that clear a check only if either can
be cleared, `kho.error-unwind` asks which undo "if any" is unsafe to leave out,
and `kho.abi-versioning` asks for each string and version under the full name
of its macro. Left out:

- **Byte order** (`kho.fdt-endianness`): every reader has it right.
- **The rest of the core**: folio and page-range details, vmalloc, the root FDT
  layout, removing a subtree, kexec metadata, debugfs, how scratch is sized, the
  next kernel's early allocations and its handling of preserved pages, image
  loading. Readers A and C are close on most of these, the errors that remain
  do not change a review, and the versions and property names that do are
  covered by the versioning question.
- **The orchestrator beyond its overview**: the ioctl interface, sessions and
  their locking, the reboot hook, bad incoming state, the handler callbacks and
  their arguments, registration, file identity, retrieve and finish, the freeze
  rollback, shared objects, memfd. There is real material here that all three
  readers get wrong (the lock that stays write-held, the reference the get calls
  take, the panic on bad state), but it is a subject of its own with one in-tree
  handler, and the size of this guide does not stretch to it. The file table
  says where each part lives. If the orchestrator gets its own guide, these
  questions are the place to start.
- **Serialization blocks, tests, configuration, documentation, the change
  checklist**: the file table names the files; the tests and stubs are found
  from there.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
             corrections  rewritten  <=15%  >=40%  kernel assumed
reader A          145        46%      5     29   6.16 to 6.19
reader B          160        83%      0     47   6.12 to 6.17
reader C          118        32%      9     17   6.19 to 7.1

question                       reader A      reader B      reader C   verdict
kho.files                      26% ( 3)      37% ( 6)      26% ( 6)   middling
kho.docs                       57% ( 2)      67% ( 1)      42% ( 2)   all weak
kho.config                     25% ( 2)      91% ( 1)      22% ( 3)   weak: reader B
kho.init-order                 53% ( 7)      86% ( 4)      36% ( 3)   weak: reader A, reader B
kho.enabled-state              56% ( 4)      86% ( 7)      27% ( 1)   weak: reader A, reader B
kho.disabled-usage             60% ( 4)      84% ( 4)      48% ( 5)   all weak
kho.tracker-structure          82% ( 6)      96% ( 3)      30% ( 6)   weak: reader A, reader B
kho.tracker-context            27% ( 2)      80% ( 1)       4% ( 0)   weak: reader B
kho.no-finalize                69% ( 5)      88% ( 2)      28% ( 1)   weak: reader A, reader B
kho.preserve-folio             24% ( 5)      75% ( 6)      29% ( 4)   weak: reader B
kho.preserve-pages             38% ( 3)      76% ( 4)      18% ( 2)   weak: reader B
kho.restore-pairing            12% ( 1)      74% ( 2)      27% ( 1)   weak: reader B
kho.unpreserve-rules           28% ( 3)      77% ( 1)      19% ( 2)   weak: reader B
kho.vmalloc                    18% ( 2)      74% ( 2)       0% ( 0)   weak: reader B
kho.alloc-preserve             22% ( 2)      67% ( 3)       0% ( 0)   weak: reader B
kho.error-unwind               39% ( 2)      79% ( 2)      44% ( 4)   weak: reader B, reader C
kho.root-fdt                   42% ( 8)      76% ( 9)       4% ( 1)   weak: reader A, reader B
kho.subtree-add                38% ( 3)      68% ( 5)       0% ( 1)   weak: reader B
kho.subtree-remove              7% ( 1)      74% ( 2)      27% ( 1)   weak: reader B
kho.subtree-retrieve           40% ( 2)      71% ( 5)      15% ( 1)   weak: reader A, reader B
kho.fdt-endianness             29% ( 5)      76% ( 1)      28% ( 5)   weak: reader B
kho.abi-versioning             65% ( 1)      89% ( 3)      30% ( 3)   weak: reader A, reader B
kho.kexec-metadata             68% ( 1)      92% ( 1)      61% ( 1)   all weak
kho.debugfs                    64% ( 1)      96% ( 4)      35% ( 1)   weak: reader A, reader B
kho.scratch-what               22% ( 7)      74% ( 8)      17% ( 8)   weak: reader B
kho.scratch-overlap            46% ( 3)      85% ( 3)      46% ( 2)   all weak
kho.incoming-memblock          59% ( 3)      86% ( 2)      38% ( 1)   weak: reader A, reader B
kho.incoming-pages             65% ( 1)      87% ( 3)      43% ( 1)   all weak
kho.kexec-load                 49% ( 1)      89% ( 3)       8% ( 0)   weak: reader A, reader B
kho.blocks                     94% ( 5)      95% ( 3)      87% ( 2)   all weak
kho.luo-overview               61% ( 6)      89% ( 7)      35% ( 2)   weak: reader A, reader B
kho.luo-uapi                   38% ( 1)      93% ( 1)      27% ( 1)   weak: reader B
kho.luo-reboot                 72% ( 2)      90% ( 2)      52% ( 3)   all weak
kho.luo-session                40% ( 6)      80% ( 4)      26% ( 6)   weak: reader A, reader B
kho.luo-locking                78% ( 1)      95% ( 1)      84% ( 2)   all weak
kho.deserialize-failure        68% ( 3)      85% ( 3)      44% ( 3)   all weak
kho.file-ops                    7% ( 2)      76% ( 2)       6% ( 2)   weak: reader B
kho.file-args                  59% ( 1)      99% ( 1)      56% ( 1)   all weak
kho.file-handler-register      43% ( 1)      97% ( 1)       0% ( 0)   weak: reader A, reader B
kho.file-identity              57% ( 2)      93% ( 1)      45% ( 1)   all weak
kho.file-retrieve-finish       10% ( 1)      89% ( 2)      36% ( 1)   weak: reader B
kho.freeze-rollback            34% ( 2)      97% ( 2)      21% ( 1)   weak: reader B
kho.flb                         0% ( 5)      89% ( 6)      42% ( 6)   weak: reader B, reader C
kho.flb-accessors              69% ( 3)      86% ( 4)      49% ( 2)   all weak
kho.memfd                      70% ( 7)      90% ( 8)      24% ( 5)   weak: reader A, reader B
kho.memfd-frozen               68% ( 1)      83% ( 3)      47% ( 2)   all weak
kho.tests                      86% ( 3)      92% ( 6)      45% ( 2)   all weak
kho.change-checklist           67% ( 3)      78% ( 5)      61% (10)   all weak
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `kho.incoming-pages`, `kho.luo-reboot`, `kho.file-args`, `kho.change-checklist`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `kho.tracker-context`, `kho.preserve-folio`, `kho.preserve-pages`, `kho.root-fdt`, `kho.fdt-endianness`, `kho.scratch-what`, `kho.luo-session`, `kho.file-ops`, `kho.file-retrieve-finish`.

## Questions reorganised

Grouped by subject: enabling and boot, preserving and restoring memory, what is handed over, scratch
regions, the orchestrator, after the file table. 30 questions became 28.
Merged: `kho.tracker-structure` and `kho.tracker-context` into `kho.tracker`; `kho.root-fdt` and
`kho.fdt-endianness` into `kho.handover-fdt`, since every reader knew the byte order and it is one
clause of the layout. `kho.file-args` and `kho.file-ops` no longer ask for fields but who owns what
between the core and a handler. `kho.incoming-pages`, `kho.scratch-what` and `kho.luo-reboot` were cut
to what a reviewer would get wrong; `kho.abi-versioning` and `kho.change-checklist` moved into what is
handed over. Nothing was dropped.
