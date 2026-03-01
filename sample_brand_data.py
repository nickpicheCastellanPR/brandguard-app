"""
sample_brand_data.py — Complete Meridian Labs sample brand data.

Single source of truth for the demo brand that ships with Signet Studio.
This data populates every field the Brand Architect supports so the sample
brand achieves the highest possible calibration score ("Fortified" across
all 5 voice clusters).

Usage:
    from sample_brand_data import SAMPLE_BRAND
    profile_data = SAMPLE_BRAND["profile_data"]
    display_name = SAMPLE_BRAND["display_name"]
"""
from __future__ import annotations

import json

# ---------------------------------------------------------------------------
# Message House pillars as a Python list (serialised to JSON for storage)
# ---------------------------------------------------------------------------
_PILLARS = [
    {
        "name": "Observability Without the PhD",
        "tagline": "Powerful tools shouldn't require a specialist to operate.",
        "headline_claim": (
            "Most observability platforms were built for the SRE team and nobody else. "
            "Meridian was built for every developer who's ever stared at a dashboard "
            "and had no idea what it was telling them."
        ),
        "proof_1": (
            "Setup to first actionable alert in under 15 minutes — no configuration "
            "files, no query language to learn."
        ),
        "proof_2": (
            "89% of Meridian users report resolving incidents faster within their first "
            "month, based on Q4 2025 customer survey (n=340)."
        ),
        "proof_3": (
            "Used by engineering teams at 200+ companies from seed to Series D, including "
            "teams that ripped out Datadog and Grafana because the learning curve was "
            "killing onboarding velocity."
        ),
    },
    {
        "name": "Infrastructure-Grade Reliability",
        "tagline": "Your monitoring tool can't be the thing that goes down.",
        "headline_claim": (
            "We process 2.1 billion events per day across three continents with 99.97% "
            "uptime over the trailing 12 months. When your production system is on fire, "
            "Meridian is the tool that's still working."
        ),
        "proof_1": (
            "Multi-region architecture with automatic failover — no single point of "
            "failure between you and your data."
        ),
        "proof_2": (
            "P99 query latency under 200ms even during peak incident response when "
            "everyone's watching the same dashboard."
        ),
        "proof_3": (
            "SOC 2 Type II certified. Your data is encrypted in transit and at rest. "
            "We passed our last audit with zero findings."
        ),
    },
    {
        "name": "Pricing That Doesn't Punish Growth",
        "tagline": "Your observability bill shouldn't scale faster than your revenue.",
        "headline_claim": (
            "The dirty secret of the observability industry is that most vendors make "
            "more money when your system gets more complex. We charge per seat, not per "
            "byte — so instrumenting more of your stack doesn't blow up your bill."
        ),
        "proof_1": (
            "Flat per-seat pricing with unlimited data ingestion. No per-GB charges, "
            "no retention fees, no surprise overages."
        ),
        "proof_2": (
            "Average customer saves 40-60% compared to their previous observability "
            "vendor within the first billing cycle."
        ),
        "proof_3": (
            "No annual contracts required. Month-to-month from day one. If we're not "
            "earning your renewal every month, that's our problem."
        ),
    },
]

# ---------------------------------------------------------------------------
# Voice DNA blob — 15 samples across 5 clusters (3 each)
# The calibration scorer counts occurrences of "CLUSTER: {NAME}" (upper-cased).
# Each [ASSET: CLUSTER: ... ] header must appear at least 3x per cluster
# for the cluster to be marked "FORTIFIED" (9 pts each, 45 pts total).
# ---------------------------------------------------------------------------
_VOICE_DNA = """
[ASSET: CLUSTER: CORPORATE AFFAIRS | SENDER: COMMUNICATIONS | AUDIENCE: MEDIA / PUBLIC | SOURCE: Press Release — Series B | DATE: 2025-09-15]
FOR IMMEDIATE RELEASE

Meridian Labs Raises $42M Series B to Expand Observability Platform for Development Teams

SAN FRANCISCO, September 15, 2025 — Meridian Labs, the observability platform built for development teams that need clarity without complexity, today announced $42 million in Series B funding led by Sequoia Capital with participation from Craft Ventures and existing investors.

The round brings total funding to $58 million and will accelerate product development, expand the engineering team, and support international growth.

"Most observability tools were built for specialists," said Maya Chen, co-founder and CEO of Meridian Labs. "We built Meridian for every developer on the team — the person who touches a dashboard twice a month and needs to understand what they're seeing immediately. This funding lets us double down on that mission."

Since launching in 2023, Meridian has grown to serve over 200 engineering teams processing 2.1 billion events daily. The platform's per-seat pricing model — which charges teams for access rather than data volume — has driven adoption among Series A through Series D companies seeking predictable observability costs during periods of rapid infrastructure growth.

Key milestones include 99.97% platform uptime over the trailing twelve months, average customer cost savings of 40-60% compared to previous vendors, and a net revenue retention rate of 138%.

Meridian Labs is headquartered in San Francisco with engineering teams in Austin and London.

Media Contact:
Jamie Torres, Head of Communications
press@meridianlabs.dev
----------------

[ASSET: CLUSTER: CORPORATE AFFAIRS | SENDER: COMMUNICATIONS | AUDIENCE: MEDIA / PUBLIC | SOURCE: Fact Sheet — Platform Overview | DATE: 2025-09-15]
MERIDIAN LABS — PLATFORM FACT SHEET

Company: Meridian Labs, Inc.
Founded: 2023
Headquarters: San Francisco, CA
Funding: $58M total (Series B, September 2025)
Investors: Sequoia Capital (lead), Craft Ventures
Team Size: 85 employees across SF, Austin, London

Platform:
Meridian is an observability platform designed for full development teams, not just SRE specialists. The platform provides monitoring, alerting, and incident response tools with an interface optimized for developers who need fast answers without deep query expertise.

Key Metrics:
- 200+ engineering teams
- 2.1 billion events processed daily
- 99.97% uptime (trailing 12 months)
- P99 query latency: <200ms
- Average setup time: 15 minutes to first actionable alert
- SOC 2 Type II certified

Pricing Model:
Per-seat, flat rate. Unlimited data ingestion. No per-GB charges. No retention fees. No annual contract required.

Product Capabilities:
- Real-time infrastructure monitoring
- Customizable alerting with context-aware routing
- Incident timeline reconstruction
- Log aggregation with natural language search
- Distributed tracing across microservices
- Team dashboards with role-based defaults

Integration Support:
AWS, GCP, Azure, Kubernetes, Docker, Terraform, GitHub Actions, GitLab CI, Jenkins, PagerDuty, Slack, Jira, Linear

Competitive Position:
Meridian competes in the observability market by prioritizing accessibility for entire development teams over power-user depth. The platform is positioned as the observability tool teams adopt when they outgrow basic monitoring but find enterprise platforms too complex for broad team adoption.
----------------

[ASSET: CLUSTER: CORPORATE AFFAIRS | SENDER: COMMUNICATIONS | AUDIENCE: MEDIA / PUBLIC | SOURCE: Press Release — SOC 2 Certification | DATE: 2026-01-08]
FOR IMMEDIATE RELEASE

Meridian Labs Achieves SOC 2 Type II Certification, Reinforcing Enterprise Security Commitment

SAN FRANCISCO, January 8, 2026 — Meridian Labs today announced the completion of its SOC 2 Type II audit, conducted by an independent third-party firm over a six-month observation period. The audit evaluated Meridian's controls across security, availability, and confidentiality with zero findings.

"Enterprise teams evaluating observability tools need to know their data is handled with the same rigor they apply to their own systems," said Maya Chen, CEO. "SOC 2 Type II certification is table stakes for that conversation, and completing the audit with zero findings reflects how we've built security into the platform from the infrastructure layer up."

The certification covers all components of the Meridian platform including data ingestion pipelines, query infrastructure, alerting systems, and the customer dashboard. Key controls validated include end-to-end encryption for data in transit and at rest, role-based access controls with audit logging, automated vulnerability scanning across the deployment pipeline, and data residency controls supporting EU and US hosting regions.

Meridian's security architecture is designed around the principle that observability data — which often contains system performance metrics, error logs, and infrastructure topology — is operationally sensitive and must be protected accordingly.

The full SOC 2 Type II report is available to current and prospective customers under NDA. Contact security@meridianlabs.dev.
----------------

[ASSET: CLUSTER: CRISIS & RESPONSE | SENDER: ENGINEERING / LEADERSHIP | AUDIENCE: CUSTOMERS | SOURCE: Incident Post-Mortem — Platform Outage | DATE: 2025-11-03]
INCIDENT REPORT: Dashboard Latency Degradation — November 3, 2025

Summary:
Between 14:22 and 15:47 UTC on November 3, 2025, Meridian customers experienced elevated dashboard load times and delayed alert delivery. The root cause was a misconfigured autoscaling rule in our US-East query processing cluster that prevented additional capacity from being provisioned during a traffic spike.

No customer data was lost. Alert delivery was delayed by an average of 4 minutes and 12 seconds during the affected window. Dashboard queries that normally resolve in under 200ms were taking 2-8 seconds.

We take this seriously. When your systems are under stress, ours can't be the tool that slows down.

Timeline:
- 14:22 UTC: Automated monitoring detected query latency exceeding P99 thresholds
- 14:28 UTC: On-call engineer paged, investigation began
- 14:41 UTC: Root cause identified — autoscaling ceiling set to previous capacity limit during a routine maintenance window on October 28 and not reverted
- 14:52 UTC: Autoscaling ceiling corrected, new instances provisioning
- 15:12 UTC: Additional capacity online, latency returning to baseline
- 15:47 UTC: All metrics within normal operating parameters

What We're Doing About It:
1. Autoscaling configurations are now covered by automated drift detection — any manual override triggers an alert if not reverted within 24 hours.
2. We've added a pre-deployment checklist item for infrastructure maintenance that verifies scaling parameters match production baseline.
3. Alert delivery pipeline has been separated from the query processing cluster so that dashboard latency cannot delay critical alerts.

We'll publish a more detailed technical post-mortem on our engineering blog within the next week.

If this incident affected your team's operations, reach out to your account lead or support@meridianlabs.dev. We want to hear about it.
----------------

[ASSET: CLUSTER: CRISIS & RESPONSE | SENDER: SECURITY TEAM | AUDIENCE: CUSTOMERS | SOURCE: Holding Statement — CVE-2025-4891 | DATE: 2025-12-12]
STATEMENT: Response to CVE-2025-4891 Disclosure

Published: December 12, 2025

We are aware of CVE-2025-4891, a vulnerability disclosed today affecting a third-party library used in our log ingestion pipeline. We want to be direct about where we stand.

What we know:
The vulnerability affects versions 3.2.0 through 3.2.4 of the logging SDK. Our platform uses version 3.2.2 in the log aggregation service. The vulnerability could theoretically allow a crafted log payload to trigger unexpected behavior in the parsing layer.

What we've done:
Our security team began assessment within 30 minutes of the CVE publication. We have confirmed that Meridian's input validation layer — which sanitizes all incoming payloads before they reach the affected library — prevents the exploitation path described in the disclosure. We have found no evidence that this vulnerability has been exploited against our platform.

We are deploying an update to the affected library version today as a defense-in-depth measure, regardless of the mitigation already in place.

What this means for you:
No action is required from Meridian customers. Your data has not been exposed, and the exploitation path is blocked by existing controls. If you use the affected SDK directly in your own infrastructure (independent of Meridian), we recommend updating to version 3.2.5 as published by the maintainer.

We will update this statement if our assessment changes. Direct questions to security@meridianlabs.dev.
----------------

[ASSET: CLUSTER: CRISIS & RESPONSE | SENDER: CEO | AUDIENCE: AFFECTED CUSTOMERS | SOURCE: Customer Apology — Billing Error | DATE: 2025-11-08]
Subject: We made a billing error on your account — here's what happened and what we're doing

To affected Meridian customers:

During our November billing cycle, a configuration error in our billing system caused 34 accounts to be charged for seat counts that included deactivated users. If you're receiving this message, your account was one of them.

Here's what happened: On October 29, we deployed an update to how seat counts are calculated for invoicing. The update was intended to improve accuracy for teams that frequently add and remove users. Instead, a logic error caused deactivated seats — users your admin had already removed — to be included in the active count for the November 1 invoice.

We caught the error on November 4 during a routine audit of billing anomalies. We should have caught it before invoices went out.

What we've done:
- Every affected account has been refunded the full overcharge amount as of today. You should see the credit within 3-5 business days depending on your payment provider.
- We've corrected the seat calculation logic and added a pre-invoice validation step that compares the calculated seat count against active user records before any charge is processed.
- We've added this scenario to our billing QA test suite to prevent recurrence.

The overcharge amounts ranged from $47 to $320 depending on the number of deactivated seats on the account. If you have questions about your specific refund, your account lead can walk you through the details.

We price Meridian per seat because we believe your bill should be predictable. This error contradicted that commitment, and we're sorry.

Maya Chen
Co-founder & CEO, Meridian Labs
----------------

[ASSET: CLUSTER: INTERNAL LEADERSHIP | SENDER: CEO | AUDIENCE: ALL EMPLOYEES | SOURCE: All-Hands Memo — Q4 Priorities | DATE: 2025-10-01]
From: Maya Chen
To: All Meridian Labs
Subject: Q4 Priorities — What Matters and What Doesn't

Team,

We closed Q3 with 214 active customers, $8.2M ARR, and a net revenue retention rate that would make our board very happy if I were allowed to share it externally (I will say: it's our best quarter).

But Q4 is where we prove whether we're building a company or riding a moment. Here's what matters.

THREE THINGS THAT MATTER IN Q4:

1. Enterprise readiness is not optional.
The SOC 2 audit is on track for January completion. Every team that touches customer data needs to treat audit prep as a first-class priority, not a side task. If your team has outstanding items on the compliance tracker, those move to the top of your sprint. I am not going to lose a six-figure deal in Q1 because we treated security documentation as homework.

2. The self-serve funnel needs to actually work.
We've been a sales-led motion with a self-serve option that technically exists. In Q4, the self-serve experience needs to go from "technically exists" to "a developer can go from signup to value in 15 minutes without talking to anyone." Product and Growth own this. If you need engineering resources to make it happen, flag it now.

3. Hiring is everyone's job.
We have 11 open roles. Every person in this company knows talented people. If you've been meaning to refer someone, this is the quarter to do it. The referral bonus is real and I'd rather pay it than agency fees.

TWO THINGS THAT DO NOT MATTER IN Q4:

1. Feature parity with competitors we're not actually losing deals to.
2. Redesigns of things that work fine but aren't pretty.

Ship what matters. Cut what doesn't. See you at the Q4 kickoff Thursday.

Maya
----------------

[ASSET: CLUSTER: INTERNAL LEADERSHIP | SENDER: VP ENGINEERING | AUDIENCE: ENGINEERING TEAM | SOURCE: Engineering Memo — Technical Debt Policy | DATE: 2025-10-15]
From: David Park, VP Engineering
To: Engineering — All Teams
Subject: How we're handling tech debt starting now

Team,

I've heard the same thing from four different team leads this month: "We can't ship the new feature because we need to fix [legacy thing] first." And in three of those four cases, they were right.

We have a tech debt problem. Not a crisis — the platform is stable and reliable. But we've been shipping features faster than we've been cleaning up after ourselves, and the compound interest on that is starting to slow us down.

Starting this sprint, here's how we're handling it:

THE 20% RULE: Every sprint, 20% of engineering capacity is reserved for tech debt, refactoring, and infrastructure improvements. This is not optional. It is not the thing that gets cut when a feature deadline feels tight. Team leads: build it into your sprint planning. If someone asks you to skip it, point them to this memo.

HOW TO PRIORITIZE TECH DEBT: Not all debt is equal. Prioritize by impact:
- Tier 1: Debt that causes customer-facing issues (latency, errors, data accuracy). Fix immediately.
- Tier 2: Debt that slows down feature development for multiple teams. Schedule within 2 sprints.
- Tier 3: Debt that bothers you aesthetically but doesn't measurably impact velocity or reliability. Log it, revisit quarterly.

TRACKING: Every tech debt item gets a ticket tagged [TECH-DEBT] with a tier level. I'll review the backlog monthly with team leads. If Tier 1 items aren't trending down, we'll increase the allocation.

I'd rather ship one fewer feature per quarter and have a codebase that lets us move fast next year than ship everything now and spend next year apologizing for reliability issues.

Questions → bring them to the engineering all-hands Thursday.

David
----------------

[ASSET: CLUSTER: INTERNAL LEADERSHIP | SENDER: CEO | AUDIENCE: ALL EMPLOYEES | SOURCE: Leadership Update — Org Change | DATE: 2025-11-20]
From: Maya Chen
To: All Meridian Labs
Subject: Org update — new Growth team, reporting changes

Team,

Two changes effective Monday that I want to explain directly rather than letting you find out through an updated org chart.

CHANGE 1: We're creating a Growth team.
Sarah Kim (currently leading Product Marketing) is moving into a new role: Head of Growth. She'll own the self-serve funnel, activation metrics, and expansion revenue. Her team will include the current Product Marketing function plus two new hires focused on product-led growth.

Why: We've been treating self-serve as a feature of the product team. It's not — it's a business function that needs dedicated ownership. Sarah has the strongest understanding of how our customers discover and adopt Meridian, and she's been informally driving this work for months. This makes it official and gives her the resources to do it properly.

CHANGE 2: Customer Success now reports to the CRO.
Previously, CS reported to me directly. Starting Monday, CS reports to James (CRO). This isn't a signal about CS performance — the team is excellent. It's a structural decision: CS, Sales, and Account Management need to operate as a unified revenue organization with shared metrics and coordinated handoffs.

What stays the same: CS's mission is customer outcomes, not revenue extraction. James and I are aligned on this. If you're on the CS team and have concerns about how this changes your day-to-day, James and your team lead will be holding a dedicated Q&A session Tuesday at 2pm PT.

I know org changes can feel unsettling. These are growth decisions, not reactive ones. We're building the structure we'll need at 150 people, not reorganizing to fix problems at 85.

Questions welcome — my calendar is open this week.

Maya
----------------

[ASSET: CLUSTER: THOUGHT LEADERSHIP | SENDER: CEO | AUDIENCE: INDUSTRY / BUYERS | SOURCE: Op-Ed — The Observability Tax | DATE: 2025-08-20]
The Observability Tax Is Killing Developer Productivity

There's a question I've started asking every CTO I meet: what percentage of your engineering time goes to observability tooling — not building features, not shipping product, but configuring, maintaining, and interpreting your monitoring stack?

The answers are consistently worse than anyone expects. 15%. 20%. One infrastructure lead at a Series C company told me his team spent a full quarter building custom dashboards because the out-of-box views in their enterprise observability platform were designed for a use case that didn't match their architecture.

This is the observability tax. Not the line item on your AWS bill — the invisible cost measured in engineering hours diverted from product work to tooling work.

The industry created this problem by building observability platforms for the 5% of engineers who think in PromQL and Splunk queries, then selling those platforms to companies where 95% of the engineering team just needs to know if their service is healthy.

The result is predictable: companies buy powerful tools that most of their team can't use effectively. The SRE team becomes a bottleneck. Developers waiting for dashboard access or custom alerts either build workarounds or — worse — ship without visibility into how their code performs in production.

I think this happens because the observability market optimized for the wrong metric. Vendors compete on capability breadth — who can ingest more data types, who has more integrations, who can handle higher cardinality. These are real technical achievements. But they don't solve the actual problem, which is that a developer who ships a new service on Tuesday morning needs to understand how it's behaving by Tuesday afternoon without filing a ticket with the platform team.

Accessibility isn't a feature. It's an architectural decision. Either you build the product around the assumption that every developer on the team will use it daily, or you build it for specialists and accept that most of your customer's engineering team will treat it as someone else's job.

We chose the first path when we built Meridian. Not because it's easier — it's significantly harder to make complex systems legible to non-specialists. But because the observability tax is an engineering leadership problem disguised as a tooling problem, and the only way to eliminate it is to build tools that don't require specialists to operate.
----------------

[ASSET: CLUSTER: THOUGHT LEADERSHIP | SENDER: CEO | AUDIENCE: ENGINEERING LEADERS | SOURCE: Conference Talk — DX as Infrastructure | DATE: 2025-10-28]
Developer Experience Is Infrastructure, Not Polish

I want to challenge an assumption I hear constantly in engineering leadership conversations: that developer experience is a "nice to have" — something you invest in after the core platform works, as a quality-of-life improvement.

This framing is wrong, and it's costing companies more than they realize.

When a developer can't understand what an alert is telling them, that's not a UX problem. It's an operational problem. It means the next incident takes longer to resolve because someone has to interpret the tool before they can interpret the data. When a new hire spends two weeks learning the monitoring stack before they can be productive, that's not an onboarding problem. It's an infrastructure problem — your tooling has an implicit training requirement that scales linearly with headcount.

Developer experience in observability is infrastructure because it directly determines operational outcomes. Mean time to detection. Mean time to resolution. How many engineers can independently investigate an issue versus how many need to escalate to the one person who knows how the dashboards work.

The companies I talk to that have the fastest incident response times aren't the ones with the most sophisticated monitoring. They're the ones where every engineer on the team — not just the SRE — can open a dashboard, understand what they're looking at, and take action within minutes.

That doesn't happen by accident. It happens because someone made the architectural decision that the tool should be legible to its broadest user, not its most expert one. That the default view should answer the most common question, not display the most data. That setup should take minutes, not sprints.

This is what I mean when I say developer experience is infrastructure. It's not about making the interface pretty. It's about reducing the operational cost of using the tool to near zero, so that the tool disappears and the developer is left staring at their system — which is what they actually need to see.
----------------

[ASSET: CLUSTER: THOUGHT LEADERSHIP | SENDER: CEO | AUDIENCE: BUYERS / INDUSTRY | SOURCE: Blog Post — Why We Charge Per Seat | DATE: 2025-07-14]
Why We Charge Per Seat (And Why the Industry Hates It)

I want to explain a pricing decision we made early at Meridian that has become, unexpectedly, one of our strongest positioning differentiators.

We charge per seat. Flat rate. Unlimited data.

This is unusual in observability. The dominant pricing model in our industry is consumption-based: you pay per GB ingested, per metric tracked, per span stored. The more data you send, the more you pay. At face value, this seems fair — you pay for what you use.

In practice, it creates a perverse incentive structure.

When your observability bill scales with data volume, you start making engineering decisions based on cost rather than coverage. Teams skip instrumenting new services because the additional data ingestion pushes them into a higher pricing tier. Engineers write less verbose logs because each log line costs money. The infrastructure team becomes a cost center that gates what the development team is allowed to monitor.

I've watched this happen at three different companies before we started Meridian. A team wants to add tracing to a new microservice. Someone checks the estimated data volume. The monthly cost increase gets flagged. The instrumentation gets deferred to "next quarter." The service ships without observability. Three months later, it causes an incident that takes four hours to diagnose because nobody can see what it's doing.

The total cost of that incident — in engineering time, in customer impact, in recovery effort — dwarfs the data ingestion fee that was being avoided. But the ingestion fee is on a dashboard with a dollar sign next to it, and the cost of an incident is distributed across fifty people's calendars and never aggregated.

Per-seat pricing eliminates this. Your team instruments everything. Logs everything. Traces everything. The bill doesn't change. The only variable is how many people have access, and that's a number that grows predictably with headcount.

The observability industry dislikes this model because consumption-based pricing has better unit economics at scale — when customers send exponentially more data, revenue grows exponentially. Our revenue grows linearly with customer team size. I'm fine with that trade. Linear growth on a product that customers don't have an incentive to underuse is a better long-term business than exponential growth on a product that penalizes thoroughness.
----------------

[ASSET: CLUSTER: BRAND MARKETING | SENDER: MARKETING | AUDIENCE: PROSPECTS | SOURCE: Website Homepage Copy | DATE: 2025-09-01]
MERIDIAN LABS — HOMEPAGE

[Hero Section]
See your system. Fix it fast. No PhD required.
Meridian is the observability platform built for your entire engineering team — not just the one person who knows how to write queries.

[CTA] Start Free. Setup takes 15 minutes.

[Section: The Problem]
Your monitoring tool shouldn't need its own specialist.
You bought an enterprise observability platform. Your SRE team loves it. Everyone else avoids it. Alerts fire and three people know what they mean. Dashboards exist and nobody looks at them. You're paying six figures a year for a tool that 80% of your team can't use independently.

Sound familiar?

[Section: The Fix]
Meridian gives every developer on your team the ability to see what's happening, understand why, and fix it — without escalating to the one person who "knows the dashboards."

- 15 minutes from signup to first actionable alert
- Natural language search across logs, metrics, and traces
- Role-based default dashboards that answer the right questions for each team
- Alerting that routes to the right person with the right context

[Section: Pricing That Makes Sense]
$45/seat/month. Unlimited data. No per-GB fees. No overages.
Your bill scales with your team, not your traffic. Instrument everything. Log everything. Trace everything. The price doesn't change.

[Section: Proof]
200+ engineering teams. 2.1B events/day. 99.97% uptime.
"We ripped out Datadog after the third surprise overage bill. Meridian costs us 60% less and our entire team actually uses it." — VP Eng, Series C fintech

[Footer CTA]
Start free. No credit card. No sales call. Just deploy the agent and see what happens.
----------------

[ASSET: CLUSTER: BRAND MARKETING | SENDER: PRODUCT MARKETING | AUDIENCE: USERS | SOURCE: Product Launch Email — Natural Language Search | DATE: 2025-11-05]
Subject: Search your logs like you'd ask a question

Hey [first_name],

We shipped something this week that we've been building toward since Meridian's first commit: natural language log search.

Instead of writing structured queries to find what you're looking for, just ask:
- "Show me all 500 errors from the payments service in the last hour"
- "What changed in the auth service before latency spiked at 3pm?"
- "Find the slowest database queries from yesterday's deploy"

Meridian translates your question into the right query, runs it, and shows you the results. If the results aren't what you meant, refine in plain English. No syntax to remember. No documentation to reference.

Why this matters:
The biggest barrier to observability adoption isn't data — it's query languages. When only three people on your team know how to search logs effectively, everyone else is either asking those people for help or guessing.

Natural language search means every developer on your team can investigate independently. That's faster incident response. That's fewer escalations. That's the whole team using the tool you're paying for.

Available now on all plans. No configuration needed — it works against your existing log data.

Try it → [link]

Cheers,
The Meridian team

P.S. Power users: you can still write structured queries. We didn't take anything away. We just removed the requirement.
----------------

[ASSET: CLUSTER: BRAND MARKETING | SENDER: CEO | AUDIENCE: USERS / PROSPECTS | SOURCE: Newsletter — Year in Review | DATE: 2026-01-15]
Subject: Meridian 2025: The year in numbers

2025 was the year Meridian went from "promising startup" to "the tool that teams actually adopt." Here's what happened.

THE NUMBERS:
- 214 engineering teams (up from 67 at the start of the year)
- 2.1 billion events processed daily (up from 400M)
- 99.97% platform uptime
- 4 major product launches
- 1 Series B ($42M, led by Sequoia)
- 0 data breaches

WHAT WE SHIPPED:
Natural language log search — ask questions in English, get answers in milliseconds.
Distributed tracing v2 — follow a request across every service it touches, with latency breakdown at each hop.
Team dashboards — role-based default views that answer the questions your team actually asks.
SOC 2 Type II — because enterprise security isn't optional, it's infrastructure.

WHAT WE LEARNED:
The biggest insight from 2025 is something our customers taught us: the gap between "the monitoring tool works" and "the team uses the monitoring tool" is where most of the value lives. Everything we shipped this year was aimed at closing that gap.

WHAT'S NEXT IN 2026:
We don't pre-announce features (our messaging guardrails won't let us). But I'll say this: we're investing heavily in making Meridian the default response to "something looks wrong" — the tool your team reaches for instinctively, not the tool they're told to check.

Thank you for building with us. Every engineering team that adopts Meridian makes the platform better for everyone.

Maya Chen
Co-founder & CEO

P.S. If you love Meridian, tell a friend. If you don't, tell us. feedback@meridianlabs.dev
----------------
""".strip()

# ---------------------------------------------------------------------------
# Social DNA blob — 3 social media samples
# ---------------------------------------------------------------------------
_SOCIAL_DNA = """
[ASSET: LINKEDIN POST | DATE: 2025-09-20]
We just crossed 200 engineering teams on Meridian.

The thing nobody tells you about developer tools: the product that wins isn't the one with the most features. It's the one the whole team actually uses.

We built Meridian for the developer who touches a dashboard twice a month — not the SRE who lives in one. That decision felt risky when we started. Turns out it was the whole business.

— Maya Chen, Co-founder & CEO
----------------

[ASSET: TWITTER POST | DATE: 2025-10-05]
Your observability bill scales with your data volume.
Your data volume scales with your growth.
Your growth is what you're trying to encourage.

So your monitoring vendor makes more money when you succeed... by charging you more? That math doesn't work for us.

Per-seat pricing. Unlimited data. meridianlabs.dev
----------------

[ASSET: LINKEDIN POST | DATE: 2025-11-12]
Unpopular opinion in the observability space: if a developer on your team can't use your monitoring tool independently after 15 minutes, the tool has failed — not the developer.

We don't build for power users and then "simplify" for everyone else. We build for everyone and make sure power users can go deeper when they need to.

Those are different design philosophies, and they produce fundamentally different products.

— Maya Chen, Co-founder & CEO
----------------
""".strip()

# ---------------------------------------------------------------------------
# Brand rules text (final_text) — the AI-generated strategy output
# This is a condensed version of what the AI would produce from the inputs.
# ---------------------------------------------------------------------------
_FINAL_TEXT = """BRAND GOVERNANCE RULES — MERIDIAN LABS

ARCHETYPE: The Creator (Builder variant)
TONE: Precise, Technical, Confident, Accessible, Opinionated

MISSION:
To give every development team the observability infrastructure they need to ship faster without guessing. We build tools that turn system complexity into clarity.

CORE VALUES:
- Clarity Over Cleverness
- Ship With Confidence
- Tooling Is Infrastructure
- Developers Deserve Better

VOICE GUIDELINES:
1. Speak directly to developers as peers. Use concrete technical language.
2. Show don't tell — reference real scenarios.
3. Default to active voice. Lead with the problem before the solution.
4. Be opinionated without being combative. Confident, not arrogant.
5. Technical precision required — vague claims undermine credibility with developer audience.

GUARDRAILS — DO:
- Speak directly to developers as peers
- Use concrete technical language
- Show don't tell — reference real scenarios
- Default to active voice
- Lead with the problem before the solution

GUARDRAILS — DON'T:
- Never use enterprise jargon (synergy, leverage, unlock, empower)
- Don't talk down to developers
- Never promise "zero downtime" or "100% reliability" — those are lies
- Don't compare directly to named competitors
- Avoid marketing superlatives (revolutionary, game-changing, industry-leading)

COLOR PALETTE:
- Primary: #1A2332 (deep navy)
- Secondary: #00B4D8 (bright cyan)
- Accent: #FF6B35 (warm orange)
- Neutral: #E8EAED (light gray)
- Text: #2D3748 (dark charcoal)

VISUAL IDENTITY:
Geometric compass rose mark — four directional points forming an abstract "M" — paired with "MERIDIAN LABS" in a clean sans-serif. Monochrome on dark backgrounds, navy on light.

MESSAGE HOUSE:
Brand Promise: We turn system complexity into developer clarity — so every team can see what's happening, understand why, and fix it before users notice.

Pillar 1: Observability Without the PhD — Powerful tools shouldn't require a specialist to operate.
Pillar 2: Infrastructure-Grade Reliability — Your monitoring tool can't be the thing that goes down.
Pillar 3: Pricing That Doesn't Punish Growth — Your observability bill shouldn't scale faster than your revenue.

Founder POV: The observability industry optimizes for power users and punishes everyone else. We think that's backwards.

SOCIAL DNA SUMMARY:
LinkedIn and Twitter presence focused on developer empathy, pricing transparency, and accessibility-first philosophy. CEO-led thought leadership with direct, peer-level voice. No corporate jargon. No competitor bashing.

VOICE CALIBRATION:
All 5 voice clusters fortified with 3+ reference samples each:
- Corporate Affairs: Press releases, fact sheets (objective, standardized)
- Crisis & Response: Incident reports, vulnerability statements, customer apologies (defensive, empathetic)
- Internal Leadership: All-hands memos, engineering policy, org updates (directive, cultural)
- Thought Leadership: Op-eds, conference talks, blog posts (persuasive, rhetorical)
- Brand Marketing: Website copy, product launch emails, newsletters (conversion-driven, energetic)
""".strip()


# ---------------------------------------------------------------------------
# The complete sample brand — ready to be inserted as a profile
# ---------------------------------------------------------------------------
SAMPLE_BRAND = {
    "display_name": "Meridian Labs (Sample Brand)",
    "profile_name": "Meridian Labs (Sample Brand)",
    "profile_data": {
        "final_text": _FINAL_TEXT,
        "calibration_score": 100,
        "inputs": {
            # ── Strategy ──
            "wiz_name": "Meridian Labs",
            "wiz_archetype": "The Creator",
            "wiz_tone": "Precise, Technical, Confident, Accessible, Opinionated",
            "wiz_mission": (
                "To give every development team the observability infrastructure they "
                "need to ship faster without guessing. We build tools that turn system "
                "complexity into clarity."
            ),
            "wiz_values": (
                "Clarity Over Cleverness, Ship With Confidence, "
                "Tooling Is Infrastructure, Developers Deserve Better"
            ),
            "wiz_guardrails": (
                "DO: Speak directly to developers as peers. Use concrete technical language. "
                "Show don't tell — reference real scenarios. Default to active voice. "
                "Lead with the problem before the solution.\n\n"
                "DON'T: Never use enterprise jargon (synergy, leverage, unlock, empower). "
                "Don't talk down to developers. Never promise 'zero downtime' or '100% reliability' "
                "— those are lies. Don't compare directly to named competitors. "
                "Avoid marketing superlatives (revolutionary, game-changing, industry-leading)."
            ),

            # ── Color Palette ──
            "palette_primary": ["#1A2332"],
            "palette_secondary": ["#00B4D8", "#E8EAED"],
            "palette_accent": ["#FF6B35"],

            # ── DNA Blobs ──
            "voice_dna": _VOICE_DNA,
            "social_dna": _SOCIAL_DNA,
            "visual_dna": (
                "[ASSET: LOGO DESCRIPTION | DATE: 2025-09-01]\n"
                "Geometric compass rose mark — four directional points forming an abstract "
                "'M' — paired with 'MERIDIAN LABS' in a clean sans-serif. Monochrome on "
                "dark backgrounds, navy on light.\n\n"
                "Primary: #1A2332 (deep navy) | Secondary: #00B4D8 (bright cyan) | "
                "Accent: #FF6B35 (warm orange) | Neutral: #E8EAED (light gray) | "
                "Text: #2D3748 (dark charcoal)\n"
                "----------------\n"
            ),

            # ── Message House ──
            "mh_brand_promise": (
                "We turn system complexity into developer clarity — so every team can see "
                "what's happening, understand why, and fix it before users notice."
            ),
            "mh_pillars_json": json.dumps(_PILLARS),
            "mh_founder_positioning": (
                "Maya Chen is the co-founder and CEO of Meridian Labs, an observability "
                "platform built on the belief that developer tools should be as clear as "
                "the systems they monitor."
            ),
            "mh_pov": (
                "The observability industry optimizes for power users and punishes everyone "
                "else. We think that's backwards — the developer who touches a dashboard "
                "twice a month needs clarity more than the SRE who lives in it."
            ),
            "mh_boilerplate": (
                "Meridian Labs builds observability tools for development teams that need "
                "clarity without complexity. Founded in 2023 and based in San Francisco, "
                "Meridian serves 200+ engineering teams with infrastructure-grade monitoring "
                "that any developer can operate. The platform processes over 2 billion events "
                "daily with 99.97% uptime. Backed by Sequoia Capital and Craft Ventures."
            ),
            "mh_offlimits": (
                "Named competitor comparisons (reference 'legacy tools' or 'traditional vendors' "
                "instead). Client names without written approval. Unverified performance claims. "
                "Internal roadmap or unreleased features."
            ),
            "mh_preapproval_claims": (
                "Any new performance statistics. Customer outcome data beyond approved case "
                "studies. Pricing comparisons with specific dollar amounts. Partnership announcements."
            ),
            "mh_tone_constraints": (
                "Never condescending toward non-technical audiences. No snark at competitors' "
                "expense — confident, not combative. No promises about future features. "
                "Technical precision required — vague claims undermine credibility with "
                "developer audience."
            ),
        },
    },
}
