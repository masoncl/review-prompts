- Schemas that show both an `if` on a fallback string and an `if` on a
  specific string:
  `Documentation/devicetree/bindings/serial/renesas,scif.yaml` and
  `Documentation/devicetree/bindings/mmc/renesas,sdhi.yaml`.
- `renesas,scif.yaml`: one `if` lists the family fallbacks
  (`renesas,rcar-gen1-scif` and later generations); another lists only
  `renesas,scif-r7s72100`.
- `Documentation/devicetree/bindings/i2c/snps,designware-i2c.yaml`: does not
  show both; its single `if` is `not: contains: const: mscc,ocelot-i2c`,
  which matches every node except that one.
- A string can be both specific and a fallback: `renesas,scif-r9a07g044`,
  `renesas,scif-r9a09g057` and `renesas,sdhi-r9a09g057` each stand alone in
  the top-level `compatible` and end another `items` list.
- An `if` that names such a string: matches the nodes of every SoC that
  falls back to it; `vqmmc-regulator` in `renesas,sdhi.yaml` reaches
  `renesas,sdhi-r9a09g047` nodes that way.
- New string in the top-level list only: every `else` branch of a
  non-matching `if` applies to it, for example
  `else: required: interrupt-names` in `renesas,scif.yaml`.
- New string that shares a fallback but needs different constraints:
  `renesas,sdhi.yaml` tests the specific strings in the outer `if` and the
  fallback only in a nested `else: if:`, so the fallback block is skipped
  for them.
- Sibling `if` blocks in `allOf`: all that match apply together; a
  `renesas,scif-r9a09g047` node matches both blocks that name
  `renesas,scif-r9a09g057`.
- Generic last fallback `renesas,scif`: named by no `if` in
  `renesas,scif.yaml`; listing it gives a node no block.
