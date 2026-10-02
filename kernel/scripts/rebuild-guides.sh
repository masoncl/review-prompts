#!/bin/bash
# rebuild-guides.sh - rebuild built subsystem guides from their question files,
# check each one, and install the ones that pass.
#
#   rebuild-guides.sh --tree <linux> [--dir kernel/subsystem/build/linus]
#                     [--jobs 4] [--scratch DIR] [--no-build] (--all | guide ...)
#
# The built guides are in one build directory, kernel/subsystem/build/linus/.
# It holds the guides of the most recent tree of Linus's that was scanned,
# and kernel-version.yaml in it says which release and commit that was.
# For each guide the script runs
# build-guides.py against one shared snapshot of the tree, keeps the final
# answers, runs check-built-guide.py on the result, and only if that passes
# copies the guide and its answers into the build directory and records the
# kernel in kernel-version.yaml. Then it makes subsystem-guide-index.txt again
# with make-guide-index.py, since the index holds the line number of every
# answer.
# The build directory holds the guides of one release. --all builds every
# guide, and when the tree has moved on it removes the guides of the earlier
# kernel, so that kernel-version.yaml is true of every guide there. Naming
# guides rebuilds them in place, and the tree has to be at the release that
# the directory records. A guide is also refused if a
# stage of its build did not run (a reader not asked, a section not checked, the
# whole guide not read through), which the build says in incomplete.txt. A guide
# that fails is left in
# the scratch directory with its run report for a person to read.
# --no-build skips the building and checks and
# installs what an earlier run left in the scratch directory, for when a check
# refused something that has since been put right.
#
# Which models to use is not in this repository. Put it in
# ~/.config/review-prompts/build.env (or the file $REVIEW_PROMPTS_CONFIG names):
#
#   REVIEW_PROMPTS_BUILDER=<model>           # answers and, by default, checks
#   REVIEW_PROMPTS_READERS="<model> <model>" # whose memory is asked first
#   REVIEW_PROMPTS_CHECKER=<model>           # optional: a different checker
#   REVIEW_PROMPTS_PERMISSION_MODE=auto      # optional
#   REVIEW_PROMPTS_FORBIDDEN='name1|name2'   # optional: names that must never
#                                            # reach a committed file
#
# See "Rebuilding" in kernel/docs/subsystem-questions.md.

set -u
here=$(cd "$(dirname "$0")" && pwd)
repo=$(cd "$here/../.." && pwd)
tree= dir= jobs=4 scratch= all=0 build=1
guides=()

die() { echo "rebuild-guides.sh: $*" >&2; exit 2; }
while [ $# -gt 0 ]; do
    case "$1" in
        --tree) tree=$2; shift 2 ;;
        --dir) dir=$2; shift 2 ;;
        --jobs) jobs=$2; shift 2 ;;
        --scratch) scratch=$2; shift 2 ;;
        --all) all=1; shift ;;
        --no-build) build=0; shift ;;
        -h|--help) sed -n '2,41p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
        -*) die "unknown option $1" ;;
        *) guides+=("$1"); shift ;;
    esac
done
[ -n "$tree" ] && [ -d "$tree/.git" -o -f "$tree/.git" ] || die "--tree must be a kernel git tree"
tree=$(cd "$tree" && pwd)

# The release and the commit of the tree, as build-guides.py will record them.
read -r tag head < <(python3 - "$here" "$tree" <<'EOF'
import importlib.util, sys
sys.path.insert(0, sys.argv[1])        # build-guides.py imports its sibling modules by name
spec = importlib.util.spec_from_file_location("bg", sys.argv[1] + "/build-guides.py")
bg = importlib.util.module_from_spec(spec); spec.loader.exec_module(bg)
print(bg.kernel_base(sys.argv[2]), bg.tree_sha(sys.argv[2], "HEAD"))
EOF
)
[[ "$tag" =~ ^v[0-9]+\.[0-9]+ ]] || die "cannot tell the release of $tree from its Makefile"
[ -n "$dir" ] || dir="$repo/kernel/subsystem/build/linus"
dir=$(mkdir -p "$dir" && cd "$dir" && pwd)
# The build directory holds the guides of one release. A guide named on the
# command line is rebuilt in place, so the tree has to be at the release that
# the directory records; a build for another release takes --all.
if [ $all = 0 ]; then
    have=$(sed -n 's/^kernel: *//p' "$dir/kernel-version.yaml" 2>/dev/null)
    [ -n "$have" ] || die "$dir holds no build yet; build every guide with --all"
    [ "$have" = "$tag" ] || die "$dir holds a build of $have and $tree is at $tag; build every guide with --all"
fi

config=${REVIEW_PROMPTS_CONFIG:-$HOME/.config/review-prompts/build.env}
# shellcheck disable=SC1090
[ -f "$config" ] && . "$config"
[ -n "${REVIEW_PROMPTS_BUILDER:-}" ] || die "set REVIEW_PROMPTS_BUILDER in $config; see the top of this script"
export REVIEW_PROMPTS_FORBIDDEN=${REVIEW_PROMPTS_FORBIDDEN:-}
readers=${REVIEW_PROMPTS_READERS:-$REVIEW_PROMPTS_BUILDER}

if [ $all = 1 ]; then
    mapfile -t guides < <(cd "$repo/kernel/subsystem/questions" && ls *.md | sed 's/\.md$//')
fi
[ ${#guides[@]} -gt 0 ] || die "nothing to rebuild: name guides, or give --all"
for g in "${guides[@]}"; do
    [[ "$g" =~ ^[A-Za-z0-9][A-Za-z0-9_.-]*$ ]] || die "not a guide name: '$g'"
    [ -f "$repo/kernel/subsystem/questions/$g.md" ] || die "no question file for '$g'"
done

# The scratch directory holds a copy of the tree the models read. Keep it out
# of your home directory, or the driver cannot deny them the rest of home.
if [ -z "$scratch" ]; then
    scratch=$(mktemp -d "${TMPDIR:-/var/tmp}/rebuild-guides.XXXXXX") || die "no scratch directory"
fi
mkdir -p "$scratch/stage/answers"
case "$(cd "$scratch" && pwd)/" in "$HOME"/*) die "--scratch must be outside your home directory" ;; esac

snap="$scratch/snapshot/linux"
if [ ! -f "$snap/Makefile" ]; then
    echo "unpacking $tree into $snap"
    python3 - "$here" "$tree" "$snap" <<'EOF' || die "could not snapshot the tree"
import importlib.util, sys
sys.path.insert(0, sys.argv[1])        # build-guides.py imports its sibling modules by name
spec = importlib.util.spec_from_file_location("bg", sys.argv[1] + "/build-guides.py")
bg = importlib.util.module_from_spec(spec); spec.loader.exec_module(bg)
bg.make_snapshot(sys.argv[2], "HEAD", sys.argv[3])
EOF
fi

build_one() {
    # Two statements: in one "local", $g would be expanded before it is set,
    # and "$scratch/" is not something to hand to rm.
    local g=$1
    local out="$scratch/$g" args=()
    [ -n "$g" ] && [ "$out" != "$scratch/" ] || { echo "build_one: no guide name" >&2; return 1; }
    rm -rf -- "$out"
    mkdir -p "$out"
    for r in $readers; do args+=(--reader-model "$r"); done
    [ -n "${REVIEW_PROMPTS_CHECKER:-}" ] && args+=(--check-model "$REVIEW_PROMPTS_CHECKER")
    [ -n "${REVIEW_PROMPTS_PERMISSION_MODE:-}" ] && args+=(--permission-mode "$REVIEW_PROMPTS_PERMISSION_MODE")
    "$here/build-guides.py" --tree "$tree" --snapshot "$snap" --guide "$g" --out "$out" \
        --model "$REVIEW_PROMPTS_BUILDER" "${args[@]}" \
        --keep-answers "$scratch/stage/answers" --record "$out/kernel-version.yaml" \
        > "$out.log" 2>&1
    echo "built $g: exit $? ($(tail -n 1 "$out.log" | cut -c1-100))"
}
export -f build_one
export here tree snap scratch readers REVIEW_PROMPTS_BUILDER
export REVIEW_PROMPTS_SCRATCH=$scratch      # check-built-guide.py refuses this path in a guide
export REVIEW_PROMPTS_CHECKER=${REVIEW_PROMPTS_CHECKER:-} REVIEW_PROMPTS_PERMISSION_MODE=${REVIEW_PROMPTS_PERMISSION_MODE:-}

if [ $build = 1 ]; then
    echo "building ${#guides[@]} guide(s), $jobs at a time, in $scratch"
    printf '%s\n' "${guides[@]}" | xargs -P "$jobs" -I{} bash -c 'build_one "$1"' _ {}
fi

# With --all, the guides of an earlier kernel must not stay beside the new
# ones, or kernel-version.yaml would be wrong for them. They are removed when
# the first new guide is installed, so a run that builds nothing removes
# nothing. Only what a build writes is removed: a guide that has a question
# file, its answers, and the index.
clear_old_build() {
    local q g
    echo "replacing the build of $(sed -n 's/^kernel: *//p' "$dir/kernel-version.yaml") in $dir"
    for q in "$repo"/kernel/subsystem/questions/*.md; do
        g=$(basename "$q" .md)
        rm -f -- "$dir/$g.md"
        rm -rf -- "$dir/answers/$g"
    done
    rm -f -- "$dir/subsystem-guide-index.txt"
}

# Install one at a time: the kernel record is one file.
ok=0 failed=() cleared=0
for g in "${guides[@]}"; do
    if [ ! -s "$scratch/$g/$g.md" ]; then failed+=("$g (no guide; see $scratch/$g.log)"); continue; fi
    # a stage that failed twice: what it would have asked or checked is not in the guide
    if [ -s "$scratch/$g/incomplete.txt" ]; then
        failed+=("$g (a stage of the build did not run; see $scratch/$g/incomplete.txt)"); continue
    fi
    # the kernel this guide was built from, as its build recorded it
    rec="$scratch/$g/kernel-version.yaml"
    if [ ! -s "$rec" ]; then failed+=("$g (its build recorded no kernel)"); continue; fi
    built=$(sed -n 's/^kernel: *//p' "$rec")
    if [ $all = 0 ] && [ "$built" != "$have" ]; then
        failed+=("$g (built from $built, and $dir holds a build of $have; build every guide with --all)"); continue
    fi
    cp "$scratch/$g/$g.md" "$scratch/stage/$g.md"
    cp "$rec" "$scratch/stage/kernel-version.yaml"
    if "$here/check-built-guide.py" --dir "$scratch/stage" "$g" > "$scratch/$g.check" 2>&1; then
        if [ $all = 1 ] && [ $cleared = 0 ] && [ -f "$dir/kernel-version.yaml" ] \
           && ! cmp -s "$rec" "$dir/kernel-version.yaml"; then
            clear_old_build
        fi
        cleared=1
        cp "$scratch/stage/$g.md" "$dir/$g.md"
        rm -rf "$dir/answers/$g"; mkdir -p "$dir/answers"
        [ -d "$scratch/stage/answers/$g" ] && cp -r "$scratch/stage/answers/$g" "$dir/answers/$g"
        # a build of every guide records its kernel; a guide rebuilt in place keeps
        # the record of the build it joins
        [ $all = 1 ] && cp "$rec" "$dir/kernel-version.yaml"
        ok=$((ok + 1)); sed -n '1,6p' "$scratch/$g.check"
    else
        failed+=("$g (see $scratch/$g.check and $scratch/$g/run-report.md)")
        cat "$scratch/$g.check"
    fi
done
# The index holds the line number of every answer, so a new guide needs a new index.
if [ $ok -gt 0 ]; then
    "$here/make-guide-index.py" --tree "$tree" --dir "$dir" || die "the index of the guides was not made"
fi
rm -rf "$repo/kernel/scripts/__pycache__"
echo "installed $ok of ${#guides[@]} into $dir"
[ ${#failed[@]} -eq 0 ] || { printf 'not installed: %s\n' "${failed[@]}"; exit 1; }
echo "read each new guide before committing it: a check that passes is not a guide that is right"
