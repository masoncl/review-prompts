- `interrupts-extended`: wins per index, when `of_parse_phandle_with_args()`
  returns 0; any other return falls back to `interrupts`, including an index
  past its last entry.
- Node with both `interrupt-controller` and `interrupt-map`: the map wins and
  the walk goes on through it.
- Map ignored: only on a node that has `interrupt-controller` and matches
  `of_irq_imap_abusers[]` in `drivers/of/irq.c`.
- `of_irq_imap_abusers[]`: holds `"CBEA,platform-spider-pic"` and
  `"sti,platform-spider-pic"`, not platform-open-pic strings, and also
  `"pasemi,rootbus"`, among others.
- Map entry whose parent is the node itself: `of_irq_parse_raw()` returns 0
  there, with the specifier taken from the map.
- `of_irq_parse_raw()` called directly: it takes its own reference on the
  input `out_irq->np`; the caller's reference is not consumed, and
  `of_irq_parse_pci()` in `drivers/pci/of.c` passes a borrowed pointer.
