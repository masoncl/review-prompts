- Tag definitions: the list is at the head of
  `Documentation/admin-guide/kernel-parameters.txt`, ahead of the line
  "Kernel parameters"; it is not in
  `Documentation/admin-guide/kernel-parameters.rst`.
- `Documentation/admin-guide/kernel-parameters.rst`: holds only the sentence
  that bracketed text states restrictions, and the paragraph on `BOOT`.
- `EARLY`: defined as "Parameter processed too early to be embedded in
  initrd."; it states a consequence and names neither `early_param()` nor
  `parse_early_param()`.
- `EARLY` is in use throughout the `.txt`, for example
  `acpi=		[HW,ACPI,X86,ARM64,RISCV64,EARLY]`.
- Undefined tags: entries use tags that have no line in the list, for example
  `MM` and `KEYS`; a tag in an entry is not proof that it is defined.
