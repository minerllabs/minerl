"""Chooses MineRL data processing pipeline stages, then runs them in the correct order.

The merge stage makes sure to compile a MineRL parser program first, and the final
  publishing stage makes sure to write the necessary version file first.

By default the render stage generates low-res videos of dimensions 64x64.
To generate videos of a different resolution, set or `export` the
MINERL_RENDER_WIDTH and MINERL_RENDER_HEIGHT environment variables.
(e.g.: `export MINERL_RENDER_WIDTH=1920 MINERL_RENDER_HEIGHT=1080`).

Alternatively, use the --high_res flag in this script to automatically set 1920x1080
resolution.
"""

import argparse
import collections
import contextlib
import os
import pathlib
import shutil
import subprocess
from typing import Mapping, Optional, Sequence

import bullet

from minerl import data
from minerl.data.pipeline import download2, generate, make_minecrafts, merge, publish, render


def download_fn(**_):
    download2.interactive_download()


PARSER_DIR = pathlib.Path(merge.__file__).parent / "parser"


def _merge_compile_parser():
    """Running the merge.py stage requires that we compile a C binary first."""
    # TODO(shwang): Move this code into the merge script itself.
    if not PARSER_DIR.is_dir():
        raise FileNotFoundError(
            "Failed to compile demonstration data parser because "
            f"PARSER_DIR={PARSER_DIR} is not a directory or could not be found.",
        )
    if shutil.which("make") is None:
        raise FileNotFoundError(
            "Failed to compile demonstration data parser because "
            "make is not installed.",
        )

    result = subprocess.run(["make", "-C", str(PARSER_DIR)])
    result.check_returncode()


def merge_fn(n_workers, parallel, regex_pattern):
    del regex_pattern
    _merge_compile_parser()
    merge.main(parallel=parallel, n_workers=n_workers)


def _render_make_minecrafts(n_workers):
    # TODO(shwang): Move this code into the merge script itself.
    if not make_minecrafts.check_installed(n_workers):
        make_minecrafts.main(n_workers)


def render_fn(n_workers, parallel, regex_pattern):
    _render_make_minecrafts(n_workers)
    render.main(parallel=parallel, n_workers=n_workers, regex_pattern=regex_pattern)


VERSION_PATH = pathlib.Path("~/minerl.data/output/data/VERSION").expanduser()


def _publish_generate_version_file():
    """Publish requires this text file as as an internal versioning sanity check."""
    path = VERSION_PATH
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w") as f:
        f.write(str(data.DATA_VERSION))
    print(f"Wrote to {path}.")


def publish_fn(parallel, n_workers, regex_pattern):
    _publish_generate_version_file()
    publish.main(n_workers=n_workers, parallel=parallel, regex_pattern=regex_pattern)


interactive_stages = collections.OrderedDict(
    [
        ("Download demonstration data", download_fn),
    ],
)

noninteractive_stages = collections.OrderedDict(
    [
        ("Run the merge.py script", merge_fn),

        # TODO: Consider automatically running make_minecraft.py if necessary?
        ("Run the render.py script", render_fn),
        ("Run the generate.py script", generate.main),
        ("Run the publish.py script", publish_fn),
    ],
)

# All stages.
stages = collections.OrderedDict()
stages.update(interactive_stages)
stages.update(noninteractive_stages)


DEFAULT_KWARGS = {
    "parallel": False,
    "n_workers": 1,
}


def _execute_stages(
        stage_names: Sequence[str],
        pipeline_kwargs: Optional[dict] = None,
) -> None:
    """Runs stages in sequence given the keys from the `stages` OrderedDict."""
    invalid_keys = set(stage_names) - set(stages.keys())
    if len(invalid_keys) > 0:
        raise ValueError(f"Invalid stage keys: {tuple(invalid_keys)}.")

    if pipeline_kwargs is None:
        pipeline_kwargs = DEFAULT_KWARGS

    for name in stage_names:
        print(f"BEGIN: {name}")
        stages[name](**pipeline_kwargs)
        print(f"END: {name}\n")


DOWNLOAD_DIR = pathlib.Path("~", "minerl.data", "downloaded_sync").expanduser()


def choose_stages_and_execute(
        interactive: bool = True,
        pipeline_kwargs: Optional[dict] = None,
) -> None:
    """Chooses MineRL data processing pipeline stages to execute, then executes them
    in sequence.

    Args:
        interactive: If False, then run all of the noninteractive stages in sequence.
            If True, bring up a command-line menu that asks users to choose which
            jobs, including interactive jobs, to run.
        pipeline_kwargs: Keyword arguments to be passed to each pipeline stage. Unused
            kwargs are silently ignored.
    """
    if interactive:
        check = bullet.Check(
            prompt="Use SPACE to select or deselect stages. Then press ENTER.",
            choices=tuple(stages.keys()),
        )

        # Launch a Bullet multiple-choice menu where we check all of the stages by
        # default.
        default_indices = list(range(len(stages)))
        stage_names = check.launch(default=default_indices)
    else:
        if not DOWNLOAD_DIR.exists():
            print(
                "ERROR: "
                f"{DOWNLOAD_DIR} does not exist, so noninteractive mode will fail. "
                "Run in interactive mode (-i) first to download files.\n",
            )
            exit(1)
        stage_names = tuple(noninteractive_stages.keys())

    if len(stage_names) == 0:
        print("Nothing to do, as no stage names were selected.")
    else:
        _execute_stages(stage_names, pipeline_kwargs)


@contextlib.contextmanager
def env_var_change_ctx(changes_dict: Mapping[str, str]):
    """Context for temporarily making changes to environment variables."""
    old_environ = os.environ.copy()
    try:
        for k, v in changes_dict.items():
            os.environ[k] = v
        yield
    finally:
        os.environ = old_environ


def main() -> None:
    parser = argparse.ArgumentParser("MineRL Data Pipeline Omnibus Script")
    parser.add_argument(
        "-j",
        "--jobs",
        action="store",
        default=1,
        type=int,
        help="Number of jobs to run in parallel.",
    )
    parser.add_argument(
        "--high_res",
        action="store_true",
        help=("When running the render stage, use 1920x1080 resolution by locally "
              "overriding the MINERL_RENDER_{WIDTH,HEIGHT} variables.")
    )
    parser.add_argument(
        "-m",
        "--match",
        type=str,
        help=("A regex pattern, for example, 'accomplished_pattypan_squash_ghost.*' "
              "which is used by the render stage to select a particular subset of "
              "demonstrations to process."
              )
        # XXX: Could add regex functionality to the generate and publish stages later.
    )

    single_stage_mapping = collections.OrderedDict(
        [
            ("download", download_fn),
            ("merge", merge_fn),
            ("render", render_fn),
            ("generate", generate.main),
            ("publish", publish_fn),
        ],
    )

    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        help="Use a menu to select scripts, including interactive scripts.",
    )
    group.add_argument(
        "-S",
        "--single_stage",
        action="store",
        choices=list(single_stage_mapping.keys()),
        default=None,
        help="Instead of running all noninteractive stages, run a particular stage.",
    )

    opt = parser.parse_args()
    parallel = opt.jobs >= 2
    if opt.jobs < 1:
        raise ValueError("Must specify positive integer for jobs, but got: {opt.jobs}")

    pipeline_kwargs = dict(parallel=parallel, n_workers=opt.jobs, regex_pattern=opt.match)
    env_changes = {}
    if opt.high_res:
        env_changes["MINERL_RENDER_WIDTH"] = "1920"
        env_changes["MINERL_RENDER_HEIGHT"] = "1080"

    with env_var_change_ctx(env_changes):
        if opt.single_stage is not None:
            stage_fn = single_stage_mapping[opt.single_stage]
            stage_fn(**pipeline_kwargs)
        else:
            choose_stages_and_execute(
                interactive=opt.interactive,
                pipeline_kwargs=pipeline_kwargs,
            )


if __name__ == "__main__":
    main()
