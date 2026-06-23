# Ailovanta Model Runtime Architecture

## Problem

Large models are expensive in two separate ways:

1. Storage and distribution of model files.
2. Runtime inference and training access.

Ailovanta must not depend on one central server for either problem.

## Wrong design

Do not design Ailovanta as:

```text
All model files live on one official server.
Every node downloads from that server.
Every inference request goes back to that server.
The server is the only trusted party.
```

That design creates high bandwidth cost, centralization risk, trust problems, and a single point of failure.

## Correct design

Ailovanta should use a four-layer model runtime network:

```text
1. Model Registry Layer
2. Artifact Distribution Layer
3. Runtime Pool Layer
4. Access Router Layer
```

## Layer 1: Model Registry

The registry stores small records only:

- model id
- version
- manifest hash
- artifact CID or object reference
- chunk hashes
- signatures
- allowed runtime tier
- evaluation score
- status

The registry does not store model weights.

## Layer 2: Artifact Distribution

Model files are stored off-chain and distributed through multiple sources:

- node cache
- regional mirror
- object storage
- IPFS-like content addressing
- storage-market providers
- official seed nodes as fallback only

A model is split into chunks. Every chunk is verified by hash before use.

Nodes do not need to trust the server that sends the file. They only need to verify the manifest and chunk hashes.

## Layer 3: Runtime Pool

Models should not be loaded by every node.

Ailovanta should maintain runtime pools by capability:

```text
CPU pool:
  data cleaning, lightweight scoring, metadata tasks

Small GPU pool:
  1B / 3B / 7B quantized inference, embeddings, adapter jobs

Large GPU pool:
  14B / 70B inference, batching, LoRA jobs

Storage pool:
  model chunks, adapter chunks, dataset shards

Validator pool:
  output checks, score reports, contribution validation

Trusted runtime pool:
  private models, protected adapters, controlled execution
```

## Layer 4: Access Router

The access router decides where each request should run.

It should consider:

- model id
- model tier
- privacy level
- latency target
- node trust score
- node hardware
- node cache state
- current load
- price
- region
- validator availability

The router should not always send requests to the same place.

## Runtime request flow

```text
User request
-> Access Router
-> select runtime pool
-> choose node or node group
-> check model manifest
-> check cached chunks
-> download missing chunks from peers/storage/seeds
-> verify hashes
-> load model or adapter
-> run inference/training task
-> return output
-> validator samples/checks result
-> record usage, score, and reward
```

## Avoid full model downloads

Most nodes should not download full large models.

Use:

- quantized models for smaller devices
- adapters instead of full fine-tuned model copies
- model chunk caching
- hot/cold model tiering
- MoE expert routing when applicable
- RAG for knowledge growth instead of weight growth
- model version manifests instead of monolithic files

## Hot and cold strategy

```text
Hot base models:
  cached by high-capacity runtime nodes

Hot adapters:
  cached near active users and workloads

Cold models:
  stored in distributed storage and loaded on demand

Private models:
  available only to trusted runtime pools

Core models:
  never sent to public nodes
```

## Trust model

Do not ask nodes to trust a central server.

Use:

```text
manifest hash
-> chunk hash
-> local verification
-> signed model version
-> validator reports
-> reputation updates
```

The server can lie, but it cannot make a wrong chunk match the expected hash.

## Performance model

The main bottlenecks are:

- cold model download
- model loading
- KV cache memory
- network latency between split model stages
- GPU memory fragmentation
- request batching
- validator overhead

Ailovanta should reduce bottlenecks through:

- warm runtime pools
- model prefetching
- continuous batching
- KV cache reuse where possible
- locality-aware routing
- hot adapter cache
- avoiding cross-region model pipelines for low-latency requests

## Best early implementation

The best MVP implementation is not a fully decentralized 70B pipeline.

Best early path:

```text
Phase 1:
  local runtime + model registry + cache manifest

Phase 2:
  node capability registry + router chooses local/small/large GPU pool

Phase 3:
  distributed artifact cache + hash verified downloads

Phase 4:
  warm inference pools for popular models

Phase 5:
  trusted runtime pool for private/protected models

Phase 6:
  experimental split-model inference for large public models
```

## Final principle

Ailovanta should not move every request to the model.

Ailovanta should move the request to the best already-warm model runtime whenever possible.

```text
Do not centralize the model.
Do not make every node download everything.
Do not trust servers.
Do route to verified, warm, capable runtimes.
```
