"""
For internal use only. Requires privileged AWS credentials.

This script syncs recorded player trajectories (raw format) from the
"s3://pizza-party" bucket to the DOWNLOAD_DIR, ~/minerl.data/downloaded_sync/.

Other scripts can process these downloaded trajectories to a format that is usable by
`minerl.data.make()` (i.e. `minerl.data.DataPipeline`).

Protip: If you need to use a particular AWS profile for this script, execute
`export AWS_PROFILE=$minerl_profile` before running.
"""

import boto3
import tqdm
import os
import subprocess
import time
from pathlib import Path
from minerl.data.util.constants import DOWNLOAD_DIR, BUCKET_NAME


s3 = boto3.resource('s3')
bucket = s3.Bucket(BUCKET_NAME)


def main():
    bucket_prefixes = ['2018', '2019', '2020']
    Path(DOWNLOAD_DIR).mkdir(exist_ok=True, parents=True)

    print("Downloading to {}".format(DOWNLOAD_DIR))

    # Output the number of files before downloading.
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


if __name__ == '__main__':
    main()
