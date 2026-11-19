# teaching

Course notebooks for control, optimal control and reinforcement learning, built on
[minilink](https://github.com/alx87grd/minilink). Each notebook opens in Colab from its badge.

> **minilink version:** the notebooks follow minilink's `dev` branch (`requirements.txt` and each
> notebook's install cell), so they can break while the library changes.
>
> **Branches:** a branch here is the twin of the minilink branch of the same name and installs
> it. `main` installs minilink `dev`; `dev-consolidation` installs minilink `dev-consolidation`.
> When a minilink branch merges into `dev`, its twin merges into `main` with its install lines
> set back to `dev`.

## Folders

The notebooks are sorted by topic, like the chapters of a textbook:

| Folder | Topic |
| --- | --- |
| `python/` | NumPy, Matplotlib and JAX basics |
| `dynamics/` | Modelling and simulation |
| `control/` | Transfer functions, frequency response, state feedback, observers |
| `optimal_control/` | LQR, gradients through a rollout, trajectory optimization, MPC |
| `dynamic_programming/` | Bellman, value iteration, policy evaluation, cost-to-go approximation |
| `reinforcement_learning/` | Gymnasium, policy gradient, PPO, comparisons with DP and LQR |
| `machine_learning/` | Least squares, stochastic gradient descent, function fitting |

A notebook goes where its main idea is, not its plant: a comparison sits with its newest method
(value iteration vs LQR in `dynamic_programming/`, the same plus RL in `reinforcement_learning/`).
A `planning/` folder (RRT, search) comes with its first notebook.

## Courses

A course is a list, not a folder: `courses/<course>.md` links the notebooks its notes cite,
in the order of the notes. A notebook on an active course's list is not renamed or moved while
the course runs.

- [GRO860](courses/gro860.md), reinforcement learning and optimal control (UdeS)
- [GRO501](courses/gro501.md), classical control (UdeS)

## Notebook names

`<plant>_<method>[_vs_<method>…][_sb3].ipynb`, in snake_case. The plant first when there is one
(`pendulum_`, `cartpole_`, `drone_`), then the **method** (`value_iteration`, `lqr`, `ppo`); the
**task** (`minimum_time`, `cost_to_go`) only when the same plant and method would collide.
Comparisons use `_vs_` in the order of the lesson; `_sb3` marks a Stable-Baselines3 twin. The
folder carries the topic: do not repeat it in the name.

## Checks

`tests/run_notebooks.py` runs the notebooks and fails on any cell error; per-notebook
timeouts and the long ones are in `tests/notebooks.json`. CI (`.github/workflows/notebooks.yml`)
runs one job per course on every push and pull request, and every notebook each night.

```bash
pip install -r requirements.txt
python tests/run_notebooks.py --course gro860
python tests/run_notebooks.py --topic control
python tests/run_notebooks.py --notebook cartpole_lqr
```

## Notebooks

Outputs are never stored in git: the `nbstripout` filter strips them at commit (`.gitattributes`).
A new clone sets the filter up once:

```bash
nbstripout --install --attributes .gitattributes
git config filter.nbstripout.clean '"python" -m nbstripout --extra-keys "metadata.kernelspec metadata.language_info metadata.colab metadata.accelerator cell.metadata.colab cell.metadata.id cell.metadata.outputId cell.metadata.executionInfo"'
```
