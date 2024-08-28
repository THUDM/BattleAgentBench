# BattleAgentBench: A Benchmark for Evaluating Cooperation and Competition Capabilities of Language Models in Multi-Agent Systems

This repository contains information and code of BattleAgentBench: A Benchmark for Evaluating Cooperation and Competition Capabilities of Language Models in Multi-Agent Systems.

## Introduction

BattleAgentBench consists of two main parts: stage design and agent interaction. In stage design, we design seven stages of three different difficulty levels. In agent interaction, we implement interactions between agents and servers to support evaluation in the above stages.

Next, we will introduce how to evaluate LLMs on BattleAgentBench.

## Install

First, execute the following command to install the necessary dependencies.

```sh
python setup.py develop
```

Second, test the installation. First, use the following command to start the game server. If executed successfully, you will see the game interface pop up.

```sh
python -m battle_city.server_sync  --turn-off-after-end --map s1
```

Then use the following command to start a random agent. If executed successfully, you will see the agent start moving randomly in the game interface.

```sh
python -m battle_city.examples.client_test  --sync
```

Third, you need to configure the key used to call the LLM. For OpenAI models, please configure the corresponding key in `battle_city/examples/agent/model/gpt.py`. For evaluating open-source small language models, such as glm4-9b, we recommend using the API provided by siliconflow, which offers free access to open-source small language models. Please configure the corresponding key in `battle_city/examples/agent/model/silicon.py`.

## Evaluation Pipline

The game runs on a server with a game window and listens for agents. Each agent is a separate client (tank) connected to the game server. The agents control their tanks by sending actions to the server. The game starts when all agents' connections are established.

First, using LLM to play games. For convenience in evaluation, we have placed server startup, clients startup, and parameter configuration into a single script, so you only need to run one script to run games.

```sh
bash run_batch.sh
```

In the script, there are two variables: `models` and `scenarios`, which define the model to be evaluated and the test stage, respectively. Users can modify these two variables according to their needs.

Second, metric calculation. We calculate the score for each game, then aggregate multiple results to calculate the average score.

```sh
cd examples
python compute_metric.py
python compute_summary.py
```

## Acknowledgement

The game used by BattleAgentBench is based on and modified from `battle-city-ai`. We would like to express our sincere gratitude to the creators and contributors for their excellent work. For more information about the original game, please visit: [battle-city-ai](https://github.com/firemark/battle-city-ai)
