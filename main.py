# -*- coding: utf-8 -*-
"""
python cloner.py -u=devalv -d=../liked_repos -v
"""

import argparse
import logging
import time
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List
import asyncio

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


async def clone_repo(directory: Path, repo_url: str) -> bool:
    # TODO: @devalv remove
    try:
        Git(directory).clone(repo_url)
    except:  # noqa
        return False
    return True


async def clone_repos_async(repos_dict: Dict[str, str], directory: Path) -> int:
    # TODO: @devalv remove
    logger.debug(f"Repos will be cloned to {directory.absolute()}")
    repos_iter: Iterable = repos_dict.items()

    # clone repos concurrently
    clone_repo_corous: set = set()
    for _, repo_url in repos_iter:
        clone_repo_corous.add(clone_repo(directory, repo_url))

    cloned_repos: List[bool] = await asyncio.gather(
        *clone_repo_corous
    )

    # check how many repos was cloned
    successfully_cloned_repos = len(list(filter(lambda r: r is True, cloned_repos)))

    return successfully_cloned_repos


def clone_repos_threads(repos_dict: Dict[str, str], directory: Path) -> int:
    raise NotImplementedError
    # TODO: do with threads
    logger.debug(f"Repos will be cloned to {directory.absolute()}")

    # cloned_repos: int = 0
    repos_iter: Iterable = repos_dict.items()

    if logger.isEnabledFor(logging.DEBUG):
        # TODO: not working with gather
        repos_iter = tqdm(repos_iter)

    # TODO: sync mode - need to compare
    # for _, repo_url in repos_iter:
    #     Git(directory).clone(repo_url)
    #     cloned_repos += 1


def clone_repos_simple(repos_dict: Dict[str, str], directory: Path) -> int:
    logger.debug(f"Repos will be cloned to {directory.absolute()}")

    cloned_repos: int = 0
    repos_iter: Iterable = repos_dict.items()

    if logger.isEnabledFor(logging.DEBUG):
        repos_iter = tqdm(repos_iter)

    for _, repo_url in repos_iter:
        Git(directory).clone(repo_url)
        cloned_repos += 1

    return cloned_repos


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


def main(username: str, directory: str, pages: int) -> None:
    if logger.isEnabledFor(logging.DEBUG):
        start_time = time.time()

    assert Path(directory).is_dir()
    date_dir: str = date.today().strftime("%Y%m%d")
    working_dir: Path = Path(f"{directory}/{date_dir}")
    if not working_dir.exists():
        working_dir.mkdir()

    repos_to_clone = get_liked_repos(username, pages)
    cloned_repos: int = clone_repos_simple(repos_to_clone, directory=working_dir)

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

    args = parser.parse_args()

    if args.verbose:
        logger.setLevel('DEBUG')

    # TODO: @devalv remove
    # asyncio.run(main(username=args.user, directory=args.dir, pages=args.pages))
    main(username=args.user, directory=args.dir, pages=args.pages)

