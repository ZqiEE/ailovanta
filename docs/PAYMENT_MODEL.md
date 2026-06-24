# Ailovanta Payment Model

Current MVP payment method:

```text
No payment required
```

Ailovanta should not ask for money before the user understands the product value.

The first version should be easy to try:

```text
open product
start guest chat
see value
come back later
then consider account or payment
```

## Current product rule

```text
No paywall.
No subscription wall.
No card collection.
No crypto checkout.
No wallet requirement.
No enterprise invoice flow in the first-use path.
```

## Why payment is deferred

```text
Payment before value reduces conversion.
Wallet before value confuses normal users.
Pricing before product proof distracts from the core experience.
Billing before retention creates unnecessary complexity.
```

## What stays for later

Ailovanta can add payment only after people already use it and need more capacity:

```text
more messages
API credits
saved history
workspace/team usage
private runtime pool
node operator payout
enterprise deployment
```

## Future customer payment methods

When payment is needed later, use normal SaaS payments first:

```text
Card
Apple Pay / Google Pay where supported
Local payment methods where supported
Bank transfer for enterprise invoices
```

Use a mature billing provider later instead of building payment rails too early:

```text
Stripe Billing
Paddle Billing / Merchant of Record option
```

## Future node payout model

Node payout is separate from customer payment.

```text
Node Operator
  -> Runtime Nodes
  -> Work Receipts
  -> Reputation
  -> Payout Profile
  -> Reward Records
```

Wallets can be optional later for:

```text
node operator identity
reward records
contribution proof
optional crypto payout
optional ecosystem credits
```

## What not to do now

Do not force normal chat users to pay.

Do not force enterprise users to pay before there is a clear enterprise product.

Do not force users to pay with crypto.

Do not store seed phrases or private keys.

Do not use a token before the product has real demand.

Do not make billing the center of the MVP.

## Final rule

```text
First prove value.
Then add identity.
Then add payment.
```
