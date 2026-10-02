- Node read: `of_translate_one()` reads the property on the node being
  crossed, starting at the device's parent; the last node of the walk, the
  one with no parent, is never read.
- Missing `ranges`: failure, except where `of_empty_ranges_quirk()` is true;
  that needs `CONFIG_PPC` and either a `"1682m-sdc"` node or a
  `"Power Macintosh"` or `"MacRISC"` machine.
- Missing `dma-ranges`: 1:1, the same as an empty one.
- Logic PIO: a node registered as a non-`LOGIC_PIO_CPU_MMIO` range ends the
  walk before `ranges` is read, and `of_translate_address()` returns
  `OF_BAD_ADDR`.
- `of_translate_dma_address()`: steps with `__of_get_dma_parent()` at every
  level, the first included.
- `__of_get_dma_parent()`: takes the `interconnects` entry at the index of
  `"dma-mem"` in `interconnect-names`; without that name, or if the entry
  does not parse, it uses `of_get_parent()`.
- Without `CONFIG_HAS_DMA` or without `CONFIG_OF_ADDRESS`:
  `__of_get_dma_parent()` is a stub in `drivers/of/of_private.h` that calls
  `of_get_parent()`.
