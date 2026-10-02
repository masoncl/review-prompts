- Never-preserved memory, table entry missing on the path:
  `kho_radix_del_key()` hits `WARN_ON()`, not `WARN_ON_ONCE()`, and returns.
- Never-preserved memory, leaf exists: the clear bit is cleared again, with no
  warning.
- Counting: the tracker holds one bit per key; preserving a block twice and
  unpreserving it once leaves it not preserved.
- `kho_unpreserve_folio()`: builds the key from `folio_order()` at the call,
  so the folio must still have the order it had when preserved.
