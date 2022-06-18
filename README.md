Liked repos cloner
---

Script takes user public liked repos and clone it to a local folder.

## Installation
pip install -r requirements.txt

## How to run

### Simple example
```bash
python main.py -u devalv -d . -w 4
```

### Arguments
```bash
-u, --user      - the name of the user whose starred repository needs to be cloned
-d, --dir       - directory where cloned repos should be stored
-w, --workers   - workers count
-c, --compress  - compress directory with cloned repos to zip archive
-t, --token     - GitHub personal access token
```
