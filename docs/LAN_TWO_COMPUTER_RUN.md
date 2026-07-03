# Two-computer LAN runtime run

This is the first local-network version of user-contributed compute.

## Computer A: coordinator

```bash
uvicorn api.main_release_ready:app --host 0.0.0.0 --port 8000
```

Find Computer A's LAN IP, for example:

```text
http://192.168.1.10:8000
```

## Computer B: worker

Install optional local model deps if you want the worker to load a transformers checkpoint:

```bash
pip install torch transformers accelerate
```

Start the worker:

```bash
uvicorn api.demo_worker_app:app --host 0.0.0.0 --port 9001
```

Join Computer A:

```bash
python scripts/join_lan_node.py --coordinator http://192.168.1.10:8000 --worker-port 9001 --gpu-memory-gb 0
```

Check joined nodes on Computer A:

```bash
curl http://192.168.1.10:8000/lan/nodes
```

## What this proves

- A normal computer can register as an Ailovanta runtime node.
- The coordinator can store its runtime profile and endpoint.
- The worker can serve owned runtime requests.
- If AutoTrain produces a local transformers artifact and an active binding points to its checkpoint, the worker can load the model directory and generate from it.

## Boundary

This is LAN runtime contribution, not the final global public network. It is the step before NAT traversal, public node admission, stronger anti-cheat, durable distributed artifact placement, and production scheduling.
