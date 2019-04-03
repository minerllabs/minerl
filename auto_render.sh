    #!/bin/bash

cd ~/cmu-rl/herobraine_parse
# warning: the path is hardcoded in download.py
/usr/bin/python3.6 ./download2.py
./merge.sh
DISPLAY=:0 /usr/bin/python3.6 ./render.py
/usr/bin/python3.6 ./generate.py 6



# 0 20 * * * ~/cmu-rl/herobraine_parse/auto_render.sh >/dev/null 2>&1
