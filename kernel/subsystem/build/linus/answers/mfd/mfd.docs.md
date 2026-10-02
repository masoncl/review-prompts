- `Documentation/devicetree/bindings/mfd/mfd.txt`: exists, as plain text; it
  has no YAML replacement.
- `Documentation/devicetree/bindings/mfd/syscon.yaml`: does not contain the
  string "simple-mfd". The rule for `syscon` combined with `simple-mfd` (at
  least three `compatible` entries) is in
  `Documentation/devicetree/bindings/mfd/syscon-common.yaml`.
- `Documentation/devicetree/bindings/writing-bindings.rst`: holds the rules on
  when `simple-mfd` and `syscon` may be used.
- ACPI handling of children: section "MFD devices" in
  `Documentation/firmware-guide/acpi/enumeration.rst`.
- The example in that section sets both `pnpid` and `adr` of
  `struct mfd_cell_acpi_match`; `mfd_acpi_add_device()` in
  `drivers/mfd/mfd-core.c` reads `adr` only when `pnpid` is `NULL`.
- `Documentation/driver-api/`: has no document for the MFD core. The only
  mention of the API there is `devm_mfd_add_devices()` in the list in
  `Documentation/driver-api/driver-model/devres.rst`.
- Kernel-doc for the core: only on `mfd_add_devices()` and
  `devm_mfd_add_devices()` in `drivers/mfd/mfd-core.c`, and no `.rst` file
  includes it. `include/linux/mfd/core.h` has plain comments only.
- `Documentation/devicetree/usage-model.rst`: the document that
  `include/linux/mfd/core.h` cites for `of_compatible`. Its
  `of_platform_populate()` example passes of_default_bus_match_table, a table
  that no source file defines.
