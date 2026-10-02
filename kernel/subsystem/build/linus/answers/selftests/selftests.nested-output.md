- `run_many()`: prints no `TAP version 13` line and no plan.
- `make run_tests`, `make kselftest`: nothing prints a version line, a plan or
  a totals line for the run; the stream holds `# selftests: ...` headers,
  `# `-prefixed program output and result lines.
- `run_kselftest.sh`: calls `ktap_print_header` and `ktap_set_plan "$total"`
  once for the whole run, before the first collection, and
  `ktap_print_totals` at the end.
- `$total`: the number of tests selected after `-t`, `-c` and `-S`, over all
  collections.
- Test numbers under `run_kselftest.sh` without `-n`: `KTAP_TESTNO` is one
  counter in one shell, so numbering continues across collections.
- Test numbers under make: each target directory's recipe sources
  `ktap_helpers.sh` afresh, so numbering restarts at 1 per directory.
- `KSFT_TAP_LEVEL`: nothing in this tree sets it; the only occurrence is the
  `getenv()` in `ksft_print_header()` in `tools/testing/selftests/kselftest.h`.
- Under either runner a C test therefore prints its own version line, which
  appears as `# TAP version 13`.
- `ktap_print_header()` in `kselftest/ktap_helpers.sh` and `print_header()` in
  `kselftest/ksft.py`: do not read `KSFT_TAP_LEVEL`; they print the version
  line unconditionally.
