# BTF Review Guidance

## BTF Is an Indexed Binary Format

Type IDs, string offsets, kinds, `vlen`, payload sizes, and section boundaries
are all part of the format contract. Check bounds before following an ID or
offset and before multiplying count-derived sizes. Do not use a successful
allocation or a non-NULL BTF handle as proof that a referenced item is valid.

## Feature Availability Is a libbpf Capability, Not a Kernel-Version Check

Pahole should be as decoupled from the target kernel as feasible. A BTF feature
is available when the libbpf API linked into pahole can implement it, not merely
because a kernel version is new enough (or because the BTF input came from a
kernel that supports it). Do not add kernel-version gates for encoder features.

The selected library is a build-time choice: the normal
`-DLIBBPF_EMBEDDED=ON` configuration builds against the repository's embedded
`lib/bpf/` copy, while `-DLIBBPF_EMBEDDED=OFF` discovers and links the available
system libbpf. Runtime feature detection must work in both cases; it describes
the libbpf actually linked to that pahole binary, not an assumed version of the
embedded subtree or host kernel.

Optional libbpf APIs are declared weakly in `dwarves.h`. Code using one must
test the function pointer before calling it. This allows one pahole binary to
run with an older libbpf: an absent symbol is a capability absence, not a loader
or process-startup failure.

```c
if (btf__add_enum64 != NULL)
	return btf__add_enum64(btf, name, size, is_signed);

/* Use the established fallback/skip policy for this feature. */
```

Keep capability checks in one feature predicate and use that same predicate for
both option handling and supported-feature reporting. `--supported_btf_features`
must list the features actually available with the linked libbpf, not every
feature compiled into pahole's source tree.

### Requested Features and Graceful Degradation

The non-strict `--btf_features`/`--features` interface is forward compatible:
an unknown or unavailable named feature should be diagnosed and ignored so a
caller can use one feature list across pahole/libbpf versions. The strict
variant may fail deliberately. Do not turn a non-strict unavailable feature
into a fatal error, and do not silently claim to have enabled it.

Feature defaults are separate from feature availability. Each feature is either
in the default set or non-default:

- `--btf_features=default` enables the supported default set.
- `--btf_features=+feature1,...` starts with that supported default set and
  adds named features.
- A non-default feature needs an explicit name; it must not become enabled just
  because another default feature is requested.
- `--btf_features=all` asks for the broader set, but its documented exclusions
  and compatibility rules still apply.

In every case, the runtime libbpf capability predicate is the final gate. Do
not advertise an unavailable default feature as enabled, or let an unavailable
non-default feature change the output. When adding a feature, decide and test
both its default-set membership and its unavailable-libbpf behavior.

For an optional feature implementation, review all three outcomes:

1. Supported and requested: enable it and test its encoded result.
2. Unsupported and requested non-strictly: report/ignore it without failure.
3. Unsupported: omit it from supported-feature output and never call its weak
   API.

Test this against the oldest libbpf configuration intended to be supported as
well as a configuration that provides the API. Where a change can affect build
integration, exercise both embedded libbpf and `-DLIBBPF_EMBEDDED=OFF` with a
system libbpf. The test should assert observed capability reporting and
successful fallback, rather than infer support from the running kernel version.

## Encoder Checklist

- [ ] Every BTF/ELF/libbpf operation has its return value checked.
- [ ] Optional libbpf APIs have a weak-symbol capability check before use.
- [ ] Feature reporting and feature enablement use the same runtime capability
      check; no kernel-version gate substitutes for libbpf availability.
- [ ] Default and non-default membership is intentional: `default`, `+…`, and
      `all` retain their documented enablement and exclusion semantics.
- [ ] Non-strict requests for unknown/unavailable BTF features degrade as the
      feature interface specifies, without a crash or false success.
- [ ] Type emission is deterministic for equivalent input.
- [ ] New filtering or deduplication does not change IDs/order required by
      later fixups, split BTF, or a distilled base.
- [ ] Function, variable, datasec, declaration-tag, type-tag, enum, and
      forward-type paths are considered when altering shared encoding logic.
- [ ] ELF symbol and section metadata agree with the emitted BTF payload.
- [ ] Failure leaves no partially written output presented as valid.

## Loader Checklist

- [ ] Validate header ranges and all variable-length records before reading.
- [ ] Preserve the distinction among BTF kinds rather than forcing uncommon
      kinds through a struct/typedef path.
- [ ] Check string offsets and NUL termination within the BTF string section.
- [ ] Maintain base/split-BTF provenance when a type may be satisfied by a
      base object.

## Vendored libbpf

`lib/bpf/` is pahole's embedded libbpf Git submodule, regularly synchronized
from [github.com/libbpf/libbpf](https://github.com/libbpf/libbpf). That GitHub
repository is itself a periodic mirror of the authoritative libbpf source at
`tools/lib/bpf` in the bpf-next Linux kernel tree. Treat an update as a
provenance-preserving sync: record/confirm the upstream revision and keep it
separate from pahole-local behavior changes.

Pahole must also work with a system libbpf selected by
`-DLIBBPF_EMBEDDED=OFF`, which can be older than the submodule headers. It
handles API skew in two complementary ways:

- Weak declarations in `dwarves.h` allow an optional symbol to be absent at
  runtime; call sites test the symbol before using it.
- Version/header macros guard code whose declarations, types, or struct fields
  do not exist at compile time with an older system libbpf.

Use the least restrictive mechanism that is correct for the API: a macro guard
for compile-time source compatibility, and a weak-symbol capability check for
an optional runtime API. Do not replace either with an assumed kernel version.
For any new libbpf API, review both embedded and system-lib builds, the
unavailable-API fallback, and supported-feature reporting. Do not demand
pahole-local coding conventions for unchanged imported code; do verify that
both embedded and system-lib CMake configurations still build. Before an
upstream libbpf change reaches the GitHub mirror/submodule, build and install
`tools/lib/bpf` from the relevant kernel tree, then configure pahole with
`-DLIBBPF_EMBEDDED=OFF`; see `build-and-test.md` for the exact workflow.

## Essential Tests

Use or extend the focused BTF tests for the changed feature (`btf_*`, split,
distilled-base, functions, tags, arrays, bitfields, or datasecs). A text-only
test is insufficient for an encoder change: validate emitted BTF with an
appropriate consumer such as `bpftool` when the existing test infrastructure
does so.
