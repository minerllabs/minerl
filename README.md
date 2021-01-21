# Minecraft Play-and-Record

This branch of minerl allows you to play, record, and upload recordings.
Once the repo is cloned, run from the root:

```bash
./play.sh
```

Or, alternatively, this command should get you started rightaway!

```bash
git clone git@github.com:minerllabs/minerl -b peterz/human_recorder --depth 1 && cd minerl && ./play.sh
```

The only python package this depends on is [boostedblob](https://github.com/hauntsaninja/boostedblob) for file upload, so it
will not mess up your environment.

Once in-game, start or continue a new survival game - your gameplay is recorded when you are in-game, and paused in menus.
The recordings are saved into `~/minerl_recordings/` folder, and are also uploaded to azure.

## Troubleshooting

The errors similar to this:
```
java.lang.UnsatisfiedLinkError: /private/var/folders/qy/yvzdp8vx0h39g66qpx1g8m1r0000gn/T/opencv_openpnp7760931626691299159/nu/pattern/opencv/osx/x86_64/libopencv_java342.dylib: dlopen(/private/var/folders/qy/yvzdp8vx0h39g66qpx1g8m1r0000gn/T/opencv_openpnp7760931626691299159/nu/pattern/opencv/osx/x86_64/libopencv_java342.dylib, 1): Library not loaded: /usr/local/opt/ffmpeg/lib/libavcodec.58.dylib
  Referenced from: /private/var/folders/qy/yvzdp8vx0h39g66qpx1g8m1r0000gn/T/opencv_openpnp7760931626691299159/nu/pattern/opencv/osx/x86_64/libopencv_java342.dylib
```

usually indicate absence of ffmpeg. Install ffmpeg (via homebrew, `brew install ffmpeg` on osx, or `sudo apt install ffmpeg` on debian-like)

The errors like this:
```
[boostedblob] Error when executing request on attempt 3, sleeping for 0.1s before retrying. Details: ServerTimeoutError: Timeout on reading data from socket, None, Request(method='PUT', url='https://oaiagidata.blob.core.windows.net/data/datasets%2Fminerl_recorder%2Fv2%2Frecording20210120-163053.avi', params={'comp': 'block', 'blockid': 'be1tyBKSAAA='}, success_codes=(201,), retry_codes=(408, 429, 500, 502, 503, 504))
```

indicate problems on video upload; can be solved by updating boostedblob (`pip install --upgrade boostedblob`). Note that these errors do not affect recording, only the upload, so the
resulting video and jsonl files with data can be uploaded later manually.
