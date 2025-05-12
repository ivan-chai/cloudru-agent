import argparse
import os
import time

import pwd
import client_lib


def parse_arguments():
    parser = argparse.ArgumentParser("Start agent")
    parser.add_argument("script", help="Path to a bash scripts with arguments.")
    parser.add_argument("--region", help="Cloud.ru region", required=True)
    parser.add_argument("--instance_type", help="Cloud.ru instance type", required=True)
    parser.add_argument("--base_image", help="Cloud.ru Docker image", required=True)
    parser.add_argument("--job_desc", help="Job description")
    parser.add_argument("--capacity", type=int, help="The number of runs", default=100)
    parser.add_argument("-p", "--parallel", type=int, help="The maximum number of concurrent jobs", default=1)
    parser.add_argument("--max-failures", type=int, help="The maximum number of failed tasks (consecutive) before stopping", default=3)
    parser.add_argument("--cloud-retries", type=int, help="The maximum number of retries after connection errors", default=3)
    parser.add_argument("--cloud-retry-interval", type=int, help="The retry time interval in seconds", default=60)
    return parser.parse_args()


class JobRunner:
    def __init__(self, args):
        self.job_kwargs = {
            "script": args.script,
            "type": "binary",
            "job_desc": args.job_desc or f"{pwd.getpwuid(os.getuid())}: agent ({args.script})",
            "region": args.region,
            "instance_type": args.instance_type,
            "base_image": args.base_image
        }
        self.n_retries = args.cloud_retries
        self.retry_interval = args.cloud_retry_interval

    def run(self):
        job = client_lib.Job(self.job_kwargs)
        for _ in range(self.n_retries):
            try:
                job.submit()
                if job.status() != "Failed":
                    return job
            except Exception as e:
                print(e)
                time.sleep(self.retry_interval)
        raise RuntimeError("Failed to run a job")


def main(args):
    runner = JobRunner(args)
    pool = []
    n_runs = 0
    n_failed = 0
    while True:
        # Parse return codes.
        for job in pool:
            if job.status() == "Failed":
                n_failed += 1
            elif job.status() == "Completed":
                n_failed = 0
        if n_failed >= args.max_failures:
            raise RuntimeError("The maximum number of failed jobs is reached")
        # Clean pool.
        pool = [job for job in pool
                if job.status() not in {"Completed", "Failed"}]
        # Run new jobs.
        if (len(pool) < args.parallel) and (n_runs < args.capacity):
            pool.append(runner.run())
            n_runs += 1
        if (not pool) and (n_runs == args.capacity):
            break
        time.sleep(10)
    print("Finished")


if __name__ == "__main__":
    main(parse_arguments())
