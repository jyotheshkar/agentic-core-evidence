# Agentic Core — AWS Architecture Case Study

From an approved business requirement to a governed workflow package.

**Status:** AWS design case studies; cloud deployment and runtime validation pending

## Business Scope
A supported document-tracker workflow for an architectural firm. Agentic Core compiles a reusable specification, reviewed operators, tests and controls into a package. Operating that package is a separately authorised activity.

## Constraints
- Single workload account; target Region eu-west-2. Selected Bedrock model/version availability must be checked before deployment.
- One project and supported input schema per run; 1,000 rows and 256 KiB are proposed prototype limits.
- Two total candidate attempts: the first cycle and at most one admitted repair. Reserve once per cycle; bound SDK and transport retries within its resource/deadline limits.
- Reviewed data-only workflow plans. No arbitrary generated-code execution or autonomous permission grants.
- Contract approval, verified-candidate owner acceptance, release authority and child operating authority are distinct.

## Seven Logical Responsibilities
- 1. Intake — Cognito + API Gateway + Lambda: Authenticate and authorise the project operation; atomically persist requirement, receipt and outbox.
- 2. Contract — Lambda + DynamoDB: Clarify supported scope and record approval of the exact contract revision/hash.
- 3. Controller — Step Functions Standard + guards: Admit the run and plan, reserve work, coordinate building, verification, repair and owner acceptance.
- 4. Builder — Bedrock + reviewed Lambda compiler: Propose a finite data-only DAG, validate it deterministically, compile pinned reviewed operators and seal candidate bytes.
- 5. Verifier — Separate Lambda role + S3: Read precise candidate versions; execute trusted tests; record evidence outside the evaluated package.
- 6. PIC — Pinned source/library + IAM: Enforce approval, ownership, permission scope, current verification, bounded repair and release conditions.
- 7. Package — S3 + delivery Lambda + ledger: Release only the accepted verified version; reconcile its actual receipt. Keep child operation separately authorised.

## Architecture Decisions

### Trusted control and AI proposals
Step Functions coordinates phases; deterministic guards and a conditional DynamoDB ledger decide authority. Bedrock proposes a bounded plan.
Alternative / trade-off: A deterministic plan template is simpler for the first supported workflow; a free-running model controller is outside this baseline.

### Durable intake and recoverable handoff
Retain v7.1 intake: transactionally record requirement + receipt + outbox; Streams/relay send to SQS; DLQ and scheduled reconciliation expose unresolved work.
Alternative / trade-off: A direct synchronous handoff is simpler but would require explicit write/start-gap reconciliation. Queue acknowledgement alone does not prove Contract Engine acceptance.

### Bounded construction
Validate a finite DAG and reviewed operator versions before compilation. One candidate-attempt ID spans proposal, compile and verify; rejected proposals consume the attempt.
Alternative / trade-off: More workers or agents can be explored after measuring useful package quality and cost.

### Independent verification
Separate builder and verifier IAM roles. The builder cannot replace trusted fixtures, publish passing evidence or change release records.
Alternative / trade-off: Roles in one account are the prototype isolation choice; separate accounts remain an enterprise extension.

### Two human decisions
Contract approval permits bounded engineering. Exact owner acceptance follows passing verification and binds the candidate and evidence.
Alternative / trade-off: Automatic post-verification release is a different policy and is not the selected v79 case-study design.

### Exact release and truthful delivery
A conditional release intent pins contract, plan, candidate, evidence, owner decision, destination and handoff ID. DELIVERED needs a matching durable receipt; timeout stays unconfirmed.
Alternative / trade-off: Object storage alone establishes availability, not recipient delivery. A candidate package does not grant authority to operate it.

### Keep the deployment bounded
Use managed regional services without an invented customer VPC/NAT/Fargate layer for these reviewed operators. IAM, logging, retention and recovery remain required.
Alternative / trade-off: Private networking or isolated container jobs require a workload need and further threat analysis. Managed Lambda isolation is not a claim of safe arbitrary hostile-code execution.

## Six-Pillar Review

### Operational Excellence
Decision: Correlated run/contract/attempt IDs, explicit phase status and versioned deployment/rollback.
Failure: A worker fails after writing a partial candidate.
Required evidence (pending cloud execution): Trace one run; inspect a tested alert and recover from a runbook without publishing partial content.

### Security
Decision: Current project permissions, exact approvals, scoped builder/verifier/release roles and private artifacts.
Failure: Another owner submits a project ID; builder attempts evidence or release writes.
Required evidence (pending cloud execution): Deny cross-project access, revoked approval, builder self-acceptance and stale acceptance. Review actual IAM policies.

### Reliability
Decision: Durable outbox, deduplication, conditional state and exact evidence bindings.
Failure: Stream relay outage, queue redelivery, stale evidence or lost delivery receipt.
Required evidence (pending cloud execution): Recover an outage beyond the stream retention window; replay duplicates; block a swapped candidate; preserve DELIVERY_UNCONFIRMED.

### Performance Efficiency
Decision: Asynchronous execution; bounded CSV, DAG, tokens and concurrency.
Failure: Oversized payload or demand exceeding a worker/model quota.
Required evidence (pending cloud execution): Measure intake p95, phase latency, throttles and errors on the declared pilot workload. Quota and model availability checks remain predeployment work.

### Cost Optimization
Decision: Two total attempts, capped inference, application work reservations and lifecycle retention.
Failure: Rejected plans and retries amplify calls or retain many versions.
Required evidence (pending cloud execution): Record per-package usage and price the pilot plus 10x volume using dated eu-west-2 rates. A budget alert does not enforce a hard spending cap.

### Sustainability
Decision: Reuse reviewed operators and valid exact results; use demand-based workers and bounded artifact retention.
Failure: Unchanged work is regenerated or obsolete versions accumulate.
Required evidence (pending cloud execution): Compare tokens, compute-seconds and retained bytes per useful package; record reuse. No carbon-reduction claim is made.

## Evidence Status
### Implemented / authored
- Authored reference architecture, directed interfaces and v79 seven-scope AWS mapping.
- Detailed supplied intake design, reviewable rules and documented acceptance-test obligations.
### Proposed AWS design
- The AWS runtime, durable handoff, conditional ledger, Bedrock proposal path, independent verifier and release adapter.
- Two human gates, two total attempts, exact artifact/evidence bindings and recovery paths.
### Pending
- Deploy AWS resources and execute authentication/IAM, recovery, failure and workload tests.
- Measure actual model quality, latency, per-run usage and costs. Confirm selected model access in the target Region.

## Suggested CV Wording
Designed a bounded AWS reference architecture for governed workflow generation using Step Functions, Lambda, DynamoDB, S3 and Bedrock, with revision-bound approvals, independent verification and controlled release; assessed decisions across all six AWS Well-Architected pillars.

## Scope Boundary
The case study is complete as a design baseline when the business scope, deployment diagram, interfaces, decisions, six-pillar review, cost model and evidence boundaries are explainable. Runtime credibility grows through deployment and measured tests; the diagram alone is not implementation evidence.

## Official Sources
- AWS Well-Architected six pillars: https://docs.aws.amazon.com/wellarchitected/latest/framework/the-pillars-of-the-framework.html
- API Gateway JWT authorizers: https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html
- DynamoDB transactions: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/transaction-apis.html
- Step Functions Standard and Express: https://docs.aws.amazon.com/step-functions/latest/dg/choosing-workflow-type.html
- S3 versioning and lifecycle: https://docs.aws.amazon.com/AmazonS3/latest/userguide/Versioning.html
- CloudFront origin access control: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html
- AWS Pricing Calculator: https://calculator.aws/
- DynamoDB Streams retention: https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Streams.html
- Lambda with SQS and partial failures: https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html
