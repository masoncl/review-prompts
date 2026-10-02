- `$schema` value: `http://devicetree.org/meta-schemas/core.yaml#` in every
  binding except three, which name
  `http://devicetree.org/meta-schemas/base.yaml#`:
  `Documentation/devicetree/bindings/nvmem/nvmem-consumer.yaml`,
  `Documentation/devicetree/bindings/nvmem/nvmem-provider.yaml` and
  `Documentation/devicetree/bindings/thermal/thermal-zones.yaml`.
- Relative `$ref` with `../`: in use across the tree for targets that exist
  under `Documentation/devicetree/bindings/`, for example
  `$ref: ../connector/usb-connector.yaml#` in
  `Documentation/devicetree/bindings/usb/maxim,max33359.yaml`.
- Refs to external schemas, absolute form: for example
  `/schemas/types.yaml#/definitions/uint32` and
  `/schemas/graph.yaml#/properties/port`.
- Refs to external schemas, bare file name: also in use, from a binding whose
  `$id` is in the same namespace directory, for example
  `$ref: reserved-memory.yaml` in
  `Documentation/devicetree/bindings/reserved-memory/ramoops.yaml`.
- External schemas in a namespace directory that also exists in the tree:
  `/schemas/i2c/i2c-controller.yaml`, `/schemas/pci/pci-host-bridge.yaml` and
  `/schemas/reserved-memory/reserved-memory.yaml` have no file under
  `Documentation/devicetree/bindings/i2c/`,
  `Documentation/devicetree/bindings/pci/` or
  `Documentation/devicetree/bindings/reserved-memory/`.
- External schemas at the top level: `/schemas/graph.yaml` and
  `/schemas/simple-bus.yaml` have no file in the tree either.
- Telling in-tree from external: look for the file under
  `Documentation/devicetree/bindings/`; the `$ref` itself looks the same.
- Stub files: a search of the tree for a moved common binding finds a short
  `.txt` pointer, for example `Documentation/devicetree/bindings/graph.txt`,
  `Documentation/devicetree/bindings/clock/clock-bindings.txt` and
  `Documentation/devicetree/bindings/reserved-memory/reserved-memory.txt`.
- Not every stub points outside the tree: for example
  `Documentation/devicetree/bindings/spi/spi-bus.txt` points to the in-tree
  `spi-controller.yaml`.
- `DT_SCHEMA_MIN_VERSION`: set to `2024.4` in
  `Documentation/devicetree/bindings/Makefile`; `check_dtschema_version`
  compares it with the output of `dt-doc-validate --version`.
- Tool invocations: `dt-doc-validate -u $(src)` and `dt-mk-schema` are in
  `Documentation/devicetree/bindings/Makefile`.
- `dt-validate`: invoked from `cmd_dtb_check` in `scripts/Makefile.dtbs`, with
  `-u` naming the bindings directory and `-p` naming `processed-schema.json`.
