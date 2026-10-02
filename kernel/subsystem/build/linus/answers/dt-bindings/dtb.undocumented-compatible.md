- Binding content when no driver matches the string yet: item I.8 of
  `Documentation/devicetree/bindings/submitting-patches.rst` asks that the
  documentation also include a compatible string that the driver does
  match.
- Completeness of the binding (`reg`, interrupts, clocks, "not a stub"): the
  file states no such requirement for this case.
- Check that the file names for the rule of item I.6: checkpatch only.
- `make dtbs_check`: not mentioned in the file.
- `make dt_binding_check`: appears only in item I.2, as validation of the
  binding files themselves.
- Vendor prefix: the file has no rule about it.
- `UNDOCUMENTED_DT_STRING` in `scripts/checkpatch.pl`: also fires on added
  `.compatible = "` lines in `.c` and `.h` files, which the DTS-only rule of
  item I.6 does not cover.
- `UNDOCUMENTED_DT_STRING` lookup: greps `Documentation/devicetree/bindings/`
  of the tree checkpatch runs in, so the binding has to be applied there
  already.
