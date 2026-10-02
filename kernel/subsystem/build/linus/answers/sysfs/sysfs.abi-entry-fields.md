- `Documentation/ABI/README` marks only `KernelVersion:` as "(Optional)";
  `What:`, `Date:`, `Contact:`, `Description:` and `Users:` are listed with no
  such mark.
- `AbiParser` in `tools/lib/python/abi/abi_parser.py` enforces less: for a
  missing field it warns only when an entry has no `Description:`; a missing
  `Date:`, `Contact:` or `Users:` passes `validate`.
- Directory for a new entry: `Documentation/ABI/README` leaves it to the
  developer who adds the interface, not to the maintainer.
