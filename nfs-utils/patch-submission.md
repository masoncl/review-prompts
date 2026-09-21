# nfs-utils Patch Submission

## Where patches go

- **Mailing list:** `linux-nfs@vger.kernel.org` (plain text, inline patches,
  `git send-email`). This is the same list as the kernel NFS client and server.
- **Upstream tree:** `git://git.linux-nfs.org/projects/steved/nfs-utils.git`
- Patches are reviewed on-list and applied by the maintainer. There is no pull
  request workflow.

Because the list is shared with the kernel side, make it obvious which tree a
patch targets. `[PATCH nfs-utils]` in the subject prefix removes all doubt and
is worth using, especially for a series that pairs with a kernel change.

## Subject line

```
<component>: <brief summary, lower case, no trailing period>
```

Component prefixes actually in use: `nfsdctl:`, `mount:`, `statd:`, `gssd:`,
`rpc.gssd:`, `exportfs:`, `mountd:`, `exportd:`, `nfsd:`, `getport:`,
`rpcctl:`, `nfs.conf:`, `configure:`. Match whatever the file's own history
uses — `git log --oneline <file>` settles it.

`Release: X.Y.Z` is reserved for the maintainer's release commits.

## Commit message

House style is terse. State the problem, then the fix. Prefer short
paragraphs and bullet lists over prose; skip the ASCII diagrams. Keep every
piece of technical substance — the race, the ordering rule, the refcount
argument — and every trailer.

Do explain:
- What was wrong, concretely enough to reproduce.
- Why the fix is correct, especially any ordering or locking reasoning.
- What is deliberately *not* handled, if a case is left open.

## Trailers

`Signed-off-by:` is required on every patch (DCO). Also in use in this tree:

```
Fixes: <12-char sha> ("<subject>")
Reported-by: Name <email>
Reviewed-by: Name <email>
Tested-by: Name <email>
Assisted-by: Claude:<model-id>
```

**`Fixes:`** — add it whenever the patch corrects a specific earlier commit;
it is used regularly here. Standard kernel format:
`git log -1 --format='Fixes: %h ("%s")' <sha>` (with `core.abbrev` at 12).

**`Assisted-by:`** — follows the kernel convention from
`Documentation/process/coding-assistants.rst`:

```
Assisted-by: Claude:<model-id> [optional specialized tools]
```

for example `Assisted-by: Claude:claude-opus-4-6`. The old email form
(`Claude <noreply@anthropic.com>`) is wrong. List specialized analysis tools
(coccinelle, sparse, smatch) if they were used; never list ordinary
development tools.

## Series structure

- One logical change per patch. The tree's own history is a good model: a
  netlink feature lands as "add the helpers", then "use them", then "handle
  the teardown".
- A uapi header sync is its own patch, containing nothing but the
  regeneration — see `subsystem/netlink.md`.
- `configure.ac` changes that a later patch depends on go first, so the tree
  builds at every commit.
- Every commit in the series must build on its own, in the default
  configuration. Bisectability matters here because the feature matrix already
  makes breakage hard to attribute.

## Before sending

- [ ] Builds clean with the default `./configure`. The tree already uses a
      large `-Werror=` set, so "clean" means zero new warnings.
- [ ] Builds with the relevant feature disabled — at minimum
      `--disable-nfsdctl`, and `--disable-gss --disable-nfsv4` if the change
      is anywhere near those. Cross-component link failures are the most
      common review comment.
- [ ] `make check` still passes (or skips cleanly without root).
- [ ] Man pages updated for any new or changed option, config tag, or
      command-line flag.
- [ ] `nfs.conf` options documented in `systemd/nfs.conf.man`.
- [ ] No generated files in the diff: `configure`, `Makefile.in`,
      `aclocal.m4`, `config.h.in`, rpcgen output, YNL headers (unless the
      patch *is* the regeneration).
- [ ] `git format-patch` output checked — no CRLF, no trailing whitespace, no
      base64 attachment.
- [ ] For a change pairing with a kernel patch: say so in the cover letter,
      and state which kernel commit or series it needs.

## Compatibility obligations

Call these out explicitly in the commit message when they apply:

- **Older kernels.** Userspace must keep working against them. New kernel
  features need runtime detection, not a build-time assumption.
- **On-disk formats.** `etab`, `rmtab`, `/var/lib/nfs/sm/*`, the nfsdcld
  sqlite schema. A format change needs an upgrade path from the previous
  release.
- **Upcall wire formats.** `support/include/cld.h`, the gss context blob, the
  qword channel encodings. These are shared with the kernel and are versioned.
- **Command-line and config interfaces.** Options are effectively permanent.
  Deprecate rather than remove, and keep the old spelling working.
