# Copyright (c) 2020 All Rights Reserved
# Author: William H. Guss, Brandon Houghton


import functools
import time
from typing import List
import os
from pathlib import Path
import subprocess

import boto3
import simple_term_menu as menus
import tqdm

from minerl.data.util.constants import DOWNLOAD_DIR, BUCKET_NAME

s3 = boto3.resource('s3')
bucket = s3.Bucket(BUCKET_NAME)


def non_interactive_download():
    bucket_prefixes = ['2018', '2019', '2020']
    Path(DOWNLOAD_DIR).mkdir(exist_ok=True)

    print("Downloading to {}".format(DOWNLOAD_DIR))

    obj_count = 0
    new_objs = 0
    files_to_download = []
    for bucket_prefix in bucket_prefixes:
        print("Year: ", bucket_prefix)
        for i, obj in enumerate(tqdm.tqdm(bucket.objects.filter(Prefix=bucket_prefix))):
            if i > 200:
                break

            key = obj.key
            filename = key.split("/")[-1]
            if not os.path.isfile(os.path.join(DOWNLOAD_DIR, filename)):
                files_to_download.append((obj.key, DOWNLOAD_DIR, filename))
                new_objs += 1

            obj_count += 1

    print("Total Files: ", obj_count, "New Files", new_objs)
    time.sleep(1)
    print("Beginning download...")
    subprocess.check_call(
        "aws s3 sync s3://{} {}".format(BUCKET_NAME, DOWNLOAD_DIR).split(" "),
    )
    print("Download complete.")


def count_keys(prefix: str, max_keys: int = 1000) -> int:
    """Count the number of keys in the S3 bucket, returning a
    number between 0 and max_keys, inclusive. If the return value
    is max_keys, then that means there are at least `max_keys` keys.

    Note that we can only view up to 1000 keys anyways, due to API restrictions.
    Therefore max_keys is restricted to up to 1000.
    """
    assert max_keys in range(1001)
    count = 0
    for _ in bucket.objects.filter(Prefix=prefix, Delimiter="/"):
        count += 1
        if count == max_keys:
            break
    return count


def build_s3_uri(prefix):
    return f"s3://{BUCKET_NAME}/{prefix}"


@functools.lru_cache(100)
def bucket_ls(prefix, dir_only=True) -> List[str]:
    """If dir_only is False, return all keys. Otherwise, only return 'directories'."""
    if prefix == ".":
        prefix = ""

    if len(prefix) > 0:
        assert prefix.endswith("/")

    reply = bucket.meta.client.list_objects(
        Bucket=bucket.name,
        Delimiter='/',
        Prefix=prefix,
    )
    result = []
    common_prefixes = reply.get('CommonPrefixes')
    for o in common_prefixes or []:
        result.append(o.get('Prefix') or "<MALFORMED COMMONPREFIX ENTRY>")

    if not dir_only:
        contents = reply.get('Contents')
        for o in contents or []:
            result.append(o.get('Key') or "<MALFORMED KEY ENTRY>")

    return result


def bucket_ls_preview(prefix_or_done: str) -> str:
    """Return a preview string of prefix directory contents, or an empty string
    if the argument is 'DONE.'"""
    if prefix_or_done == "DONE":
        return ""
    return "\n".join(bucket_ls(prefix_or_done, dir_only=False))


def interactive_download():
    """Displays a series of interactive shell menus, allowing user to interactively
    choose a particular year, month, or day directory before downloading that choice.
    """
    download_dir = Path(DOWNLOAD_DIR)
    download_dir.mkdir(exist_ok=True, parents=True)
    print("Will download to {}".format(download_dir))

    curr_prefix: str = ""
    for _ in range(4):
        print("Select subdirectory to download, or select DONE to download "
              + build_s3_uri(curr_prefix))

        subdirs = bucket_ls(str(curr_prefix))
        assert all("DONE" != prefix for prefix in subdirs)

        menu = menus.TerminalMenu(
            ["DONE"] + [str(sd) for sd in subdirs],
            preview_command=bucket_ls_preview,
            preview_size=0.5,
            )
        i = menu.show()
        if i is None:  # KeyboardInterrupt. Exit program.
            exit(1)
        elif i == 0:  # Done selecting.
            break
        else:  # Finer selection deeper.
            curr_prefix = subdirs[i - 1]

    aws_call = ["aws", "s3", "sync", build_s3_uri(curr_prefix),
                f"{DOWNLOAD_DIR}/{curr_prefix}"]
    print("About to execute:", aws_call)
    print("Is this ok?")

    menu = menus.TerminalMenu(["yes", "no"])
    i = menu.show()
    if i in [None, 1]:
        exit(1)

    subprocess.check_call(aws_call)
    print("Download complete.")


if __name__ == '__main__':
    non_interactive_download()
