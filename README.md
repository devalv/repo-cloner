Liked repos cloner
---

Script takes user public liked repos and clone it to a local folder.

## Installation

Install git (if it`s not installed).

```bash
git clone https://github.com/devalv/repo-cloner && cd repo-cloner
python3 -m venv venv
venv/bin/pip3 install -r requirements.txt
```

## How to run

### Simple example

```bash
venv/bin/python3 main.py -u devalv -d . -w 4 2>&1 | tee repo-cloner.log
```

### Arguments
```bash
-u, --user      - the name of the user whose starred repository needs to be cloned
-d, --dir       - directory where cloned repos should be stored
-w, --workers   - workers count
-c, --compress  - compress directory with cloned repos to zip archive
-t, --token     - GitHub personal access token
```
