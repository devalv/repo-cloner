# -*- coding: utf-8 -*-
"""
python cloner.py -u=devalv -d=../liked_repos -v -p 10 -w 4
"""

import argparse
import logging
import time
from concurrent import futures
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List

from tqdm import tqdm
import httpx
from git import Git


# logging configuration
formatter = logging.Formatter()
logging.basicConfig(encoding="utf-8", format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("repo_cloner")

# argparse configuration
parser = argparse.ArgumentParser(description="Download liked repos.")
parser.add_argument(
    "-u", "--user", help="username which liked repos to clone", required=True
)
parser.add_argument(
    "-d", "--dir", help="directory where repos should be created", required=True
)
parser.add_argument(
    "-v", "--verbose", help="verbose mode", required=False, default=False, action='store_true'
)
parser.add_argument(
    "-p", "--pages", help="pages of starred repos to get", required=False, default=10, type=int
)
parser.add_argument(
    "-w", "--workers", help="num of threads", required=False, default=2, type=int
)


def clone_repo(directory: Path, url: str) -> bool:
    try:
        logger.debug(f'Cloning {url}...')
        # Git(directory).clone(url)
    except Exception as msg:  # noqa
        logger.error(msg)
        return False
    return True


def clone_repos(repos_dict: Dict[str, str], directory: Path, max_workers: int) -> int:
    cloned_repos_count: int = 0

    with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        to_do_map = dict()
        for repo, url in repos_dict.items():
            future = executor.submit(clone_repo, directory, url)
            to_do_map[future] = url

        print(f'{to_do_map=}')
        done_iter: Iterable = futures.as_completed(to_do_map)

        if logger.isEnabledFor(logging.DEBUG):
            # TODO: @devalv not verbose тут и в еще одном месте
            done_iter: Iterable = tqdm(done_iter, total=len(repos_dict))

        for future in done_iter:
            res_status = future.result()
            if res_status:
                cloned_repos_count += 1

    return cloned_repos_count


def get_liked_repos(username: str, pages: int) -> Dict[str, str]:
    liked_repos: Dict[str, str] = dict()

    pages_iter: Iterable = range(pages + 1)

    if logger.isEnabledFor(logging.DEBUG):
        pages_iter = tqdm(pages_iter)

    for page in pages_iter:
        response = httpx.get(
            f"https://api.github.com/users/{username}/starred",
            headers={"accept": "application/vnd.github.v3+json"},
            params={"page": page, "per_page": 10},
        )
        if not response.is_success:
            logger.error(f"Can`t fetch data: {response.text}")
            break

        for repo in response.json():
            name: str = repo.get("name")
            url: str = repo.get("clone_url")
            if not name:
                logger.warning(f"Can`t get name of {url=}")
                continue
            if not url:
                logger.warning(f"Can`t get url of {name=}")
                continue
            liked_repos[name] = url

    logger.info(f"Got {len(liked_repos)} liked repos.")
    return liked_repos


def main(username: str, directory: str, pages: int, workers: int) -> None:
    if logger.isEnabledFor(logging.DEBUG):
        start_time = time.time()

    assert Path(directory).is_dir()
    date_dir: str = date.today().strftime("%Y%m%d")
    working_dir: Path = Path(f"{directory}/{date_dir}")
    if not working_dir.exists():
        working_dir.mkdir()

    repos_to_clone = get_liked_repos(username, pages)
    # repos_to_clone = {v: v for v in range(100)}

    cloned_repos: int = clone_repos(repos_to_clone, directory=working_dir, max_workers=workers)

    if logger.isEnabledFor(logging.DEBUG):
        end_time = time.time()
        logger.debug(f'Got {cloned_repos} repos for a {round(end_time-start_time)} sec.')

    assert (
        len(repos_to_clone) == cloned_repos
    ),  f"Not all repos are cloned ({cloned_repos}/{len(repos_to_clone)}."

    return None


if __name__ == "__main__":

    # TODO: create archive?
    # import shutil
    # shutil.make_archive(output_filename, 'zip', dir_name)

    # TODO: create readme
    # TODO: create repo
    # TODO: install githook and github action for linting

    # TODO: треды не сработали - задача не отпускает gil. процессы?

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel('DEBUG')

    main(username=args.user, directory=args.dir, pages=args.pages, workers=args.workers)

