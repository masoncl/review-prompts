# RPM Review Prompts for Claude Code

AI-assisted review prompts for RPM packages, supporting Fedora and
CentOS Stream distributions.

## Installation

Run the top-level setup script from the repository root to install
the skill and slash commands:

    ./setup.sh claude rpm

`./setup.sh -h` lists the other supported agents. For Claude Code this
will install:
- The `rpm` skill to `~/.claude/skills/rpm/SKILL.md`
- Slash commands to `~/.claude/commands/`

## Usage

The RPM skill loads automatically when working with spec files or in
a dist-git repository structure.

### Slash Commands

- `/rpm-review` - Review spec files and packages for policy compliance
- `/rpm-debug`  - Debug build failures and packaging issues
- `/rpm-verify` - Verify findings against false positive patterns

### Distribution Detection

The prompts automatically detect the target distribution from context:
- %{dist} tag values (.fc*, .el*)
- Macro usage (%{?fedora}, %{?rhel})
- Branch naming (f*, rawhide, c*s)
- Default: Fedora (most strict)

## File Structure

| File | Purpose | When Loaded |
|------|---------|-------------|
| **review-core.md** | Main review protocol | Reviews (entry point) |
| **debugging.md** | Build failure debugging protocol | Debugging (entry point) |
| **technical-patterns.md** | Core RPM patterns | Always (loaded first) |
| **false-positive-guide.md** | False positive elimination | During verification |
| **spec-file.md** | Spec file structure | Spec file reviews |
| **macros.md** | RPM macro reference | Complex macro usage |
| **scriptlets.md** | Scriptlet safety | Scriptlet review |
| **dependencies.md** | Dependency management | Dependency issues |
| **licensing.md** | License handling | License review |
| **security.md** | Security advisory triage | CVE bugs, bundled copies |
| **distro/distro.md** | Distribution detection | Always (after context detection) |
| **distro/fedora.md** | Fedora guidelines | Fedora targets |
| **distro/centos-stream.md** | CentOS Stream guidelines | CentOS/RHEL targets |
| **ecosystem/ecosystem.md** | Language ecosystem detection | Always (after context detection) |
| **ecosystem/rust.md** | Rust / cargo-rpm-macros | Rust packages |
| **ecosystem/golang.md** | Go / go-rpm-macros / go-vendor-tools | Go packages |
| **ecosystem/python.md** | Python / pyproject-rpm-macros | Python packages |

Each ecosystem file has review checks, common build failures, and
ecosystem-specific false positives, so it is shared by the review, debug,
and verify workflows.

## Integration

This setup coexists with the other projects' review prompts. Each
installs to a separate skill directory; run `./setup.sh <agent> <project>`
once per project.

## Supported Distributions

- **Fedora** (rawhide and stable releases)
- **CentOS Stream** (9, 10)
- **EPEL** (via CentOS Stream guidelines)
