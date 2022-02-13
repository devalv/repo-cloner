# -*- coding: utf-8 -*-
"""
python cloner.py -u=devalv -d=../liked_repos -v -p 10 -w 1 -c -r
"""

import argparse
import logging
import shutil
from datetime import date
from functools import wraps
from multiprocessing import Pool
from pathlib import Path
from time import time
from typing import Iterable, List, Set, Tuple

import httpx
from git import Git
from tqdm import tqdm

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
    "-v",
    "--verbose",
    help="verbose mode",
    required=False,
    default=False,
    action="store_true",
)
parser.add_argument(
    "-p",
    "--pages",
    help="pages of starred repos to get",
    required=False,
    default=10,
    type=int,
)
parser.add_argument(
    "-w", "--workers", help="num of threads", required=False, default=1, type=int
)
parser.add_argument(
    "-r",
    "--remove",
    help="remove downloaded dir",
    required=False,
    default=False,
    action="store_true",
)
parser.add_argument(
    "-c",
    "--compress",
    help="compress downloaded",
    required=False,
    default=False,
    action="store_true",
)


def timing(func):
    """Execution timer."""

    @wraps(func)
    def wrap(*args, **kw):
        if logger.isEnabledFor(logging.DEBUG):
            start_time = time()

        result = func(*args, **kw)

        if logger.isEnabledFor(logging.DEBUG):
            end_time = time()
            logger.debug(
                f"Func `{func.__name__}` took {round(end_time - start_time)} sec."
            )

        return result

    return wrap


def clone_repo(directory: Path, url: str) -> bool:
    try:
        Git(directory).clone(url)
    except Exception as msg:  # noqa
        logger.error(msg)
        return False
    return True


@timing
def clone_repos_mp(directory: Path, max_workers: int, repos_urls: Set[str]) -> int:
    """Run {max_workers} processes with clone_repo for each of repos_urls."""
    clone_repo_args_iter: Set[Tuple[Path, str]] = {(directory, url) for url in repos_urls}

    with Pool(processes=max_workers) as p:
        results: List[bool] = p.starmap(clone_repo, clone_repo_args_iter)

    return results.count(True)


@timing
def clone_repos_sync(directory: Path, repos_urls: Set[str]) -> int:
    """Run clone_repo for each of repos_urls."""
    cloned_repos: int = 0
    repos_iter: Iterable = repos_urls

    if logger.isEnabledFor(logging.DEBUG):
        repos_iter: Iterable = tqdm(repos_urls)

    for repo_url in repos_iter:
        result: bool = clone_repo(directory, repo_url)
        if result:
            cloned_repos += 1

    return cloned_repos


@timing
def get_liked_repos(username: str, pages: int) -> Set[str]:
    """Synchronously generates a set of repositories from Github that are starred by user."""
    liked_repos: Set[str] = set()
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
            url: str = repo.get("clone_url")
            if not url:
                _name: str = repo.get("name")
                logger.warning(f"Can`t get url of {_name=}")
                continue

            liked_repos.add(url)

    logger.debug(f"Got {len(liked_repos)} liked repos.")
    return liked_repos


@timing
def compress_repos(directory: Path, delete_dir: bool) -> None:
    shutil.make_archive(directory.name, "zip", directory)
    if delete_dir:
        try:
            shutil.rmtree(directory)
        except PermissionError:
            logger.error(f"Can`t delete {directory.name}")
    return None


@timing
def main(
    username: str, directory: str, pages: int, workers: int, compress: bool, remove: bool
) -> None:
    assert Path(directory).is_dir()
    date_dir: str = date.today().strftime("%Y%m%d")
    working_dir: Path = Path(f"{directory}/{date_dir}")
    if not working_dir.exists():
        working_dir.mkdir()

    repos_to_clone = get_liked_repos(username, pages)

    if workers > 1:
        cloned_repos: int = clone_repos_mp(
            repos_urls=repos_to_clone, directory=working_dir, max_workers=workers
        )
    else:
        cloned_repos: int = clone_repos_sync(
            repos_urls=repos_to_clone, directory=working_dir
        )

    if len(repos_to_clone) != cloned_repos:
        logger.error(f"Not all repos are cloned ({cloned_repos}/{len(repos_to_clone)})")
    elif compress:
        compress_repos(working_dir, delete_dir=remove)

    return None


if __name__ == "__main__":

    # TODO: create readme
    # TODO: install githook and github action for linting

    user_args = parser.parse_args()

    if user_args.verbose:
        logger.setLevel("DEBUG")

    main(
        username=user_args.user,
        directory=user_args.dir,
        pages=user_args.pages,
        workers=user_args.workers,
        compress=user_args.compress,
        remove=user_args.remove,
    )
