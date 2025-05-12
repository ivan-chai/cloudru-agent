import argparse
import os
import time
import logging

import client_lib


logger = logging.getLogger("main")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)


def parse_arguments():
    parser = argparse.ArgumentParser("Start agent")
    parser.add_argument("script", help="Path to a bash scripts with arguments.", nargs="+")
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
            "script": " ".join(args.script),
            "type": "binary",
            "job_desc": args.job_desc or f"{os.environ['HOSTNAME']}: agent ({args.script})",
            "region": args.region,
            "instance_type": args.instance_type,
            "base_image": args.base_image
        }
        self.n_retries = args.cloud_retries
        self.retry_interval = args.cloud_retry_interval

    def run(self):
        job = client_lib.Job(**self.job_kwargs)
        for _ in range(self.n_retries):
            try:
                job.submit()
                if job.status() != "Failed":
                    logger.info(f"Started {job.job_name}")
                    return job
            except Exception as e:
                logger.error(str(e))
                time.sleep(self.retry_interval)
        raise RuntimeError("Failed to run a job")


def get_status(job, args):
    n_retries = args.cloud_retries
    retry_interval = args.cloud_retry_interval
    for _ in range(n_retries):
        try:
            status = job.status()
            if "=" not in status:
                raise RuntimeError(f"Failed to get status for job {job.job_name}")
            return status.split("=")[-1].strip().lower()
        except Exception as e:
            logger.warning(str(e))
            time.sleep(retry_interval)
    raise RuntimeError(f"Failed to get status for job {job.job_name}")


def main(args):
    runner = JobRunner(args)
    pool = []
    n_runs = 0
    n_failed = 0
    while True:
        # Parse return codes.
        for job in pool:
            status = get_status(job, args)
            if status == "failed":
                logger.info(f"Failed {job.job_name}")
                n_failed += 1
            elif status == "completed":
                logger.info(f"Completed {job.job_name}")
                n_failed = 0
        if n_failed >= args.max_failures:
            raise RuntimeError("The maximum number of failed jobs is reached")
        # Clean pool.
        pool = [job for job in pool
                if get_status(job, args) not in {"completed", "failed"}]
        # Run new jobs.
        if (len(pool) < args.parallel) and (n_runs < args.capacity):
            pool.append(runner.run())
            n_runs += 1
        if (not pool) and (n_runs == args.capacity):
            break
        time.sleep(10)
    logger.info("Finished")


if __name__ == "__main__":
    main(parse_arguments())
