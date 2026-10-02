- Read while the device may be resetting:
  `Documentation/driver-api/device-io.rst` says the flushing read may then be
  expected to fail and should be done from config space, which it calls
  guaranteed to soft-fail if the card does not respond.
- The document does not recommend choosing an MMIO register that is safe to
  read during reset.
- `ioremap_np()`: the generic version in `include/asm-generic/io.h` returns
  `NULL`; only `arch/arm64/include/asm/io.h` provides a real non-posted
  mapping.
- `ioremap_np()` on PCI BARs: `device-io.rst` forbids it, since PCI memory
  writes are always posted; the read-back is the method there.
