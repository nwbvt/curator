from threading import Thread
import time
import logging as log

from curator import config
from curator.describer import run_describer
from curator.imageLocation import load_images

def task():
    while True:
        log.info("Running scheduled task")
        load_images()
        run_describer()
        time.sleep(config.settings.scheduler_interval)

def start_scheduler():
    """
    Starts the scheduler to run tasks at regular intervals.
    """
    t = Thread(target=task, daemon=True)
    t.start()