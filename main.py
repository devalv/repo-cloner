# -*- coding: utf-8 -*-
"""
python cloner.py -u=devalv -d=../liked_repos -v -p 10 -w 1
"""

import argparse
import logging
import time
from datetime import date
from pathlib import Path
from typing import Iterable, List, Set, Tuple

from multiprocessing import Pool
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
    "-w", "--workers", help="num of threads", required=False, default=1, type=int
)


def clone_repo(directory: Path, url: str) -> bool:
    try:
        Git(directory).clone(url)
    except Exception as msg:  # noqa
        logger.error(msg)
        return False
    return True


def clone_repos_mp(directory: Path, max_workers: int, repos_urls: Set[str]) -> int:
    """Run {max_workers} processes with clone_repo for each of repos_urls."""
    clone_repo_args_iter: Set[Tuple[Path, str]] = {(directory, url) for url in repos_urls}

    with Pool(processes=max_workers) as p:
        results: List[bool] = p.starmap(clone_repo, clone_repo_args_iter)

    return results.count(True)


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


def main(username: str, directory: str, pages: int, workers: int) -> None:
    if logger.isEnabledFor(logging.DEBUG):
        start_time = time.time()

    assert Path(directory).is_dir()
    date_dir: str = date.today().strftime("%Y%m%d")
    working_dir: Path = Path(f"{directory}/{date_dir}")
    if not working_dir.exists():
        working_dir.mkdir()

    repos_to_clone = get_liked_repos(username, pages)

    if workers > 1:
        cloned_repos: int = clone_repos_mp(repos_urls=repos_to_clone, directory=working_dir, max_workers=workers)
    else:
        cloned_repos: int = clone_repos_sync(repos_urls=repos_to_clone, directory=working_dir)

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
    # TODO: install githook and github action for linting

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel('DEBUG')

    main(username=args.user, directory=args.dir, pages=args.pages, workers=args.workers)

