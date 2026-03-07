# API Cost Baseline - Meridian Labs Sample Brand
Generated: 2026-03-07
Model: claude-opus-4-6
Pricing: Input $5.00/MTok, Output $25.00/MTok

## Per-Action Costs

| Module | Input Tokens | Output Tokens | Input Cost | Output Cost | Total Cost |
|--------|-------------|---------------|------------|-------------|------------|
| Content Generator | 2,705 | 814 | $0.0135 | $0.0204 | $0.0339 |
| Copy Editor | 2,798 | 1,233 | $0.0140 | $0.0308 | $0.0448 |
| Social Assistant | 3,128 | 1,635 | $0.0156 | $0.0409 | $0.0565 |
| Visual Audit (AI) | 419 | 726 | $0.0021 | $0.0181 | $0.0202 |

**Average cost per action: $0.0389**

## Monthly Cost Projections

Assumptions: Average cost per action = $0.0389

| Scenario | Users | Actions/User/Mo | Total Actions | Est. Monthly Cost | Cost/User |
|----------|-------|-----------------|---------------|-------------------|-----------|
| Light | 10 | 20 | 200 | $7.77 | $0.78 |
| Moderate | 25 | 40 | 1000 | $38.86 | $1.55 |
| Heavy | 50 | 80 | 4000 | $155.45 | $3.11 |

## Gross Margin Analysis

| Tier | Price | Est. Cost/User (40 actions) | Gross Margin |
|------|-------|---------------------------|-------------|
| Solo ($49.99) | $49.99/seat | $1.55 | 96.9% |
| Agency ($299.99 / 5 seats) | $60.00/seat | $1.55 | 97.4% |
| Enterprise ($499.99 / 10 seats) | $50.00/seat | $1.55 | 96.9% |

## Prompt Efficiency Notes

- Total brand data tokens (Meridian Labs, fully calibrated, all clusters): ~8,592 tokens
- Total brand data tokens (single cluster filter): ~2,625 tokens
- Voice samples account for ~83% of all-cluster input (7,217 tokens)
- Message house accounts for ~11% of all-cluster input (967 tokens)
- Cluster filtering saves ~5,967 tokens per request (69% reduction)
- Cluster filtering is ALREADY IMPLEMENTED and working correctly
- System instructions are minimal (~200-400 tokens) - efficient

## Efficiency Recommendations

1. **Cluster filtering is working.** Only the relevant cluster's voice samples are injected. Savings: ~5,967 tokens per request (69%). Already implemented.
2. **Message house is always fully included.** For Content Generator, the full MH (~967 tokens) is justified - the AI needs proof points and guardrails. For Visual Audit, only guardrails are needed - could save ~700 tokens.
3. **Social Assistant includes Brand Marketing voice samples + social samples.** This is correct - social content needs both tone references.
4. **Visual Audit AI component is lightweight.** Short profile text, no voice samples, no MH. Cost-efficient by design.
5. **No redundant data detected.** Brand name appears in headers but not duplicated in body sections.