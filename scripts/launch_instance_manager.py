import minerl
import coloredlogs
import logging

coloredlogs.install(logging.DEBUG)
from minerl.env.malmo import launch_instance_manager

if __name__ == "__main__":
    launch_instance_manager()
