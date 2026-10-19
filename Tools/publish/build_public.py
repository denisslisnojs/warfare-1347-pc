import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
EXCLUDE = os.path.join(ROOT, "docs", "readme", "public-exclude.txt")
INDEX = os.path.join(ROOT, ".git", "public-index")
BRANCH = "public"


def git(*args, env=None):
    return subprocess.run(["git", *args], cwd=ROOT, env=env, check=True, capture_output=True, text=True).stdout.strip()


def main():
    title = sys.argv[1] if len(sys.argv) > 1 else "Public snapshot of Warfare 1347"
    message = title + "\n\nCo-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
    env = dict(os.environ, GIT_INDEX_FILE=INDEX)
    git("read-tree", "main", env=env)
    patterns = [p.strip() for p in open(EXCLUDE, encoding="utf-8") if p.strip()]
    git("rm", "-r", "--cached", "--ignore-unmatch", "--quiet", "--", *patterns, env=env)
    tree = git("write-tree", env=env)
    os.remove(INDEX)
    parent = subprocess.run(["git", "rev-parse", "--verify", "--quiet", BRANCH], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    if parent and git("rev-parse", parent + "^{tree}") == tree:
        print("public branch already matches main")
        return
    args = ["commit-tree", tree, "-m", message]
    if parent:
        args += ["-p", parent]
    commit = git(*args)
    git("branch", "-f", BRANCH, commit)
    files = git("ls-tree", "-r", "--name-only", commit).count("\n") + 1
    print(f"{BRANCH} -> {commit[:8]}, {files} files")


main()
