- Models take a failing `dt-validate` to fail the build. `cmd_dtb_check` in
  `scripts/Makefile.dtbs` ends in `|| true`, so its exit status is dropped.
- Models take a fallback to be right when the device is a "subset" of the
  earlier one. `Documentation/devicetree/bindings/writing-bindings.rst`:
  DON'T add fake fallback compatibles that software cannot use to match and
  bind to a device and still operate correctly.
- Models take new `include/dt-bindings/` macros to be the normal way to name
  IDs. `Documentation/process/maintainer-soc.rst` says to avoid them for
  constants derivable from a datasheet and to use them "only ... as a last
  resort".
- Models do not know that
  `Documentation/devicetree/bindings/writing-schema.rst` ("Coding style")
  asks for `properties` and `required` entries in the same order, following
  `Documentation/devicetree/bindings/dts-coding-style.rst`.
- Models take `Documentation/process/` to have no devicetree handbook.
  `Documentation/process/maintainer-devicetree.rst` exists: bindings are
  reviewed by DT maintainers but should be applied by subsystem maintainers
  "except in certain cases"; DTS and driver review by them is generally not
  expected.
