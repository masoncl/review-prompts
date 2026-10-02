- `protocol` (top-level property, default `genetlink`) selects the level;
  `SpecFamily.__init__()` in `tools/net/ynl/pyynl/lib/nlspec.py` loads
  `<protocol>.yaml` from the parent of the spec's directory.
- Specs carry no `$schema` line; under `Documentation/netlink/` `$schema`
  appears only inside the four schema files.
- The schema files are not strict supersets: `genetlink-c.yaml` and
  `netlink-raw.yaml` accept only `admin-perm` under `flags`;
  `genetlink.yaml` and `genetlink-legacy.yaml` also accept
  `uns-admin-perm`.
- `netlink-raw.yaml`: accepts only `netlink-raw` as `protocol`.
- `genetlink.yaml` already accepts `name-prefix` and `enum-name` on
  attribute sets and on `operations`; `genetlink-c.yaml` adds the remaining
  C naming properties, marked by "Start genetlink-c" comments.
- No spec under `Documentation/netlink/specs/` declares `genetlink-c`.
- `make -C tools/net/ynl schema_check`: runs
  `./pyynl/cli.py --spec <spec> --validate` on each `*.yaml` in
  `Documentation/netlink/specs/` and prints `ok` or `not ok` per spec.
- `schema_check` exit status: 0 even when a spec fails, because the recipe
  is one shell loop that ends with the counter increment; read the output.
- `make -C tools/net/ynl lint`: runs only `yamllint` on
  `Documentation/netlink/specs/`; it lints neither the schema files nor the
  Python tools.
- yamllint configuration: none for the specs; the only `.yamllint` in the
  tree is `Documentation/devicetree/bindings/.yamllint`.
