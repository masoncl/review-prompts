#!/usr/bin/env python3
"""build-guides.py - build subsystem guides by asking the question files.

kernel/subsystem/questions/<guide>.md holds plainly worded questions about one
kernel subsystem, each with a relevance score. This puts
each question to a model that can read and search one kernel tree, and writes
the answers, in order, into that tree's guide:

    ask the readers from memory  ->  answer every group  ->  check every group
        ->  correct the whole guide  ->  write

A guide does not explain the code: it states the difference between what the
models that read it believe and what the tree does. So the build first finds out
what they believe: each model that will read the guide is asked every question
with no sources and no tools. The answerer, which does have the tree, sees what
they said and writes only where they were wrong, out of date, blank or silent
about something the question asks for.

Questions that belong together (one section, or quick checks that share a
group label) are put to the model as one group, so it reads the code once
and the answers fit each other. No number limits an answer. When every group
is answered, a second, independent reader
checks each group against the tree with all the guide's other answers beside
it, so it can also catch answers that contradict or repeat each other, and
hands back corrected answers; what goes in the guide is the corrected text,
and the report lists what was changed. Then one reader goes through the whole
guide for accuracy and a checker verifies its changes. Nothing rewrites the
guide after that: text that has been checked is not touched again. If semcode
is available it is given to both the answerer and the checker. See kernel/docs/subsystem-questions.md.

The model process is isolated. It runs with an empty agent configuration (no
skills, commands, plugins, memory or settings), with file read, search and
glob tools only, in a throwaway snapshot of the tree that has no .git, and
with read access to this repository, the output and your home directory
denied. It must not be able to see an existing subsystem guide, and it cannot
write anywhere: it prints its answer and this script writes the file. The
driver finds your credentials (an API key or cloud variables in the
environment, an apiKeyHelper in your settings, or your stored login) and
hands over those and nothing else.

With --no-sources there is no tree and no tools: the model answers from its
own knowledge of the latest Linux. That is a baseline to compare a real build
against, and its guide says so at the top.

Only the claude CLI is supported so far; the part that knows about it is the
ClaudeCLI class.

Usage:
    build-guides.py --tree <linux> --out <dir> [--guide mm-vma ...]
                    [--min-relevance 2] [--only ID ...] [--jobs 8]
                    [--model MODEL] [--permission-mode MODE]
                    [--rev HEAD | --snapshot DIR] [--dry-run]
    build-guides.py --no-sources [--tree <linux>] --out <dir> [--guide ...]
"""

import argparse
import concurrent.futures as cf
import difflib
import glob
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import threading
import time
import uuid

import math

from question_file import HISTORY_RE, OLD_FORMAT_RE, SHA_RE, parse, read_verbatim, safe_id

HERE = os.path.dirname(os.path.abspath(__file__))
KERNEL_DIR = os.path.dirname(HERE)
REPO_ROOT = os.path.dirname(KERNEL_DIR)

# Environment handed to the model process. Everything else is dropped, so a
# run started from inside another agent session inherits nothing from it.
PASS_ENV = ("PATH", "LANG", "LC_ALL", "LC_CTYPE", "TERM", "TMPDIR", "TZ",
            "HTTP_PROXY", "HTTPS_PROXY", "NO_PROXY", "http_proxy",
            "https_proxy", "no_proxy", "SSL_CERT_FILE", "SSL_CERT_DIR",
            "NODE_EXTRA_CA_CERTS", "CLOUD_ML_REGION")


PASS_ENV_PREFIXES = ("ANTHROPIC_", "AWS_", "GOOGLE_", "VERTEX_",
                     "CLAUDE_CODE_USE_", "CLAUDE_CODE_SKIP_")


log_lock = threading.Lock()


def log(msg):
    with log_lock:
        print(msg, file=sys.stderr, flush=True)


AGENT_CONFIG = {".claude", ".mcp.json", ".claude.json", "CLAUDE.md", "CLAUDE.local.md",
                "AGENTS.md"}


def agent_config_in(root):
    """Agent configuration or instruction files anywhere under root."""
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        for name in list(dirnames) + filenames:
            if name in AGENT_CONFIG:
                out.append(os.path.relpath(os.path.join(dirpath, name), root))
        dirnames[:] = [d for d in dirnames if d not in AGENT_CONFIG]
    return out


def escaping_symlinks(root):
    """Symlinks under root that lead outside it, as paths relative to root.

    A tree is untrusted, and a link such as notes -> ~/.ssh/id_rsa would put a
    file from outside the snapshot inside the one directory the model may
    read. Links that stay inside the tree, which the kernel has a few of, are
    harmless and are left alone.
    """
    root = os.path.realpath(root)
    out = []
    for dirpath, dirnames, filenames in os.walk(root):
        for name in dirnames + filenames:
            p = os.path.join(dirpath, name)
            if os.path.islink(p):
                target = os.path.realpath(p)
                if target != root and not target.startswith(root + os.sep):
                    out.append(os.path.relpath(p, root))
        # os.walk does not follow links to directories, so nothing more to do.
    return out


def make_snapshot(tree, rev, dest):
    """Unpack <rev> of <tree> into dest as plain files with no .git."""
    os.makedirs(dest, exist_ok=True)
    t0 = time.time()
    archive = subprocess.Popen(["git", "-C", tree, "archive", "--format=tar", rev],
                               stdout=subprocess.PIPE)
    untar = subprocess.run(["tar", "-x", "-C", dest], stdin=archive.stdout)
    archive.stdout.close()
    if archive.wait() != 0 or untar.returncode != 0:
        raise SystemExit(f"could not unpack {rev} of {tree}")
    # The tree is untrusted: do not let it bring agent configuration with it.
    for p in agent_config_in(dest):
        full = os.path.join(dest, p)
        shutil.rmtree(full) if os.path.isdir(full) else os.remove(full)
    bad = escaping_symlinks(dest)
    for rel in bad:
        os.remove(os.path.join(dest, rel))
    if bad:
        log(f"removed {len(bad)} symlinks that led outside the snapshot: "
            + ", ".join(bad[:5]) + (" ..." if len(bad) > 5 else ""))
    log(f"snapshot of {rev} unpacked in {time.time() - t0:.0f}s")


def kernel_version(root):
    """VERSION.PATCHLEVEL.SUBLEVEL-EXTRAVERSION from the top Makefile."""
    try:
        with open(os.path.join(root, "Makefile"), encoding="utf-8",
                  errors="replace") as f:
            head = f.read(2000)
    except OSError:
        return "unknown"
    v = {k: (re.search(rf"^{k}\s*=\s*(.*)$", head, re.M) or [None, ""])[1].strip()
         for k in ("VERSION", "PATCHLEVEL", "SUBLEVEL", "EXTRAVERSION")}
    return f"{v['VERSION']}.{v['PATCHLEVEL']}.{v['SUBLEVEL']}{v['EXTRAVERSION']}"


def kernel_base(root):
    """The release the tree is based on, as a tag would spell it: v7.3-rc4, v6.12.5."""
    v = kernel_version(root)
    m = re.match(r"(\d+)\.(\d+)\.(\d+)(.*)$", v)
    if not m:
        return "unknown"
    major, minor, sub, extra = m.groups()
    return f"v{major}.{minor}" + (f".{sub}" if sub != "0" else "") + extra


def tree_sha(tree, rev):
    """The commit the answers were read from and checked against."""
    try:
        out = subprocess.run(["git", "-C", tree, "rev-parse", "--verify", f"{rev}^{{commit}}"],
                             capture_output=True, text=True, timeout=30)
        return out.stdout.strip() if out.returncode == 0 else "unknown"
    except (OSError, subprocess.SubprocessError):
        return "unknown"


RECORD_HEAD = ("# The kernel tree every guide in this directory was built from and checked\n"
               "# against: the release it is based on and the commit. Written by\n"
               "# kernel/scripts/build-guides.py --record; do not edit by hand.\n")


def record_build(path, base, sha):
    """Note in a YAML file which kernel a build was made from.

    A build directory holds the guides of one kernel, so the file has one
    release and one commit. This script both writes and reads it, so it is
    kept to a shape that needs no YAML library.
    """
    with open(path, "w", encoding="utf-8") as f:
        f.write(RECORD_HEAD + f"kernel: {base}\nsha: {sha}\n")


def read_record(path):
    """{"kernel": ..., "sha": ...} from a file record_build() wrote; {} if there is none."""
    out = {}
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                m = re.match(r"^(kernel|sha):\s*(\S+)\s*$", line)
                if m:
                    out[m.group(1)] = m.group(2)
    except OSError:
        pass
    return out if len(out) == 2 else {}


class HarnessError(Exception):
    pass


_private = {}


def private_dir(work):
    """Where this run keeps what the model process needs but must not read.

    Under the user's home directory, because the whole of that is on the read
    deny list of every run. If it sat in the scratch directory under /tmp, the
    login link of one run would be readable by another run going on at the
    same time, whose deny list does not name it. Falls back to the scratch
    directory, which is denied by name, when home is not writable.
    """
    if work not in _private:
        base = os.path.join(os.environ.get("XDG_CACHE_HOME")
                            or os.path.expanduser("~/.cache"), "build-guides")
        try:
            os.makedirs(base, mode=0o700, exist_ok=True)
            _private[work] = tempfile.mkdtemp(prefix="run-", dir=base)
        except OSError:
            _private[work] = os.path.join(work, "private")
    return _private[work]


def secret_strings(path):
    """Every longish string value in a JSON credentials file."""
    out = set()

    def walk(v):
        if isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
        elif isinstance(v, str) and len(v) >= 20:
            out.add(v)
    try:
        with open(path, encoding="utf-8") as f:
            walk(json.load(f))
    except (OSError, ValueError):
        pass
    return out


TOKEN_RE = re.compile(
    r"sk-ant-[A-Za-z0-9_\-]{8,}"                               # Anthropic keys
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?(?:-----END [A-Z ]*PRIVATE KEY-----|\Z)"
    r"|\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"                          # AWS key ids
    r"|\bgh[pousr]_[A-Za-z0-9]{30,}\b"                         # GitHub tokens
    r"|\beyJ[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{20,}\.[A-Za-z0-9_\-]{10,}\b")  # JWTs


def scrub(text, secrets):
    """Remove credentials from model output. Returns (text, how many)."""
    n = 0
    for s in secrets:
        if s in text:
            n += text.count(s)
            text = text.replace(s, "[redacted credential]")
    text, k = TOKEN_RE.subn("[redacted credential]", text)
    return text, n + k


def read_denials(cwd, repo, out, private):
    """Places the model's read tool must not reach.

    Deny rules win over allow rules, so this cannot be written as "only the
    snapshot". It lists this repository, the output, the private part of the
    scratch directory, the user's home, and the system directories that hold
    credentials or process state, leaving out any that contain the snapshot.
    A container that mounts nothing but the snapshot is stronger.
    """
    cwd = os.path.realpath(cwd)

    def contains_cwd(d):
        d = os.path.realpath(d)
        return os.path.commonpath([cwd, d]) == d

    home = os.path.expanduser("~")
    deny = [repo, out, private, os.path.dirname(private)]
    deny += glob.glob(os.path.join(tempfile.gettempdir(), "build-guides-*", "private"))
    if contains_cwd(home):
        log("warning: the snapshot is inside your home directory, so home cannot be "
            "denied as a whole; only the usual secret locations in it are. Put "
            "--work and --snapshot outside it.")
    if not contains_cwd(home):
        deny.append(home)
    else:
        deny += [os.path.join(home, d) for d in
                 (".claude", ".claude.json", ".config", ".ssh", ".aws", ".gnupg",
                  ".netrc", ".docker", ".kube", ".npmrc", ".pypirc", ".git-credentials",
                  ".bash_history", ".zsh_history")]
    for d in ("/proc", "/etc", "/var", "/run", "/sys", "/root", "/home", "/mnt",
              "/media", "/srv", "/boot"):
        if os.path.exists(d) and not contains_cwd(d):
            deny.append(d)
    seen, out_list = set(), []
    for d in deny:
        d = os.path.abspath(d)
        if d not in seen and os.path.exists(d):
            seen.add(d)
            out_list.append(d)
    return out_list


SEMCODE_TOOLS = ["file_survey", "find_function", "find_type", "find_callers",
                 "find_calls", "find_callchain", "find_implementors",
                 "find_registrations", "grep_functions", "vgrep_functions"]


# semcode's other tools reach into commit history and the mailing lists, which
# is exactly what a built guide must not contain. Denied by name, so they are
# refused even in a permission mode that would otherwise approve them.
SEMCODE_DENIED = ["find_commit", "vcommit_similar_commits", "lore_search", "dig",
                  "vlore_similar_emails", "diff_functions", "indexing_status",
                  "list_branches", "compare_branches"]
# Tools a machine-level plugin may add that no empty configuration can remove.
STRAY_TOOLS = ["mcp__easel"]


def find_semcode(opts, tree, private):
    """Write an MCP config that starts semcode on this tree; (path, how) or (None, why).

    semcode is used if the user has an MCP server of that name in their own
    agent configuration, or failing that if semcode-mcp is on PATH and the tree
    has a .semcode.db. The tree's own .mcp.json is never consulted: the tree is
    untrusted, and an MCP entry is a command to run. The model works in a
    snapshot with no .git and no database, so the server is pointed at the
    real tree. Only its code-query tools are allowed: the
    commit-history and mailing-list tools would bring in exactly the history a
    built guide must not have.
    """
    if opts.no_semcode:
        return None, "off (--no-semcode)"
    tree = os.path.abspath(tree)
    entry, how = None, ""
    home = os.path.expanduser("~")
    places = [(os.path.join(os.environ.get("CLAUDE_CONFIG_DIR", home), ".claude.json"), tree),
              (os.path.join(home, ".claude.json"), tree)]
    for path, project in places:
        try:
            with open(path, encoding="utf-8") as f:
                cfg = json.load(f)
        except (OSError, ValueError):
            continue
        pools = [cfg.get("mcpServers")]
        if project:
            pools += [(cfg.get("projects") or {}).get(d, {}).get("mcpServers")
                      for d in (project, os.getcwd())]
        for pool in pools:
            for name, e in (pool or {}).items():
                if name.lower() == "semcode" and isinstance(e, dict) and entry is None:
                    entry, how = dict(e), f"the '{name}' server configured in {path}"
    if entry is None:
        exe = shutil.which("semcode-mcp")
        if exe and os.path.isdir(os.path.join(tree, ".semcode.db")):
            entry, how = {"command": exe, "args": []}, f"{exe} and the tree's .semcode.db"
    if entry is None:
        return None, "not found (no MCP server named semcode, or no semcode-mcp and .semcode.db)"
    if "command" in entry:
        args = [str(a) for a in entry.get("args") or []]

        def has(*names):
            return any(a in names or a.startswith(tuple(n + "=" for n in names)) for a in args)
        if not has("-d", "--database"):
            args += ["-d", tree]
        if not has("--git-repo") and "SEMCODE_GIT_REPO" not in (entry.get("env") or {}):
            args += ["--git-repo", tree]
        models = os.path.join(home, ".cache", "semcode", "models")
        if not has("--model-path") and os.path.isdir(models):
            args += ["--model-path", models]      # HOME is replaced for the model process
        entry["args"] = args
    path = os.path.join(private, "mcp.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"mcpServers": {"semcode": entry}}, f, indent=1)
    started = (" ".join([entry["command"], *entry.get("args", [])]) if "command" in entry
               else entry.get("url", "?"))
    return path, f"{how}; it is started as: {started}"


SLOW_CALL = 600         # seconds; a call that takes longer leaves a record too
WATCH_EVERY = 10        # seconds between looks at a running call


def transcript_of(config_dir, session):
    """Where the CLI keeps the transcript of this session, or None if it has none yet."""
    found = glob.glob(os.path.join(config_dir, "projects", "*", session + ".jsonl"))
    return found[0] if found else None


class Steps:
    """Counts the steps a running call takes, from the transcript the CLI keeps of it.

    A step is the model saying something or asking for a tool, or a tool
    answering. A request the CLI sends, or sends again, is not one: a call that
    is stalled goes on sending them.
    """

    def __init__(self, config_dir, session):
        self.config_dir, self.session = config_dir, session
        self.path, self.offset, self.part = None, 0, b""
        self.count, self.last = 0, time.time()

    def look(self):
        """Read what has been added since the last look; returns the time of the last step."""
        self.path = self.path or transcript_of(self.config_dir, self.session)
        if not self.path:
            return self.last
        try:
            with open(self.path, "rb") as f:
                f.seek(self.offset)
                new = f.read()
        except OSError:
            return self.last
        self.offset += len(new)
        lines = (self.part + new).split(b"\n")
        self.part = lines.pop()             # a line still being written
        for line in lines:
            try:
                e = json.loads(line)
            except ValueError:
                continue
            msg = e.get("message") if isinstance(e.get("message"), dict) else {}
            content = msg.get("content")
            answered = any(isinstance(c, dict) and c.get("type") == "tool_result"
                           for c in (content if isinstance(content, list) else []))
            if e.get("type") == "assistant" or (e.get("type") == "user" and answered):
                self.count += 1
                self.last = time.time()
        return self.last


def session_record(config_dir, prompt, since, session=None):
    """What the session that was given this prompt did, and when, as lines of text.

    The CLI keeps a transcript of each session under its configuration
    directory, every event with its time. A call that stalls shows there as a
    long gap, and what came just before the gap says what it was waiting for:
    the model, or a tool. Nothing of what was said is copied, only the kinds
    of event and their times.
    """
    # The whole prompt, not its end: the checks of one guide are all given the rest of
    # the guide last, so their prompts end alike and only differ further up.
    want = " ".join(prompt.split())
    known = transcript_of(config_dir, session) if session else None
    for path in [known] if known else sorted(
            glob.glob(os.path.join(config_dir, "projects", "*", "*.jsonl")),
            key=os.path.getmtime, reverse=True):
        try:
            if not known and os.path.getmtime(path) < since - 5:
                continue
            events, mine = [], bool(known)
            with open(path, encoding="utf-8", errors="replace") as f:
                for line in f:
                    try:
                        e = json.loads(line)
                    except ValueError:
                        continue
                    msg = e.get("message") if isinstance(e.get("message"), dict) else {}
                    content = msg.get("content")
                    kinds = []
                    for c in content if isinstance(content, list) else []:
                        if not isinstance(c, dict):
                            continue
                        kinds.append(c.get("type", "?") + (":" + str(c.get("name"))
                                                           if c.get("type") == "tool_use" else ""))
                        if e.get("type") == "user" and not mine \
                                and want in " ".join(str(c.get("text", "")).split()):
                            mine = True
                    if e.get("type") == "user" and not mine and isinstance(content, str) \
                            and want in " ".join(content.split()):
                        mine = True
                    if e.get("timestamp"):
                        events.append((str(e["timestamp"]), str(e.get("type")), ",".join(kinds)))
        except OSError:
            continue
        if not mine or not events:
            continue

        def at(stamp):
            try:
                return time.mktime(time.strptime(stamp[:19], "%Y-%m-%dT%H:%M:%S"))
            except ValueError:
                return 0.0
        gaps = sorted(((at(b[0]) - at(a[0]), a, b) for a, b in zip(events, events[1:], strict=False)),
                      key=lambda g: -g[0])[:3]
        out = [f"## the session: {len(events)} events, {events[0][0][11:19]} to {events[-1][0][11:19]} UTC",
               "", "longest waits, and what came before and after each:"]
        out += [f"- {g:.0f}s after {a[0][11:19]} {a[1]} {a[2]}, before {b[1]} {b[2]}"
                for g, a, b in gaps]
        out += ["", "the last events:"] + [f"- {s[11:19]} {k} {what}" for s, k, what in events[-12:]]
        debug = os.path.join(config_dir, "debug",
                             os.path.splitext(os.path.basename(path))[0] + ".txt")
        try:
            with open(debug, encoding="utf-8", errors="replace") as f:
                out += ["", "## the end of the session's debug log", ""] + \
                       [ln.rstrip()[:300] for ln in f.readlines()[-40:]]
        except OSError:
            pass
        return out
    return ["## the session: no transcript of it was found"]


class ClaudeCLI:
    """Runs one isolated, read-only model turn with the claude CLI."""

    TOOLS = ["Read", "Grep", "Glob"]
    NEVER = ["Bash", "Write", "Edit", "MultiEdit", "NotebookEdit", "WebFetch",
             "WebSearch", "Task", "Agent", "Skill"]

    def __init__(self, opts, work, deny_dirs):
        self.exe = opts.claude
        self.model = opts.model
        self.timeout = opts.timeout
        self.quiet = opts.quiet
        self.watch = False              # set by preflight, if a call can be watched
        self.failed_dir = getattr(opts, "failed_dir", None)
        self.failed_lock, self.failed = threading.Lock(), 0
        self.max_turns = opts.max_turns
        self.permission_mode = opts.permission_mode
        self.mcp_config = os.path.abspath(opts.mcp_config) if opts.mcp_config else None
        self.mcp_allow = [opts.mcp_allow]
        self.has_tree = not opts.no_sources or getattr(opts, "check_memory", False)
        self.tools = self.TOOLS if self.has_tree else []
        if not self.has_tree:
            self.mcp_config = None      # no sources means no code search either
        # Everything the model process needs but must not read goes under
        # one directory that is on the deny list: its configuration (which may
        # hold a link to the user's login), its HOME and its settings.
        self.private = private_dir(work)
        self.config_dir = os.path.join(self.private, "agent-config")
        self.home = os.path.join(self.private, "home") if not opts.keep_home else None
        os.makedirs(self.config_dir, exist_ok=True)
        os.chmod(self.private, 0o700)
        if self.home:
            os.makedirs(self.home, exist_ok=True)
        # Absolute paths in a permission rule are written with two slashes.
        deny = []
        for d in deny_dirs:
            for spelt in dict.fromkeys((os.path.abspath(d), os.path.realpath(d))):
                deny.append(f"Read(/{spelt}" + ("/**)" if os.path.isdir(d) else ")"))
        self.settings = os.path.join(self.private, "settings.json")
        self.secrets = set()
        settings = {"permissions": {"deny": deny}}
        how, what = self.find_auth(opts)
        self.auth = how
        self.login_src = self.login_dst = None
        # --bare never reads a stored login, so that route runs without it.
        # The configuration directory still holds nothing but the login.
        self.bare = how != "login"
        if how == "helper":
            settings["apiKeyHelper"] = what
        elif how == "login":
            # A link, not a copy: when the CLI refreshes the token the new one
            # must reach the real file, or the user's own sessions are logged
            # out. finish() copes with a CLI that replaces the link.
            self.login_src = os.path.realpath(what)
            self.login_dst = os.path.join(self.config_dir, ".credentials.json")
            os.symlink(self.login_src, self.login_dst)
            self.secrets |= secret_strings(self.login_src)
        for k in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
            if len(os.environ.get(k, "")) >= 12:
                self.secrets.add(os.environ[k])
        with open(self.settings, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=1)
        log(f"credentials: {self.AUTH_WORDS[how]}")
        self.env = {k: v for k, v in os.environ.items()
                    if k in PASS_ENV or k.startswith(PASS_ENV_PREFIXES)
                    or k in opts.pass_env}
        # A call is watched through the transcript the CLI keeps of it. A parent
        # that turns transcripts off for its own children, as a terminal
        # multiplexer started by an agent does, must not turn them off here: a
        # stalled call would then be stopped only by the time limit.
        self.env.pop("CLAUDE_CODE_SKIP_PROMPT_HISTORY", None)
        self.env["CLAUDE_CONFIG_DIR"] = self.config_dir
        self.env["HOME"] = self.home or os.environ.get("HOME", "/")
        self.env["GIT_PAGER"] = "cat"

    AUTH_WORDS = {
        "env": "API key or cloud provider variables from the environment",
        "helper": "an apiKeyHelper command",
        "login": "your stored login, linked alone into an empty configuration",
    }
    ENV_AUTH = ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN",
                "CLAUDE_CODE_USE_BEDROCK", "CLAUDE_CODE_USE_VERTEX")

    @classmethod
    def find_auth(cls, opts):
        """How the isolated process will authenticate: (route, detail).

        The process cannot see the user's agent configuration, so whatever it
        needs is found here and handed over explicitly, and nothing else is.
        """
        if opts.credentials:
            return "login", opts.credentials
        if opts.api_key_helper:
            return "helper", opts.api_key_helper
        if any(os.environ.get(k) for k in cls.ENV_AUTH):
            return "env", None
        user = os.environ.get("CLAUDE_CONFIG_DIR") or os.path.expanduser("~/.claude")
        try:
            with open(os.path.join(user, "settings.json"), encoding="utf-8") as f:
                helper = json.load(f).get("apiKeyHelper")
        except (OSError, ValueError):
            helper = None
        if helper:
            return "helper", helper
        login = os.path.join(user, ".credentials.json")
        if os.path.exists(login):
            return "login", login
        raise SystemExit(
            "no credentials for the model process. It runs isolated from your agent\n"
            "configuration, so it needs one of: ANTHROPIC_API_KEY (or the Bedrock or\n"
            f"Vertex variables) in the environment; a stored login at {login}\n"
            "(log in with the claude CLI once); --api-key-helper; or --credentials.\n"
            "A login kept in the macOS keychain cannot be handed over; use a key.")

    def finish(self):
        """Put a refreshed login back if the CLI replaced our link with a file."""
        dst, src = self.login_dst, self.login_src
        if not dst or not os.path.lexists(dst):
            return
        if not os.path.islink(dst):
            tmp = src + ".build-guides"
            shutil.copyfile(dst, tmp)
            os.chmod(tmp, 0o600)
            os.replace(tmp, src)
        os.remove(dst)

    def preflight(self, cwd):
        """One tiny turn, so a credentials problem stops the run at once."""
        try:
            _, usage = self.run("Reply with the single word: ok", cwd)
            log("model: " + (", ".join(usage.get("models") or []) or "not reported")
                + ("" if self.model else " (the harness default; use --model to choose)"))
            # A call can be watched if the CLI kept a transcript of this one where it
            # is looked for. If not, only the time limit stops a call.
            self.watch = bool(self.quiet and usage.get("steps"))
            log(f"a call is stopped after {self.quiet}s without a step, or {self.timeout}s in all"
                if self.watch else
                f"a call is stopped after {self.timeout}s; its steps cannot be watched")
        except HarnessError as e:
            raise SystemExit(f"the model process could not run ({self.AUTH_WORDS[self.auth]}):\n  {e}")

    def command(self, memory=False, model=None, session=None):
        """The command line; with memory, the model gets no tools of any kind."""
        cmd = [self.exe, "-p", "--output-format", "json",
               "--setting-sources", "", "--settings", self.settings,
               "--strict-mcp-config"]
        if session:
            cmd += ["--session-id", session]    # so that its transcript can be found
        if self.bare:
            cmd.insert(2, "--bare")
        if self.mcp_config and not memory:
            cmd += ["--mcp-config", self.mcp_config,
                    "--allowedTools", *self.mcp_allow]
        cmd += ["--disallowedTools", *self.NEVER, *STRAY_TOOLS,
                *(f"mcp__semcode__{t}" for t in SEMCODE_DENIED)]
        if model or self.model:
            cmd += ["--model", model or self.model]
        if self.max_turns:
            cmd += ["--max-turns", str(self.max_turns)]
        if self.permission_mode:
            # Whatever the mode, the tool list above and the deny rules in the
            # settings file still apply; deny rules win over any approval.
            cmd += ["--permission-mode", self.permission_mode]
        # --tools takes a list, so it goes last; the prompt arrives on stdin.
        cmd += ["--tools", *(([] if memory else self.tools) or [""])]
        return cmd

    def keep_failed(self, what, prompt, began, out, err, model, session=None):
        """Keep what is known of a call that failed or stalled; returns where, for the log."""
        if not self.failed_dir:
            return ""
        with self.failed_lock:
            self.failed += 1
            n = self.failed
        lines = [what, "",
                 f"started {time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(began))} UTC, "
                 f"ended after {time.time() - began:.0f}s",
                 f"model asked for: {model or self.model or 'the default'}",
                 "the prompt ends: ..." + " ".join(prompt.split())[-300:], ""]
        lines += session_record(self.config_dir, prompt, began, session)
        lines += ["", "## what it wrote to stderr, the end of it", "", (err or "").strip()[-4000:],
                  "", "## what it wrote to stdout, the end of it", "", (out or "").strip()[-2000:]]
        try:
            os.makedirs(self.failed_dir, exist_ok=True)
            path = os.path.join(self.failed_dir, f"{n:03d}.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(scrub("\n".join(lines), self.secrets)[0] + "\n")
        except OSError:
            return ""
        return f"; what it left is in {path}"

    def run(self, prompt, cwd, memory=False, model=None, timeout=None):
        """Return (text the model printed, usage dict)."""
        limit, began = timeout or self.timeout, time.time()
        session = str(uuid.uuid4())
        steps = Steps(self.config_dir, session)

        def fail(what, out="", err=""):
            return HarnessError(what + self.keep_failed(what, prompt, began, out, err, model,
                                                        session))
        try:
            # its own process group: the CLI starts a code search server, and killing
            # the CLI alone would leave that running
            p = subprocess.Popen(self.command(memory, model, session), stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                 cwd=cwd, env=self.env, start_new_session=True)
        except OSError as e:
            raise HarnessError(f"cannot run {self.exe}: {e}")
        # A call that is working is left to work, up to the limit. One that has taken
        # no step for a while is waiting for something that is not coming: the CLI
        # goes on trying for most of an hour, and a fresh call answers in minutes.
        sent, why = False, ""
        while True:
            try:
                out, err = p.communicate(None if sent else prompt,
                                         timeout=min(WATCH_EVERY, limit))
                break
            except subprocess.TimeoutExpired:
                sent = True
                ran, still = time.time() - began, time.time() - steps.look()
                if ran >= limit:
                    why = f"timed out after {limit}s"
                elif self.watch and still >= self.quiet:
                    why = (f"stopped after {ran:.0f}s: no step for {still:.0f}s, "
                           f"after {steps.count} steps")
                if not why:
                    continue
                try:
                    os.killpg(p.pid, signal.SIGKILL)
                except OSError:
                    p.kill()
                out, err = p.communicate()
                raise fail(why, out, err)
        steps.look()
        out = out.strip()
        if p.returncode != 0 and not out:
            raise fail(f"exit {p.returncode}: {err.strip()[-400:]}", out, err)
        try:
            env = json.loads(out)
        except ValueError:
            raise fail(f"output is not the JSON envelope: {out[:200]!r}", out, err)
        if isinstance(env, list):       # stream of events; the last is the result
            env = next((e for e in reversed(env) if e.get("type") == "result"), {})
        if env.get("is_error") or "result" not in env:
            raise fail(f"agent error: {str(env.get('result', env))[:300]}", out, err)
        if time.time() - began > SLOW_CALL:     # it answered, but something held it up
            self.keep_failed(f"answered, after {time.time() - began:.0f}s", prompt, began,
                             "", err, model, session)
        usage = {"cost_usd": env.get("total_cost_usd") or 0.0,
                 "steps": steps.count,
                 "turns": env.get("num_turns") or 0,
                 "seconds": (env.get("duration_ms") or 0) / 1000.0}
        for k, v in (env.get("usage") or {}).items():
            if isinstance(v, (int, float)):
                usage[k] = v
        # The envelope says which model or models actually served the turn.
        usage["models"] = sorted(env.get("modelUsage") or {})
        return env["result"], usage


# ---------------------------------------------------------------- questions

def load(qdir, guides):
    """The question files to build, as {stem: (header, [Question])}."""
    files = {}
    for path in sorted(glob.glob(os.path.join(qdir, "*.md"))):
        stem = os.path.splitext(os.path.basename(path))[0]
        if guides and stem not in guides:
            continue
        with open(path, encoding="utf-8") as f:
            if OLD_FORMAT_RE.search(f.read()):
                if guides:
                    raise SystemExit(f"{path} is still in the old format; convert it first")
                log(f"skipping {stem}: still in the old question format")
                continue
        header, questions, problems = parse(path)
        if problems:
            raise SystemExit(f"{path} does not parse; run lint-questions.py")
        for q in questions:
            if q.verbatim_problem:
                raise SystemExit(f"{path}: {q.id}: {q.verbatim_problem}")
        files[stem] = (header, questions)
    missing = set(guides) - set(files)
    if missing:
        raise SystemExit(f"no question file for: {', '.join(sorted(missing))}")
    return files


DEFAULT_MIN_RELEVANCE = 2


def select(files, min_rel, only):
    """The questions to ask, per guide, in file order.

    min_rel of None means each guide's own "- min-relevance:" header, or 2.
    """
    out = {}
    for stem, (header, questions) in files.items():
        if only:
            out[stem] = [q for q in questions if q.id in only]
            continue
        own = header.get("min-relevance", "")
        floor = min_rel if min_rel is not None else \
            int(own) if own.isdigit() else DEFAULT_MIN_RELEVANCE
        out[stem] = [q for q in questions
                     if q.is_verbatim or (q.relevance is not None and q.relevance >= floor)]
    return out


# ------------------------------------------------------------------ asking

def read_prompt(name):
    with open(os.path.join(KERNEL_DIR, "agent", name), encoding="utf-8") as f:
        return f.read()


def form_of(q):
    if q.quick:
        return "a quick check: one bullet in a list, written as a single paragraph"
    if q.fields.get("drafts") == "all":
        return ("a bulleted list of mistakes, one to a bullet: first what a model believes, "
                "which is a statement about the readers and not about the tree, then what is "
                "true in this tree and where to see it, which is what has to be checked")
    if q.section:
        return (f"one item in the section \"{q.section}\": a short bulleted list, one "
                "fact per bullet (or a small table if the question asks for one), shown "
                "under its title in bold")
    return "a section of the guide"


ANSWER_MARK = "=== answer ==="
CHANGES_MARK = "=== changes ==="
# "=== answer: <id> ===", tolerating decoration and a title copied in after the id
BLOCK_RE = re.compile(r"^[*`\s]*=== answer: *`?([A-Za-z0-9_.\-]+)`?:?[^=\n]*===[*`\s]*$", re.M)
DIFF_RE = re.compile(r"^[*`\s]*=== differences: *`?([A-Za-z0-9_.\-]+)`?:?[^=\n]*===[*`\s]*$", re.M)
KEEP_LABEL_RE = re.compile(r"unsafe|incorrect|correct|usage|do not|don't|not\b|fine\b|safe\b",
                           re.I)


def make_groups(questions, max_q):
    """Questions that are answered together, in file order.

    A group is the questions of one section, which is everything the guide
    says about one subject, or the quick checks that share a group label;
    anything else is on its own. One builder sees the whole of it, so that it
    says each thing once. Only a group with a great many questions is split,
    into even parts.
    """
    by = {}
    for q in questions:
        if not q.is_verbatim:           # text to insert, not a question to answer
            by.setdefault(q.group or q.id, []).append(q)
    groups = []
    for label, qs in by.items():
        parts = max(math.ceil(len(qs) / max_q), 1)
        size = math.ceil(len(qs) / parts)
        for i in range(0, len(qs), size):
            rest = [o.title for o in qs if o not in qs[i:i + size]]
            groups.append({"label": label, "questions": qs[i:i + size], "rest": rest,
                           "guide": [o for o in questions if not o.is_verbatim]})
    return groups


def question_block(q, answer=None):
    out = [f"## {q.id}: {q.title}", f"Form: {form_of(q)}", "",
           q.text, ""]
    if answer is not None:
        out += ["Answer to check:", "", answer.strip() or "(no answer was given)", ""]
    return out


def ask_prompt(group, guide_title, no_sources, only=None, drafts=None):
    """The prompt for one group, or for the questions in it named by only.

    drafts is {question id: [(reader model, what it answered from memory)]}.
    """
    name = "answer-from-memory.md" if no_sources else "answer-question.md"
    qs = [q for q in group["questions"] if only is None or q.id in only]
    parts = [read_prompt(name), "", "---", "", f"Guide: {guide_title}", "",
             f"# The question{'s' if len(qs) > 1 else ''}", ""]
    for q in qs:
        parts += question_block(q)
    others = group["rest"] + [q.title for q in group["questions"] if q not in qs]
    if others:
        parts += ["# Also in this part of the guide, answered separately", "",
                  "Do not repeat what they cover:", ""] + [f"- {t}" for t in others] + [""]
    believed = [(q, drafts[q.id]) for q in qs if drafts and drafts.get(q.id)
                and q.fields.get("drafts") != "all"]
    everything = [(o, drafts[o.id]) for o in group.get("guide", [])
                  if drafts and drafts.get(o.id) and o.fields.get("drafts") != "all"] \
        if any(q.fields.get("drafts") == "all" for q in qs) and not no_sources else []
    if everything:
        parts += ["# What each reader said from memory, for every question in this guide", "",
                  "Each reader was asked every question in this guide from memory, with no tree "
                  "and no tools. Its drafts are below, unchecked, each under the question it "
                  "answers.", ""]
        for o, said in everything:
            parts += [f"## {o.id}: {o.title}", "", " ".join(o.text.split()), ""]
            for who, text in said:
                parts += [f"Reader `{who}`:", "", text.strip(), ""]
    if believed and not no_sources:
        parts += ["# What a reader already believes", "",
                  "Each reader was asked these questions from memory, with no tree and no "
                  "tools. Its drafts are below, unchecked.", ""]
        for q, said in believed:
            parts += [f"## {q.id}", ""]
            for who, text in said:
                parts += [f"Reader `{who}`:", "", text.strip(), ""]
    return "\n".join(parts)


def notes_about(group, others):
    """What the checks of other groups changed that names an answer of this one.

    others is [(group, its list of changes)]. A check that cuts something from
    its own answer because another has it says which; this is how the check of
    that other answer gets to hear, and to confirm the fact is still there.
    """
    mine = {q.id for q in group["questions"]}
    out = []
    for other, changes in others:
        if other is group:
            continue
        for c in changes:
            lead = re.match(r"`?([\w.\-]+)`?\s*:", c)
            if lead and lead.group(1) in mine:
                continue
            if any(f"`{i}`" in c for i in mine) and c not in out:
                out.append(c)
    return out


def check_prompt(group, guide_title, answers, by_id, prior=None, about=None, last=False):
    """One group's answers to check, with the rest of the guide beside them."""
    mine = {q.id for q in group["questions"]}
    parts = [read_prompt("check-answer.md"), "", "---", "", f"Guide: {guide_title}", "",
             "# The questions and answers to check", ""]
    for q in group["questions"]:
        parts += question_block(q, answers.get(q.id, ""))
    if prior:
        parts += ["# What the previous check changed", "",
                  "These answers have been checked once against the tree. The fixes that "
                  "check made, and its reasons, are below. Check the answers as they are "
                  "now. Don't put back what a fix deleted unless you have read the code "
                  "yourself and it shows the fix was wrong. If you do put it back, name the "
                  "function and say what it does.", ""]
        parts += [f"- {c}" for c in prior] + [""]
    if about:
        parts += ["# What was cut elsewhere because your answers were said to have it", "",
                  "The last check of the other answers in this guide made the changes below. "
                  "Each one names an answer you are checking.", "",
                  "- If a fact was deleted from another answer because yours was said to have "
                  "it, find it in yours as it is now.",
                  "- If yours does not have it, the guide is about to lose that fact. Two "
                  "checks each deleted it, and each trusted the other to keep it. Check the "
                  "fact against the tree like any other claim. Then put it in the answer "
                  "whose question asks for it, in the words that were deleted, and say so in "
                  "your changes.",
                  "- If a note reports a contradiction with one of your answers, read the "
                  "code. Fix yours if it is the one that is wrong.", ""]
        parts += [f"- {c}" for c in about] + [""]
    if last:
        parts += ["# This is the last check", "",
                  "No section check follows yours. Delete nothing because another answer "
                  "says it, in this group or outside it. No one is left to confirm that the "
                  "other answer still says it. Only delete what is wrong or what you cannot "
                  "confirm in the code.", ""]
    parts += ["# The rest of this guide", "",
              "The other answers, so you can check this group against them. You are "
              "not correcting these here.", ""]
    for qid, text in answers.items():
        if qid not in mine and text and qid in by_id:
            parts += [f"### {qid}: {by_id[qid].title}", "", text.strip(), ""]
    return "\n".join(parts)


CHECKED_MARK = "=== checked"
FIXED_MARK = "=== fixed ==="
CORRECTIONS_MARK = "=== corrections ==="


def bullets(text):
    """The items of a bulleted list, each on one line; "- none" is no items."""
    items = [" ".join(c.split()) for c in
             re.findall(r"^[-*]\s+(.*(?:\n(?![-*]\s|===).+)*)", text, re.M)]
    return [c for c in items if c.lower().strip(". `") != "none"]


# After its sections are checked a guide is read through whole by a reader whose only
# concern is whether it is true, and whose edits a checker verifies from one diff, the
# two taking turns until one changes nothing. That is the guide.
LOOPS = (
    {"name": "correct", "doing": "correcting", "did": "Correcting",
     "reader": "correct-guide.md", "checker": "check-corrections.md",
     "base": "the first checked version",
     "what": "A reader went through the whole guide for accuracy alone and corrected it; a "
             "checker verified one diff from the first checked version."},
)


def guide_diff(first, now, base="the first checked version"):
    """One unified diff, from the version a loop started with to this one."""
    d = list(difflib.unified_diff(first.splitlines(), now.splitlines(),
                                  base, "now", n=2, lineterm=""))
    return "\n".join(d) if d else "(no difference)"


TAG_NOTE = ("The line in square brackets above each answer gives its id. Those lines are "
            "not part of the guide.")


def read_through_prompt(guide_title, copy, fixed, corrections, loop=LOOPS[0], notes=None):
    parts = [read_prompt(loop["reader"]), "", "---", "", f"Guide: {guide_title}", ""]
    if notes:
        parts += ["# Notes from the section checks", "",
                  "Each was left by the check of one answer and names another, which "
                  "that check could not change.", ""]
        parts += [f"- {c}" for c in notes] + [""]
    if corrections:
        parts += ["# What the checker corrected", "",
                  "The checker's corrections to your last version, and its reasons. They "
                  "are already in the guide below.", ""]
        parts += [f"- {c}" for c in corrections] + [""]
    parts += ["# Your list so far", ""] + ([f"- {c}" for c in fixed] or ["- none"]) + [""]
    parts += ["# The guide", "", TAG_NOTE, "", copy]
    return "\n".join(parts)


def edits_prompt(guide_title, questions, copy, diff, fixed, loop=LOOPS[0]):
    parts = [read_prompt(loop["checker"]), "", "---", "", f"Guide: {guide_title}", "",
             "# The questions the answers are to", ""]
    for q in questions:
        if not q.is_verbatim:
            parts.append(f"- `{q.id}`, {q.title}: " + " ".join(q.text.split()))
    parts += ["", "# The guide as it now stands", "", TAG_NOTE, "", copy,
              f"# One diff, from {loop['base']} to now", "", "```diff", diff, "```", "",
              f"# The editor's list of what it has fixed since {loop['base']}", ""]
    parts += [f"- {c}" for c in fixed] or ["- none"]
    return "\n".join(parts) + "\n"


def split_answers(text, questions):
    """{id: cleaned answer} from a reply that marks each answer with its id."""
    body = text.split(CHANGES_MARK, 1)[0]
    titles = {q.id: q.title for q in questions}
    found = {}
    pieces = BLOCK_RE.split(body)           # [before, id, text, id, text, ...]
    short = {q.id.split(".", 1)[-1]: q.id for q in questions}     # a reply may drop the prefix
    for qid, chunk in zip(pieces[1::2], pieces[2::2], strict=False):
        qid = qid.strip("`*:")
        qid = qid if qid in titles else short.get(qid.split(".", 1)[-1], qid)
        if qid in titles and clean(chunk, titles[qid]):
            found[qid] = clean(chunk, titles[qid])
    if not found and len(questions) == 1:   # a lone question may use the plain marker
        only = clean(body, questions[0].title)
        if only:
            found[questions[0].id] = only
    return found


def split_changes(text):
    tail = text.partition(CHANGES_MARK)[2]
    changes = [" ".join(c.split()) for c in
               re.findall(r"^[-*]\s+(.*(?:\n(?![-*]\s).+)*)", tail, re.M)]
    # "checked out, left as is" is not a change, and must not earn another pass
    idle = re.compile(r"check(?:s|ed) out|left (?:as is|as it (?:is|was)|unchanged|alone)|"
                      r"no contradiction|no change|nothing to (?:change|correct)", re.I)
    return [c for c in changes if c.lower().strip(". `") != "none"
            and not (idle.search(c) and not re.search(
                r"\b(?:added|cut|removed|changed|replaced|reworded|dropped|fixed|moved|"
                r"qualified|narrowed|now says)\b", c, re.I))]


def clean(text, title=None):
    """The markdown body of a reply: no fence, no heading, no repeated title."""
    t = text.strip()
    if ANSWER_MARK in t:
        t = t.split(ANSWER_MARK, 1)[1].strip()
    m = re.fullmatch(r"```(?:markdown|md)?\s*\n(.*?)\n```", t, re.S)
    if m:
        t = m.group(1).strip()
    lines = t.split("\n")
    def is_title(line):
        bare = re.sub(r"[*_`:.\s]+", " ", line).strip().lower()
        return bool(title) and bare == re.sub(r"[*_`:.\s]+", " ", title).strip().lower()

    while lines and (lines[0].startswith("#") or not lines[0].strip() or is_title(lines[0])):
        lines.pop(0)
    t = "\n".join(lines).strip()
    # "**The title.** Yes, ..." or "- **Some label:** ...": the title is ours to add
    m = re.match(r"^(?P<bullet>[-*]\s+)?\*\*(?P<label>[^*\n]{3,90})\*\*(?P<colon>[.:]?)\s*", t)
    if m and t[m.end():].strip():
        label = m.group("label")
        short_label = (len(label.split()) <= 5 and (label.rstrip().endswith(":")
                       or m.group("colon") == ":") and not KEEP_LABEL_RE.search(label)
                       and not re.search(r"\*\*[^*\n]{2,40}:\*\*|\*\*[^*\n]{2,40}\*\*:",
                                         t[m.end():]))   # one of a set of labels: keep
        if is_title(label) or short_label:     # never a bold sentence: that is content
            t = (m.group("bullet") or "") + t[m.end():]
    return t.strip()


def problems_in(text):
    """Things an answer must not contain, whatever it says."""
    out = []
    if SHA_RE.search(text):
        out.append("contains what looks like a commit or blob SHA")
    if HISTORY_RE.search(text):
        out.append("contains version history ('since vX.Y')")
    if re.search(r"\.[chS]:\d+", text):
        out.append("contains a line number")
    return out


class Runner:
    def __init__(self, harness, cwd, opts, empty=None):
        self.harness, self.cwd, self.opts = harness, cwd, opts
        self.empty = empty or cwd       # where a from-memory turn runs: nothing to read
        self.usage, self.models, self.rows = {}, {}, {}
        self.drafts = {}                # id -> [(reader model, from-memory answer)]
        self.reviews = {}               # guide -> loop name -> what each round did, and sizes
        self.not_run = []               # stages that failed on the second try as well
        self.lock = threading.Lock()

    def missed(self, what, why):
        """A stage that did not run: the guide built without it is not one to install."""
        with self.lock:
            self.not_run.append(f"{what}: {' '.join(str(why).split())[:300]}")

    def memory_group(self, group, guide_title, model):
        """What one reader model says about a group with nothing in front of it."""
        t0, qs = time.time(), group["questions"]
        try:
            got = split_answers(self.turn(ask_prompt(group, guide_title, True),
                                          memory=True, model=model), qs)
        except HarnessError as e:
            log(f"  {model or 'default model'} could not answer {group['label']} "
                f"from memory: {e}")
            self.missed(f"a reader was not asked \"{group['label']}\" from memory", e)
            return {}
        log(f"  from memory, {model or 'default model'}: {group['label']} "
            f"({len(got)} of {len(qs)}) in {time.time() - t0:.0f}s")
        return got

    def keep_unparsed(self, group, text, what):
        """A reply nothing could be read from is kept for a person to look at."""
        path = getattr(self.opts, "unparsed_dir", None)
        if not path or not text:
            return
        os.makedirs(path, exist_ok=True)
        name = re.sub(r"[^A-Za-z0-9]+", "-", f"{what}-{group['label']}")[:80]
        with open(os.path.join(path, name + ".txt"), "w", encoding="utf-8") as f:
            f.write(text)

    def turn(self, prompt, memory=False, model=None):
        # One model call in a long build can fail for a reason that has nothing to
        # do with the question (a login that lapses for a moment, a dropped
        # connection), and an unanswered group leaves holes that fail the whole
        # guide. Try such a call once more before giving up on it.
        # The second try is given twice as long in all: if the first was cut
        # off because the work really is that long, it still gets done.
        for attempt in (1, 2):
            try:
                text, usage = self.harness.run(prompt, self.empty if memory else self.cwd,
                                               memory=memory, model=model,
                                               timeout=self.opts.timeout * attempt)
                break
            except HarnessError as e:
                if attempt == 2:
                    raise
                log(f"  a model call failed ({str(e)[:120]}); trying it once more")
                time.sleep(10)
        text, leaked = scrub(text, self.harness.secrets)
        with self.lock:
            for m in usage.pop("models", []):
                self.models[m] = self.models.get(m, 0) + 1
            for k, v in usage.items():
                self.usage[k] = self.usage.get(k, 0) + v
        if leaked:
            raise HarnessError("the reply contained a credential (redacted); the tree "
                               "may carry an injected instruction, answer discarded")
        return text

    def row(self, q):
        with self.lock:
            return self.rows.setdefault(q.id, {
                "id": q.id, "relevance": q.relevance, "asked": q.words or 0, "got": 0,
                "notes": [], "changes": [], "checked": False, "seconds": 0.0})

    def note(self, q, msg):
        self.row(q)["notes"].append(msg)

    def keep_differences(self, reply, questions):
        """Save what the builder said each reader had wrong, beside the build.

        Before its answers the builder lists, for each question, the differences
        between what the readers said from memory and what the code does. They
        are not part of the guide, but they are the record of how the models
        are wrong, for whoever reviews a build.
        """
        where = getattr(self.opts, "differences_dir", None)
        head = BLOCK_RE.split(reply.split(CHANGES_MARK, 1)[0])[0]
        pieces = DIFF_RE.split(head)
        ids = {q.id for q in questions}
        short = {q.id.split(".", 1)[-1]: q.id for q in questions}
        for qid, chunk in zip(pieces[1::2], pieces[2::2], strict=False):
            qid = qid.strip("`*:")
            qid = qid if qid in ids else short.get(qid.split(".", 1)[-1], qid)
            if where and qid in ids and chunk.strip():
                os.makedirs(where, exist_ok=True)
                with open(answer_path(where, qid), "w", encoding="utf-8") as f:
                    f.write(scrub(chunk.strip(), self.harness.secrets if self.harness else [])[0] + "\n")

    def answer_group(self, group, guide_title):
        """Answer one group; questions the reply skipped are asked again once."""
        t0, qs, got = time.time(), group["questions"], {}
        for q in qs:
            self.row(q)
        try:
            mem = self.opts.no_sources
            who = self.opts.reader_model[0] if mem and self.opts.reader_model else None
            reply = self.turn(ask_prompt(group, guide_title, mem, drafts=self.drafts),
                              memory=mem, model=who)
            got = split_answers(reply, qs)
            if not mem:
                self.keep_differences(reply, qs)
            if not got:
                self.keep_unparsed(group, reply, "answer")
            missing = [q for q in qs if q.id not in got]
            if missing:
                ids = {q.id for q in missing}
                for q in missing:
                    self.note(q, "left out of the group's reply; asked again")
                got.update(split_answers(self.turn(ask_prompt(
                    group, guide_title, mem, only=ids, drafts=self.drafts),
                    memory=mem, model=who), missing))
        except HarnessError as e:
            self.missed(f"\"{group['label']}\" was not answered", e)
            for q in qs:
                if q.id not in got:
                    self.note(q, f"failed: {e}")
        for q in qs:
            r = self.row(q)
            r["seconds"] += (time.time() - t0) / len(qs)
            if q.id not in got:
                r["notes"].append("no answer")
        log(f"  answered {group['label']}: " + ", ".join(
f"{q.id.split('.', 1)[-1]} {len(got.get(q.id, '').split())}" for q in qs)
            + f" in {time.time() - t0:.0f}s")
        return got

    def check_group(self, group, guide_title, answers, by_id, prior=None, about=None,
                    last=False):
        """Check one group against the tree and the rest of the guide.

        Returns ({id: corrected answer}, [what was changed]); an answer the
        reply leaves out is kept as it was.
        """
        t0, qs = time.time(), [q for q in group["questions"] if answers.get(q.id)]
        if not qs:
            return {}, []
        sub = dict(group, questions=qs)
        try:
            reply = self.turn(check_prompt(sub, guide_title, answers, by_id, prior, about,
                                           last),
                              model=self.opts.check_model)
        except HarnessError as e:
            self.missed(f"a check of \"{group['label']}\" did not run", e)
            for q in qs:
                self.note(q, f"the check did not run: {e}")
            return {}, []
        reply, mark, shown = reply.partition(CHECKED_MARK)
        if mark and getattr(self.opts, "checked_dir", None):
            # what the checker says it looked at, bullet by bullet: kept, not parsed
            os.makedirs(self.opts.checked_dir, exist_ok=True)
            name = re.sub(r"[^A-Za-z0-9_.-]+", "-", group["label"]).strip("-") or "group"
            with open(os.path.join(self.opts.checked_dir, name + ".md"), "w",
                      encoding="utf-8") as f:
                f.write(mark + shown.rstrip() + "\n")
        fixed, changes = split_answers(reply, qs), split_changes(reply)
        for q in qs:
            r = self.row(q)
            r["checked"] = True
            r["seconds"] += (time.time() - t0) / len(qs)
            if q.id not in fixed:
                r["notes"].append("the check returned no text for this answer; kept as it was")
        # a change belongs to the answers it names; one that names none, to the group
        for c in changes:
            lead = re.match(r"`?([\w.\-]+)`?\s*:", c)
            named = [q for q in qs if lead and q.id == lead.group(1)] \
                or [q for q in qs if q.id in c]
            for q in (named[:1] or qs[:1]):
                self.row(q)["changes"].append(c)
        log(f"  checked {group['label']}: {len(changes)} corrections in {time.time() - t0:.0f}s")
        return fixed, changes


    def accept(self, got, questions, answers, guide_title):
        """Take edited answers into the guide; returns the ids that really changed."""
        changed = []
        for q in questions:
            text = got.get(q.id)
            if not text or text.strip() == answers.get(q.id, "").strip():
                continue
            answers[q.id] = text
            changed.append(q.id)
        return changed

    def review(self, stem, header, questions, answers, guide_title, loop=LOOPS[0], notes=None):
        """One loop over the whole guide: a reader edits it, a checker checks the edits.

        The reader edits the guide and lists what it has done since the version
        the loop started with. The checker gets one diff from that version to
        now, and the list, and hands back corrections with reasons. They take
        turns until one of them changes nothing: the reader accepting the
        checker's version, or the checker accepting the reader's. Which
        prompts they follow, and so what they are looking for, is the loop's:
        see LOOPS. notes are what the last section check of one group said
        about an answer of another: no later section check reads them, so
        the reader does. Returns the ids whose answers changed.
        """
        qs = [q for q in questions if answers.get(q.id)]
        mine = [q for q in qs if not q.is_verbatim]
        first = render(header, stem, qs, answers, False)
        start = {q.id: answers[q.id] for q in mine}
        fixed, corrections, rounds = [], [], []
        record = {"rounds": rounds, "before": len(first.split())}
        self.reviews.setdefault(stem, {})[loop["name"]] = record
        for n in range(1, self.opts.rounds + 1):
            t0 = time.time()
            copy = render(header, stem, qs, answers, False, tags=True)
            try:
                reply = self.turn(read_through_prompt(guide_title, copy, fixed, corrections, loop,
                                                      notes),
                                  model=self.opts.read_model)
            except HarnessError as e:
                self.missed(f"the reader of the whole of {stem} did not run", e)
                rounds.append({"round": n, "stopped": f"the reader did not run: {e}"})
                break
            body, mark, tail = reply.partition(FIXED_MARK)
            edited = self.accept(split_answers(body, mine), mine, answers, guide_title)
            if mark:
                fixed = bullets(tail)
            entry = {"round": n, "edited": edited, "fixed": list(fixed)}
            rounds.append(entry)
            log(f"  {stem}: {loop['doing']}, round {n}: the reader changed {len(edited)} "
                f"answers in {time.time() - t0:.0f}s")
            if not edited:                  # it takes the guide as it stands
                entry["stopped"] = "the reader changed nothing"
                break
            t0 = time.time()
            now = render(header, stem, qs, answers, False)
            copy = render(header, stem, qs, answers, False, tags=True)
            try:
                reply = self.turn(edits_prompt(guide_title, qs, copy,
                                               guide_diff(first, now, loop["base"]), fixed, loop),
                                  model=self.opts.check_model)
            except HarnessError as e:
                self.missed(f"the checker of the reader's changes to {stem} did not run", e)
                entry["stopped"] = f"the checker did not run: {e}"
                break
            body, _, tail = reply.partition(CORRECTIONS_MARK)
            entry["corrected"] = self.accept(split_answers(body, mine), mine, answers, guide_title)
            entry["corrections"] = corrections = bullets(tail)
            log(f"  {stem}: {loop['doing']}, round {n}: the checker changed "
                f"{len(entry['corrected'])} answers in {time.time() - t0:.0f}s")
            if not entry["corrected"]:      # it takes the reader's version
                entry["stopped"] = "the checker changed nothing"
                break
        else:
            rounds[-1]["stopped"] = (f"still changing after {self.opts.rounds} rounds; "
                                     "stopped there")
        record["after"] = len(render(header, stem, qs, answers, False).split())
        log(f"  {stem}: {loop['doing']} took it from {record['before']} to {record['after']} words")
        return [q.id for q in mine if answers[q.id] != start[q.id]]


# ------------------------------------------------------------------- render

NO_SOURCES_STAMP = (
    "> **Built with `--no-sources`.** Nothing here was read from a kernel tree.\n"
    "> It is what a model recalled about the latest Linux it knows, and it has\n"
    "> not been checked against anything. It exists to be compared with a real\n"
    "> build. Do not review patches with it.\n")


def lead_in(title, text):
    """An item in a section: its title in bold, then the answer."""
    first, _, rest = text.strip().partition("\n\n")
    lines = first.splitlines()
    starts_block = ("|", "- ", "* ", "1. ", "```")
    # A sentence with a list straight under it, no blank line between: the list
    # is its own block, or reflowing the sentence would swallow the bullets.
    if not first.lstrip().startswith(starts_block):
        for i, line in enumerate(lines[1:], 1):
            if line.lstrip().startswith(starts_block):
                rest = "\n".join(lines[i:]) + (f"\n\n{rest}" if rest.strip() else "")
                first, lines = "\n".join(lines[:i]), lines[:i]
                break
    # A table may be written without its outer pipes: "a | b" over "---|---".
    bare_table = (len(lines) > 1 and "|" in lines[0]
                  and re.fullmatch(r"[\s|:-]*-{3,}[\s|:-]*", lines[1]) and "|" in lines[1])
    if bare_table or first.lstrip().startswith(starts_block):
        return f"**{title}**\n\n{text.strip()}"
    lead = re.sub(r"`[^`\n]+`", lambda m: m.group(0).replace(" ", "\x00"),
                  " ".join(first.split()))
    para = "\n".join(textwrap.wrap(f"**{title}:** {lead}", width=79,
                                    break_long_words=False, break_on_hyphens=False))
    return para.replace("\x00", " ") + (f"\n\n{rest.strip()}" if rest.strip() else "")


CHECKED_MEMORY_STAMP = (
    "> **Built with `--no-sources --check-memory`.** Each answer was written from\n"
    "> a model's memory with no sources, then corrected against the tree. It is a\n"
    "> measurement of what the model already knows: compare `answers/<id>.first.md`\n"
    "> with `answers/<id>.md`, and see the run report.\n")


def wrap_bullet(title, text):
    """A quick check: '- **Title**: text', continuation lines indented."""
    text = re.sub(r"^\s*[-*]\s+", "", text.strip())     # the bullet is ours to add
    paras = [p for p in re.split(r"\n\s*\n", text) if p.strip()]
    first = re.sub(r"`[^`\n]+`", lambda m: m.group(0).replace(" ", "\x00"),
                   " ".join(paras[0].split())) if paras else ""
    out = textwrap.wrap(f"**{title}**: {first}", width=79, initial_indent="- ",
                        subsequent_indent="  ", break_long_words=False,
                        break_on_hyphens=False)
    lines = [l.replace("\x00", " ") for l in out]
    for p in paras[1:]:
        lines += [("  " + l if l.strip() else "") for l in p.split("\n")]
    return "\n".join(lines)


def render(header, stem, questions, answers, no_sources, tags=False):
    """The guide. With tags, a line above each answer gives its id, for a model
    that is to hand back edits by id; those lines are not rendered."""
    out = [f"# {header.get('title', stem)}", ""]

    def tag(q):
        if not tags:
            return []
        return [f"[{q.id}]" + (" (inserted text)" if q.is_verbatim else "")]
    if no_sources:
        out += [CHECKED_MEMORY_STAMP if no_sources == "checked" else NO_SOURCES_STAMP]
    in_quick, section, part = False, None, None
    # A part whose answers all sit in one section needs no heading for it: the
    # part's own heading already says where the reader is.
    sections_in = {}
    for q in questions:
        if answers.get(q.id) and not q.quick:
            sections_in.setdefault(q.part, []).append(q.section)
    lone = {p for p, s in sections_in.items() if p and len(set(s)) == 1 and s[0]}
    for q in questions:
        text = answers.get(q.id)
        if not text:
            continue
        if q.quick:
            if not in_quick:
                out += ["## Quick Checks", ""]
                in_quick = True
            out.append(wrap_bullet(q.title, text))
            continue
        if in_quick:
            out.append("")
        in_quick = False
        if q.part != part:
            part, section = q.part, None
            if part:
                out += [f"## {part}", ""]
        deeper = "#" if part else ""
        if not q.section:
            section = None
            out += tag(q) + [f"##{deeper} {q.title}", "", text, ""]
            continue
        if q.section != section:
            section = q.section
            if part not in lone:
                out += [f"##{deeper} {section}", ""]
        out += tag(q) + [f"**{q.title}**\n\n{text.strip()}" if q.is_verbatim
                         else lead_in(q.title, text), ""]
    return "\n".join(out).rstrip() + "\n"


def answer_path(directory, qid):
    """directory/<id>.md, refusing an id or a guide name that would leave it.

    The parser already refuses such ids; this is the last check before a path
    is opened, for a caller that did not come through the parser.
    """
    path = os.path.join(directory, qid + ".md")
    if not safe_id(qid) or os.path.dirname(os.path.abspath(path)) != os.path.abspath(directory):
        raise SystemExit(f"refusing to use {qid!r} as a file name")
    return path


MODELS_SEEN = os.path.join("~", ".config", "review-prompts", "models-seen")


def remember_models(opts):
    """Note, outside the repository, every model this run was told to use.

    check-built-guide.py refuses these names in anything about to be committed.
    This repository is public and cannot list them, and a build started by hand
    would otherwise use a model that no check knows the name of.
    """
    names = {m for m in [opts.model, opts.check_model, getattr(opts, "read_model", None)]
             + list(opts.reader_model) if m}
    if not names:
        return
    path = os.path.expanduser(os.environ.get("REVIEW_PROMPTS_MODELS_SEEN") or MODELS_SEEN)
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        try:
            with open(path, encoding="utf-8") as f:
                have = {line.strip() for line in f}
        except OSError:
            have = set()
        new = sorted(names - have)
        if new:
            fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o600)
            with os.fdopen(fd, "a", encoding="utf-8") as f:
                f.write("".join(n + "\n" for n in new))
    except OSError as e:
        log(f"could not note the models used in {path}: {e}")


def keep_answers(root, chosen, answers):
    """Each guide's final answers, one file per question, with nothing about the run.

    With these and the question file a guide can be rendered again, so a change
    to the renderer does not need a model. Verbatim items are not kept: their
    text is the hand-maintained file's.
    """
    for stem, qs in chosen.items():
        if not safe_id(stem):
            raise SystemExit(f"refusing to use {stem!r} as a directory name")
        d = os.path.join(root, stem)
        if os.path.isdir(d):
            for name in os.listdir(d):          # answers to questions since removed
                if name.endswith(".md"):
                    os.remove(os.path.join(d, name))
        os.makedirs(d, exist_ok=True)
        for q in qs:
            if answers.get(q.id) and not q.is_verbatim:
                with open(answer_path(d, q.id), "w", encoding="utf-8") as f:
                    f.write(answers[q.id].strip() + "\n")


def render_only(opts):
    """Render guides from kept answers: no tree, no model."""
    files = load(opts.questions, set(opts.guide))
    out = os.path.abspath(opts.out)
    os.makedirs(out, exist_ok=True)
    missing = 0
    for stem, (header, questions) in sorted(files.items()):
        path = os.path.join(out, stem + ".md")
        if header.get("verbatim"):
            text = read_verbatim(header["verbatim"]) + "\n"
        else:
            answers = {}
            for q in questions:
                if q.is_verbatim:
                    answers[q.id] = q.verbatim_text()
                    continue
                cand = answer_path(os.path.join(opts.render_only, stem), q.id)
                if os.path.isfile(cand) and not os.path.islink(cand):
                    with open(cand, encoding="utf-8") as f:
                        answers[q.id] = f.read().strip()
            asked = select({stem: (header, questions)}, opts.min_relevance, set())[stem]
            gone = [q.id for q in asked if q.id not in answers]
            if gone:
                missing += len(gone)
                log(f"{stem}: no kept answer for {', '.join(gone)}")
            if not any(not q.is_verbatim for q in questions if q.id in answers):
                log(f"{stem}: no kept answers at all; not written")
                continue
            text = render(header, stem, [q for q in questions if q.id in answers],
                          answers, False)
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        log(f"{path}: rendered")
    return 1 if missing else 0


def write_report(path, opts, chosen, runner, version, semcode):
    if opts.no_sources and opts.check_memory:
        where = ("Answered from the model's own knowledge with no sources, then "
                 f"corrected against `{os.path.abspath(opts.tree)}`, kernel {version}. "
                 f"semcode for the check: {semcode}. \"Rewritten\" is the share of each "
                 "from-memory answer the check replaced.")
    elif opts.no_sources:
        where = ("No sources: answered from the model's own knowledge of the latest "
                 "Linux, unchecked.")
    else:
        read_from = (f"the snapshot `{os.path.abspath(opts.snapshot)}`" if opts.snapshot
                     else "a copy unpacked for this run")
        where = (f"Tree: `{os.path.abspath(opts.tree)}`, kernel {version}, read from "
                 f"{read_from}. semcode: {semcode}.")
    models = ", ".join(f"`{m}` ({n} turns)" for m, n in sorted(runner.models.items()))
    rows = [runner.rows[q.id] for qs in chosen.values() for q in qs if q.id in runner.rows]
    L = ["# Run report", "", where,
         "Model: " + (models or "not reported by the harness")
         + (f"; `--model {opts.model}` was asked for" if opts.model
            else "; none was asked for, so this is the harness default") + ".",
         f"Guides: {', '.join(sorted(chosen))}. Minimum relevance {opts.min_relevance if opts.min_relevance is not None else "as each question file says, or 2"}."
         + ("" if opts.no_sources or opts.no_memory_pass else
            " Readers asked from memory first: "
            + ", ".join(f"`{m or 'the default model'}`"
                        for m in (opts.reader_model or [opts.model])) + "."),
         ""]
    for stem, loop, record in [(s, l, r[l["name"]]) for s, r in sorted(runner.reviews.items())
                               for l in LOOPS if l["name"] in r]:
        rounds = record["rounds"]
        L += [f"## {loop['did']} {stem}", "", loop["what"] + " They took turns until one changed "
              f"nothing. The guide went from {record['before']} to "
              f"{record.get('after', record['before'])} words.", ""]
        for e in rounds:
            L.append(f"**Round {e['round']}.** The reader edited "
                     + (", ".join(f"`{i}`" for i in e.get("edited", [])) or "nothing") + "."
                     + (" The checker corrected "
                        + (", ".join(f"`{i}`" for i in e["corrected"]) or "nothing") + "."
                        if "corrected" in e else "")
                     + (f" Stopped: {e['stopped']}." if e.get("stopped") else ""))
            L += [""] + [f"- checker: {c}" for c in e.get("corrections", [])]
            L.append("")
        last = next((e for e in reversed(rounds) if e.get("fixed")), None)
        if last:
            L += [f"What the reader did since {loop['base']}, as it lists it:", ""]
            L += [f"- {c}" for c in last["fixed"]] + [""]
    if runner.not_run:
        L += ["## Stages that did not run", "",
              "Each failed twice. The guide was built without them and is not to be "
              "installed; build it again.", ""] + [f"- {x}" for x in runner.not_run] + [""]
    L += ["## Questions", "",
         "| question | relevance | words asked | words got | corrections | rewritten | notes |",
         "|---|---|---|---|---|---|---|"]
    for r in rows:
        fixes = len(r["changes"]) if r["checked"] else "not checked"
        redone = f"{r['rewritten']}%" if r.get("rewritten") is not None else ""
        L.append(f"| `{r['id']}` | {r['relevance']} | {r['asked']} | {r['got']} | {fixes} | "
                 f"{redone} | {'; '.join(r['notes'])} |")
    fixed = [r for r in rows if r["changes"]]
    if fixed:
        L += ["", "## What the check corrected", "",
              "Each group of answers was checked against the tree, and against the "
              "rest of the guide, by a second, independent reader. What is in the "
              "guide is the corrected text. The first drafts are in "
              "`answers/<id>.first.md`.", ""]
        for r in fixed:
            L.append(f"**`{r['id']}`**")
            L += [f"- {c}" for c in dict.fromkeys(r["changes"])]
            L.append("")
    L.append("")
    u = runner.usage
    tokens_in = sum(u.get(k, 0) for k in ("input_tokens", "cache_read_input_tokens",
                                          "cache_creation_input_tokens"))
    L += ["## Cost", "",
          f"- model turns: {int(u.get('turns', 0))}, agent time: "
          f"{u.get('seconds', 0) / 60:.0f} min, input tokens: {int(tokens_in)}, "
          f"output tokens: {int(u.get('output_tokens', 0))}, "
          f"cost: ${u.get('cost_usd', 0):.2f}", ""]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(L))


# --------------------------------------------------------------------- main

def selftest():
    """Exercise everything that needs no model. Returns 0 if it all holds."""
    import textwrap as tw
    failures = []

    def check(name, cond):
        if not cond:
            failures.append(name)
        print(("ok    " if cond else "FAIL  ") + name)

    root = tempfile.mkdtemp(prefix="build-guides-selftest-")
    try:
        sub = os.path.join(root, "subsystem")
        os.makedirs(os.path.join(sub, "questions"))
        os.makedirs(os.path.join(sub, "verbatim"))
        os.makedirs(os.path.join(root, "outside"))
        with open(os.path.join(sub, "verbatim", "spec.md"), "w") as f:
            f.write("*   **A rule.** The specification says \"x\".\n")
        with open(os.path.join(root, "outside", "secret.md"), "w") as f:
            f.write("secret\n")
        os.symlink(os.path.join(root, "outside", "secret.md"),
                   os.path.join(sub, "verbatim", "link.md"))
        qf = os.path.join(sub, "questions", "demo.md")
        with open(qf, "w") as f:
            f.write(tw.dedent("""\
                # Questions: demo

                - guide: demo.md
                - title: Demo
                - min-relevance: 3

                # Where to look

                ## demo.files: Core files

                - section: Finding your way
                - relevance: 4 - test
                - words: 40

                Which files hold the demo code, and what is in each of them today?

                # Facts

                ## demo.a: First fact

                - section: Queue
                - relevance: 5 - test
                - words: 40

                What does the first thing do when the second thing is absent here?

                ## demo.low: Minor fact

                - section: Queue
                - relevance: 2 - test
                - words: 40

                What does the minor thing do when nothing else at all is happening?

                ## demo.spec: What the specification says

                - section: Queue
                - verbatim: ../verbatim/spec.md

                ## demo.b: Second fact

                - section: Locks
                - relevance: 5 - test
                - words: 40

                What does the second thing do when the first thing is absent here?
                """))
        header, qs, problems = parse(qf)
        check("question file parses", not problems and len(qs) == 5)
        from question_file import safe_id as ok_id
        for qid, ok in (("demo.a", True), ("mm-vma.lock_2", True), ("../../x", False),
                        ("a/b", False), ("..", False), ("a..b", False), (".hidden", False)):
            check(f"question id {qid}: {'allowed' if ok else 'refused'}", ok_id(qid) == ok)
        bad = os.path.join(sub, "questions", "bad.md")
        with open(bad, "w") as f:
            f.write("# Questions: bad\n\n- guide: bad.md\n- title: Bad\n\n# Sections\n\n"
                    "## ../../outside/pwned: Title here\n\n- relevance: 5 - x\n- words: 40\n\n"
                    "What does this question do when its id tries to leave the directory?\n")
        check("a question file with a path for an id does not parse", bool(parse(bad)[2]))
        try:
            answer_path(root, "../x")
            check("answer_path refuses an id that leaves the directory", False)
        except SystemExit:
            check("answer_path refuses an id that leaves the directory", True)
        from question_file import resolve_verbatim
        for value, ok in (("../verbatim/spec.md", True), ("/etc/passwd", False),
                          ("../../outside/secret.md", False), ("../verbatim/link.md", False),
                          ("../verbatim/spec.txt", False)):
            check(f"verbatim path {value}: {'allowed' if ok else 'refused'}",
                  (resolve_verbatim(qf, value)[0] is not None) == ok)
        files = {"demo": (header, qs)}
        check("header min-relevance is honoured",
              [q.id for q in select(files, None, set())["demo"]]
              == ["demo.files", "demo.a", "demo.spec", "demo.b"])
        check("--min-relevance overrides the header",
              "demo.low" in [q.id for q in select(files, 0, set())["demo"]])
        groups = make_groups(qs, 8)
        check("verbatim items are not put to a model",
              all(not q.is_verbatim for g in groups for q in g["questions"]))
        answers = {"demo.files": "Area | File\n---|---\ncore | `mm/demo.c`",
                   "demo.a": "In order:\n- `x()`: returns 0.\n- `y()`: warns.",
                   "demo.b": "`z()` takes the lock; nothing else does.",
                   "demo.spec": qs[3].verbatim_text()}
        text = render(header, "demo", [q for q in qs if q.id in answers], answers, False)
        check("a part with one section has no section heading",
              "### Finding your way" not in text and "## Where to look" in text)
        check("a part with two sections keeps them",
              "### Queue" in text and "### Locks" in text)
        check("a table without outer pipes stays a table",
              "**Core files**\n\nArea | File\n---|---" in text)
        check("a lead sentence is split from the list under it",
              "**First fact:** In order:\n\n- `x()`: returns 0." in text)
        check("a one-line answer runs on from its title",
              "**Second fact:** `z()` takes the lock" in text)
        check("verbatim text goes in as it is",
              "**What the specification says**\n\n*   **A rule.** The specification says" in text)
        ga, gb = {"questions": [qs[1]]}, {"questions": [qs[4]]}
        cut = "`demo.a`: cut the bullet \"`y()` warns\"; `demo.b` already says it."
        own = "`demo.b`: `z()` takes the lock, not asserts it."
        check("a check hears what another cut because it was said to have it",
              notes_about(gb, [(ga, [cut]), (gb, [own])]) == [cut]
              and notes_about(ga, [(ga, [cut]), (gb, [own])]) == [])
        p = check_prompt(gb, "Demo", {"demo.a": "- a", "demo.b": "- b"},
                         {q.id: q for q in qs}, None, [cut], True)
        check("and is asked to confirm the fact is still there; the last check cuts nothing as repeated",
              "# What was cut elsewhere because your answers were said to have it" in p
              and cut in p and "# This is the last check" in p
              and "# This is the last check" not in check_prompt(
                  gb, "Demo", {"demo.b": "- b"}, {q.id: q for q in qs}))
        reply = ("=== answer: demo.a: First fact ===\n- one\n"
                 "**=== answer: b ===**\n- two\n=== changes ===\n- `demo.a`: fixed\n")
        got = split_answers(reply, [qs[1], qs[4]])
        check("answer markers: a copied title, a dropped prefix, decoration",
              sorted(got) == ["demo.a", "demo.b"])
        y = os.path.join(root, "kernel-version.yaml")
        check("no kernel record reads as none", read_record(y) == {})
        record_build(y, "v7.3-rc4", "1" * 40)
        record_build(y, "v7.3-rc5", "2" * 40)
        check("the kernel record holds one kernel",
              read_record(y) == {"kernel": "v7.3-rc5", "sha": "2" * 40}
              and open(y).read().count("kernel:") == 1)
        with open(os.path.join(root, "Makefile"), "w") as f:
            f.write("VERSION = 7\nPATCHLEVEL = 3\nSUBLEVEL = 0\nEXTRAVERSION = -rc4\n")
        check("kernel base is spelled as a tag", kernel_base(root) == "v7.3-rc4")
        kept = os.path.join(root, "kept")
        keep_answers(kept, {"demo": qs}, answers)
        check("kept answers leave out verbatim items",
              sorted(os.listdir(os.path.join(kept, "demo")))
              == ["demo.a.md", "demo.b.md", "demo.files.md"])
        opts = argparse.Namespace(questions=os.path.join(sub, "questions"), guide=["demo"],
                                  out=os.path.join(root, "out"), render_only=kept,
                                  min_relevance=None)
        class Script(Runner):
            """A runner whose model is a list of canned replies."""
            def __init__(self, replies, rounds=4):
                Runner.__init__(self, None, root, argparse.Namespace(
                    rounds=rounds, read_model=None, check_model=None, no_sources=False,
                    reader_model=[]))
                self.replies, self.prompts = list(replies), []
            def turn(self, prompt, memory=False, model=None):
                self.prompts.append(prompt)
                return self.replies.pop(0)
        live = [q for q in qs if q.id in answers]
        base = dict(answers)
        # round 1: the reader cuts a bullet; the checker puts it back, with a reason
        # round 2: the reader accepts that and changes nothing
        s = Script(["=== answer: demo.a ===\nIn order:\n- `x()`: returns 0.\n=== fixed ===\n"
                    "- `demo.a`: `y()` does not warn; cut.\n",
                    "=== answer: demo.a ===\nIn order:\n- `x()`: returns 0.\n- `y()`: warns.\n"
                    "=== corrections ===\n- `demo.a`: `y()` does warn, in `y()`; restored.\n",
                    "=== fixed ===\n- none\n"])
        a = dict(base)
        changed = s.review("demo", header, live, a, "Demo")
        check("the loop stops when the reader accepts the checker's version",
              len(s.prompts) == 3 and not s.replies and changed == []
              and s.reviews["demo"]["correct"]["rounds"][-1]["stopped"] == "the reader changed nothing")
        check("the checker gets one diff from the first version, and the reader's list",
              "--- the first checked version" in s.prompts[1]
              and "-- `y()`: warns." in s.prompts[1] and "does not warn; cut" in s.prompts[1])
        check("the reader is shown the checker's reasons on its next turn",
              "does warn, in `y()`; restored" in s.prompts[2])
        check("inserted text is shown as such and cannot be edited",
              "[demo.spec] (inserted text)" in s.prompts[0]
              and "\n[demo.a]\n" in s.prompts[0])
        # the checker accepts the reader's edit at once
        s = Script(["=== answer: demo.b ===\n`z()` takes the lock.\n=== fixed ===\n"
                    "- `demo.b`: nothing else was checked; cut the claim.\n",
                    "=== corrections ===\n- none\n"])
        a = dict(base)
        check("the loop stops when the checker accepts the reader's version",
              s.review("demo", header, live, a, "Demo") == ["demo.b"] and len(s.prompts) == 2
              and a["demo.b"] == "`z()` takes the lock.")
        # nothing caps the length of an edit: the read-through distils, no number does
        long = "- " + " ".join(["word"] * 120)
        s = Script(["=== answer: demo.b ===\n" + long + "\n=== fixed ===\n- `demo.b`: longer\n",
                    "=== corrections ===\n- none\n"])
        a = dict(base)
        s.review("demo", header, live, a, "Demo")
        check("a long edit is taken as it is, with no call to cut it to a number",
              a["demo.b"] == long and len(s.prompts) == 2)
        # what the last section check said about another group is given to the reader
        s = Script(["=== fixed ===\n- none\n"])
        a = dict(base)
        s.review("demo", header, live, a, "Demo",
                 notes=["`demo.a`: `demo.b` says the count may be zero; the code does not bear it out"])
        check("what the last section check said about another group reaches the reader",
              "# Notes from the section checks" in s.prompts[0]
              and "the code does not bear it out" in s.prompts[0])
        # a reader with nothing to fix costs one call
        s = Script(["=== fixed ===\n- none\n"])
        check("a reader with nothing to fix ends it after one call",
              s.review("demo", header, live, a, "Demo") == [] and len(s.prompts) == 1 and a == base)
        # two that never agree stop at the cap, and the diff is still from the first version
        flip = ["=== answer: demo.b ===\n`z()` takes the lock; nothing else does. v%d\n=== %s ===\n- `demo.b`: again\n"
                % (i, "fixed" if i % 2 == 0 else "corrections") for i in range(6)]
        s = Script(flip, rounds=3)
        a = dict(base)
        s.review("demo", header, live, a, "Demo")
        check("two that never agree stop at the cap",
              len(s.prompts) == 6 and "still changing after 3 rounds" in s.reviews["demo"]["correct"]["rounds"][-1]["stopped"])
        check("however many rounds, the diff is from the first version",
              all("-**Second fact:** `z()` takes the lock; nothing else does." in p
                  for p in s.prompts[1::2]))
        # the builder's list of differences is kept beside the build and is not part of an answer
        s = Script([])
        s.opts.differences_dir = os.path.join(root, "diffs")
        s.keep_differences("=== differences: demo.a ===\n- reader 2: says x; the code: y\n- all right: z\n"
                           "=== answer: demo.a ===\n- `y()`: warns.\n", live)
        check("the differences are kept, and only what comes before the answers",
              open(os.path.join(root, "diffs", "demo.a.md")).read().startswith("- reader 2: says x")
              and "warns" not in open(os.path.join(root, "diffs", "demo.a.md")).read()
              and split_answers("=== differences: demo.a ===\n- reader 2: x\n=== answer: demo.a ===\n- `y()`: warns.\n",
                                live) == {"demo.a": "- `y()`: warns."})
        seen = os.path.join(root, "models-seen")
        os.environ["REVIEW_PROMPTS_MODELS_SEEN"] = seen
        ns = argparse.Namespace(model="aaa-1", check_model=None, reader_model=["bbb-2", "aaa-1"])
        remember_models(ns)
        remember_models(ns)
        check("the models a run is given are noted once each, outside the repository",
              open(seen).read().split() == ["aaa-1", "bbb-2"]
              and (os.stat(seen).st_mode & 0o077) == 0)
        del os.environ["REVIEW_PROMPTS_MODELS_SEEN"]
        class Dead(Script):
            def turn(self, prompt, memory=False, model=None):
                raise HarnessError("timed out after 1s")
        d = Dead([])
        a = dict(base)
        got = d.check_group({"label": "sec", "questions": live}, "Demo", a, {q.id: q for q in live})
        check("a check that does not run leaves the answers alone and is counted against the guide",
              got == ({}, []) and a == base and len(d.not_run) == 1
              and d.not_run[0].startswith("a check of \"sec\" did not run"))
        # a call that outlives its time: stopped with what it started, and a record kept
        fake = os.path.join(root, "fake-cli")
        with open(fake, "w") as f:
            f.write("#!/bin/sh\nsleep 300 &\necho started >&2\nsleep 300\n")
        os.chmod(fake, 0o755)
        hopts = build_parser().parse_args(["--no-sources", "--out", os.path.join(root, "out"),
                                           "--claude", fake, "--timeout", "1",
                                           "--api-key-helper", "/bin/true"])
        hopts.failed_dir = os.path.join(root, "failed-calls")
        hwork = os.path.join(root, "hwork")
        os.makedirs(hwork)
        h = ClaudeCLI(hopts, hwork, [])
        proj = os.path.join(h.config_dir, "projects", "p")
        os.makedirs(proj)
        with open(os.path.join(proj, "s1.jsonl"), "w") as f:
            for stamp, kind, content in (
                    ("2026-01-01T00:00:00.000Z", "user",
                     "first part of a prompt, the end of the prompt"),
                    ("2026-01-01T00:00:05.000Z", "assistant",
                     [{"type": "tool_use", "name": "mcp__semcode__find_function"}]),
                    ("2026-01-01T00:50:05.000Z", "user", [{"type": "tool_result"}])):
                f.write(json.dumps({"timestamp": stamp, "type": kind,
                                    "message": {"content": content}}) + "\n")
        try:
            h.run("first part of a prompt, the end of the prompt", root)
            said = ""
        except HarnessError as e:
            said = str(e)
        kept = os.path.join(hopts.failed_dir, "001.txt")
        body = open(kept).read() if os.path.exists(kept) else ""
        left = subprocess.run(["pgrep", "-f", "sleep 300"], capture_output=True, text=True).stdout
        mine = [p for p in left.split() if os.path.exists(f"/proc/{p}/cwd")
                and os.path.realpath(f"/proc/{p}/cwd") == os.path.realpath(root)]
        check("a call that outlives its time is stopped, with what it started",
              "timed out after 1s" in said and not mine)
        check("and what it was doing is kept: the longest wait, and what came before it",
              "what it left is in" in said and "started" in body
              and "3000s after 00:00:05 assistant tool_use:mcp__semcode__find_function" in body)
        check("a record is of the call's own session, not of one whose prompt ends the same",
              session_record(h.config_dir, "another prompt, the end of the prompt", 0)
              == ["## the session: no transcript of it was found"])
        # a call is watched: one that goes on taking steps is left alone, one that stops is stopped
        step = ('{"type":"assistant","message":{"content":[{"type":"text"}]}}')
        asked = ('{"type":"api-request"}')
        with open(fake, "w") as f:
            f.write("#!/bin/sh\n"
                    "while [ $# -gt 0 ]; do [ \"$1\" = --session-id ] && id=$2; shift; done\n"
                    "d=$CLAUDE_CONFIG_DIR/projects/q; mkdir -p $d; t=$d/$id.jsonl\n"
                    "read how\n"
                    "echo '%s' >> $t\n"
                    "if [ \"$how\" = works ]; then\n"
                    "  for i in 1 2 3 4; do sleep 1; echo '%s' >> $t; done\n"
                    "  echo '{\"result\": \"done\"}'; exit 0\n"
                    "fi\n"
                    "while :; do sleep 1; echo '%s' >> $t; done\n" % (step, step, asked))
        every = globals()["WATCH_EVERY"]
        globals()["WATCH_EVERY"] = 1
        h.timeout, h.quiet, h.watch = 30, 2, True
        try:
            reply, used = h.run("works\n", root)
            said = ""
        except HarnessError as e:
            reply, used, said = "", {}, str(e)
        check("a call that goes on taking steps is left to finish, however long it is quiet for",
              reply == "done" and used.get("steps") == 5 and not said)
        began = time.time()
        try:
            h.run("stalls\n", root)
            said = ""
        except HarnessError as e:
            said = str(e)
        check("a call that takes no step is stopped, though the CLI goes on sending requests",
              "no step for" in said and "after 1 steps" in said and time.time() - began < 15)
        h.watch = False
        h.timeout = 3
        try:
            h.run("stalls\n", root)
            said = ""
        except HarnessError as e:
            said = str(e)
        check("and where a call cannot be watched, the time limit alone stops it",
              "timed out after 3s" in said)
        globals()["WATCH_EVERY"] = every
        shutil.rmtree(private_dir(hwork), ignore_errors=True)
        check("render-only reproduces the guide",
              render_only(opts) == 0
              and open(os.path.join(root, "out", "demo.md")).read() == text)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print(f"{len(failures)} failed" if failures else "all passed")
    return 1 if failures else 0


def build_parser():
    ap = argparse.ArgumentParser(
        description="Build subsystem guides by asking the question files.",
        epilog="See kernel/docs/subsystem-questions.md.")
    ap.add_argument("--tree", help="kernel git tree to describe")
    ap.add_argument("--no-sources", action="store_true",
                    help="give the model no tree and no tools; it answers from its "
                    "own knowledge of the latest Linux. A baseline, not a guide")
    ap.add_argument("--check-memory", action="store_true",
                    help="with --no-sources and --tree: after the model has answered "
                    "from memory, correct its answers against the tree and report how "
                    "much had to change. Measures what the model already knows")
    ap.add_argument("--out", help="directory for guides and the report")
    ap.add_argument("--guide", action="append", default=[],
                    help="guide to build, e.g. mm-vma (repeatable; default all)")
    ap.add_argument("--min-relevance", type=int, default=None,
                    help="ask the questions at this relevance and up (default: the "
                    "question file's own '- min-relevance:' header, or 2)")
    ap.add_argument("--keep-answers", metavar="DIR",
                    help="after a build, also write each guide's final answers to "
                    "DIR/<guide>/<id>.md, so the guide can be rendered again later "
                    "without a model")
    ap.add_argument("--render-only", metavar="DIR",
                    help="run no model: render each guide from the answers kept in "
                    "DIR/<guide>/<id>.md and the verbatim files")
    ap.add_argument("--rounds", type=int, default=4,
                    help="after the sections are checked a reader goes through the whole "
                    "guide for accuracy alone and corrects it, and a checker verifies one "
                    "diff from the first checked version; they take turns until one changes "
                    "nothing, or this many rounds (default 4, 0 to skip)")
    ap.add_argument("--read-model",
                    help="model for the reader of the whole guide, if not --model")
    ap.add_argument("--check-model",
                    help="model for the checking phase, if not --model: an "
                    "independent reader of what the builder wrote")
    ap.add_argument("--selftest", action="store_true",
                    help="test the parser, the renderer and the rest without a model")
    ap.add_argument("--only", nargs="+", default=[], help="ask just these question ids")
    ap.add_argument("--questions", default=os.path.join(KERNEL_DIR, "subsystem", "questions"))
    ap.add_argument("--rev", default="HEAD", help="revision of --tree to snapshot")
    ap.add_argument("--snapshot", help="use this directory of plain files "
                    "instead of unpacking --rev")
    ap.add_argument("--work", help="scratch directory (default: a new one in /tmp)")
    ap.add_argument("--keep-work", action="store_true")
    ap.add_argument("--record", metavar="FILE",
                    help="after a build from sources, note in this YAML file which "
                    "kernel (base release and commit) the build was made from")
    ap.add_argument("--jobs", type=int, default=8, help="groups in flight")
    ap.add_argument("--checks", type=int, default=2,
                    help="how many times a group of answers may be checked against "
                    "the tree by an independent reader and corrected; a group is "
                    "checked again only if the last pass changed it (default 2, "
                    "0 to skip)")
    ap.add_argument("--group-questions", type=int, default=12,
                    help="most questions answered in one go; a section with more "
                    "is split into even parts (default 12)")
    ap.add_argument("--no-semcode", action="store_true",
                    help="do not give the model semcode even if it is available")
    ap.add_argument("--claude", default="claude", help="claude CLI to run")
    ap.add_argument("--model")
    ap.add_argument("--reader-model", action="append", default=[],
                    help="model whose memory is asked first, if not --model: a model "
                    "that will read the guide (repeatable; the answerer sees what "
                    "each of them said)")
    ap.add_argument("--no-memory-pass", action="store_true",
                    help="do not ask the reader models from memory first; the answerer "
                    "then has nothing to tell it what readers already know")
    ap.add_argument("--max-turns", type=int)
    ap.add_argument("--permission-mode",
                    help="permission mode to start the model process in, e.g. auto")
    ap.add_argument("--timeout", type=int, default=3600,
                    help="seconds a model run may take in all before it is stopped and tried "
                    "once more, with twice as long (default 3600)")
    ap.add_argument("--quiet", type=int, default=300,
                    help="seconds a model run may go without taking a step before it is "
                    "stopped and tried once more; 0 to go by --timeout alone (default 300)")
    ap.add_argument("--mcp-config", help="MCP servers to give the model, instead of "
                    "looking for semcode")
    ap.add_argument("--mcp-allow", default="mcp__semcode",
                    help="tool pattern to allow from --mcp-config")
    ap.add_argument("--pass-env", nargs="+", default=[],
                    help="extra environment variables to hand to the model process")
    ap.add_argument("--keep-home", action="store_true",
                    help="leave HOME alone (needed if credentials live in it)")
    ap.add_argument("--api-key-helper",
                    help="command that prints an API key; set as apiKeyHelper")
    ap.add_argument("--credentials",
                    help="stored login file to use instead of the one in your "
                    "agent configuration")
    ap.add_argument("--dry-run", action="store_true",
                    help="list the groups that would be asked and show one prompt; "
                    "run nothing")
    return ap


def main():
    ap = build_parser()
    opts = ap.parse_args()
    if opts.selftest:
        return selftest()
    if not opts.out:
        ap.error("--out is required")
    if opts.render_only:
        return render_only(opts)
    remember_models(opts)
    if not opts.tree and not opts.no_sources:
        ap.error("--tree is required unless --no-sources is given")
    if opts.check_memory and not (opts.no_sources and opts.tree):
        ap.error("--check-memory needs --no-sources and --tree")
    if opts.no_sources and opts.snapshot and not opts.check_memory:
        ap.error("--snapshot makes no sense with --no-sources")

    files = load(opts.questions, set(opts.guide))
    chosen = select(files, opts.min_relevance, set(opts.only))
    groups = {stem: make_groups(qs, opts.group_questions)
              for stem, qs in chosen.items()}
    total = sum(len(v) for v in chosen.values())
    log(f"{total} questions in {sum(len(g) for g in groups.values())} groups")
    if opts.dry_run:
        for stem, gs in groups.items():
            for g in gs:
                print(f"{stem}: {g['label']} ({len(g['questions'])} questions)")
                for q in g["questions"]:
                    print(f"    {q.relevance} {'check  ' if q.quick else 'section'} {q.id}")
        first = next((g for gs in groups.values() for g in gs), None)
        if first:
            print("\n--- what the model is given for the first group "
                  "(after the instructions) ---\n")
            print(ask_prompt(first, "guide", opts.no_sources).split("\n---\n", 1)[1])
        return 0
    copies = [stem for stem, (header, _) in files.items() if header.get("verbatim")]
    if not total and not copies:
        raise SystemExit("nothing to ask")

    out = os.path.abspath(opts.out)
    work = os.path.abspath(opts.work) if opts.work else tempfile.mkdtemp(prefix="build-guides-")
    for a, b in ((work, out), (work, REPO_ROOT)):
        if os.path.commonpath([a, b]) == b:
            raise SystemExit("the scratch directory must be outside --out and this repository")
    os.makedirs(os.path.join(out, "answers"), exist_ok=True)
    opts.unparsed_dir = os.path.join(out, "unparsed")
    opts.checked_dir = os.path.join(out, "checked")
    opts.differences_dir = os.path.join(out, "differences")
    opts.failed_dir = os.path.join(out, "failed-calls")
    os.makedirs(private_dir(work), exist_ok=True)
    version, semcode = "unknown", "off (no sources)"
    empty = os.path.join(work, "empty")         # nothing to read, on purpose
    os.makedirs(empty, exist_ok=True)
    has_tree = not opts.no_sources or opts.check_memory
    if not has_tree:
        cwd = empty
    else:
        cwd = os.path.abspath(opts.snapshot) if opts.snapshot else os.path.join(work, "tree")
        if opts.snapshot:
            bad = escaping_symlinks(cwd) + agent_config_in(cwd)
            if bad:
                raise SystemExit(
                    f"{cwd} has symlinks that lead outside it or agent instruction "
                    "files, either of which could steer the model or let it read "
                    "files it must not: " + ", ".join(bad[:10])
                    + "\nRemove them, or let the driver make its own snapshot.")
        else:
            make_snapshot(opts.tree, opts.rev, cwd)
        cwd = os.path.realpath(cwd)
        version = kernel_version(cwd)
    harness = ClaudeCLI(opts, work, read_denials(cwd, REPO_ROOT, out, private_dir(work)))
    if has_tree and not opts.mcp_config:
        path, semcode = find_semcode(opts, opts.tree, private_dir(work))
        if path:
            harness.mcp_config = path
            harness.mcp_allow = [f"mcp__semcode__{t}" for t in SEMCODE_TOOLS]
            semcode = "on, " + semcode
        log(f"semcode: {semcode}")
    elif opts.mcp_config:
        semcode = f"--mcp-config {opts.mcp_config}"
    runner = Runner(harness, cwd, opts, empty)
    answers, firsts = {}, {}

    def save(q, suffix=""):
        with open(os.path.join(out, "answers", q.id + suffix + ".md"), "w",
                  encoding="utf-8") as f:
            f.write(answers[q.id] + "\n")

    try:
        if total:                   # nothing to ask means no model to reach
            harness.preflight(cwd)
        title = {stem: files[stem][0].get("title", stem) for stem in files}
        jobs = [(stem, g) for stem, gs in groups.items() for g in gs]
        jobs.sort(key=lambda j: -len(j[1]["questions"]))      # the biggest groups first
        with cf.ThreadPoolExecutor(max(1, opts.jobs)) as ex:
            # 0. what do the readers already know? Asked with no tools at all.
            if has_tree and not opts.no_sources and not opts.no_memory_pass:
                readers = opts.reader_model or [opts.model]
                log(f"asking {len(readers)} reader model(s) from memory")
                # every reader and every group at once: they do not depend on each other
                # a question about what the readers get wrong is not one to put to them
                futures = {ex.submit(runner.memory_group, g, title[stem], who): (n, who)
                           for n, who in enumerate(readers) for stem, g in jobs
                           if not all(q.fields.get("drafts") == "all" for q in g["questions"])}
                got = {}
                for fut in cf.as_completed(futures):
                    n, who = futures[fut]
                    for qid, text in fut.result().items():
                        got[(qid, n)] = (who or "the default model", text)
                        name = f"{qid}.memory{n + 1 if len(readers) > 1 else ''}.md"
                        with open(os.path.join(out, "answers", name), "w",
                                  encoding="utf-8") as f:
                            f.write(f"<!-- from memory, no sources: "
                                    f"{who or 'the default model'} -->\n{text}\n")
                for (qid, n) in sorted(got):            # readers in the order given
                    runner.drafts.setdefault(qid, []).append(got[(qid, n)])
            # 1. answer every group
            log(f"answering {len(jobs)} groups")
            futures = {ex.submit(runner.answer_group, g, title[stem]): g for stem, g in jobs}
            for fut in cf.as_completed(futures):
                answers.update(fut.result())
                for q in futures[fut]["questions"]:
                    if q.id in answers:
                        firsts[q.id] = answers[q.id]
                        save(q)
                        save(q, ".first")
            for qs in chosen.values():
                for q in qs:
                    if q.is_verbatim:
                        # confined to kernel/subsystem/ by the parser; scrubbed like any text
                        answers[q.id] = scrub(q.verbatim_text(), harness.secrets)[0]
                        runner.note(q, f"inserted as it is from {os.path.relpath(q.verbatim, REPO_ROOT)}")
                        save(q)
            # 2. check every group, with the rest of its guide beside it
            todo = jobs if has_tree else []
            last_changes = {}           # what the previous pass changed, per group
            said = {}                   # and what it said, checking others, about this one
            for n in range(opts.checks):
                if not todo:
                    break
                log(f"checking {len(todo)} groups (pass {n + 1})")
                futures = {}
                for stem, g in todo:
                    by_id = {q.id: q for q in chosen[stem]}
                    # inserted text is not a model's to see or to "correct"
                    beside = {i: answers[i] for i in by_id
                              if i in answers and not by_id[i].is_verbatim}
                    futures[ex.submit(runner.check_group, g, title[stem], beside, by_id,
                                      last_changes.get(id(g)), said.get(id(g)),
                                      n == opts.checks - 1)] = (stem, g)
                todo, done, last_changes = [], [], {}
                for fut in cf.as_completed(futures):
                    fixed, changes = fut.result()
                    answers.update(fixed)
                    for q in futures[fut][1]["questions"]:
                        if q.id in fixed:
                            save(q)
                    done.append((futures[fut], changes))
                    if changes:
                        todo.append(futures[fut])     # changed: worth one more look
                        last_changes[id(futures[fut][1])] = changes
                # a group another check named, as having what it cut, is looked at again
                # too: it is the one that can tell whether the fact is still in the guide
                said = {}
                for stem, g in jobs:
                    about = notes_about(g, [(og, ch) for (ostem, og), ch in done
                                            if ostem == stem])
                    if about:
                        said[id(g)] = about
                        if not any(tg is g for _, tg in todo):
                            todo.append((stem, g))
        # 3. read each guide through whole, and check what that changes
        if has_tree and not opts.no_sources and opts.rounds > 0 and not opts.only:
            # what the last pass said about answers outside the group that said it:
            # there is no next section check to hear it
            unheard = {}
            for stem, g in jobs:
                for c in said.get(id(g), []):
                    if c not in unheard.setdefault(stem, []):
                        unheard[stem].append(c)
            for stem, qs in chosen.items():
                header, _ = files[stem]
                if header.get("verbatim") or not any(answers.get(q.id) for q in qs):
                    continue
                for loop in LOOPS:
                    log(f"{loop['doing']} {stem}"
                        + (f", with {len(unheard[stem])} notes from the section checks"
                           if loop is LOOPS[0] and unheard.get(stem) else ""))
                    for qid in runner.review(stem, header, qs, answers, title[stem], loop,
                                             unheard.get(stem) if loop is LOOPS[0] else None):
                        save(next(q for q in qs if q.id == qid))
        for qs in chosen.values():
            for q in qs:
                r = runner.row(q)
                r["got"] = len(answers.get(q.id, "").split())
                if r["checked"] and firsts.get(q.id):
                    same = difflib.SequenceMatcher(None, firsts[q.id].split(),
                                                   answers.get(q.id, "").split()).ratio()
                    r["rewritten"] = round(100 - same * 100)
                r["notes"] += problems_in(answers.get(q.id, ""))
        written = []
        for stem, qs in chosen.items():
            header, _ = files[stem]
            path = os.path.join(out, stem + ".md")
            with open(path, "w", encoding="utf-8") as f:
                if header.get("verbatim"):          # hand-maintained: copied as it is
                    f.write(scrub(read_verbatim(header["verbatim"]), harness.secrets)[0] + "\n")
                else:
                    f.write(render(header, stem, qs, answers,
                                   "checked" if opts.check_memory else opts.no_sources))
            written.append(path)
            log(f"{path}: {sum(1 for q in qs if answers.get(q.id))} of {len(qs)} answered")
        if opts.keep_answers:
            keep_answers(opts.keep_answers, chosen, answers)
        if opts.record and has_tree and not opts.no_sources:
            record_build(opts.record, kernel_base(cwd),
                         tree_sha(os.path.abspath(opts.tree), opts.rev))
            log(f"recorded the kernel in {opts.record}")
        write_report(os.path.join(out, "run-report.md"), opts, chosen, runner, version,
                     semcode)
        log(f"report: {os.path.join(out, 'run-report.md')}")
        if runner.not_run:
            # what is in the guide was not all asked, answered or checked: say so where
            # whatever installs the guide will find it
            with open(os.path.join(out, "incomplete.txt"), "w", encoding="utf-8") as f:
                f.write("\n".join(runner.not_run) + "\n")
            log(f"{len(runner.not_run)} stage(s) did not run: {os.path.join(out, 'incomplete.txt')}")
    finally:
        harness.finish()
        if not opts.keep_work:
            shutil.rmtree(private_dir(work), ignore_errors=True)
        if not opts.keep_work and not opts.work:
            shutil.rmtree(work, ignore_errors=True)
    return 1 if runner.not_run or any(not answers.get(q.id)
                                      for qs in chosen.values() for q in qs) else 0


if __name__ == "__main__":
    sys.exit(main())
