# cloudru-agent
A simple tool for dynamic allocation of agents on Cloud.ru.

The tool automatically starts new jobs, when previously submitted jobs have finished. It is particularly useful for hyper-parameter tuning, with each job being a single trial.

Example:
```sh
python3 -m cloudru_agent <script-with-args> --region <region> --instance_type <type> --base_image <image> --capacity <num-runs>
```

Extra args:
```
-p: the maximum number of parallel jobs.
--job_desc: job description.
```
