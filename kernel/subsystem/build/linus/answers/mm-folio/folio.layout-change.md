- Field names in `struct page`: `compound_info` and `__folio_index`. There is
  no compound_head or index field in `struct page`; the `FOLIO_MATCH`,
  `TABLE_MATCH`, `SLAB_MATCH` and `ZPDESC_MATCH` lines use these names.
- `flags`: `memdesc_flags_t` in `struct page`, `struct folio`, `struct slab`
  and `struct ptdesc` (`pt_flags`); the bits are in `.f`. `_flags_1` to
  `_flags_3` are plain `unsigned long`.
- `sizeof(struct folio)`: no `static_assert` bounds it. Each group is a union
  with a `struct page`; a group that outgrows it fails the next group's
  `FOLIO_MATCH(flags, _flags_N)`.
- Tail 3 group: nothing follows it, so nothing fails to compile if it grows
  past `sizeof(struct page)`.
- Tail 1: the fields sit in a union with `_usable_1[4]`; growth past four
  words moves `_mapcount_1` and `_refcount_1`, and their `FOLIO_MATCH` lines
  fail.
- Tails 2 and 3: only `_flags_N` and `_head_N` are matched. A field appended
  there that reaches the tail's `_mapcount` or `_refcount` overlays them and
  no assert fails. Tail 3 is already full up to that point, and so is tail 2
  without `CONFIG_64BIT`.
- `TABLE_MATCH`, `SLAB_MATCH`, `ZPDESC_MATCH`, `NETMEM_DESC_ASSERT_OFFSET`:
  compare the descriptor with `struct page`, never with `struct folio`. A
  change to `struct folio` alone trips only `FOLIO_MATCH`.
- `struct netmem_desc` in `include/net/netmem.h`: its size assert is
  `sizeof(struct netmem_desc) <= offsetof(struct page, _refcount)`, tighter
  than the `<= sizeof(struct page)` of the other descriptors.
- `sizeof(struct page)`: `compound_info_has_mask()` tests
  `is_power_of_2(sizeof(struct page))`, so with
  `CONFIG_HUGETLB_PAGE_OPTIMIZE_VMEMMAP` a field that changes the size can
  switch the encoding of `compound_info` in every tail. No build check is
  tied to that switch; with `BITS_PER_LONG` 64, `__mm_zero_struct_page()` in
  `include/linux/mm.h` has `BUILD_BUG_ON()` only for a size that is not a
  multiple of 8, below 56 or above 96.
- Not checked at compile time, to update by hand for a new tail field:
  - `prep_compound_head()` in `mm/internal.h`, which sets the initial value.
  - `free_tail_page_prepare()` in `mm/page_alloc.c`, which checks per tail
    index.
  - `snapshot_page()` in `mm/util.c`, which copies the head, tail 1 and
    `__page_2` and never `__page_3`.
  - `__NR_USED_SUBPAGE` in `include/linux/hugetlb.h`, a plain constant that
    nothing ties to `struct folio`; `hugetlb_vmemmap_init()` has the
    `BUILD_BUG_ON()` against `HUGETLB_VMEMMAP_RESERVE_PAGES`.
