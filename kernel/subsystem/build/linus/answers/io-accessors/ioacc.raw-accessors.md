- Merging: `Documentation/driver-api/device-io.rst` says "multiple consecutive
  accesses can be combined on the bus"; only the no-split property is
  described, and only as "usually atomic".
- `ioremap()` section of the same document: the "No write-combining" property
  "may or may not be enforced when using __raw I/O accessors".
- Safe in portable code: the document's term is "memory behind a device bus";
  the paragraph names neither frame buffers nor prefetchable memory.
- Not safe in portable code: "MMIO registers"; the only reason the paragraph
  gives is ordering ("other MMIO accesses or even spinlocks"), not byte order.
