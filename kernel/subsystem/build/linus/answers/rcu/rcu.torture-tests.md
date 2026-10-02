- No mandatory minimum is written in the tree:
  `Documentation/RCU/torture.rst` says not all changes need all scenarios,
  and gives `--configs 'SRCU-N SRCU-P'` for a Tree SRCU change.
- `kvm.sh` with no `--configs`: runs
  `tools/testing/selftests/rcutorture/configs/rcu/CFLIST`; the word `CFLIST`
  inside `--configs` expands to the same list, as in `'5*CFLIST'`.
- `CFLIST` TREE entries: `TREE01` to `TREE05`, `TREE07` and `TREE09` only.
- Scenario files present but not in `CFLIST`, run only when named in
  `--configs`: `TREE06`, `TREE08`, `TREE10`, `NOCB01`, `NOCB02`, `TRIVIAL`,
  `TRIVIAL-PREEMPT`, `BUSTED`, `BUSTED-BOOST`.
- `rcu_nocbs=all`: only in `TREE08.boot`, `NOCB01.boot` and `NOCB02.boot`,
  so a default run never boots with every CPU offloaded.
- `CONFIG_PREEMPT_RT`: set by no file under
  `tools/testing/selftests/rcutorture/configs/rcu/`; `torture.sh` adds it to
  `TREE03` through `--kconfig` (`--do-rt`, on by default).
- `torture.sh` defaults: KASAN pass on, KCSAN pass off; `--do-kcsan` or
  `--do-all` turns KCSAN on.
- Working directory: `kvm.sh` changes to the top of the tree itself;
  `torture.sh` builds its paths from `pwd` and must be started there.
- `kvm.sh` defaults: 30 minutes per scenario; with neither `--cpus` nor
  `--allcpus` each scenario runs in its own batch, one after another.
- Only one `kvm.sh` per source tree: it takes a `flock` on `.kvm.sh.lock`
  and exits if another run holds it; `--kill-previous` kills the holder.
- `tools/testing/selftests/rcutorture/Makefile`: its `all` target runs only
  `kvm.sh --duration 10 --configs TREE01`.
- `kvm.sh` exit status comes from `kvm-recheck.sh`: 1 for `.config` errors,
  2 for build errors, 3 for runtime errors; when several kinds occur the
  highest number wins.
- `.config` errors: `configcheck.sh` reports a scenario when the built
  `.config` lacks a line that the scenario file sets to other than `=n`, or
  sets an option that the file gives as `=n`; `#CHECK#` lines are tested
  too. So a patch that renames or re-gates a `CONFIG_RCU_` option that a
  scenario turns on must update the scenario files.
- Runtime errors: `parse-console.sh` flags console lines matched by
  `console-badness.sh`, whose patterns include `Warn`, `BUG` and `!!!`, so
  a new message under `kernel/rcu/` with such text fails every scenario that
  prints it.
