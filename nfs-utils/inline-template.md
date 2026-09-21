# Review Report Template

When findings survive the false-positive check, create `review-inline.txt`
using this template. The audience is `linux-nfs@vger.kernel.org`.

## Formatting Rules

1. **Plain text only** — no markdown, no backticks, no bullet glyphs.
2. **Wrap at 72 characters.** Code snippets may run to 78.
3. Indent code with a tab or four spaces; do not fence it.
4. Refer to code by file and function name. Add a line number only when the
   function is long and the line is not otherwise findable.
5. Factual tone. No severity theatrics, no "critical security vulnerability!"
   framing — state the condition and the consequence and let it speak.
6. Quote the patch with `> ` when replying to a posted patch.

## Template

```
Subject: Re: [PATCH] <original subject>

<One or two sentences: what the patch does, and the headline finding.>

=== Issue 1: <brief description> ===

File: <path/from/tree/root.c>
Function: <function_name>()
Severity: CRITICAL | HIGH | MEDIUM

<What is wrong, in one or two sentences.>

	<the relevant code, indented>

<Why it is wrong.>

Reachable via: <the concrete call path, or the concrete input>

Suggested fix:

	<the corrected code, if it is short and obvious>

=== Issue 2: <brief description> ===

<repeat>

Analysis notes:
- <call paths traced>
- <configurations checked, e.g. built with --disable-nfsdctl>
- <assumptions verified, and anything left unverified>
```

## Example

This is an illustration of the *format*, using an invented patch. Do not
pattern-match your analysis to it — derive your findings from the code in
front of you.

```
Subject: Re: [PATCH] mountd: cache the export root lookup

The caching is fine, but the new early return leaks the RPC client
and the addrinfo, and it bypasses the rootdir confinement.

=== Issue 1: RPC client leaked on the new cache-hit path ===

File: utils/mountd/cache.c
Function: lookup_export_root()
Severity: HIGH

The new cache-hit branch returns before CLNT_DESTROY(), so every
cached lookup leaks a CLIENT and its socket. mountd is long-lived
and this path runs once per MOUNT request.

	clnt = nfs_get_rpcclient(sap, salen, IPPROTO_TCP, ...);
	if (!clnt)
		return NULL;

	if (cached_root) 	/* added by this patch */
		return cached_root;

	res = do_lookup(clnt);
	CLNT_DESTROY(clnt);

The client is acquired before the cache is consulted, so the fast
path never releases it. Moving the cache check above the acquire
would fix both the leak and the pointless connection.

Reachable via: any second MOUNT request for the same export.

Suggested fix:

	if (cached_root)
		return cached_root;

	clnt = nfs_get_rpcclient(sap, salen, IPPROTO_TCP, ...);

=== Issue 2: addrinfo released with freeaddrinfo() ===

File: utils/mountd/cache.c
Function: lookup_export_root()
Severity: MEDIUM

	freeaddrinfo(ai);

Should be nfs_freeaddrinfo(). The wrapper exists because some
implementations of freeaddrinfo(3) fault when passed NULL, and ai
is NULL on the getaddrinfo() failure path added just above.

Analysis notes:
- Traced from mount_dispatch() through lookup_export_root()
- Checked the other CLNT_DESTROY sites in this file for the pattern
- Built with --disable-nfsdctl; no link change needed
```

## Checklist Before Writing

- [ ] Every finding checked against `false-positive-guide.md`.
- [ ] Every path traced, not inferred.
- [ ] Concrete input or sequence stated for each finding.
- [ ] Nothing speculative included.
- [ ] Nothing style-only included.
- [ ] Formatting rules followed.

If nothing survives, do not create the file. Say the patch looks correct and
state what you checked.

## File Creation

Write to `./review-inline.txt` in the current directory.
