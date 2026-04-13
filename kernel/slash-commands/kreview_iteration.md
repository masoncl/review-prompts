Read the prompt REVIEW_DIR/kreview-iteration/orchestrator.md

The kernel review prompt directory (referred to as `<prompt_dir>` inside the
kreview-iteration prompts) is: REVIEW_DIR

The argument is either:
- a git branch name (review the branch's commits vs its merge-base with master/upstream)
- a git range (e.g. `abc123..def456`) or set of commit SHAs
- one or more patch file paths

Execute the kreview-iteration orchestrator protocol against the provided target. The
orchestrator spawns an agent team (using agent teams, not subagents) where
teammates act as unbiased subsystem maintainers, the patch author, and an
optional tester. A core reviewer is only involved when maintainers disagree,
core/ABI code is touched, or escalation is needed. The review is performed in kernel
mailing list style: maintainers cross-review each other, the author applies
sensible feedback (with user approval), and maintainers re-review the
revised series.

The maintainer and author teammates must have access to the same prompts,
context and tools used by /kreview (review-core.md, the subsystem guides,
technical-patterns.md, callstack.md, inline-template.md, semcode, lore, etc.).

Agent teams require `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. If teams are not
available, fall back to running the orchestrator's phases inline with Task
subagents and say so in the final summary.

The orchestrator is tmux-aware: if it detects `$TMUX`, it reports the tmux
session and lets Claude Code's teammate spawner pick split-pane mode so each
teammate gets its own pane. Outside tmux, teammates run in-process
(Shift+Down to cycle). The orchestrator does not create tmux sessions or
panes itself.

## HARD RULES — read-only mailing list interaction

This command performs a *simulated* mailing list review entirely on the local
machine. It MUST NOT contact any real mailing list, recipient, or SMTP
server. Specifically:

1. **Read-only lore access.** The only permitted way to look at upstream
   mailing list traffic is via lore.kernel.org (HTTP fetches, the semcode
   `lore_search` / `dig` MCP tools, or already-downloaded archives). No
   other mail source is allowed.
2. **No outbound mail.** Do not run `git send-email`, `git imap-send`,
   `sendmail`, `msmtp`, `mutt`, `mailx`, `mail`, `swaks`, `s-nail`, any
   SMTP client, any IMAP/JMAP upload, or any HTTP POST to a mailing list
   web interface or patchwork instance. Do not invoke `b4 send`, `b4
   prep --submit`, or any other tool that publishes patches.
3. **No drafts in user mailboxes.** Do not write to `~/Mail`, `~/.mbox`,
   Maildir directories, or any local mail spool. All teammate "replies"
   live as plain text files under `./kreview-iteration/thread/` only.
4. **No outbound network at all** for the purpose of "sending" the
   review. Network is allowed for *fetching* lore, MAINTAINERS lookups,
   and semcode queries — that's it.
5. **No git push.** The author teammate may commit to a local scratch
   branch and run `git format-patch`, but must never `git push`,
   force-push, or otherwise publish the revised series.

If a teammate (or you) is tempted to "send" a reply, stop. The output is
the files under `./kreview-iteration/thread/` and `./kreview-iteration/summary.md`,
which the user reads themselves. Nothing leaves this machine.
