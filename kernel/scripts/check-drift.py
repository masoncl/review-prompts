#!/usr/bin/env python3
"""check-drift.py - report stale citations in the subsystem guides.

The guides under kernel/subsystem/ cite kernel paths, symbols, and commits.
The kernel moves, so a citation rots: a function is renamed, a file moves, a
symbol is removed. This checks the mechanically checkable citations in a guide
against a local kernel tree and prints each stale one, so the guides can be
kept current without a maintainer re-reading every reference by hand.

The kernel tree is reached through git plumbing (git cat-file, git grep,
git log) only, so the tree is never modified and any revision can be checked
(--rev, default the tree's HEAD). Diagnostics are one line each,
<guide>:<line>: <check>: <message>; a broken citation exits non-zero, an age
warning does not. See kernel/docs/drift-checker.md for the citation model and
the check/skip decisions.

Usage:
    check-drift.py --tree <linux> [--rev REV] [--all] [--require-footer]
                   [--stats] [--spec-index FILE] guide.md [guide.md ...]
    check-drift.py --selftest
"""

import argparse
import concurrent.futures as cf
import os
import re
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict, namedtuple
from datetime import date

# --------------------------------------------------------------------------
# Extraction: parse a guide into candidate citations.
#
# A citation is a backticked token in prose, a C identifier inside a fenced
# example, a >=12-hex commit SHA, or a backticked commit subject. Each is
# tagged with a class (C1 path, C2 symbol, C3 SHA, C3b subject, C5 spec ref)
# and a subclass; illustrative tokens (placeholders, literals, example locals)
# and non-citation prose are tagged so they can be counted but not checked.
# --------------------------------------------------------------------------

C_KEYWORDS = set("""auto break case char const continue default do double else enum extern
float for goto if inline int long register return short signed sizeof static struct switch
typedef union unsigned void volatile while bool true false NULL sizeof""".split())

# Identifiers that appear only as locals in the guides' worked examples.
SNIPPET_LOCALS = set("""val idx slots hva gfn err out cond flags local_args local_vcpu
host_args do_sve addr order size handle_hcall update_hyp_state""".split())

COMMIT_VERBS = ("Fix", "Add", "Only", "Make", "Correct", "Initialize",
                "Remove", "Introduce")

SRC_EXT = re.compile(r"\.(c|h|rst|awk|S|rs|py|txt|sh|sysreg)$")
SHA_RE = re.compile(r"^[0-9a-f]{12,40}$")
IDENT_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
FENCE_RE = re.compile(r"^\s*```")
SPAN_RE = re.compile(r"`([^`]+?)`", re.DOTALL)
NUM_RE = re.compile(r"0[xXbB][0-9A-Fa-f]+")
SPEC_SECTION = re.compile(r"\b[A-Z][0-9]+(?:\.[0-9]+)+\b")
ARM_CTX = re.compile(r"Arm ARM|ARM ARM|DDI\s*0487")
SPEC_ANCHOR = re.compile(r"DDI\s*0487|\bR_[A-Z]{5}\b")
SHA_IN_TEXT = re.compile(r"\b[0-9a-f]{12,40}\b")
META = re.compile(r"<[A-Za-z0-9_|,.]+>")             # <REG>, <cc>, <n>, <0|1>
BRACE_EXPANSION = re.compile(r"\{[^}]*[,|][^}]*\}")   # {0,1}, {I,F}
MD_REF = re.compile(r"^[A-Za-z0-9._-]+\.md$")         # guide-internal reference

# The kernel tree's top-level directories. An extensionless slashed token is a
# real path only under one of these; a bare `foo/end` or `gpio/` is not.
KNOWN_TOPDIRS = {"arch", "block", "certs", "crypto", "drivers", "Documentation",
                 "fs", "include", "init", "io_uring", "ipc", "kernel", "lib",
                 "mm", "net", "rust", "samples", "scripts", "security", "sound",
                 "tools", "usr", "virt"}

Cite = namedtuple("Cite", "guide line cls sub token raw in_fence")


def is_repo_internal(s):
    """A reference into the review-prompts repo (a sibling guide, an agent
    prompt, a repo-relative path), which is verified against that repo, not the
    kernel tree. A bare `.md` extension is a file-type reference, not a target."""
    return (bool(re.search(r"[A-Za-z0-9_-]\.md$", s))
            or s.startswith("../")
            or s.startswith("review-prompts/"))


def is_commit_subject(c):
    s = c.strip()
    if re.match(r"^(KVM|arm64|kvm-arm64|hyp-arm64)\b.*:\s", s):
        return True
    w = s.split()
    if (len(w) >= 4 and s[0].isupper() and w[0] in COMMIT_VERBS
            and not re.search(r"[;{}=]|&&|\|\||->|==", s)):
        return True
    return False


def is_path(c):
    s = c.strip()
    if s.startswith("<") or " " in s or s.startswith("http"):
        return False
    if s.startswith("/"):                             # absolute runtime path (/proc, /sys, /dev)
        return False
    if s.endswith("/"):                               # directory
        body = s.rstrip("/")
        return "/" in body or body in KNOWN_TOPDIRS
    if SRC_EXT.search(s):
        return True
    if "/" in s and re.search(r"/[a-z][a-z0-9_.-]*$", s):
        return s.split("/", 1)[0] in KNOWN_TOPDIRS    # extensionless path only under a real top dir
    return False


def looks_placeholder(c):
    return ("<" in c and ">" in c) or "..." in c or "…" in c


def register_field_shape(t):
    return bool(re.search(r"_EL[012x]\b", t) or re.match(r"^[A-Z][A-Z0-9]*_EL[012x]", t))


def macro_shape(t):
    return bool(re.match(r"^[A-Z_][A-Z0-9_]{2,}$", t))


def code_snippet(c):
    return bool(re.search(r"[;{}]|==|&&|\|\||\breturn\b|\bgoto\b|\bif\b\s*\(", c))


def pattern_token(s, start, end):
    """True when the token at [start:end] in s is a wildcard/metavariable pattern
    rather than a citation, decided by ADJACENCY only: an immediately-following
    glob '*' or brace-expansion, or enclosure in a <...> metavariable group. A
    leading pointer '*', a block brace elsewhere on the line, or a comparison
    operator does NOT make the token a pattern."""
    after = s[end:end + 1]
    before = s[start - 1:start]
    if after == "*":                                      # ID_AA64*, fpsimd_..._*
        return True
    if after == "<" and META.match(s[end:]):              # CB<cc>, GICD_ICENABLER<n>
        return True
    if after == "{" and BRACE_EXPANSION.match(s[end:]):   # ICC_IAR{0,1}
        return True
    if before == "}":                                     # copy_{from,to}_user
        return True
    for mm in META.finditer(s):                           # token inside <...>
        if mm.start() <= start and end <= mm.end():
            return True
    return False


class Extractor:
    """Collects the citations of one guide into self.rows."""

    def __init__(self, guide):
        self.guide = guide
        self.rows = []

    def add(self, ln, cls, sub, tok, raw, fence):
        self.rows.append(Cite(self.guide, ln, cls, sub, tok, raw, fence))

    def classify_ident(self, lineno, t, c, m, snip):
        if pattern_token(c, m.start(), m.end()):
            self.add(lineno, "illustrative", "placeholder", t, c, False)
            return
        if m.start() > 0 and c[m.start() - 1].isdigit():   # tail of a digit-led name (8250_dwlib)
            self.add(lineno, "illustrative", "fragment", t, c, False)
            return
        if t.startswith("CONFIG_"):
            self.add(lineno, "C2", "config", t, c, False)
        elif t.startswith("FEAT_"):
            self.add(lineno, "C5", "spec-feature", t, c, False)
        elif register_field_shape(t):
            self.add(lineno, "C2", "register-or-field", t, c, False)
        elif macro_shape(t):
            self.add(lineno, "C2", "macro", t, c, False)
        elif snip and t in SNIPPET_LOCALS:
            self.add(lineno, "illustrative", "snippet-local", t, c, False)
        elif (t + "()") in c.replace(" ", ""):
            self.add(lineno, "C2", "function", t, c, False)
        elif t[0].islower():
            self.add(lineno, "C2", "function-or-type", t, c, False)
        else:
            self.add(lineno, "C2", "type-or-const", t, c, False)

    def process_span(self, lineno, c):
        if is_commit_subject(c):
            self.add(lineno, "C3b", "commit-subject", c.strip(), c, False)
            return
        s = c.strip()
        if is_repo_internal(s):                       # sibling guide / agent prompt / repo path
            self.add(lineno, "C1", "repo-internal", s, c, False)
            return
        if s.startswith("/"):                         # absolute runtime path, not a source citation
            self.add(lineno, "illustrative", "abs-path", s, c, False)
            return
        if "/" in s and (re.search(r"[*,]", s) or "->" in s):   # glob / enumeration path
            self.add(lineno, "illustrative", "pattern-path", s, c, False)
            return
        if is_path(c):
            s = c.strip()
            if s.endswith("/"):
                sub = "dir"
            elif "/" in s:
                sub = "exact" if s.startswith(("arch/", "Documentation/", "include/",
                      "kernel/", "drivers/", "mm/", "fs/", "tools/", "virt/")) else "fragment"
            else:
                sub = "basename"
            self.add(lineno, "C1", sub, s, c, False)
            return
        if SHA_RE.match(c.strip()):
            self.add(lineno, "C3", "sha", c.strip(), c, False)
            return
        if looks_placeholder(c):
            self.add(lineno, "illustrative", "placeholder", c.strip(), c, False)
            return
        snip = code_snippet(c)
        num_spans = [(m.start(), m.end()) for m in NUM_RE.finditer(c)]
        for a, b in num_spans:
            self.add(lineno, "illustrative", "numeric-literal", c[a:b], c, False)
        idents = [m for m in IDENT_RE.finditer(c)
                  if m.group(0) not in C_KEYWORDS
                  and not any(a <= m.start() < b for a, b in num_spans)]
        if not idents:
            if not num_spans:
                self.add(lineno, "other", "no-ident", c.strip(), c, False)
            return
        for m in idents:
            self.classify_ident(lineno, m.group(0), c, m, snip)


def extract_citations(text_lines, guide):
    """Return the citations of one guide (already split into lines)."""
    ex = Extractor(guide)

    # Prose backtick spans: mask fenced-code lines to blanks so a code fence
    # never reads as prose, preserving line numbers, then scan spans (which may
    # wrap across single newlines) over the masked stream.
    in_fence = False
    prose = []
    for ln in text_lines:
        if FENCE_RE.match(ln):
            in_fence = not in_fence
            prose.append("")
        elif in_fence:
            prose.append("")
        else:
            prose.append(ln)
    text = "\n".join(prose)
    starts = [0]
    for ln in prose:
        starts.append(starts[-1] + len(ln) + 1)

    def lineno_of(off):
        import bisect
        return bisect.bisect_right(starts, off)

    for m in SPAN_RE.finditer(text):
        c = m.group(1)
        if "\n\n" in c:
            continue
        c = re.sub(r"\s+", " ", c).strip()
        ex.process_span(lineno_of(m.start()), c)

    # Fenced-code identifiers and in-fence SHAs, plus spec references in prose.
    in_fence = False
    for lineno, ln in enumerate(text_lines, 1):
        if FENCE_RE.match(ln):
            in_fence = not in_fence
            continue
        if in_fence:
            ln_code = re.sub(r"/\*.*?\*/", "", ln)      # comment words are not citations
            ln_code = re.sub(r"//.*", "", ln_code)
            num_spans = [(m.start(), m.end()) for m in NUM_RE.finditer(ln_code)]
            for mm in IDENT_RE.finditer(ln_code):
                t = mm.group(0)
                if t in C_KEYWORDS:
                    continue
                if any(a <= mm.start() < b for a, b in num_spans):
                    continue
                if pattern_token(ln_code, mm.start(), mm.end()):
                    ex.add(lineno, "illustrative", "placeholder", t, ln.strip(), True)
                    continue
                if mm.start() > 0 and ln_code[mm.start() - 1].isdigit():
                    ex.add(lineno, "illustrative", "fragment", t, ln.strip(), True)
                    continue
                sub = "in-fence-local" if t in SNIPPET_LOCALS else "in-fence"
                ex.add(lineno, "C2", sub, t, ln.strip(), True)
            for mm in SHA_IN_TEXT.finditer(ln):
                ex.add(lineno, "C3", "sha-in-fence", mm.group(0), ln.strip(), True)
            continue
        if ARM_CTX.search(ln):
            for mm in SPEC_SECTION.finditer(ln):
                ex.add(lineno, "C5", "spec-section", mm.group(0), ln.strip(), False)
        for mm in SPEC_ANCHOR.finditer(ln):
            ex.add(lineno, "C5", "spec-anchor", mm.group(0), ln.strip(), False)
    return ex.rows


# --------------------------------------------------------------------------
# Decision: which citations are checked, and which are skipped.
#
# The bar for a check is near-zero false positives and real power: a check
# that cannot fail because its token is everywhere adds nothing. So only
# specific, kernel-namespaced citations are checked; architectural names,
# placeholders, and generic tokens are skipped. A token occurring more than
# GENERIC_THRESHOLD times cannot meaningfully fail an existence check.
# --------------------------------------------------------------------------

GENERIC_THRESHOLD = 100

# Identifiers that appear only in worked examples and would otherwise read as
# checkable symbols.
EXAMPLE_LOCALS = {"captured_seq", "do_sve", "handle_hcall", "host_args", "local_args",
                  "local_vcpu", "update_hyp_state", "vcpu_reset_args", "VALID_FLAG"}
# Author shorthand for a longer symbol, and metavariables/concept labels.
SKIP_SHORTHAND = {"MIN_PKVM", "PKVM_ONLY",   # __KVM_HOST_SMCCC_FUNC_MIN_PKVM etc.
                  "VNCR_r",                  # VNCR(r) = __VNCR_START__ + VNCR_r/8
                  "hyp_fixmap"}              # concept label; hyp_fixmap_map/_unmap are real
SKIP_EXPLICIT = EXAMPLE_LOCALS | SKIP_SHORTHAND
# Lowercase ISA / lock mnemonics cited in prose, not kernel symbols.
SPEC_MNEMONIC = {"BnA", "DnI", "ERETA", "RVAE1IS", "S12E1R", "TBIDn",
                 "TBNZ", "TBZ", "TRCIT", "eret", "irqsave"}
# A bare file-type reference (`*.c`, `.sysreg`), not a specific path citation.
TYPEREF_RE = re.compile(r"^\*?\.[a-z0-9]+$")
# Metasyntactic placeholder components used in worked examples across the guides
# (`my_free`, `foo_pm_ops`, `alloc_thing`, `SOME_SUBSYSTEM`). A conventional
# stand-in, never a real kernel symbol.
METASYNTACTIC = {"foo", "bar", "baz", "qux", "quux", "my", "some", "thing",
                 "things", "wrapper", "dummy", "example", "frob", "blah", "mine"}
# The guide names an absent symbol precisely to document its removal.
REMOVED_WORD = re.compile(r"\b(removed|renamed|replaced|deleted|gone)\b")


def is_metasyntactic(tok):
    return any(part.lower() in METASYNTACTIC for part in tok.split("_"))


def documents_removal(context, tok):
    """True when the guide's own sentence says this token is gone, so flagging
    it as undefined would be reporting a removal the author is documenting on
    purpose (only ever consulted for an already-absent token). The removal word
    must take the token as its subject (`X is removed`, `X ... have been
    removed`), not merely appear nearby: `add_to_swap() ... remains until
    explicitly removed` describes the folio, not the function."""
    esc = re.escape(tok)
    context = context.replace("`", " ")               # markdown emphasis is not prose
    return bool(re.search(esc + r"[\s,()]*(\w+[,]?\s+){0,6}"
                          r"(is|are|was|were|has been|have been|been)\s+"
                          + REMOVED_WORD.pattern, context)
                or re.search(r"\b(is|are) no\b[^.]{0,45}" + esc, context)
                or re.search(r"\bno (function|symbol|macro|helper|field|member|such)"
                             r"[^.]{0,45}" + esc, context)
                or re.search(esc + r"[^.]{0,45}no longer\b", context))


def is_typeref(tok):
    return bool(TYPEREF_RE.match(tok))


def kernel_namespaced(tok):
    """A checkable kernel symbol carries an underscore (kvm_id_reg_rw_mask,
    ESR_ELx_IL, CONFIG_BUG) or is a lowercase identifier of four or more chars
    (memcpy, finalize_pkvm). Anything else, all-caps or mixed-case with no
    underscore, is an ARM ISA mnemonic, a register abbreviation, or a prose
    word, and is left to prose review."""
    if "_" in tok:
        return True
    return tok[0].islower() and len(tok) >= 4


# --------------------------------------------------------------------------
# Kernel tree: rev-parameterized git plumbing.
# --------------------------------------------------------------------------

CORPUS_EXCLUDE = ":(exclude)Documentation/"


class KernelTree:
    """Read-only access to a kernel tree through git plumbing.

    Symbol lookups grep the working tree when --rev is the tree's own HEAD
    (git keeps the files uncompressed on disk, so a fixed-string grep is fast),
    and grep at the revision otherwise (correct for any release, but slower
    because git decompresses tree objects on each query)."""

    def __init__(self, path, rev="HEAD", jobs=12):
        self.path = path
        self.jobs = jobs
        self.rev = self._rev_parse(rev)
        self.head = self._rev_parse("HEAD")
        self.at_head = self.rev == self.head
        self.shallow = (self._git(["rev-parse", "--is-shallow-repository"])
                        .stdout.strip() == "true")
        self._files = None

    def _git(self, args, check=False):
        r = subprocess.run(["git", "-C", self.path] + args,
                           capture_output=True, encoding="utf-8", errors="replace")
        if check and r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()}")
        return r

    def _rev_parse(self, rev):
        r = self._git(["rev-parse", "--verify", "-q", f"{rev}^{{commit}}"])
        if r.returncode != 0:
            raise SystemExit(f"check-drift.py: cannot resolve rev '{rev}' in {self.path}")
        return r.stdout.strip()

    def files(self):
        """The set of tracked paths at the revision."""
        if self._files is None:
            out = self._git(["ls-tree", "-r", "--name-only", self.rev], check=True).stdout
            self._files = set(out.splitlines())
        return self._files

    def resolve_path(self, token):
        """(count, kind) for a path: exact, else directory, else unique suffix.
        kind is 'exact', 'dir', 'suffix', or 'none'; count is the match count."""
        s = token[2:] if token.startswith("./") else token
        files = self.files()
        if s in files:
            return 1, "exact"
        prefix = s.rstrip("/") + "/"                  # directory, with or without a slash
        if any(f.startswith(prefix) for f in files):
            return 1, "dir"
        n = sum(1 for f in files if f == s or f.endswith("/" + s))
        return n, ("suffix" if n else "none")

    def symbol_counts(self, tokens):
        """Map each token to its whole-word match-line count in the corpus
        (the source tree with Documentation/ excluded), probed in parallel."""
        def probe(tok):
            args = ["grep", "-F", "-w", "-I", "-c", "-e", tok]
            if not self.at_head:
                args.append(self.rev)
            args += ["--", CORPUS_EXCLUDE]
            r = self._git(args)
            total = 0
            for line in r.stdout.splitlines():
                m = re.search(r":(\d+)$", line)
                if m:
                    total += int(m.group(1))
            return tok, total
        with cf.ThreadPoolExecutor(max_workers=self.jobs) as ex:
            return dict(ex.map(probe, tokens))

    def commit_exists(self, sha):
        return self._git(["cat-file", "-e", f"{sha}^{{commit}}"]).returncode == 0

    def commit_subject(self, sha):
        return self._git(["log", "-1", "--format=%s", sha]).stdout.strip()

    def subject_count(self, subject):
        """Commits in --rev's history whose SUBJECT contains the string. --grep
        (a whole-message match) is a cheap prefilter; the subject-only filter
        keeps a citation from validating against an unrelated commit's body."""
        r = self._git(["log", "--fixed-strings", f"--grep={subject}",
                       "--format=%s", self.rev])
        return sum(1 for s in r.stdout.splitlines() if subject in s)

    def is_ancestor(self, older, newer):
        return self._git(["merge-base", "--is-ancestor", older, newer]).returncode == 0


# --------------------------------------------------------------------------
# Verification footer (C4).
# --------------------------------------------------------------------------

FOOTER_MARKER = re.compile(r"<!--\s*drift-checked:")
FOOTER_RE = re.compile(
    r"<!--\s*drift-checked:\s*rev=([0-9a-fA-F]{12,40})\s+date=(\d{4}-\d{2}-\d{2})\s*-->")


def parse_footer(text_lines):
    """(rev, date, status, line) where status is 'ok' (valid footer), 'malformed'
    (a drift-checked marker that does not parse), or 'absent'. line is the footer's
    1-based line number, or 1 when absent."""
    for idx in range(len(text_lines) - 1, -1, -1):
        ln = text_lines[idx]
        if not ln.strip():
            continue
        m = FOOTER_RE.search(ln)
        if m:
            return m.group(1), m.group(2), "ok", idx + 1
        if FOOTER_MARKER.search(ln):
            return None, None, "malformed", idx + 1
        break
    return None, None, "absent", 1


# --------------------------------------------------------------------------
# Checking a guide.
# --------------------------------------------------------------------------

Finding = namedtuple("Finding", "guide line check level message")


def paragraph_of(text_lines):
    """Map 1-based line number to a paragraph id (blank-line separated)."""
    out = {}
    pid = 0
    prev_blank = True
    for i, ln in enumerate(text_lines, 1):
        if not ln.strip():
            prev_blank = True
            continue
        if prev_blank:
            pid += 1
        prev_blank = False
        out[i] = pid
    return out


def decide(cite, sym_hit, path_res, shallow=False):
    """(decision, reason) for one citation. decision is 'check', 'skip', or
    'ignore'; reason is a short tag, with reasons starting 'DRIFT' / 'gone' /
    'ambiguous' marking a finding. On a shallow tree the commit-history checks
    (C3, C3b) are skipped: their git plumbing needs history the tree omits, and
    a missing object would otherwise read as a broken citation."""
    cls, sub, tok = cite.cls, cite.sub, cite.token
    if cls == "C1":
        if sub == "repo-internal":               # verified against the prompts repo, not the kernel
            return "check", "repo-ref"
        if is_typeref(tok):
            return "skip", "path-typeref"
        n, kind = path_res[tok]
        if n == 0:
            return "check", "gone-path"
        if kind == "suffix" and n > 1:
            if "/" not in tok:                   # a bare basename matching several files still exists
                return "skip", "ambiguous-basename"
            return "check", "ambiguous-path"
        return "check", "resolves"
    if cls == "C3":
        if sub == "sha-in-fence":
            return "ignore", "example-sha"
        return ("skip", "shallow-history") if shallow else ("check", "sha")
    if cls == "C3b":
        return ("skip", "shallow-history") if shallow else ("check", "subject")
    if cls == "C5":
        return "ignore", "spec"
    if cls == "illustrative":
        return "ignore", sub
    if cls == "other":
        return "ignore", "no-ident"
    # C2 symbol.
    hit = sym_hit.get(tok, 0)
    if tok in SKIP_EXPLICIT or sub in ("in-fence-local", "snippet-local"):
        return "skip", "example"
    if sub == "register-or-field" or tok in SPEC_MNEMONIC:
        return "skip", "spec-arch"
    if not kernel_namespaced(tok):
        return "skip", "spec-arch"
    if hit == 0 and re.search(r"_EL[012x]", tok):
        return "skip", "spec-arch"               # architectural register name
    if hit >= GENERIC_THRESHOLD:
        return "skip", "generic"
    if hit > 0:
        return "check", "resolves"
    # hit == 0 would be a DRIFT finding; a resolving token is real, so these
    # false-positive shapes are only suppressed here, never for a live symbol.
    if re.match(r"^_[^_]", tok) or re.search(r"[^_]_$", tok):
        return "skip", "fragment"                # prefix/suffix stub: _scoped, QCM_, _WRITE
    if re.fullmatch(r"[a-z0-9_]*[NX][a-z0-9_]*", tok) and re.search(r"[a-z][NX]", tok):
        return "skip", "metavar"                 # family placeholder: __raw_readN, pXd_mkspecial
    if is_metasyntactic(tok):
        return "skip", "example"                 # metasyntactic stand-in: foo_pm_ops, alloc_thing
    return "check", "DRIFT"


def paired_path(cite, same_line_paths, para_paths, line_para):
    """The single path cited alongside a symbol (same line, else the sole path
    in its paragraph), or None."""
    on_line = same_line_paths.get(cite.line)
    if on_line and len(on_line) == 1:
        return next(iter(on_line))
    pp = line_para.get(cite.line)
    inpara = para_paths.get(pp) if pp else None
    if inpara and len(inpara) == 1:
        return next(iter(inpara))
    return None


def check_guide(tree, path, text_lines, cites, sym_hit, opts, repo_files=frozenset()):
    """Findings for one guide whose citations are being checked."""
    guide = os.path.basename(path)
    findings = []
    stats = Counter()

    path_res = {}
    for c in cites:
        if c.cls == "C1" and c.sub != "repo-internal" and not is_typeref(c.token):
            path_res[c.token] = tree.resolve_path(c.token)

    # Symbol<->path pairing, used only to name the cited file in a finding.
    line_para = paragraph_of(text_lines)
    same_line_paths = defaultdict(set)
    para_paths = defaultdict(set)
    for c in cites:
        if c.cls != "C1" or c.sub == "repo-internal":
            continue
        decision, reason = decide(c, sym_hit, path_res, tree.shallow)
        if decision == "check" and not reason.startswith(("gone", "ambiguous")):
            same_line_paths[c.line].add(c.token)
            pp = line_para.get(c.line)
            if pp:
                para_paths[pp].add(c.token)

    for c in cites:
        decision, reason = decide(c, sym_hit, path_res, tree.shallow)
        stats[(c.cls, decision)] += 1
        if decision != "check":
            continue
        if c.cls == "C1":
            if reason == "repo-ref":
                if not repo_resolves(c.token, repo_files):
                    findings.append(Finding(guide, c.line, "C1", "error",
                                            f"unresolved guide reference '{c.token}'"))
            elif reason == "gone-path":
                findings.append(Finding(guide, c.line, "C1", "error",
                                        f"undefined path '{c.token}'"))
            elif reason == "ambiguous-path":
                findings.append(Finding(guide, c.line, "C1", "error",
                                        f"ambiguous path fragment '{c.token}' "
                                        f"({path_res[c.token][0]} matches)"))
        elif c.cls == "C2":
            if reason == "DRIFT":
                if documents_removal(paragraph_text(text_lines, c.line), c.token):
                    stats[(c.cls, "check")] -= 1     # the guide documents this removal on purpose
                    stats[(c.cls, "skip")] += 1
                    continue
                near = paired_path(c, same_line_paths, para_paths, line_para)
                msg = f"undefined symbol '{c.token}'"
                if near:
                    msg += f" (cited near {near})"
                findings.append(Finding(guide, c.line, "C2", "error", msg))
        elif c.cls == "C3":
            if not tree.commit_exists(c.token):
                findings.append(Finding(guide, c.line, "C3", "error",
                                        f"unknown commit {c.token}"))
            elif not tree.is_ancestor(c.token, tree.rev):
                findings.append(Finding(guide, c.line, "C3", "error",
                                        f"commit {c.token} not in history of "
                                        f"{tree.rev[:12]}"))
            else:
                quoted = adjacent_subject(paragraph_text(text_lines, c.line), c.token)
                if quoted:
                    have = tree.commit_subject(c.token)
                    if have != quoted:
                        findings.append(Finding(guide, c.line, "C3", "error",
                                        f"commit {c.token} subject changed: "
                                        f'guide "{quoted}" tree "{have}"'))
        elif c.cls == "C3b":
            if tree.subject_count(c.token) == 0:
                findings.append(Finding(guide, c.line, "C3", "error",
                                        f'no commit matches subject "{c.token}"'))
    return findings, stats


def adjacent_subject(context, sha):
    """The quoted subject in the immediately-adjacent `<sha> ("subject")`
    idiom, else None. The guides also quote commit bodies further along the
    sentence, so the parenthesised quote must follow the sha directly (only a
    closing backtick and spaces between)."""
    m = re.search(re.escape(sha) + r'[`\s]*\(\s*"([^"]+)"', context)
    return m.group(1) if m else None


def paragraph_text(text_lines, lineno):
    """The blank-line-delimited paragraph containing a 1-based line, joined and
    whitespace-collapsed, so a citation that wraps across lines reads as one."""
    lo = hi = lineno - 1
    while lo > 0 and text_lines[lo - 1].strip():
        lo -= 1
    while hi + 1 < len(text_lines) and text_lines[hi + 1].strip():
        hi += 1
    return re.sub(r"\s+", " ", " ".join(text_lines[lo:hi + 1]))


def check_footer(tree, guide, text_lines, opts):
    """Footer findings and whether the guide's citations should be checked."""
    findings = []
    rev, fdate, status, fline = parse_footer(text_lines)
    if status == "ok":
        if not tree.shallow:                          # ancestry needs history
            if not tree.commit_exists(rev):
                findings.append(Finding(guide, fline, "C4", "error",
                                        f"footer rev {rev} does not resolve"))
            elif not tree.is_ancestor(rev, tree.rev):
                findings.append(Finding(guide, fline, "C4", "error",
                                        f"footer rev {rev} is not an ancestor of "
                                        f"{tree.rev[:12]}"))
        try:
            age = (date.today() - date.fromisoformat(fdate)).days
            if age > 90:
                findings.append(Finding(guide, fline, "C4", "warn",
                                        f"footer dated {fdate} is {age} days old"))
        except ValueError:
            findings.append(Finding(guide, fline, "C4", "error",
                                    f"footer date '{fdate}' is not YYYY-MM-DD"))
        return findings, True
    if status == "malformed":
        findings.append(Finding(guide, fline, "C4", "error",
                                "malformed drift-checked footer"))
        return findings, opts.all
    # absent
    if opts.require_footer:
        findings.append(Finding(guide, 1, "C4", "error", "no drift-checked footer"))
        return findings, False
    if opts.all:
        return findings, True
    findings.append(Finding(guide, 1, "C4", "info",
                            "not onboarded (no drift-checked footer); skipped"))
    return findings, False


def load_spec_index(path):
    if not path:
        return None
    with open(path) as f:
        return {ln.strip() for ln in f if ln.strip() and not ln.startswith("#")}


def repo_file_set(guide_path):
    """The set of files in the prompts repo containing the guide, for resolving
    repo-internal references. Uses git if the guide is tracked, else walks the
    enclosing tree."""
    d = os.path.dirname(os.path.abspath(guide_path)) or "."
    r = subprocess.run(["git", "-C", d, "rev-parse", "--show-toplevel"],
                       capture_output=True, encoding="utf-8", errors="replace")
    if r.returncode == 0:
        root = r.stdout.strip()
        files = subprocess.run(["git", "-C", root, "ls-files"],
                               capture_output=True, encoding="utf-8", errors="replace").stdout
        return set(files.splitlines())
    out = set()                                       # untracked guide: walk its own directory
    for base, _, names in os.walk(d):
        rel = os.path.relpath(base, d)
        for n in names:
            out.add(n if rel == "." else os.path.join(rel, n))
    return out


def repo_resolves(token, repo_files):
    """A repo-internal reference resolves if the prompts repo has a matching
    file (exact, or a unique-enough basename/suffix), or a directory for a
    trailing-slash reference."""
    s = token.lstrip("./")
    while s.startswith("../"):
        s = s[3:]
    if s.startswith("review-prompts/"):
        s = s[len("review-prompts/"):]
    if s.endswith("/"):
        pre = s.rstrip("/") + "/"
        return any(("/" + f).endswith("/" + pre[:-1] + "/") or f.startswith(pre)
                   for f in repo_files)
    return any(f == s or f.endswith("/" + s) for f in repo_files)


def run(tree, guides, opts):
    """Check every guide; return (findings, stats). Symbol lookups for all
    guides are batched into one probe pass."""
    per_guide = []
    footer_findings = []
    spec_index = load_spec_index(opts.spec_index)
    repo_files = repo_file_set(guides[0]) if guides else frozenset()
    for path in guides:
        guide = os.path.basename(path)
        with open(path, encoding="utf-8") as f:
            lines = f.read().splitlines()
        ff, do_check = check_footer(tree, guide, lines, opts)
        footer_findings += ff
        if do_check:
            per_guide.append((path, lines, extract_citations(lines, guide)))

    sym_tokens = sorted({c.token for _, _, cites in per_guide
                         for c in cites if c.cls == "C2"})
    sym_hit = tree.symbol_counts(sym_tokens) if sym_tokens else {}

    findings = list(footer_findings)
    stats = Counter()
    for path, lines, cites in per_guide:
        gf, gs = check_guide(tree, path, lines, cites, sym_hit, opts, repo_files)
        findings += gf
        stats += gs
        if spec_index is not None:
            guide = os.path.basename(path)
            for c in cites:
                if c.cls == "C5" and c.token not in spec_index:
                    findings.append(Finding(guide, c.line, "C5", "warn",
                                    f"unknown spec reference '{c.token}'"))
    return findings, stats


# --------------------------------------------------------------------------
# Reporting.
# --------------------------------------------------------------------------

def report(findings, stats, opts):
    errors = 0
    for f in sorted(findings, key=lambda f: (f.level != "error", f.guide, f.line)):
        line = f"{f.guide}:{f.line}: {f.check}: {f.message}"
        if f.level == "error":
            errors += 1
            print(line)
        elif f.level == "warn":
            print(f"{f.guide}:{f.line}: {f.check}: warning: {f.message}")
        else:
            print(line, file=sys.stderr)
    if opts.stats:
        print_stats(stats)
    return errors


def print_stats(stats):
    classes = ["C1", "C2", "C3", "C3b", "C5", "illustrative", "other"]
    checked = Counter()
    skipped = Counter()
    ignored = Counter()
    for (cls, decision), n in stats.items():
        {"check": checked, "skip": skipped, "ignore": ignored}[decision][cls] += n
    print(f"\n  {'citations':13}{'checked':>8}{'skipped':>9}{'ignored':>9}",
          file=sys.stderr)
    for cls in classes:
        if checked[cls] or skipped[cls] or ignored[cls]:
            print(f"  {cls:13}{checked[cls]:>8}{skipped[cls]:>9}{ignored[cls]:>9}",
                  file=sys.stderr)
    print(f"  {'total':13}{sum(checked.values()):>8}{sum(skipped.values()):>9}"
          f"{sum(ignored.values()):>9}", file=sys.stderr)


# --------------------------------------------------------------------------
# Self-test: build a tiny kernel-shaped repo in a tempdir and exercise each
# check's pass and fail path, so the checker is testable without a kernel tree.
# --------------------------------------------------------------------------

def selftest():
    Opts = namedtuple("Opts", "all require_footer stats spec_index")

    with tempfile.TemporaryDirectory() as d:
        repo = os.path.join(d, "linux")
        os.makedirs(os.path.join(repo, "mm"))
        os.makedirs(os.path.join(repo, "Documentation"))
        with open(os.path.join(repo, "mm", "good.c"), "w") as f:
            f.write("int live_helper(void) { return 0; }\n"
                    "struct memslot_map { int member; };\n")
        with open(os.path.join(repo, "mm", "other.c"), "w") as f:
            f.write("void unrelated(void) {}\n")
        os.makedirs(os.path.join(repo, "net"))
        with open(os.path.join(repo, "mm", "shared.c"), "w") as f:
            f.write("void mm_fn(void) {}\n")
        with open(os.path.join(repo, "net", "shared.c"), "w") as f:
            f.write("void net_fn(void) {}\n")
        with open(os.path.join(repo, "Documentation", "note.rst"), "w") as f:
            f.write("The doc_only_symbol lives only here.\n")
        env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t",
                   GIT_COMMITTER_NAME="t", GIT_COMMITTER_EMAIL="t@t")
        for args in (["init", "-q"], ["add", "-A"],
                     ["commit", "-q", "-m", "kvm: add live_helper for the memslot map"]):
            subprocess.run(["git", "-C", repo] + args, check=True, env=env)
        sha = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"],
                             capture_output=True, text=True).stdout.strip()
        # A later commit whose body mentions a commit-subject-shaped phrase absent
        # from its own subject: exercises the C3b subject-only match, and being
        # outside the first commit's history, the C3 ancestry scope.
        subprocess.run(["git", "-C", repo, "commit", "-q", "--allow-empty",
                        "-m", "KVM: arm64: real subject present\n\n"
                        "Body text mentions KVM: arm64: body-only phrase here."],
                       check=True, env=env)
        sha2 = subprocess.run(["git", "-C", repo, "rev-parse", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
        tree = KernelTree(repo)
        tree_old = KernelTree(repo, rev=sha)
        opts = Opts(all=True, require_footer=False, stats=False, spec_index=None)

        def findings_for(body):
            gp = os.path.join(d, "guide.md")
            with open(gp, "w") as fh:
                fh.write(body)
            found, _ = run(tree, [gp], opts)
            return {(x.check, x.level, x.message) for x in found}

        checks = []

        def want(name, got, must_have, must_not):
            ok = all(m in got for m in must_have) and all(m not in got for m in must_not)
            checks.append((name, ok, got))

        # C1: valid exact path, valid suffix fragment, and a gone path.
        got = findings_for("`mm/good.c` and `good.c` exist, `mm/gone.c` does not.\n")
        want("C1 gone", got,
             [("C1", "error", "undefined path 'mm/gone.c'")],
             [("C1", "error", "undefined path 'mm/good.c'"),
              ("C1", "error", "undefined path 'good.c'")])

        # C2: a live symbol resolves, a vanished one is a finding, a symbol that
        # survives only under Documentation/ is a finding (corpus excludes it).
        got = findings_for("`live_helper` is fine, `vanished_helper` is called here, "
                           "`doc_only_symbol` appears in docs.\n")
        want("C2 gone", got,
             [("C2", "error", "undefined symbol 'vanished_helper'"),
              ("C2", "error", "undefined symbol 'doc_only_symbol'")],
             [("C2", "error", "undefined symbol 'live_helper'")])

        # Parser generalizations (F4): each FP class the repo-wide sweep exposed.
        with open(os.path.join(d, "sibling.md"), "w") as fh:
            fh.write("x\n")
        # Repo-internal references resolve against the prompts repo, not the kernel.
        got = findings_for("See `sibling.md`, but `nope.md` is missing.\n")
        want("repo-internal resolves vs missing", got,
             [("C1", "error", "unresolved guide reference 'nope.md'")],
             [("C1", "error", "unresolved guide reference 'sibling.md'")])

        # Absolute runtime paths and glob/enumeration paths are not citations.
        got = findings_for("Read `/proc/meminfo`; touch `include/linux/bpf*.h` "
                           "and `wrap_begin/end`.\n")
        want("abs and glob paths skipped", got, [],
             [("C1", "error", "undefined path '/proc/meminfo'"),
              ("C1", "error", "undefined path 'include/linux/bpf*.h'")])

        # A bare basename matching several real files still exists; not a finding.
        got = findings_for("The helper lives in `shared.c` in the tree.\n")
        want("ambiguous basename skipped", got, [],
             [("C1", "error", "ambiguous path fragment 'shared.c' (2 matches)")])

        # A 0-hit fragment / metavariable / metasyntactic placeholder is not drift.
        got = findings_for("`8250_dwlib.o`, `_scoped` variants, `QCM_` prefix, "
                           "`__raw_readN` family, `pXd_mkspecial`, `foo_pm_ops`, "
                           "`alloc_thing`, `my_free`.\n")
        want("fragment/metavar/metasyntactic skipped", got, [],
             [("C2", "error", "undefined symbol '_dwlib'"),
              ("C2", "error", "undefined symbol '_scoped'"),
              ("C2", "error", "undefined symbol 'QCM_'"),
              ("C2", "error", "undefined symbol '__raw_readN'"),
              ("C2", "error", "undefined symbol 'pXd_mkspecial'"),
              ("C2", "error", "undefined symbol 'foo_pm_ops'"),
              ("C2", "error", "undefined symbol 'alloc_thing'"),
              ("C2", "error", "undefined symbol 'my_free'")])

        # A live symbol keeps its underscore/metavariable shape (suppression is
        # only for 0-hit tokens, never a real symbol).
        got = findings_for("`live_helper` is fine even as `_live_helper` shape.\n")
        want("suppression never hides a live symbol", got, [],
             [("C2", "error", "undefined symbol 'live_helper'")])

        # A citation the guide documents as removed is not flagged as drift.
        got = findings_for("`vanished_helper` has been removed from the tree.\n")
        want("removal-notice suppressed", got, [],
             [("C2", "error", "undefined symbol 'vanished_helper'")])

        # A live symbol cited beside an unrelated file is not a finding:
        # existence is tree-wide, and a same-paragraph path is a coincidence,
        # not a containment claim, so scoping to it would be a false positive.
        got = findings_for("The helper `live_helper` is mentioned near `mm/other.c`.\n")
        want("C2 tree-wide (no paired-file FP)", got, [],
             [("C2", "error", "undefined symbol 'live_helper'")])

        # C3: a resolving SHA with an unchanged subject, and a bogus SHA.
        got = findings_for(f"See `{sha}` and `deadbeefdeadbeef`.\n")
        want("C3 sha", got,
             [("C3", "error", "unknown commit deadbeefdeadbeef")],
             [("C3", "error", f"unknown commit {sha}")])

        # C3 subject compare: adjacent quoted subject that no longer matches.
        got = findings_for(f'Commit `{sha}` ("kvm: renamed subject").\n')
        want("C3 subject-mismatch", got,
             [("C3", "error", f'commit {sha} subject changed: '
               f'guide "kvm: renamed subject" '
               f'tree "kvm: add live_helper for the memslot map"')],
             [])

        # C3b: a backticked commit subject resolved by substring.
        got = findings_for("`KVM: arm64: nonexistent subject line here`\n")
        want("C3b subject-gone", got,
             [("C3", "error", 'no commit matches subject '
               '"KVM: arm64: nonexistent subject line here"')],
             [])

        # C3b subject-only: a commit-subject-shaped phrase present only in a
        # commit BODY is a finding (--grep matches the body, the subject-only
        # filter rejects it); the actual subject resolves.
        got = findings_for("`KVM: arm64: body-only phrase here`\n")
        want("C3b body-only rejected", got,
             [("C3", "error", 'no commit matches subject '
               '"KVM: arm64: body-only phrase here"')], [])
        got = findings_for("`KVM: arm64: real subject present`\n")
        want("C3b real subject resolves", got, [],
             [("C3", "error", 'no commit matches subject '
               '"KVM: arm64: real subject present"')])

        # C3 ancestry: a valid commit outside the checked rev's history is a
        # finding; the rev's own commit is not (a commit is its own ancestor).
        def findings_at(tree_x, body):
            gp = os.path.join(d, "guide.md")
            with open(gp, "w") as fh:
                fh.write(body)
            found, _ = run(tree_x, [gp], opts)
            return {(x.check, x.level, x.message) for x in found}
        want("C3 not-in-history", findings_at(tree_old, f"See `{sha2}`.\n"),
             [("C3", "error", f"commit {sha2} not in history of {sha[:12]}")], [])
        want("C3 in-history self", findings_at(tree_old, f"See `{sha}`.\n"),
             [], [("C3", "error", f"commit {sha} not in history of {sha[:12]}")])

        # C4: footer absent (default skip / --require-footer error) and stale.
        Opts0 = Opts(all=False, require_footer=False, stats=False, spec_index=None)
        f0, _ = run(tree, [_write(d, "`vanished_helper`\n")], Opts0)
        want("C4 no-footer skip", {(x.check, x.level, x.message) for x in f0},
             [("C4", "info", "not onboarded (no drift-checked footer); skipped")],
             [("C2", "error", "undefined symbol 'vanished_helper'")])

        Optsr = Opts(all=False, require_footer=True, stats=False, spec_index=None)
        fr, _ = run(tree, [_write(d, "`vanished_helper`\n")], Optsr)
        want("C4 require-footer", {(x.check, x.level, x.message) for x in fr},
             [("C4", "error", "no drift-checked footer")], [])

        good_footer = f"body\n\n<!-- drift-checked: rev={sha} date=2000-01-01 -->\n"
        fg, _ = run(tree, [_write(d, good_footer)], Opts0)
        want("C4 stale-footer", {(x.check, x.level, x.message) for x in fg},
             [("C4", "warn", "footer dated 2000-01-01 is "
               f"{(date.today() - date(2000, 1, 1)).days} days old")],
             [("C4", "info", "not onboarded (no drift-checked footer); skipped")])

        bad_rev = "body\n\n<!-- drift-checked: rev=000000000000 date=2099-01-01 -->\n"
        fb, _ = run(tree, [_write(d, bad_rev)], Opts0)
        want("C4 bad-rev", {(x.check, x.level, x.message) for x in fb},
             [("C4", "error", "footer rev 000000000000 does not resolve")], [])

        malformed = "body\n\n<!-- drift-checked: rev=xyz -->\n"
        fm, _ = run(tree, [_write(d, malformed)], Opts0)
        want("C4 malformed", {(x.check, x.level, x.message) for x in fm},
             [("C4", "error", "malformed drift-checked footer")], [])

        # Shallow tree (a depth-1 CI clone): the commit-history checks omit their
        # git plumbing rather than false-flag citations whose history is absent,
        # while path and symbol checks, which read only the tip, still run.
        shallow = os.path.join(d, "shallow")
        subprocess.run(["git", "clone", "-q", "--depth", "1", f"file://{repo}",
                        shallow], check=True, env=env)
        tree_sh = KernelTree(shallow)
        assert tree_sh.shallow

        def findings_sh(tree_x, body, o=opts):
            gp = os.path.join(d, "guide.md")
            with open(gp, "w") as fh:
                fh.write(body)
            found, _ = run(tree_x, [gp], o)
            return {(x.check, x.level, x.message) for x in found}

        want("shallow skips C3, keeps C1/C2",
             findings_sh(tree_sh, "`deadbeefdeadbeef`, gone `mm/nope.c`, "
                         "gone `vanished_helper`.\n"),
             [("C1", "error", "undefined path 'mm/nope.c'"),
              ("C2", "error", "undefined symbol 'vanished_helper'")],
             [("C3", "error", "unknown commit deadbeefdeadbeef")])
        want("shallow skips C3b",
             findings_sh(tree_sh, "`KVM: arm64: nonexistent subject line here`\n"),
             [], [("C3", "error", 'no commit matches subject '
                   '"KVM: arm64: nonexistent subject line here"')])
        # A footer whose rev is outside the shallow history: no false rev error,
        # and the age warning still fires.
        want("shallow footer keeps age, skips ancestry",
             findings_sh(tree_sh,
                         "body\n\n<!-- drift-checked: rev=000000000000 "
                         "date=2000-01-01 -->\n", Opts0),
             [("C4", "warn", "footer dated 2000-01-01 is "
               f"{(date.today() - date(2000, 1, 1)).days} days old")],
             [("C4", "error", "footer rev 000000000000 does not resolve")])

    ok = True
    for name, passed, got in checks:
        print(f"  {'ok  ' if passed else 'FAIL'}  {name}")
        if not passed:
            ok = False
            for g in sorted(got):
                print(f"          got: {g}")
    print("selftest:", "PASS" if ok else "FAIL")
    return 0 if ok else 1


def _write(d, body):
    gp = os.path.join(d, f"g{abs(hash(body)) % 10000}.md")
    with open(gp, "w") as f:
        f.write(body)
    return gp


# --------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description="Report stale citations in the "
                                 "subsystem guides against a kernel tree.")
    ap.add_argument("guides", nargs="*", help="guide markdown files to check")
    ap.add_argument("--tree", help="path to a local kernel git tree")
    ap.add_argument("--rev", default="HEAD",
                    help="revision to check against (default: the tree's HEAD)")
    ap.add_argument("--all", action="store_true",
                    help="check a guide's citations even without a footer")
    ap.add_argument("--require-footer", action="store_true",
                    help="treat a missing footer as an error")
    ap.add_argument("--stats", action="store_true",
                    help="print per-class checked/skipped/ignored counts")
    ap.add_argument("--spec-index",
                    help="file of known spec references to validate C5 against")
    ap.add_argument("--jobs", type=int, default=12, help="parallel grep workers")
    ap.add_argument("--selftest", action="store_true",
                    help="run the built-in self-test (needs no kernel tree)")
    opts = ap.parse_args()

    if opts.selftest:
        return selftest()
    if not opts.tree or not opts.guides:
        ap.error("--tree and at least one guide are required")

    tree = KernelTree(opts.tree, opts.rev, opts.jobs)
    if tree.shallow:
        print("check-drift.py: shallow kernel tree; commit-history checks "
              "(C3 commit citations, footer ancestry) skipped", file=sys.stderr)
    findings, stats = run(tree, opts.guides, opts)
    errors = report(findings, stats, opts)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
