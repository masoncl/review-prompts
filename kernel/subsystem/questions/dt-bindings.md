# Questions: Device Tree Bindings

- guide: dt-bindings.md
- title: Device Tree Bindings Subsystem Details

The guide built from these questions states where this tree differs from what the models that read
it believe; it does not explain the code. Such a model has the kernel tree open and can search it,
so no question asks for what opening a file shows: the members of a structure, the callers of a
function, the options an option depends on. Each asks for one of three things. A requirement: what
the code requires for safe usage. A contract: what a helper guarantees, returns and locks, and
which of several look-alikes is used when. Orientation: where something lives and what this tree
calls it, where a reader's memory offers another name. `catalogue/dt-bindings-measurement.md` is
the wider set the readers were measured on and `catalogue/dt-bindings-measurement-results.md` says
what they got wrong. No number says how long an answer or the guide should be. Format:
`../../docs/subsystem-questions.md`.

# Main structures

## dtb.overview: Objects and how they relate

- relevance: 5 - everything else in the guide assumes it

In a few sentences, what is this code for? Then, one line each, the structures a reader has to
have in mind (what each represents, not what is in it) and how they relate to one another. Do not
say where helpers are declared or list a structure's members: write what a reviewer new to this
code could not work out from the headers. Leave to the later sections what a function requires,
what it returns and what it does when it fails.

# Where to look

## dtb.doc-map: Authoritative documents

- section: Finding your way
- relevance: 4 - most review feedback quotes one of these

A table and nothing else, subject to the document under `Documentation/devicetree/bindings/` or
`Documentation/process/` that is the authority on it: schema syntax; binding design; submitting
binding patches; ABI stability; DTS coding style; how devicetree patches are reviewed and
applied. Where a reader is likely to look for a document that does not exist in this tree, say so
in the row.

## dtb.external-schemas: Schemas outside the tree

- section: Finding your way
- relevance: 4 - half of what a binding references is not in the kernel tree

Where do the meta-schema named in a binding's `$schema`, the type definitions that bindings reach
through /schemas/types.yaml, and the core schemas for common properties such as clocks, interrupts
and GPIOs live: in this tree or somewhere else? How does a `$ref` in a kernel binding reach them?

# Checks and tools

## dtb.make-targets: Make targets

- section: Checks and tools
- relevance: 4 - what a submitter is told to run

A table, job to make target and where the target is defined: validate the binding documents;
build the processed schema; validate built DTBs against the schemas; check for undocumented
compatibles; check a single schema file with its example. Start from the top-level `Makefile` and
`Documentation/devicetree/bindings/Makefile`.

## dtb.check-steps: Steps of the binding check

- section: Checks and tools
- relevance: 4 - each step catches a different class of mistake

Which separate checks does `dt_binding_check` run over the schema files and over their examples,
with which tool each, and which of them stop the build when they find a problem and which only
print it? What does a run that finishes therefore not tell a reviewer?

## dtb.style-checker: Example style checker

- section: Checks and tools
- relevance: 4 - decides what style a new example is held to

Does this tree carry its own checker for the DTS coding style of binding examples, and if so where
is it? Does `dt_binding_check` run it, and with which options? What does the documentation ask new
bindings to pass? If the tree has no such checker, say so and stop.

## dtb.checkpatch: checkpatch warnings for bindings

- section: Checks and tools
- relevance: 3 - what is caught before a person looks

What triggers each of the warnings `scripts/checkpatch.pl` has that are specific to devicetree
bindings, and which lines of the patch or files of the tree does each test read?

# Schema structure

## dtb.schema-id: Schema identifier

- section: Schema structure
- relevance: 4 - every cross-reference is resolved against it, and copying a file breaks it

What must a schema's `$id` look like in relation to where the file is, and how is a `$ref`
resolved against it, with a leading slash and without? Does a step of `dt_binding_check` check the
`$id` against the path of the file, and if so does that step stop the build?

## dtb.additional-vs-unevaluated: additionalProperties and unevaluatedProperties

- section: Schema structure
- relevance: 5 - the wrong one either rejects valid nodes or accepts anything

When does `Documentation/devicetree/bindings/writing-schema.rst` require a schema to end with
`additionalProperties: false` and when with `unevaluatedProperties: false`, and when does it allow
`additionalProperties: true`, at the top level and in a nested node? What does
`Documentation/devicetree/bindings/spi/spi-controller.yaml` set for its child nodes, and does that
fit the rule for a nested node, and why?

## dtb.conditional-shape: Properties inside if/then blocks

- section: Schema structure
- relevance: 5 - the rule that decides where a constraint is written

When one schema covers several similar devices that differ in some properties, where must each
property be defined and where may it be narrowed? What does `additionalProperties: false` or
`unevaluatedProperties: false` do to a property that is defined only inside an `if`/`then` block?
Start from `Documentation/devicetree/bindings/writing-schema.rst`.

## dtb.compatible-conditions: Conditions on compatible

- section: Schema structure
- relevance: 5 - nothing fails when a block is missed

In a schema whose `allOf` holds `if` blocks keyed on `compatible`, what are the requirements for
adding a new compatible string so that the constraints of those blocks apply to nodes that use it?
Which nodes does an `if` match when its `contains` names a fallback string, and which when it
lists the specific strings? Name an in-tree schema that shows both.

# Properties

## dtb.property-naming: Property naming

- section: Properties
- relevance: 4 - decides whether a new property is accepted at all

What does `Documentation/devicetree/bindings/writing-bindings.rst` require of the name of a new
property, and what does it say about redefining a common property and about a property whose value
could be deduced from the compatible?

## dtb.property-types: Vendor property schemas

- section: Properties
- relevance: 4 - asked for on nearly every new binding

What must the schema of a vendor-specific property contain, and which properties need no type
reference?

## dtb.array-fixups: Implicit array constraints

- section: Properties
- relevance: 4 - explains why minItems appears where maxItems does not

Which constraints do the tools add to a schema automatically from an `items` list, and when must
`minItems` still be written by hand? Start from
`Documentation/devicetree/bindings/example-schema.yaml`.

## dtb.names-properties: Ordered lists and names

- section: Properties
- relevance: 4 - order and names are both ABI

What does `Documentation/devicetree/bindings/writing-bindings.rst` require about the order of
entries in a list of phandles such as clocks or interrupts, about when a matching `-names`
property is included, and about the constraints the two must share?

## dtb.provider-properties: Provider properties

- section: Properties
- relevance: 4 - a provider without its cells property cannot be referenced

What constraint does the binding of a provider, such as a clock or an interrupt controller, have
to put on its cell-count property, and do the documents under `Documentation/devicetree/bindings/`
say whether that property is listed in `required`? What does
`Documentation/devicetree/bindings/example-schema.yaml` do? Name a binding that shows it.

# Compatible strings and ABI

## dtb.compatible-naming: Compatible string rules

- section: Compatible strings and ABI
- relevance: 5 - the most common review comment

What rules do the documents give for how specific a compatible string must be: wildcards and
family names, when a SoC-specific string is required, and versioned IP blocks? Say for each
whether the document forbids, discourages or requires. Start from
`Documentation/devicetree/bindings/writing-bindings.rst`.

## dtb.compatible-fallbacks: Fallback compatibles

- section: Compatible strings and ABI
- relevance: 5 - a fake fallback and a missing one are both sent back

When do the documents call a fallback compatible right and when wrong? How is a `compatible`
property written in a schema so that it allows a specific string followed by a fallback, and also
the fallback on its own? Start from `Documentation/devicetree/bindings/example-schema.yaml`.

## dtb.registry-schemas: Vendor-prefix and trivial-device schemas

- section: Compatible strings and ABI
- relevance: 3 - a new vendor or a trivial device touches one of them

What are `Documentation/devicetree/bindings/vendor-prefixes.yaml`,
`Documentation/devicetree/bindings/trivial-devices.yaml` and
`Documentation/devicetree/bindings/incomplete-devices.yaml` each for, what does each allow or
refuse for a node that uses one of its compatibles, and when does a patch have to touch each?

## dtb.abi-changes: Changes that break old device trees

- section: Compatible strings and ABI
- relevance: 5 - the diff looks like a harmless schema tweak

What are the requirements for a change to an existing binding in order to assure safe usage by
device trees that are already in use? What do the documents require when an incompatible change is
needed, and whose compatibility besides the Linux kernel's do they name? Start from
`Documentation/devicetree/bindings/ABI.rst`.

# Design rules and examples

## dtb.design-nodes: Nodes and generic compatibles

- section: Design rules and examples
- relevance: 4 - each is a reason bindings are sent back

What does `Documentation/devicetree/bindings/writing-bindings.rst` say about child nodes that
exist only to instantiate drivers, about generic compatibles such as `syscon` and `simple-mfd`,
and about node names as ABI?

## dtb.design-hardware-description: Driver-neutral hardware description

- section: Design rules and examples
- relevance: 4 - each is a reason bindings are sent back

What does `Documentation/devicetree/bindings/writing-bindings.rst` say about mentioning Linux or a
driver in a binding, about leaving out features the driver does not use yet, and about instance
index properties and custom aliases?

## dtb.examples: Example contents

- section: Design rules and examples
- relevance: 4 - examples are compiled and validated

What does `Documentation/devicetree/bindings/writing-schema.rst` say an example in a binding
should contain and leave out? What does the build wrap around an example before it compiles it,
and what must the example write out itself so that macros from headers are available?

## dtb.example-indentation: Schema and DTS indentation

- section: Design rules and examples
- relevance: 4 - a style comment that is made on many new bindings

What indentation does `Documentation/devicetree/bindings/writing-schema.rst` ask for in a schema
file, and what indentation in the DTS example inside it?

# Patches

## dtb.patch-split: Patch split and order

- section: Patches
- relevance: 4 - checked by script and by every reviewer

According to `Documentation/devicetree/bindings/submitting-patches.rst`, which part of a change
must be a separate binding patch, in what order do binding, driver and DTS patches appear in a
series, and what reasons does it give for keeping DTS patches apart?

## dtb.undocumented-compatible: Documenting compatibles before use

- section: Patches
- relevance: 4 - a DTS or driver may not get ahead of the binding

According to `Documentation/devicetree/bindings/submitting-patches.rst`, what has to be documented
before a compatible string may be used in a DTS file, does that hold when no driver matches the
string yet, and what should the binding contain in that case?

# Model gaps

## dtb.model-gaps: Other mistakes models make

- drafts: all
- relevance: 5 - a model that is told how it is wrong can correct for it

Going by what each reader said from memory for every question in this guide, which is given
below, what do models believe about this code that is wrong in this tree? One bullet per mistake:
the belief, put plainly as a model would hold it, then what is true here and where to see it.
Cover names that are gone and what does the job now, numbers and limits that have changed,
behaviour that has changed, rules the readers state more broadly than the code supports, and what
is new that none of them knew. Most consequential first: a belief that would make a reviewer
approve a bug or reject correct code comes before a file that moved. Leave out what the readers
had right, and a slip only one of them made that the others show is not a belief. One or two lines to
a bullet: the belief and the truth. Every section of this guide already corrects what models
get wrong about its subject, and what a section covers is taken out of this list afterwards, so what
matters most here is what no question above asks about.
