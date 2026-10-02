| Topic | Preference | Reason the documents state |
|---|---|---|
| Array | `multi-attr`: the attribute itself repeats, no wrapper nest | "(no extra nesting)"; the `indexed-array` wrapper limits the array to 64kB |
| C structure | one attribute per member | `Documentation/userspace-api/netlink/intro.rst`: structures "caused problems with validation and extensibility" |
| Integer width | `sint` / `uint` over fixed-width types "in majority of cases" | none stated |
| Narrower than 32 bits | avoid | no memory saved in the message, due to alignment |

- Per-element extension and "the index carries no meaning": not reasons the
  documents give for `multi-attr`.
- C layout or padding: not a reason the documents give against structures.
- `sint` / `uint` and alignment:
  `Documentation/userspace-api/netlink/specs.rst` warns that the full 64 bit
  value may be unaligned; avoiding alignment problems is not a stated benefit.
- `nla_put_uint()` and `nla_put_sint()` in `include/net/netlink.h`: emit the
  8-byte form with `nla_put()`, not `nla_put_64bit()`, so no pad attribute is
  added.
- `type-value` nesting:
  `Documentation/userspace-api/netlink/genetlink-legacy.rst` says modern
  families should use a flat structure, "the nesting serves no good purpose".
