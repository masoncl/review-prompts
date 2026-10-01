# pahole Review False-Positive Guide

## Legacy Code Is Context, Not Automatically a Finding

Flag regressions introduced by the patch. Do not turn a review of a focused
change into a demand to rewrite adjacent legacy style or error handling unless
the new code depends on it or makes it unsafe.

## Not Every Missing Debug Attribute Is a Bug

Many DWARF attributes are optional and declarations need not have full layout
information. Flag code only when it dereferences or relies on an optional value
without handling its absence, or when a documented supported input loses data.

## Do Not Assume All Type Aliases Must Be Followed

Following a typedef is right for operations that require the underlying
aggregate; retaining the typedef is right when output must reflect source-level
identity. Ask which representation the caller promises before reporting a
missing `tag__follow_typedef()`.

## Output Differences Need a Contract

Whitespace or ordering differences are not automatically regressions. Flag them
when a documented interface, an existing focused test, a parser, or an option’s
semantics establishes that behavior. Conversely, treat BTF ID/order changes as
significant when split BTF, deduplication, or reproducible output consumes them.

## Existing libbpf Is Imported Code

Do not apply pahole-local style expectations to unchanged `lib/bpf/` contents.
For modifications there, ask whether this is an intentional upstream sync and
whether integration paths still work.

## Environment-Dependent Tests

A test requiring `vmlinux`, `bpftool`, a particular compiler, or network access
may legitimately skip. Flag a test failure only after separating a missing
prerequisite from an assertion failure, and do not call a feature untested if a
focused fixture covers the behavior without that optional dependency.
