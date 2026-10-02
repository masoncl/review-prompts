- Separate binding patch: item I.1 of
  `Documentation/devicetree/bindings/submitting-patches.rst` names "the
  Documentation/ and include/dt-bindings/ portion", so a header under
  `include/dt-bindings/` goes in the binding patch, not in the driver patch.
- DTS placement: item I.7 gives two accepted forms, a separate posting, or
  the end of the patchset when combined with driver patches.
- Reasons for keeping DTS apart: item I.7 gives exactly two.
  - DTS is driver-independent hardware description, so placing it last
    shows that the drivers do not depend on the DTS.
  - DTS is applied through a separate tree or branch anyway, so any other
    order indicates a non-bisectable series.
- Merge conflicts, merge timing and ABI stability across kernel versions:
  not given as reasons anywhere in the file.
- ABI: mentioned only in section III, as a pointer to
  `Documentation/devicetree/bindings/ABI.rst`.
- Use by projects other than Linux: item I.9 gives it as a reason for care
  when changing existing bindings, not as a reason for the DTS split.
- Reversed subject prefix `<binding dir>: dt-bindings: ...`: the file lists
  ASoC, media, regulators, SCSI, SPI and UFS.
- Words to keep out of the subject: "Documentation", "doc" and "YAML", and
  a repeated "binding".
