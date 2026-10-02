# What the dt-bindings measurement found

Three models were asked the 45 questions in `dt-bindings-measurement.md` with
no sources, and a checker that had the sources then corrected each answer
against a mainline tree (kernel 7.3.0-rc4). The readers are labelled A, B and
C; which models they were does not matter here. Reader C was the most current
(it assumed kernels from 6.14 to 6.17), reader A a little behind it (6.12), and
reader B older (6.10 to 6.12) and much weaker: every answer of its was mostly
rewritten. The hand-written guide was never checked against current sources,
so differences between it and the built guide are expected and are noted near
the end.

Bindings are conventions written down in a handful of documents, and readers A
and C have read those documents: they know the json-schema vocabulary, how
`$id` and `$ref` work, how conditionals on compatible are written and what the
design rules are about. What they get wrong is the tooling this tree has grown
since, the fine print of what the documents actually say (as opposed to what
reviewers are known to ask for), and the numbers. Reader B is also wrong about
the basics.

## What all three readers got wrong

- **The tree has its own style checker for examples.** All three said example
  style is enforced only by review. `scripts/dtc/dt-check-style` checks the
  examples in `.yaml` bindings and `.dts`, `.dtsi` and `.dtso` files, in a
  `relaxed` and a `strict` mode. `dt_binding_check` runs the relaxed mode
  (`cmd_chk_style`, stamp `.dt-style.checked`); `submitting-patches.rst` asks
  new bindings to pass strict mode, and `maintainer-soc.rst` asks new DTS code
  for no relaxed warnings. Its own tests are `make dt_style_selftest`. So all
  three also left the style step out of what `dt_binding_check` does.
- **Checking one schema.** None knew the top-level `%.yaml` rule:
  `make sram/sram.yaml` builds that file's example and runs
  `dt_binding_check_one`. A said there was no such target, C was unsure and
  invented an exported variable, B offered a `make -C` workaround.
- **Minimum dtschema version.** All said 2023.9 or "2023.x".
  `DT_SCHEMA_MIN_VERSION` is 2024.4, compared against
  `dt-doc-validate --version`.
- **The registry schemas.** `trivial-devices.yaml` allows `reg`, `interrupts`
  and `spi-max-frequency` beside `compatible` and nothing else; A and C said it
  allows a supply, B said only `reg`. `incomplete-devices.yaml` was blank for
  A, "does not exist" for B and half right for C: it lists compatibles that
  drivers match but that are banned from DTS, and makes any node using one fail
  by requiring a property named `broken-usage-of-incorrect-compatible`.
- **Header macros.** `maintainer-soc.rst` calls macros in
  `include/dt-bindings/` a last resort, not for constants that can be read off
  a datasheet, and lists four ways round the cross-tree dependency. No reader
  had more than one of them, and B said the document forbids renumbering, which
  it does not mention.
- **What the undocumented-compatible tools match.** `dt-extract-compatibles`
  reads `.c` files for `of_device_id` tables, the `OF_` and `IRQCHIP_` declare
  and match macros and the compatible lookup calls; checkpatch looks at added
  `compatible` lines in `.dts`, `.dtsi`, `.c` and `.h` files, greps the whole
  bindings directory for the string and checks only the vendor prefix against
  `vendor-prefixes.yaml`. Each reader blurred or missed part of this; B said
  checkpatch has no such check.
- **checkpatch's binding warnings.** None could name them or their triggers:
  `DT_SPLIT_BINDING_PATCH` (binding side is `Documentation/devicetree/` or
  `include/dt-bindings/`, `MAINTAINERS` is ignored), `DT_SCHEMA_BINDING_PATCH`
  (only a newly created `.txt`), `UNDOCUMENTED_DT_STRING`, and two
  `SPDX_LICENSE_TAG` checks (documents must be GPL-2.0 or GPL-2.0-only `OR
  BSD-2-Clause`; headers GPL-2.0 or GPL-2.0-only `OR` anything).
- **Subject lines.** The subsystems that want the prefix reversed are ASoC,
  media, regulators, SCSI, SPI and UFS; readers named one to four. The words to
  leave out are "Documentation", "doc", "YAML" and a repeated "binding", not
  "schema": the conversion subject is "Convert to DT schema".
- **What the documents say about examples.** As complete as possible, known
  defines for flags, no `status` in typical cases, no unrelated or
  phandle-target nodes, phandles need not resolve, four-space indent preferred,
  default `#address-cells` and `#size-cells` of 1, includes written out. Each
  reader had some of it and added rules the documents do not contain.
- **ABI wording.** All three named U-Boot, the BSDs or firmware as the other
  users. `writing-bindings.rst` says only "other open-source upstream
  projects", and `ABI.rst` names none. `ABI.rst` allows adding properties that
  default to the old behaviour and changing the compatible string for an
  incompatible change; it has no list of "relaxing constraints".
- **`deprecated: true` is in no document.** Over three hundred schemas use it
  and no `.rst` under `Documentation/devicetree/` mentions it. B said it was
  documented; A and C hedged.
- **The maintainer profile.** `Documentation/process/maintainer-devicetree.rst`
  says bindings are reviewed by the DT maintainers and normally applied by the
  subsystem maintainer. C said no such file exists, A left it out, B cited a
  file name that is not in the tree.
- **Counts.** About 634 `.txt` bindings remain beside about 5,700 schemas.
  Guesses ran from "low tens" to 900.

## What only some readers got wrong

- Reader A said `additionalProperties: false` cannot be combined with a `$ref`
  or `allOf`, and that a top-level `additionalProperties: true` is usually
  paired with `select: false`. `example-schema.yaml` combines the first pair,
  and `writing-schema.rst` allows it when only some of a referenced schema's
  properties are wanted. About 330 schemas have the top-level `true`, 20 have
  `select: false`. A also made `dtbs_check W=1` a general rule; the documents
  ask it of RISC-V and Samsung only.
- Readers A and B said a schema without `select` is matched on compatible
  alone. The node name is used too, which is how the root-node board schemas
  match.
- Reader C said `additionalProperties: false` ignores a property defined only
  inside an `if`/`then`; it rejects it. C also said `contains` matches a
  fallback at the end of the list; it matches at any position.
- Reader B alone: the meta-schemas, `types.yaml` and the core schemas are in
  the kernel tree (they are in dtschema); the tools do not infer `minItems`
  (they do, which is why it sometimes has to be written); a top-level
  `additionalProperties: true` is "essentially never right"; a versioned IP
  block gets a version suffix (the document says the opposite); wildcards are
  only discouraged; a SoC-specific compatible is needed only when behaviour may
  differ; `dt-doc-validate` stops the build (the lint, binding-check and
  style steps and the DTB check end in `|| true`; the schema version check,
  example extraction, schema processing and `dtc` itself do stop it); a trivial compatible addition may ride in the driver patch.
- Readers A and B missed that DTS patches may be a separate posting instead of
  the tail of the series, and gave their own reasons for keeping them apart.
  The document's are that DTS is driver independent, goes through another tree,
  and any other order suggests a series that cannot be bisected.

## What the readers already knew

Readers A and C needed little or nothing on `$id` and how `$ref` resolves
against it, on what a wrong `$id` does and that `dt-doc-validate` reports it,
on conditions that test an optional property, on where a property is defined
and where it is narrowed, on matching compatible with `contains`, on vendor
property types, on provider properties, on the `oneOf` shape for a compatible
with a fallback, on `DT_SCHEMA_FILES` and on the external schemas. Reader C
also had `select`, the closing keyword, the design rules and property naming
right. That is, the three topics of the hand-written guide are the three that
the better readers know best.

## Where the hand-written guide is stale

`dt-bindings.md` names nothing that is missing from the tree; the sentence it
quotes from `example-schema.yaml` is still there word for word. What it gets
wrong is tone and coverage:

- It says every cell-count property must have a `const`. Nearly all do, and a
  few correct bindings use `enum` (`clock/st,stm32-rcc.yaml`,
  `pwm/pwm-rockchip.yaml`).
- It says provider properties must be added to `required`. No document says
  so. `example-schema.yaml` itself requires `interrupt-controller` and not
  `#interrupt-cells`. Most in-tree provider bindings do require them.
- It says every `if` block that lists earlier generations has to gain the new
  string. It does not say that a new string placed in front of a fallback is
  already covered by blocks that test the fallback with `contains`, which is
  the form the documents prefer, or that a block's `else` applies to a string
  that was left out.
- It says `dt_binding_check` is defined in the bindings `Makefile`. The
  top-level `Makefile` defines it too and sets `CHECK_DTBS`; and it says a bad
  `$id` may "silently skip validation", where in fact the binding check that
  would report it only prints: it is one of the steps that end in `|| true`.
- It has nothing on the closing keyword, the ABI rules, compatible naming,
  the patch rules, the registries or any of the tools.

## Left out of the build set

The hand-written guide is 617 words and no answer is budgeted under 40, so the
build set holds 10 of the 45 questions, with budgets of 45 to 65 words that add
up to 520. Kept: what every reader got wrong and a reviewer meets on most
patches (the tools and what they do, the registries, checkpatch), the two
questions rated 5 where a reader was wrong on substance (the closing keyword,
compatible naming), the ABI rule, and the one topic of the hand-written guide
that no tool reports when it is missed (a new compatible left out of an `if`
block). Left out although a reader got them wrong: the dtschema version,
`DT_SCHEMA_FILES`, the style rule table and the undocumented-compatible tools
(one `grep` away once the tool is named); the patch split and order (the split
is what checkpatch's `DT_SPLIT_BINDING_PATCH` reports, which the guide carries,
and the order is one numbered list in the document the map points to); header
macros, example contents, YAML style, the design rules, property naming, file
naming and the subject line (each is a short list in one document that the map
points to); `select`, child nodes, array fix-ups, deprecation and splitting a
schema (readers A and C were close, and B is wrong everywhere); who applies
what; text bindings. Left out because readers A and C had them right: `$id`
rules and what a wrong `$id` does, provider properties, where a property is
defined and where it is narrowed, the external schemas, vendor property types,
the compatible `oneOf` shape, names properties, conditions on compatible and on
optional properties, forbidding a property. A wrong `$id`, provider properties
and where a property is defined are the rest of the hand-written guide's own
topics: at 25 words each they came out as fragments, and at 40 they would take
room from what the readers lack.

## The numbers

Share of each from-memory answer the checker rewrote, with the number of
corrections in brackets. Rewritten counts rewording too; the corrections are
what count.

```
reader A: 79 corrections, 40% rewritten on average
reader B: 86 corrections, 78% rewritten on average
reader C: 63 corrections, 22% rewritten on average

question                           reader A      reader B      reader C
dtb.doc-map                        35% ( 5)      34% ( 7)      24% ( 5)
dtb.registry-schemas               73% ( 3)      86% ( 3)      49% ( 2)
dtb.external-schemas                0% ( 0)      80% ( 2)       7% ( 1)
dtb.headers                        45% ( 1)      87% ( 1)      54% ( 1)
dtb.make-targets                   30% ( 2)      80% ( 1)      30% ( 3)
dtb.check-steps                    12% ( 1)      91% ( 3)       6% ( 1)
dtb.schema-files-var               24% ( 1)      81% ( 1)       3% ( 1)
dtb.dtschema-version               22% ( 1)      81% ( 1)      30% ( 1)
dtb.style-checker                  92% ( 1)      91% ( 1)      98% ( 1)
dtb.style-rules                   100% ( 1)      98% ( 1)      98% ( 1)
dtb.dtbs-check-behaviour           70% ( 2)      90% ( 1)      33% ( 1)
dtb.compatible-check               50% ( 2)      93% ( 2)      50% ( 1)
dtb.top-level-keys                 34% ( 4)      79% ( 4)      29% ( 1)
dtb.id-rules                       20% ( 1)      64% ( 1)       0% ( 0)
dtb.id-mismatch                     0% ( 0)      73% ( 1)       0% ( 0)
dtb.select                         30% ( 1)      65% ( 1)       0% ( 0)
dtb.additional-vs-unevaluated      56% ( 4)      83% ( 1)       0% ( 0)
dtb.child-nodes                    39% ( 1)      56% ( 1)      22% ( 1)
dtb.property-types                  0% ( 2)      84% ( 1)       2% ( 1)
dtb.array-fixups                   21% ( 1)      82% ( 1)      24% ( 3)
dtb.compatible-schema              20% ( 1)      69% ( 1)       9% ( 1)
dtb.names-properties               45% ( 1)      76% ( 1)      22% ( 2)
dtb.provider-properties            10% ( 1)      74% ( 2)      12% ( 2)
dtb.deprecated                     40% ( 1)      72% ( 2)      31% ( 1)
dtb.conditional-shape               7% ( 1)      66% ( 3)       8% ( 1)
dtb.if-compatible-matching          3% ( 1)      80% ( 1)       3% ( 1)
dtb.new-compatible-usage           38% ( 1)      86% ( 1)       8% ( 1)
dtb.if-optional-property            0% ( 0)      57% ( 1)      12% ( 1)
dtb.forbid-property                48% ( 1)      58% ( 1)       0% ( 0)
dtb.split-schema                   59% ( 1)      78% ( 1)      25% ( 1)
dtb.compatible-naming              66% ( 6)      88% ( 9)      30% ( 3)
dtb.file-naming                    50% ( 1)      79% ( 1)      12% ( 1)
dtb.design-donts                   46% ( 3)      82% ( 4)       0% ( 0)
dtb.property-naming                41% ( 1)      77% ( 1)       0% ( 0)
dtb.examples                       67% ( 1)      91% ( 3)      40% ( 3)
dtb.yaml-style                     69% ( 2)      83% ( 2)      39% ( 2)
dtb.abi-rules                      81% ( 3)      84% ( 4)      10% ( 1)
dtb.abi-break-usage                24% ( 2)      55% ( 3)      22% ( 4)
dtb.patch-split                    54% ( 4)      87% ( 3)      27% ( 3)
dtb.subject-prefix                 46% ( 3)      81% ( 1)      41% ( 3)
dtb.license                        39% ( 1)      66% ( 1)      15% ( 1)
dtb.checkpatch                     53% ( 3)      94% ( 2)      40% ( 3)
dtb.who-applies                    54% ( 3)      79% ( 1)      18% ( 1)
dtb.undocumented-compatible        34% ( 2)      88% ( 1)      11% ( 1)
dtb.txt-bindings                   56% ( 1)      82% ( 1)      36% ( 1)
```

## Questions put back

These were measured, matter to a review, and were answered badly by the readers, but were
left out of the first build set to keep the guide to a word count. No guide is held to a
word count now, so they are back in the build set: `dtb.examples`, `dtb.abi-rules`, `dtb.patch-split`.
Every budget is also back to what the question was first given.
A guide is written for the weakest of its readers, not for most of them, so a question is left
out only when every reader already answers it. Put back on that rule, having been left out
because most readers knew the answer although one did not: `dtb.external-schemas`, `dtb.id-rules`, `dtb.id-mismatch`, `dtb.property-types`, `dtb.array-fixups`, `dtb.compatible-schema`, `dtb.names-properties`, `dtb.provider-properties`, `dtb.conditional-shape`, `dtb.if-compatible-matching`, `dtb.design-donts`, `dtb.property-naming`, `dtb.undocumented-compatible`.

## Questions reorganised

Organised by subject, 28 questions before and 26 after: checks and tools, schema structure,
properties, compatible strings and ABI, design rules and examples, patches.
Merged: `dtb.id-rules` and `dtb.id-mismatch` into `dtb.schema-id`; `dtb.if-compatible-matching`
and `dtb.new-compatible-usage` into `dtb.compatible-conditions`; `dtb.abi-rules` and
`dtb.abi-break-usage` into `dtb.abi-changes`; `dtb.compatible-schema` and the fallback half of
`dtb.compatible-naming` into `dtb.compatible-fallbacks`.
Split, each having asked six things: `dtb.compatible-naming` keeps how specific a string must be;
`dtb.design-donts` is now `dtb.design-nodes` and `dtb.design-hardware-description`. None dropped.
