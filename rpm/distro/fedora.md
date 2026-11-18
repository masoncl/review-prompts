# Fedora Packaging Guidelines

## When to Load

Load this file when the target distribution is Fedora (detected by .fc* dist
tag, %{?fedora} macro, rawhide branch, or f* branch names).

## Fedora Packaging Guidelines Reference

The authoritative source is:
https://docs.fedoraproject.org/en-US/packaging-guidelines/

## Fedora-Specific Requirements

### License
- SPDX license identifiers mandatory since Fedora 38
- Reference: https://docs.fedoraproject.org/en-US/legal/allowed-licenses/

### Naming Conventions
- Python packages: `python3-*`
- Rust packages: `rust-*` (with `rust-*-devel` for library crates)
- Go packages: `golang-*`
- Ruby packages: `rubygem-*`
- Perl packages: `perl-*`
- Compatibility packages: `compat-*`

### Source Handling
- `%forgemeta` / `%forgesource` for GitHub/GitLab/etc. hosted projects
- `%pyproject_*` macros for Python packages
- `%cargo_*` macros for Rust packages
- `%gometa` / `%golist` for Go packages

### Build Requirements
- Use `%generate_buildrequires` with `%pyproject_buildrequires` for Python
- Dynamic BuildRequires supported and encouraged

### Filesystem
- `/usr/lib/` for noarch data, `/usr/lib64/` for 64-bit libraries
- No `/usr/lib/` for 64-bit libraries (use `%{_libdir}`)
- `/usr/libexec/` for internal executables

## Fedora Review Process

### Package Review Checklist
A Fedora package review typically checks:
1. Spec file follows naming guidelines
2. License is correct and allowed
3. Source URL works and matches upstream
4. Package builds in mock
5. rpmlint output is clean (or false positives documented)
6. File permissions are correct
7. Scriptlets are safe
8. Dependencies are correct and minimal
9. %check section runs tests (if available)
10. Documentation and license files are packaged

### Common Fedora-Specific Issues
- Missing `%{?_isa}` on library dependencies
- Using `%{_lib}` instead of `%{_libdir}`
- Not using `%pyproject_*` macros for Python packages
- Missing `%check` when upstream has tests
- Static libraries shipped without `-static` subpackage

## AI-Assisted Contributions

Fedora's AI-Assisted Contributions Policy (Fedora Council, v1.0,
2025-10-24) applies to anything contributed to the Fedora Project,
including EPEL: dist-git commits, pull requests to Fedora-hosted tooling
and docs, Bugzilla comments, and package reviews.

https://docs.fedoraproject.org/en-US/council/policy/ai-contribution-policy/

### Commits
- The human contributor is the author and is fully accountable. Never set
  an AI agent as the commit author or co-author
- Disclose AI assistance. Disclosure is required when a significant part
  of the contribution is taken from the tool without changes, and
  recommended otherwise. For git, the policy's recommended method is an
  `Assisted-by:` commit message trailer
- Use `Assisted-by:`, NOT `Co-Authored-By:`, even if the agent's default
  attribution says otherwise
- Recommended format, naming the agent and the model:
  ```
  Assisted-by: Claude Code:claude-opus-5-5
  ```
  Name the agent and the exact model actually in use, not the model
  family or a guess. Additional non-obvious tools may follow; everyday
  tooling (git, editors, the build system) does not belong there.
  Fedora's own examples are free-form (`Assisted-by: generic LLM
  chatbot`), so any format that identifies the tool is acceptable
- This is the Linux kernel's original format,
  `Assisted-by: AGENT_NAME:MODEL_VERSION [TOOL1] [TOOL2]` (78d979db6cef,
  2025-12-23, Linux 7.0). The kernel later reduced it to
  `Assisted-by: LLM [TOOL1] [TOOL2]` (816d9992d9ed, 2026-07-01, Linux
  7.3), then removed the tag in favour of describing tool use in the
  cover letter (1e035297ffda, 2026-10-13, Linux 7.4). Fedora still
  recommends the trailer, with the rationale that information about the
  use of AI tools "will help us evaluate their impact". Naming the agent
  and model serves that and a bare `LLM` does not, so the original
  kernel format remains the best fit
- The agent must never add a `Signed-off-by:` of its own: a DCO sign-off
  is a certification only a person can make. If the human directs the
  agent to commit with sign-off (`git commit -s`), the sign-off and the
  certification are the human's, so ask before each commit rather than
  committing unprompted
- With `%autochangelog` (rpmautospec), the commit message feeds the RPM
  changelog; keep the subject line a meaningful changelog entry and put the
  trailer at the end of the message body

### Other contributions
- Where authorship is normally indicated but there is no git history
  (Bugzilla comments, review reports, wiki pages, docs without trailers),
  disclose AI assistance in the text itself, e.g. a short note at the top
  or bottom of the comment
- Routine grammar/spelling/wording help does not need disclosure

### Reviews and evaluation
- AI analysis MAY assist human reviewers
- AI MUST NOT be the sole or final arbiter of a substantive or subjective
  judgment on a contribution. In package reviews, the decision to approve
  (setting `fedora-review+`) and to sponsor a packager stays with the
  human reviewer
- AI MUST NOT be used to evaluate a person's standing in the community
- Objective automated checks (CI, rpmlint, fedora-review tooling, tests)
  are not affected

## Fedora CI on Dist-git Pull Requests

Fedora CI on dist-git PRs runs through Packit: a Koji scratch build,
then Testing Farm plans (installability, rpmlint, rpminspect,
rmdepcheck, license-validate, and the package's own TMT plans as
`custom`). It is retriggered with PR comments
(https://packit.dev/fedora-ci/retriggering):
```
/packit-ci scratch-build          # rerun the scratch build (packagers only)
/packit-ci test                   # rerun all tests (packagers only)
/packit-ci test <id>              # one plan: installability, rpmlint,
                                  # rpminspect, rmdepcheck,
                                  # license-validate, custom
/packit-ci test --target eln      # restrict to one target
/packit-ci help                   # list commands
```
- The prefix is `/packit-ci`; `/packit build` and `/packit test` belong
  to Packit's upstream service and do nothing for Fedora CI on dist-git
- A force-push can clear the CI flags without starting a new run;
  retrigger with `/packit-ci scratch-build` (tests follow a successful
  scratch build automatically)
- Testing Farm plans often fail for infrastructure reasons unrelated to
  the package (e.g. rmdepcheck or license-validate erroring during
  container setup, the rpmlint harness crashing with
  `No module named 'copr'`). Read the plan's log before treating a red
  flag as a package problem, and retry just that plan with
  `/packit-ci test <id>`

## Before Creating a Side Tag Update

While a side tag is open, the target (e.g. rawhide) keeps moving: other
maintainers build the same packages there, and new users of the changed
library appear. Either can silently undo the side tag's work once the
update lands. The longer the tag stays open, the likelier this is, so
run these checks right before creating the Bodhi update, not only when
the tag is first populated.

### Builds Overtaken in the Target

If the target's build of a package sorts above the side tag's, the
target's build wins once the update lands, and the side-tag rebuild is
lost:
```
tag=<sidetag> target=<target, e.g. f46>
koji list-tagged --latest --quiet "$tag" | while read -r nvr _; do
    name=${nvr%-*-*}
    cur=$(koji latest-build --quiet "$target" "$name" | awk '{print $1}')
    [ -n "$cur" ] && rpmdev-vercmp "${nvr#"$name"-}" "${cur#"$name"-}" |
        tail -1 | sed "s/^/$name: /"
done | grep -v ' > '
```
- `list-tagged` without `--inherit` lists only the builds made in the
  side tag. Any output line is a package whose side-tag build is not
  newer than the target's: rebuild it in the side tag from the current
  dist-git branch, so it sorts above the target's build again
- Example: during the libical 4 rebuilds, `asterisk-24.0.0-1.fc46.1`
  was rebuilt in the side tag while its maintainer built
  `asterisk-24.0.0-3.fc46` in plain rawhide, against libical 3. Merging
  would have shipped `-3`, built against the old libical

### New Reverse Dependencies

- Rerun the reverse-dependency query for the changed or removed
  provides against the target, and compare it with the rebuild list,
  e.g. `fedrq whatrequires -b rawhide -F source 'libfoo.so.N()(64bit)'`
  (and `-A src` with the `-devel` provides for the BuildRequires side).
  A new package, or one that started using the library, built in the
  target since the list was drawn up still links the old soname and
  becomes uninstallable once the update lands: rebuild or port it in
  the side tag
- Example: the libical 4 rebuild list was settled on 2026-11-03; the
  new `ical` package was built in plain f46 on 2026-11-05, against
  `libical.so.3`

### Builds Already in Another Update

- Bodhi refuses the side-tag update if any of its builds is already
  part of another update. This usually means a borrowed build: one
  from another pending update (a security fix, a dependency bump)
  tagged into the side tag to build against, which keeps the update
  more self-contained than a buildroot override. Untag it from the
  side tag (`koji untag-build <sidetag> <nvr>`) before creating the
  update. If the update's builds need it at runtime (unlike statically
  linked Rust binaries), don't let the update go stable before the
  borrowed build's update does. Each NVR should give `0 updates found`
  with `bodhi updates query --builds <nvr>`

## Reference Data

### Dist-git Pull Requests
To read a pull request on src.fedoraproject.org without a clone:
```
https://src.fedoraproject.org/api/0/rpms/<pkg>/pull-request/<n>  # metadata and comments (JSON)
https://src.fedoraproject.org/rpms/<pkg>/pull-request/<n>.patch   # its commits as a patch
```
- In November 2026 both returned the real content, but a file's
  `raw/` URL in the contributor's fork returned the Anubis anti-bot
  page (HTML, with HTTP 200) instead of the file. Check that a
  download is the file, not HTML, before using it
- For anything beyond reading the diff (applying a changed patch file
  to the new sources, a local build), work from a clone with the
  contributor's fork as a remote
  (`ssh://pkgs.fedoraproject.org/forks/<user>/rpms/<pkg>.git`)

### Fedora Spec Archive
An archive of all current Fedora spec files is available at:
https://src.fedoraproject.org/lookaside/rpm-specs-latest.tar.xz

When you need to:
- Find real-world examples of a packaging pattern
- Verify how existing Fedora packages handle a specific case
- Check whether a macro or convention is widely used
- Compare a spec file against common Fedora conventions

Download and search this archive. It contains the latest spec files for all
Fedora packages and is the most comprehensive reference for actual packaging
practice in the distribution.

## Current Fedora Macros

### Recently Introduced
- `%bcond` shorthand (replaces `%bcond_with`/`%bcond_without` pair)
- `%conf` section for ./configure-like steps
- `%generate_buildrequires` for dynamic BuildRequires
- `%pyproject_*` family for Python packaging

### Still Available but Discouraged
- `%{?_smp_mflags}` - prefer `%make_build`
- `%setup -q` alone - prefer `%autosetup` when using patches
- `%{__rm}`, `%{__install}` - just use `rm`, `install` directly
