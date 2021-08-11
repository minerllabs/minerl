# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton
import argparse
import os
from urllib.error import URLError
from urllib.error import HTTPError

import shutil
import tarfile
import time
from threading import Thread

from minerl.data.util import download_with_resume

import logging

from minerl.data.version import DATA_VERSION, assert_version
from minerl.herobraine import envs
import tempfile
from typing import Optional
import coloredlogs

logger = logging.getLogger(__name__)


def download(
        directory: Optional[str] = None,
        environment: Optional[str] = None,
        competition: Optional[str] = None,
        resolution: str = 'low',
        texture_pack: int = 0,
        update_environment_variables: bool = True,
        disable_cache: bool = False,
) -> None:
    """Low-level interface for downloading MineRL dataset.

    Using the `python -m minerl.data.download` CLI script is preferred because it performs
    more input validation and hides internal-use arguments.

    Run this command with `environment=None` and `competition=None` to download a minimal
    dataset with 2 demonstrations from each environment.
    Provide the `environment` or `competition` arguments to download a full dataset for
    a particular environment or competition.

    Args:
        directory: Destination folder for downloading MineRL datasets. If None, then use
            the `MINERL_DATA_ROOT` environment variable, or error if this environment
            variable is not set.
        environment: The name of a MineRL environment or None. If this argument is the
            name of a MineRL environment and `competition` is None, then this function
            downloads the full dataset for the specifies MineRL environment.

            If both `environment=None` and `competition=None`, then this function
            downloads a minimal dataset.
        competition: The name of a MineRL competition ("diamond" or "basalt") or None. If
            this argument is the name of a MineRL environment and `competition` is None,
            then this function downloads the full dataset for the specified MineRL
            competition.

            If both `environment=None` and `competition=None`, then this function
            downloads a minimal dataset.
        resolution: For internal use only. One of ['low', 'high'] corresponding to video
            resolutions of [64x64,1024x1024] respectively (note: high resolution is not currently
            supported).
        texture_pack: For internal use only. 0: default Minecraft texture
            pack, 1: flat semi-realistic texture pack.
        update_environment_variables: For internal use only. If True, then export of
            MINERL_DATA_ROOT environment variable (note: for some os this is only for the
            current shell).
        disable_cache: If False (default), then the tar download and other temporary
            download files are saved inside `directory`.

            If disable_cache is False on
            a future call to this function and temporary download files are detected, then
            the download is resumed from previous download progress. If disable_cache is
            False on a future call to this function and the completed tar file is
            detected, then the download is skipped entirely and we immediately extract the tar
            to `directory`.
    """
    assert texture_pack in (0, 1)
    if competition is not None and environment is not None:
        raise ValueError(
            f"At most one of the `competition={competition}` and `environment={environment}` "
            "arguments can be non-None."
        )

    if competition is None and environment is None:
        logger.warning("DOWNLOADING ONLY THE MINIMAL DATASET by default.")
        logger.info("For information on downloading full "
                    "datasets see the docstring for minerl.data.download or "
                    "https://minerl.readthedocs.io/en/latest/tutorials/data_sampling.html#downloading-the-minerl-dataset-with-minerl-data-download"  # noqa: E501
                    )

    if directory is None:
        if 'MINERL_DATA_ROOT' in os.environ and len(os.environ['MINERL_DATA_ROOT']) > 0:
            directory = os.environ['MINERL_DATA_ROOT']
        else:
            raise ValueError("Provided directory is None and $MINERL_DATA_ROOT is not defined")
    elif update_environment_variables:
        os.environ['MINERL_DATA_ROOT'] = os.path.expanduser(
            os.path.expandvars(os.path.normpath(directory)))

    if os.path.exists(directory):
        try:
            assert_version(directory)
        except RuntimeError as r:
            if r.comparison == "less":
                raise r
            logger.error(str(r))
            logger.error("Deleting existing data and forcing a data update!")
            try:
                shutil.rmtree(directory)
            except Exception as e:
                logger.error("Could not delete {}. Do you have permission?".format(directory))
                raise e
            try:
                os.makedirs(directory)
            except:
                pass

    download_path = os.path.join(directory,
                                 'download') if not disable_cache else tempfile.mkdtemp()
    mirrors = [
        "https://minerl.s3.amazonaws.com/",
        "https://minerl-asia.s3.amazonaws.com/",
        "https://minerl-europe.s3.amazonaws.com/"]

    if environment is None and competition is None:
        competition = 'minimal_all'

    if competition is not None:
        logger.info("Downloading dataset for {} competition(s)".format(competition))
        competition_string = competition + '_'
        if competition == 'minimal_all':
            min_str = '_minimal'
            competition_string = ''
        else:
            min_str = ''
        filename = "v{}/{}data_texture_{}_{}_res{}.tar".format(DATA_VERSION,
                                                               competition_string,
                                                               texture_pack,
                                                               resolution,
                                                               min_str)
    else:
        logger.info(f"Downloading dataset for {environment} to {directory}")
        filename = f"v{DATA_VERSION}/{environment}.tar"

    urls = [mirror + filename for mirror in mirrors]

    try:
        # logger.info("Fetching download hash ...")
        # obj.fetch_hash_sums() 
        # TODO: Add flag to verify hash
        # logger.warning("As of MineRL 0.3.0 automatic hash checking has been disabled.")
        logger.info("Starting download ...")
        dest_file = os.path.join(download_path, filename)
        os.makedirs(os.path.dirname(dest_file), exist_ok=True)
        download_with_resume(urls, dest_file)
    except HTTPError as e:
        logger.error("HTTP {} error encountered when downloading files!".format(e.code))
        if environment is not None:
            logger.error("Is \"{}\" a valid minerl environment?".format(environment))
        return None
    except URLError as e:
        logger.error("URL error encountered when downloading - please try again")
        logger.error(e.errno)
        return None
    except TimeoutError as e:
        logger.error("Timeout encountered when downloading - is your connection stable")
        logger.error(e.errno)
        return None
    except IOError as e:
        logger.error("IO error encountered when downloading - please try again")
        logger.error(e.errno)
        return None
    except KeyboardInterrupt as e:
        logger.error("Download canceled by user")
        return None

    logging.info('Success - downloaded {}'.format(dest_file))

    logging.info('Extracting downloaded files - this may take some time')
    with tarfile.open(dest_file, mode="r:*") as tf:
        t = Thread(target=tf.extractall(path=directory))
        t.start()
        while t.is_alive():
            time.sleep(5)
            logging.info('.', end='')

        logging.info('Success - extracted files to {}'.format(directory))

    if disable_cache:
        logging.info('Deleting cached tar file')
        os.remove(dest_file)

    try:
        assert_version(directory)
    except RuntimeError as r:
        logger.error(str(r))

    return directory


def main():
    description = """
    Data download script for MineRL Diamond and BASALT competitions. Run this script with
    no arguments to download a minimal dataset containing two demonstrations for every
    environment.

    See https://minerl.readthedocs.io/en/latest/tutorials/data_sampling.html
    for example usage of this script.
    """
    parser = argparse.ArgumentParser(
        description=description,
    )

    # Error if both --environment and --competition provided
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--environment",
        help="""
        Download the full dataset for a particular environment, e.g
        "MineRLBasaltBuildVillageHouse-v0".
        """,
        type=str,
        action="store",
        default=None,
    )
    group.add_argument(
        "--competition",
        help="Download the full dataset for a particular competition.",
        type=str,
        choices=["diamond", "basalt"],
        default=None,
    )
    args = parser.parse_args()
    coloredlogs.install(logging.DEBUG)

    # Sanity check that args.environment is valid before we proceed to download.
    if args.environment is not None:
        env_names = [env_spec.name for env_spec in envs.HAS_DATASET_ENV_SPECS]
        if args.environment not in env_names:
            logger.error(f"Invalid environment value, '{args.environment}'")
            logger.error(f"Allowed values are: {env_names}")
            exit(1)

    download(environment=args.environment, competition=args.competition)


if __name__ == '__main__':
    main()
