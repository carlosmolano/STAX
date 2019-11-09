import json
import os
import time

import requests
from redis import Redis
from rq import Queue

from server_utils_new_utils import run_arima_job, run_ets_job, run_statistics_job, run_tbats_job
import pymongo

MONGO_DB_URI = os.environ.get("MONGO_DB_URI")
STAX_BACKEND_API = os.environ.get("STAX_BACKEND_URI")

HEADERS = {
    "X-Auth-Token": os.environ.get("BACKEND_AUTH_TOKEN"),
    "content-type": "application/json"
}

REDIS_HOST = os.environ.get("REDIS_HOST")

# Mongo stuff
client = pymongo.MongoClient(MONGO_DB_URI)
db = client.get_database()

experiments = db["experiments"]
tokens = db["tokens"]
enqueued_experiments = db["enqueued_experiments"]

# Redis Stuff

redis_conn = Redis(host=REDIS_HOST)
q = Queue(connection=redis_conn,
          default_timeout=600)  # no args implies the default queue

while True:
    for pending_experiments in experiments.find({"status": "pending"}):
        # Post Job To Queue
        _series = pending_experiments["_series"]
        _experiment = pending_experiments["_id"]

        userUID = pending_experiments["userUID"]
        user_token = tokens.find_one({"userUID": userUID})["token"]

        experiment_check = list(
            enqueued_experiments.find({"_experiment": str(_experiment)}))

        print(experiment_check)

        if len(experiment_check) == 0:
            # Enqueue Jobs
            print(f"Enqueueing Jobs on {_experiment}")
            jobs_to_do = [
                run_arima_job, run_ets_job, run_statistics_job, run_tbats_job
            ]

            for task in jobs_to_do:
                print(f"Enqueuing Task {task}")
                job = q.enqueue(task,
                                args=(str(_series), str(_experiment)),
                                timeout=600)

            # Enqueue statistics
            enqueued_experiments.insert_one({"_experiment": str(_experiment)})
            print("Enqueued Experiment Sent to DB")

        time.sleep(20)