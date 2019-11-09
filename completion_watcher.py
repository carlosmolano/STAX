import json
import os
import time

import requests
from redis import Redis
from rq import Queue

from server_utils_new_utils import run_arima_job, run_ets_job, run_statistics_job, run_tbats_job, get_experiment, put_experiment
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

while True:
    for experiment in experiments.find({"status": "pending"}):
        try:
            if ((len(experiment["_models"]) == 3) &
                (experiment["_decomposition"] is not None) &
                (experiment["_autocorrelation"] is not None)):

                print("Updating Experiments Data")
                experiment_data = get_experiment(experiment["_id"])
                experiment_data["status"] = "complete"
                res = put_experiment(experiment["_id"], experiment_data)
                print(f"Experiment Update compete with status code {res}")
                assert res.status_code == 200
        except:
            print(
                "An Error occured. Experiment might not be ready. Sleeping for 10 seconds."
            )
    time.sleep(10)