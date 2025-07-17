import sched
import time
import logging as log

from curator import config
from curator.describer import run_describer
from curator.imageLocation import load_images

scheduler = sched.scheduler(time.time, time.sleep)

def task():
    log.info("Running scheduled task")
    load_images()
    run_describer()
    scheduler.enter(config.settings.scheduler_interval, 1, task)

def start_scheduler():
    """
    Starts the scheduler to run tasks at regular intervals.
    """
    log.info("Starting scheduler with interval %d seconds", config.settings.scheduler_interval)
    scheduler.enter(0, 1, task)
    scheduler.run()