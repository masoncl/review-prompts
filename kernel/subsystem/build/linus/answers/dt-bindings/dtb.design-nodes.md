- `Documentation/devicetree/bindings/writing-bindings.rst`: describes itself
  as a list of common review feedback items, and says every rule has
  exceptions and bindings have many gray areas.
- Child nodes of a multi-function device: needed only when the child nodes
  have their own DT resources; the file gives no other allowance and names no
  driver mechanism.
- One node, several providers: the same bullet says a single node can be
  multiple providers, for example clocks and resets.
- `syscon`: not to be used alone; the specific compatible must be unique
  enough to infer the register layout of the entire block, at a minimum.
- `syscon` compatible order: the `syscon` bullet says nothing about which
  entry comes first.
- `simple-mfd`: the rule is not "never alone"; it is not to be used for
  non-trivial devices where children depend on some resources from the
  parent.
- `simple-bus`: same bullet as `simple-mfd`; not for complex buses, and a
  'regs' property (the file's spelling) means the device is not a simple bus.
- "syscon" as a property name: a second item, under "Typical cases and
  caveats", says it is not a generic property; use vendor and type, e.g.
  "vendor,power-manager-syscon".
- Node names: the file says DON'T treat them as a stable ABI; find sibling
  devices by phandle or compatible instead.
- Node name exception: sub-nodes of a given device could be treated as ABI if
  the binding documents them explicitly, so a binding may require a child
  node name.
