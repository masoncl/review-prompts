- Completeness example in
  `Documentation/devicetree/bindings/writing-bindings.rst`: if the device has
  an interrupt, include `interrupts` even if the driver is polled-only.
- Stated basis, given in the Linux and driver bullet: bindings are based on
  what the hardware has, not what an OS and driver currently support; the
  file does not give ABI breakage as the reason here.
- Linux and driver rule: covers references to Linux or "device driver"; it
  says nothing about `linux,`-prefixed property names.
- Instance index rule: sits under "Typical cases and caveats", worded "Do not
  add instance index (IDs) properties or custom OF aliases", not under
  "Overall design" or "Properties".
- Alternatives the file gives, in full:
  - devices with a different programming model might need different
    compatibles
  - devices that use some other device differently (e.g. program the phy
    differently) use cell/phandle arguments
- Standard aliases, unit address, `reg`: the file names none of them as a
  substitute for an instance index.
- `cell-index`: not mentioned in the file.
