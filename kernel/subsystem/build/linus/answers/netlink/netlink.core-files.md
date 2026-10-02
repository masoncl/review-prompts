| Job | Where, and what is easy to miss |
|---|---|
| Kernel-internal Generic Netlink header | `include/net/genetlink.h`; there is no include/linux/genetlink.h in this tree |
| `struct netlink_ext_ack`, `NL_SET_ERR_MSG()` | `include/linux/netlink.h`, not `include/net/netlink.h` |
| Generated kernel code | no naming rule and not only under `net/`; search for `YNL-GEN kernel`; for example `net/core/netdev-genl-gen.c`, `net/devlink/netlink_gen.c`, `fs/nfsd/netlink.c`, `drivers/dpll/dpll_nl.c` |
| Generated uAPI headers | search for `YNL-GEN uapi header`; file name and directory need not match the family, for example `include/uapi/linux/ethtool_netlink_generated.h`, `include/uapi/drm/drm_ras.h` |
| Specs without a generated uAPI header | about half of the specs; for example `include/uapi/linux/devlink.h` is hand-written although `net/devlink/netlink_gen.c` is generated |
| Regenerating checked-in generated files | `tools/net/ynl/ynl-regen.sh` |
| Generated user-space C code | `tools/net/ynl/generated/` holds only `Makefile` and `.gitignore`; the `-user.c` and `-user.h` files are build output; `GENS_UNSUP` there leaves out conntrack and nftables |
| C sample and test programs | `tools/net/ynl/tests/`; there is no tools/net/ynl/samples/ in this tree |
| C command-line tool on top of `libynl.a` | `tools/net/ynl/ynltool/` |
| Rendered spec documentation | `Documentation/netlink/specs/index.rst`, parsed by `Documentation/sphinx/parser_yaml.py` using `tools/net/ynl/pyynl/lib/doc_generator.py`; there is no Documentation/networking/netlink_spec/ |
| Running the YNL tests | `make -C tools/net/ynl` first, then `make -C tools/net/ynl run_tests`; `run_tests` in `tools/net/ynl/tests/Makefile` has no build prerequisite |
| What `run_tests` runs | the `TEST_PROGS` scripts only; the `TEST_GEN_PROGS` binaries are built by `all` and not run by `run_tests` |
| YNL tests and kselftest | `tools/net/ynl/tests/` is not a `TARGETS` entry in `tools/testing/selftests/Makefile`; needed kernel options are in `tools/net/ynl/tests/config` |
| Spec lint and schema check | `lint` and `schema_check` targets in `tools/net/ynl/Makefile` |
| Selftest for the `nlctrl` family (family info and policy dump) | `tools/testing/selftests/net/nl_nlctrl.py` |
| YNL glue for kselftests | C: `tools/testing/selftests/net/ynl.mk` builds `libynl.a` for the families in `YNL_GENS`; Python: `tools/testing/selftests/net/lib/py/ynl.py` |
