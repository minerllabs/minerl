from minerl.data.pipeline.download3 import download_partition
from minerl.data.pipeline.merge import merge
from minerl.data.pipeline.render import main as render_main
from minerl.data.pipeline.make_minecrafts import main as make_minecrafts_main
from minerl.data.pipeline.generate import main as generate_main
from minerl.data.pipeline.publish import publish

def upload():
    pass

def pipeline():
    make_minecrafts_main()
    download_partition()
    merge(4)
    render_main()
    generate_main()
    publish()
    upload()

if __name__ == '__main__':
    pipeline()
