# Node Trust

Node proof verification now has a local trust registry.

## Register node

```bash
python scripts/node_trust.py register --node-id node-1 --secret example-secret --trust-score 0.9
```

## Disable node

```bash
python scripts/node_trust.py disable --node-id node-1
```

## Proof export

```bash
python scripts/export_parcel_receipts.py --require-proof
```

## Environment

```text
AILOVANTA_NODE_TRUST_PATH=runtime_data/node_trust.sqlite3
AILOVANTA_NODE_SECRETS_JSON={"node-1":"example-secret"}
```

The registry stores secret hashes and node status. The raw secret is still only supplied temporarily for HMAC proof verification.
