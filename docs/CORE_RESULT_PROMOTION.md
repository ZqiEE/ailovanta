# Core Result Promotion

## Purpose

This layer connects `ailovanta-core` training output back into the public runtime layer.

## Flow

```text
ailovanta-core result manifest
-> public core result store
-> runtime model manifest
-> trusted runtime pool
-> owned model route
```

## Register a core result

Core produces a manifest with schema:

```text
ailovanta.core_result.v1
```

The public repo stores it through `CoreResultStore`.

## Runtime registration

A promotable core result becomes a runtime model manifest only when:

```text
promotion_status is candidate or promoted
accepted_candidates > 0
next_model_version exists
```

The runtime model is registered as:

```text
model_id: ailovanta-owned
version: next_model_version
privacy_level: protected
allowed_pools: trusted_runtime_pool, enterprise_pool
```

## Next step

Wire `api.core_result_api.router` into `api.main`, then connect `/ailovanta/v1/chat` owned-model mode to `OwnedModelRuntime`.
