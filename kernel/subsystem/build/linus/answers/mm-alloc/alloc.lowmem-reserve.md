- Empty upper zone `j`: its entry is not forced to 0; it repeats the entry
  for `j - 1`, because `setup_per_zone_lowmem_reserve()` divides a running
  sum.
- `lowmem_reserve[j]` is therefore non-decreasing in `j`;
  `calculate_totalreserve_pages()` relies on that and takes the first
  non-zero entry from the top.
- All entries of a zone are 0 when its ratio is 0 or the zone itself has no
  managed pages.
- The sum covers the zones above `i` on the same node only.
- Entries with `j <= i`, including index 0 of every zone, are never written.
- `highest_zoneidx` 0 gives a test with no reserve term; `__isolate_free_page()`
  and `mm/page_reporting.c` call `zone_watermark_ok()` that way.
