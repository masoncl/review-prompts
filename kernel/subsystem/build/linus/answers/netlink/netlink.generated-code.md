- Marker match: `ynl-regen.sh` uses `git grep`, so it finds only files
  tracked by git; a new generated file needs the two marker lines and a
  `git add` first (see `Documentation/userspace-api/netlink/intro-specs.rst`).
- Marker layout: `/* YNL-GEN <mode> <type> */` must start a line, and the
  spec path must be the comment on the line directly before it.
- Modes: `kernel`, `uapi` and `user`; uAPI headers under `include/uapi/`
  carry `/* YNL-GEN uapi header */` and are regenerated the same way.
- `/* YNL-ARG ... */`: a separate line that holds `--user-header`,
  `--exclude-op` and `--function-prefix`; `ynl-regen.sh` passes it on
  verbatim, for example in `drivers/net/wireguard/generated/netlink.c`.
- `/* To regenerate run: tools/net/ynl/ynl-regen.sh */`: written by `main()`
  in `tools/net/ynl/pyynl/ynl_gen_c.py` into every generated file.
- Skip test: compares the file's mtime with the spec's only; a change to
  `ynl_gen_c.py` regenerates nothing without `-f`.
- Family struct gate: `kernel_can_gen_family_struct()`, true only for
  `protocol` `genetlink`; the op table and policies have no such gate.

| Level | Op policies | Op table | `struct genl_family` |
|---|---|---|---|
| `genetlink` | static | static, `[]` | emitted |
| `genetlink-c` | static | exported, sized | not emitted |
| `genetlink-legacy` | static if `split`, else exported | exported, sized | not emitted |
| `netlink-raw` | no kernel file in tree | no kernel file in tree | not emitted |

- Exported op table: `const`, with an explicit element count, declared
  `extern` in the generated header; the hand-written family points at it,
  as `net/mptcp/pm_netlink.c` does with `mptcp_pm_nl_ops`.
- Policies of nested attribute sets used in a request: exported and
  declared in the header at every level, including `genetlink`.
- `netlink-raw`: the kernel-mode path of `main()` has no test that refuses
  it; no committed kernel file is generated from a netlink-raw spec.
