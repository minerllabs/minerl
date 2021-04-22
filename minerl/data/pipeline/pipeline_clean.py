"""Performs common cleaning tasks for deleting MineRL data pipeline results.

By default, deletes ~/minerl.data/* after confirming with the user.
Use the -f flag to skip confirmation.

Interactive mode (-i flag) brings up a menu that allows the user to select particular
stages for which associated output files should be deleted. Note that
selecting every option in interactive mode is not equivalent to noninteractive mode.
"""

import argparse
import collections
import pathlib
import shutil

import bullet

from minerl.data.util import blacklist

SRC = pathlib.Path("~", "minerl.data").expanduser()


def rm(path):
    if path.exists():
        print(f"rm {path}")
        shutil.rmtree(path)
    else:
        print(f"{path} doesn't exist!")


def purge(force):
    yesno = bullet.YesNo(
        f"About to delete {SRC}/* and wipe publish.py blacklist. Are you sure? ",
        default="n",
    )
    ok = force or yesno.launch()
    if not ok:
        print("aborting")
        return
    else:
        for x in SRC.iterdir():
            rm(x)
        wipe_blacklist()


def wipe_s3_replay():
    rm(SRC / "downloaded_sync")


def wipe_merged_mcpr():
    rm(SRC / "output" / "merged")


def wipe_rendered_mcpr():
    rm(SRC / "output" / "rendered")


def wipe_generated_datasets():
    rm(SRC / "output" / "data")


def wipe_blacklist():
    rm(pathlib.Path(blacklist.BLACKLIST_DIR_PATH))


stages = collections.OrderedDict(
    # TODO(shwang): Consider adding in an option for deleting outputs of download
    #  stage, if that turns out to be useful.
    [
        ("Wipe render.py files (pre-dataset mp4, json)", wipe_rendered_mcpr),
        ("Wipe merge.py files (MCPR)", wipe_merged_mcpr),
        ("Wipe generate.py and publish.py files (datasets)", wipe_generated_datasets),
        ("Wipe publish.py blacklist", wipe_blacklist),
    ],
)


def main_interactive():
    check = bullet.Check(
        prompt="Use SPACE to select or deselect cleaning stages. Then press ENTER.",
        choices=tuple(stages.keys()),
    )
    choices = check.launch()
    print()

    if len(choices) == 0:
        print("No choices selected. Did you forget to press SPACE?")
    else:
        for k in choices:
            stages[k]()


def main_console():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="Noninteractive-mode-only flag. Makes sure that program "
             "doesn't prompt user for file deletion confirmation.",
    )
    group.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Open a menu that allows fine-grained selections of pipeline stages"
             " to clean.",
    )

    namespace = parser.parse_args()
    if namespace.interactive:
        main_interactive()
    else:
        purge(force=namespace.force)


if __name__ == "__main__":
    main_console()
