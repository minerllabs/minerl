#!/bin/bash

cd ~/cmu-rl/herobraine_parse
# warning: the path is hardcoded in download.py
/home/cmr-rl/herobraine_parse/python3 ./download.py
./merge.sh
home/cmr-rl/herobraine_parse/python3 ./render.py
home/cmr-rl/herobraine_parse/python3 ./generate.py



# 0 20 * * * ~/cmu-rl/herobraine_parse/auto_render.sh >/dev/null 2>&1