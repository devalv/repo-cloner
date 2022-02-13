Liked repos cloner
---

Script takes user public liked repos and clone it to a local folder.

## How to run

### Simple example
```bash
python cloner.py -u=devalv -d=../liked_repos -v -p 10 -w 1 -c -r
```

### Arguments
```bash
-u, --user      - the name of the user whose starred repository needs to be cloned
-d, --dir       - directory where cloned repos should be stored
-v, --verbose   - verbose mode
-p, --pages     - total pages count for github paginator
-w, --workers   - if > 1, processes with the specified number will be created for parallel cloning
-c, --compress  - compress directory with cloned repos to zip archive
-r, --remove    - remove directory with cloned repos (uncompressed)
```
