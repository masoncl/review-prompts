- Comparison function: `r4k_entry_cmp()`; there is no r4k_vpn_cmp here.
- Sort key, in order: wired first, global first, ascending VPN, ascending
  ASID, descending page size.
- Candidate: a (VPN, ASID) pair whose VPN never decreases; it is not
  `UNIQUE_ENTRYHI(n)`.
- Cursors: `widx` (wired), `gidx` (global) and `idx` only move forward, and
  the candidate is compared with the entry at each cursor only.
- Relied on: within each group the entries are in ascending VPN order, so
  an entry the cursor has passed is never looked at again.
- Slot written: `tlb_vpns[i].index`; after `sort()` the array position `i`
  is not a TLB index.
- Order of overwriting: sorted order, starting at the first non-wired
  entry, so global entries are replaced before the others.
- After each write: `tlb_vpns[i]` gets the new VPN, ASID and page size, so a
  cursor that reaches it later sees the value now in the TLB.
