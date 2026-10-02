- Not in the checklist: reset or kexec survival, unsharing host and guest
  memory, zero-checking flags or padding, argument validation, compat
  handling, MSR index lists, `scripts/checkpatch.pl`.
- Item 1: cites `Documentation/process/coding-style.rst` and
  `Documentation/process/submitting-patches.rst` only.
- Item 3 applies when a patch "introduces or modifies" a userspace API, not
  only when it adds one.
- Item 5: performance improvements "can and should default to on"; only
  features default to off.
- Item 6: new CPU features "should be exposed via" KVM_GET_SUPPORTED_CPUID2
  "or its equivalent for non-x86 architectures"; that name is defined nowhere
  in the tree, the ioctl is `KVM_GET_SUPPORTED_CPUID`.
- Items 8 and 9: changes "should be vendor neutral when possible", and common
  and arch-independent code is preferred; nothing requires a feature to work
  or be tested on every vendor.
- Item 10: user/kernel and guest/host interfaces "must be 64-bit clean":
  naturally aligned on 64-bit, `u64` rather than `ulong`.
- Item 11: a guest-visible feature must be documented in a hardware manual or
  come with documentation; the item names no location for it.
- Tests: item 7 says "should be testable"; the testing section asks for "some
  kind of tests and/or enablement in open source guests and VMMs", not
  selftests specifically.
- Maintainers "reserve the right to require more tests" and may waive the
  requirement.
- New hardware features (new registers, no new APIs): tested via
  kvm-unit-tests; selftests can be used instead in some cases, or for
  save/restore corner cases.
- New APIs: the submitter demonstrates the use case; selftests cover API
  corner cases, and basic host and guest operation if no open source VMM uses
  the feature.
- Bigger host-plus-guest features: supported by Linux guests, except Hyper-V
  features testable on Windows guests; selftests cover at least API error
  cases.
