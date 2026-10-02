- `Documentation/devicetree/bindings/mfd/syscon.yaml`: has no `select:` block
  and no `simple-mfd` entry; a new plain compatible is added in one place, the
  first `enum` of the `oneOf` under `properties: compatible`.
- Compatible with a fallback (specific, fallback, `syscon`): a new `items`
  entry in that `oneOf`; three such entries exist.
- `syscon.yaml` properties: only `compatible`, `reg` and `resets`, plus
  `reg-io-width` through the `$ref` to `syscon-common.yaml`, with
  `unevaluatedProperties: false`; a node with `simple-mfd`, children or other
  properties gets its own binding file.
- Own binding files: list `const: syscon` in their own `compatible` and do not
  reference `syscon-common.yaml`; only `syscon.yaml` has that `$ref`.
- `Documentation/devicetree/bindings/mfd/syscon-common.yaml`: applies to every
  node whose `compatible` contains `syscon`, through its own `select:`.
- Order: `syscon-common.yaml` checks only `contains`, `minItems` and
  `maxItems`; the position of `syscon` and `simple-mfd` comes from the `items`
  list of each device schema.
- `maxItems: 5`: applies to `compatible` with and without `simple-mfd`.
- `syscon` together with `simple-bus`: rejected, except for a closed list of
  compatibles in `syscon-common.yaml` marked as not allowed to grow.
