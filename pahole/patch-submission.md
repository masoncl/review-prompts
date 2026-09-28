# Submitting pahole Patches

Use a focused component prefix in the subject, such as:

```
dwarf_loader: handle arm64 floating-point parameter registers
btf_encoder: preserve declaration tag component index
pahole: apply a filter to unions
tests: cover a bitfield layout edge case
```

The body should state the input shape that triggers the issue, the incorrect
current behavior, and why the proposed handling preserves DWARF/BTF or output
semantics. Mention the test added or updated. Include `Fixes:` when applicable
and a `Signed-off-by:` line according to the project’s contribution workflow.

Send reviewable changes as logical patches: do not mix loader semantics, output
cleanup, test refactoring, and a `lib/bpf` sync in one patch. Build and run the
focused test before posting; run the broader suite where the change crosses
shared type, loader, or encoder infrastructure.

The project release tooling references `dwarves@vger.kernel.org`; use the
maintainer/project instructions current at submission time for recipients and
branch targeting.
