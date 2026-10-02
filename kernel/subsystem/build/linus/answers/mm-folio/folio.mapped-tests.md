- There is no page_mapped() and no page_mapcount() in this tree. "Is this
  page's folio mapped" is `folio_mapped(page_folio(page))`.
- One page, in one VMA: `page_vma_mapped_walk()`. `page_mapped_in_vma()` in
  `mm/page_vma_mapped.c` is built only with `CONFIG_MEMORY_FAILURE` and
  returns the address or -EFAULT.
- With `CONFIG_NO_PAGE_MAPCOUNT`: no helper answers whether one page of a
  large folio is mapped without a page table walk.
