# -*- coding: utf-8 -*-
"""
python main.py -u=devalv -d=. -w 4
"""

import argparse
import logging
import re
import shutil
import subprocess
from datetime import date
from multiprocessing import Pool, freeze_support
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import httpx

# logging configuration
formatter = logging.Formatter()
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
    "-w", "--workers", help="num of processes", required=False, default=1, type=int
)
parser.add_argument(
    "-c",
    "--compress",
    help="compress downloaded",
    required=False,
    default=True,
    action="store_true",
)
parser.add_argument(
    "-t", "--token", help="github personal access token", required=False
)


def _get_total_pages(username: str, token: Optional[str] = None) -> int:
    headers: Dict[str, str] = {"accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    response = httpx.get(
        f"https://api.github.com/users/{username}/starred",
        headers=headers,
        params={"page": 1, "per_page": 10},
    )
    if not response.is_success:
        logger.error(f"Can`t fetch data: {response.text}.")
        exit(1)

    page_pattern = r"(?<=\?page=)(\d+)|(?<=\&page=)(\d+)"
    page_search: List[Tuple[str, str]] = re.findall(
        page_pattern, response.headers.get("link", ""), re.IGNORECASE
    )
    total_pages: int = 0
    for group1, group2 in page_search:
        page: int = int(group1) if group1 else int(group2)
        if page > total_pages:
            total_pages = page

    if total_pages == 0:
        logger.error("Can`t extract total pages.")
        exit(1)

    return total_pages


def get_liked_repos(
    root_dir: Path, username: str, token: Optional[str] = None
) -> List[Tuple[str, Path]]:
    liked_repos: List[Tuple[str, Path]] = list()
    total_pages: int = _get_total_pages(username=username, token=token)
    headers: Dict[str, str] = {"accept": "application/vnd.github.v3+json"}
    if token:
        headers["Authorization"] = f"token {token}"
    for page in range(1, total_pages + 1):
        response = httpx.get(
            f"https://api.github.com/users/{username}/starred",
            headers=headers,
            params={"page": page, "per_page": 10},
        )
        if not response.is_success:
            logger.error(f"Can`t fetch data: {response.text}")
            break

        for repo in response.json():
            url: str = repo.get("clone_url")
            dir_name: str = repo.get("full_name")
            if not url or not dir_name:
                logger.warning(f"Can`t get url or name of {url=}|{dir_name=}")
                continue

            repo_dir: Path = Path(f"{root_dir}/{dir_name}")
            liked_repos.append((url, repo_dir))

    return liked_repos


def _run_subprocess(url: str, directory: Path) -> bool:
    try:
        subprocess.run(["git", "clone", url, directory], check=True)
    except subprocess.CalledProcessError as msg:
        logger.error(msg)
        return False
    return True


def clone_repos(max_workers: int, repos_for_download: List[Tuple[str, Path]]) -> int:
    with Pool(processes=max_workers) as pool:
        results: List[bool] = pool.starmap(_run_subprocess, repos_for_download)
    return results.count(True)


def compress_repos(directory: Path) -> None:
    shutil.make_archive(directory.name, "zip", directory)
    try:
        shutil.rmtree(directory)
    except PermissionError:
        logger.error(f"Can`t delete {directory.name}")
    return None


def main(
    username: str, directory: str, workers: int, compress: bool, token: str
) -> None:
    assert Path(directory).is_dir()
    date_dir: str = date.today().strftime("%Y%m%d")
    root_dir: Path = Path(f"{directory}/{date_dir}")

    repos_to_clone: List[Tuple[str, Path]] = get_liked_repos(
        root_dir=root_dir, username=username, token=token
    )
    cloned_repos_count: int = clone_repos(
        repos_for_download=repos_to_clone, max_workers=workers
    )

    if len(repos_to_clone) != cloned_repos_count:
        logger.error(
            f"Not all repos are cloned ({cloned_repos_count}/{len(repos_to_clone)})"
        )

    if compress and cloned_repos_count > 0:
        compress_repos(root_dir)
    return None


if __name__ == "__main__":
    logging.basicConfig(
        encoding="utf-8", format="%(asctime)s - %(levelname)s - %(message)s"
    )
    user_args = parser.parse_args()
    freeze_support()
    main(
        username=user_args.user,
        directory=user_args.dir,
        workers=user_args.workers,
        compress=user_args.compress,
        token=user_args.token,
    )
