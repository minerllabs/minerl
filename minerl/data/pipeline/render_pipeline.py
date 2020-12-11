from minerl.data.pipeline.download3 import download_partition
from minerl.data.pipeline.merge import main as merge_main
from minerl.data.pipeline.render import main as render_main
from minerl.data.pipeline.make_minecrafts import main as make_minecrafts_main
from minerl.data.pipeline.generate import main as generate_main
from minerl.data.pipeline.publish import main as publish_main

def upload():
    pass

def pipeline():
    make_minecrafts_main()
    download_partition()
    merge_main()
    render_main()
    generate_main()
    publish_main()
    upload()

if __name__ == '__main__':
    pipeline()
