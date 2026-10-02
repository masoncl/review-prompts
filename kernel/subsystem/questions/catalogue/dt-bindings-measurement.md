# Questions: Device Tree Bindings (measurement set)

- guide: dt-bindings.md
- title: Device Tree Bindings Subsystem Details

A wide set of questions about device tree binding documents: the schema files
under `Documentation/devicetree/bindings/`, the documents that say how to
write and submit them, the make targets and scripts that check them, and the
conventions reviewers hold them to. It is used to measure what a model already
knows before deciding what the built guide should spend its words on. The
hand-written guide it will replace is 617 words and covers three topics:
conditionals keyed on compatible, provider properties, and `$id`. The C code
that parses a device tree at run time is left to the `of` guide. Format:
`../../../docs/subsystem-questions.md`.

# Where to look

## dtb.doc-map: Authoritative documents

- section: Documents and registries
- relevance: 4 - most review feedback quotes one of these
- words: 90

Which documents under `Documentation/devicetree/bindings/` and
`Documentation/process/` are the authority on schema syntax, on binding design,
on submitting binding patches, on ABI stability, on DTS coding style and on how
devicetree patches are reviewed and applied? A table.

## dtb.registry-schemas: Registry schemas

- section: Documents and registries
- relevance: 3 - a new vendor or a trivial device touches one of them
- words: 70

What are `Documentation/devicetree/bindings/vendor-prefixes.yaml`,
`Documentation/devicetree/bindings/trivial-devices.yaml` and
`Documentation/devicetree/bindings/incomplete-devices.yaml` each for, and when
does a patch have to touch each?

## dtb.external-schemas: Schemas outside the tree

- section: Documents and registries
- relevance: 4 - half of what a binding references is not in the kernel tree
- words: 60

Where do the meta-schema named in a binding's `$schema`, the types under
`/schemas/types.yaml` and the core schemas for common properties such as
clocks, interrupts and GPIOs live: in this tree or somewhere else? How does a
`$ref` in a kernel binding reach them?

## dtb.headers: Binding header files

- section: Documents and registries
- relevance: 3 - constants in a header become ABI
- words: 50

What belongs in a header under `include/dt-bindings/` and what does not, and
what does the tree's documentation say about adding macros there? Start from
`Documentation/process/maintainer-soc.rst`.

## dtb.make-targets: Make targets

- section: Build targets and tools
- relevance: 4 - what a submitter is told to run
- words: 90

Which make targets validate the binding documents, build the processed schema,
validate built DTBs against the schemas, check for undocumented compatibles,
and check a single schema file with its example? Say where each is defined.
Start from the top-level `Makefile` and
`Documentation/devicetree/bindings/Makefile`.

## dtb.check-steps: Steps of the binding check

- section: Build targets and tools
- relevance: 4 - each step catches a different class of mistake
- words: 90

List the separate checks `dt_binding_check` runs over the schema files and over
their examples, naming the tool each uses. Which of them stop the build when
they find a problem and which only print it?

## dtb.schema-files-var: Limiting the checked files

- section: Build targets and tools
- relevance: 3 - the fast way to check one binding
- words: 50

How does `DT_SCHEMA_FILES` select schema files (exact path, pattern or
substring, and how several are separated), and how does setting it change what
`dtbs_check` validates? Start from `scripts/Makefile.dtbs`.

## dtb.dtschema-version: Tool version requirement

- section: Build targets and tools
- relevance: 2 - an old install gives confusing errors
- words: 30

Which external package supplies the validation tools, what minimum version does
this tree demand, and where is that set?

## dtb.style-checker: Example style checker

- section: Build targets and tools
- relevance: 4 - decides what style a new example is held to
- words: 70

Does this tree carry its own checker for the DTS coding style of binding
examples? If it does, say where it is, what modes it has, which mode runs as
part of `dt_binding_check`, and which mode new bindings are asked to pass. If
it does not, say so and stop.

## dtb.style-rules: Style checker rules

- section: Build targets and tools
- relevance: 2 - the table is one command away
- words: 100

If the tree has a DTS style checker for binding examples, give a table of its
rules with the mode that enables each, and say how its own tests are run. If it
has none, say so and stop.

## dtb.dtbs-check-behaviour: Validating DTS files

- section: Build targets and tools
- relevance: 3 - explains why a broken schema hides DTS warnings
- words: 50

When `dtbs_check` meets a schema file that itself has errors, what happens to
that schema, and what does the process documentation expect of a DTS patch
with respect to `dtbs_check` warnings?

## dtb.compatible-check: Undocumented compatible checks

- section: Build targets and tools
- relevance: 3 - the rule is enforced by a script most people never run
- words: 60

Which in-tree tools look for compatible strings that drivers or DTS files use
and no binding documents, and what does each match on? Start from
`scripts/dtc/dt-extract-compatibles` and `scripts/checkpatch.pl`.

# Schema structure

## dtb.top-level-keys: Top-level keys

- section: Top level of a schema
- relevance: 3 - the meta-schema rejects a missing one
- words: 50

Which top-level keys must every binding schema have and which are optional?
Start from `Documentation/devicetree/bindings/writing-schema.rst`.

## dtb.id-rules: Schema identifier

- section: Top level of a schema
- relevance: 4 - every cross-reference is resolved against it
- words: 60

What must a schema's `$id` look like in relation to where the file is, and how
are a `$ref` with a leading slash and a `$ref` with only a relative path or
file name resolved against it?

## dtb.id-mismatch: Wrong schema identifier

- section: Top level of a schema
- relevance: 4 - easy to introduce when a file is copied, moved or converted
- words: 50

What goes wrong when a schema's `$id` does not correspond to where the file is,
which step of `dt_binding_check` reports it, and is that check made by code in
this tree or by an external tool?

## dtb.select: Matching nodes to a schema

- section: Top level of a schema
- relevance: 3 - a wrong select applies a schema to every node or to none
- words: 50

How is it decided which nodes a schema is applied to when it has no `select`,
when does a schema need one, and what do `select: false` and `select: true`
mean?

## dtb.additional-vs-unevaluated: Closing the property set

- section: Top level of a schema
- relevance: 5 - the wrong one either rejects valid nodes or accepts anything
- words: 80

When does a schema end with `additionalProperties: false`, when with
`unevaluatedProperties: false`, and in which cases is
`additionalProperties: true` right, at the top level and in a nested node?
Bus controller schemas such as `spi/spi-controller.yaml` leave their child
nodes open while listing more than a compatible for them: say why that is
correct there, so that the rule for a nested node carries its precondition.

## dtb.child-nodes: Child nodes

- section: Top level of a schema
- relevance: 3 - nested nodes are where the closing keyword is forgotten
- words: 50

What does a child node described inside its parent's schema need, and how is a
child that has its own compatible and its own schema file written in the
parent?

## dtb.property-types: Vendor property schemas

- section: Properties
- relevance: 4 - asked for on nearly every new binding
- words: 50

What must the schema of a vendor-specific property contain, and which
properties need no type reference?

## dtb.array-fixups: Implicit array constraints

- section: Properties
- relevance: 4 - explains why minItems appears where maxItems does not
- words: 50

Which constraints do the tools add to a schema automatically from an `items`
list, and when must `minItems` still be written by hand? Start from
`Documentation/devicetree/bindings/example-schema.yaml`.

## dtb.compatible-schema: Compatible with fallbacks

- section: Properties
- relevance: 4 - the shape every multi-device binding uses
- words: 50

How is a `compatible` property written that allows a specific string followed
by a fallback, and also the fallback on its own? Start from
`Documentation/devicetree/bindings/example-schema.yaml`.

## dtb.names-properties: Ordered lists and names

- section: Properties
- relevance: 4 - order and names are both ABI
- words: 60

What do the conventions say about the order of entries in clocks, interrupts,
dmas and resets, when a matching `-names` property is wanted and when it adds
nothing, what constraints the two must share, and how the names are spelled?

## dtb.provider-properties: Provider properties

- section: Properties
- relevance: 4 - a provider without its cells property cannot be referenced
- words: 80

For a device that is a GPIO, clock, interrupt, reset or PWM provider, which
properties does its binding declare, what constraint does the cell-count
property usually carry, and does any document say whether they belong in
`required`? Name an in-tree binding that shows it.

## dtb.deprecated: Deprecating properties and compatibles

- section: Properties
- relevance: 3 - the alternative to an ABI break
- words: 40

How do in-tree schemas mark a property or a compatible string as deprecated,
and do the writing guides document that?

## dtb.conditional-shape: Per-variant constraints

- section: Conditionals
- relevance: 5 - the rule that decides where a constraint is written
- words: 60

When one schema covers several similar devices that differ in some properties,
where is each property defined and where is it narrowed, and what is an
`if`/`then` block not supposed to do? Start from
`Documentation/devicetree/bindings/writing-schema.rst`.

## dtb.if-compatible-matching: Conditions on compatible

- section: Conditionals
- relevance: 4 - decides whether a new variant is covered
- words: 60

How do `if` blocks usually test the compatible string, and what is the
difference in coverage between a `contains` that names a fallback string and
one that lists the specific strings? Name an in-tree binding that uses each.

## dtb.new-compatible-usage: Adding a compatible

- section: Conditionals
- relevance: 5 - nothing fails when a block is missed
- words: 90

A patch adds a compatible string to a schema whose `allOf` holds `if` blocks
keyed on compatible. What does validation do for a node using the new string
if it is left out of a block that lists its sibling devices, and what form of
addition is already covered by the existing blocks without editing them? Name
an in-tree schema that shows both.

## dtb.if-optional-property: Conditions on optional properties

- section: Conditionals
- relevance: 3 - the condition matches when the property is missing
- words: 50

What does an `if` that tests the value of a property evaluate to when the node
does not have that property, and how do in-tree schemas write the condition so
that absence does not match?

## dtb.forbid-property: Forbidding a property

- section: Conditionals
- relevance: 3 - the other half of making one required
- words: 30

How does a schema say that a property must not be present for some variants?
Start from `Documentation/devicetree/bindings/example-schema.yaml`.

## dtb.split-schema: Splitting a binding

- section: Conditionals
- relevance: 3 - the way out when conditionals pile up
- words: 50

When do the documents say to split variants into separate schema files instead
of adding conditionals, and how is a shared part written so that several files
can reference it?

# Conventions

## dtb.compatible-naming: Compatible string rules

- section: Naming and design
- relevance: 5 - the most common review comment
- words: 80

What rules do the documents give for forming compatible strings: how specific,
wildcards and family names, SoC-specific strings, when a fallback is right and
when it is fake, bus and device-type suffixes, versioned IP blocks? Start from
`Documentation/devicetree/bindings/writing-bindings.rst`.

## dtb.file-naming: File name and location

- section: Naming and design
- relevance: 3 - asked for at the first review
- words: 30

How should a binding file be named, and what name is used when it covers
several compatibles?

## dtb.design-donts: Design rules

- section: Naming and design
- relevance: 4 - each is a reason bindings are sent back
- words: 90

What do the documents say about mentioning Linux or drivers in a binding,
child nodes that exist only to instantiate drivers, node names as ABI,
`syscon`, `simple-mfd` and `simple-bus`, instance index properties and custom
aliases, and leaving out features the driver does not use yet?

## dtb.property-naming: Property naming

- section: Naming and design
- relevance: 4 - decides whether a new property is accepted at all
- words: 60

What do the documents say about vendor prefixes on property names, unit
suffixes, redefining common properties, and properties whose value could be
deduced from the compatible?

## dtb.examples: Example contents

- section: Naming and design
- relevance: 4 - examples are compiled and validated
- words: 80

What should an example in a binding contain and leave out, which defaults is it
compiled with, how are macros from headers made available, and what
indentation does it use?

## dtb.yaml-style: YAML style

- section: Naming and design
- relevance: 2 - the linter reports most of it
- words: 60

What do the documents and `Documentation/devicetree/bindings/.yamllint` ask
for in indentation, line length, quoting, the order of entries in `properties`
and `required`, and the choice between plain, folded and literal description
blocks?

## dtb.abi-rules: ABI stability

- section: Compatibility
- relevance: 5 - decides whether a change to an existing binding is allowed
- words: 70

Which changes to an existing binding keep it compatible and which do not, what
is to be done when an incompatible change is truly needed, and whose
compatibility besides the Linux kernel's counts? Start from
`Documentation/devicetree/bindings/ABI.rst`.

## dtb.abi-break-usage: Changes that break old device trees

- section: Compatibility
- relevance: 5 - the diff looks like a harmless schema tweak
- words: 80

What changes to an existing schema are unsafe for device trees already in use,
and what that looks similar is correct? Consider the `required` list, the order
and number of entries in a list property, and the meaning of an existing
property. What does the patch description owe the reader when a break is
deliberate?

# Process

## dtb.patch-split: Patch split and order

- section: Patches
- relevance: 4 - checked by script and by every reviewer
- words: 70

What goes in a binding patch and what must be in a separate one, in what order
do binding, driver and DTS patches appear in a series, and why are DTS patches
kept apart?

## dtb.subject-prefix: Subject line

- section: Patches
- relevance: 3 - differs by subsystem
- words: 50

What subject prefix do binding patches use, which subsystems want it the other
way round, which words are to be left out of the subject, and what does a
conversion patch's subject look like?

## dtb.license: Licence tags

- section: Patches
- relevance: 3 - checkpatch warns on it
- words: 40

Which licence is preferred for binding documents and which for headers under
`include/dt-bindings/`, and what exactly does `scripts/checkpatch.pl` accept
for each?

## dtb.checkpatch: Script checks on binding patches

- section: Patches
- relevance: 3 - what is caught before a person looks
- words: 60

Which warnings does `scripts/checkpatch.pl` have that are specific to
devicetree bindings, and what triggers each?

## dtb.who-applies: Review and merge path

- section: Patches
- relevance: 3 - explains whose ack a binding needs
- words: 60

Who reviews binding patches and who applies them, when may a subsystem
maintainer take a binding without a devicetree maintainer's ack, and through
which trees do DTS files go?

## dtb.undocumented-compatible: Documenting before use

- section: Patches
- relevance: 4 - a DTS or driver may not get ahead of the binding
- words: 50

What has to be documented before a compatible string may be used in a DTS
file, does that hold when no driver matches the string yet, and what should
the binding contain in that case?

## dtb.txt-bindings: Text bindings

- section: Patches
- relevance: 2 - settled, but old files remain
- words: 40

May a new binding be added as a `.txt` file, what checks that, and roughly how
many text bindings does this tree still have beside the schema files?
