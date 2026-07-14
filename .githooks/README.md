# Git hooks

This repository ships hooks that strip automated co-author trailers from commit messages.

Enable once per clone:

```powershell
git config core.hooksPath .githooks
```

On Windows, ensure `.githooks/commit-msg` is executable or run:

```powershell
git update-index --add --chmod=+x .githooks/commit-msg
```
