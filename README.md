# cloudru-agent
A simple tool for dynamic allocation of agents on cloud.ru

By now only WandB sweeps are supported.

## Wandb
```sh
python3 -m cloudru_agent <script-with-args> --region <region> --instance_type <type> --base_image <image> --capacity <num-runs>
```

WandB sweep must be provided in the form ```<login>/<project>/<sweep-id>```.
