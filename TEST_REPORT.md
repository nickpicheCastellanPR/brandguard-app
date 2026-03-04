# SIGNET TEST REPORT
Generated: 2026-03-03 18:29:03
Python: 3.14.2
SQLite: 3.50.4

## SUMMARY
- Total Tests: 135
- Passed: 124
- Warnings: 11
- Failed: 0
- Errors: 0

## FAILURES & ERRORS
None!

## WARNINGS
### [WARN] Cat 1: Import webhook_handler
```
Import failed (likely FastAPI/uvicorn dependency): No module named 'fastapi'
```

### [WARN] Cat 10: Valid signature
```
webhook_handler import failed
```

### [WARN] Cat 10: Invalid signature
```
webhook_handler import failed
```

### [WARN] Cat 10: Missing secret (dev mode)
```
webhook_handler import failed
```

### [WARN] Cat 10: Find user by email
```
webhook_handler import failed
```

### [WARN] Cat 10: Subscription created
```
webhook_handler import failed
```

### [WARN] Cat 10: Subscription cancelled
```
webhook_handler import failed
```

### [WARN] Cat 10: Non-existent user
```
webhook_handler import failed
```

### [WARN] Cat 11: FORTIFIED/UNSTABLE/EMPTY labels
```
Found 25 string-literal occurrences of FORTIFIED/UNSTABLE/EMPTY. These appear in calibration logic code. Verify they are not shown directly to end users in the UI (some may be internal labels).
```

### [WARN] Cat 12: Missing ANTHROPIC_API_KEY handling
```
ANTHROPIC_API_KEY is set — cannot test missing key behavior
```

### [WARN] Cat 14: Webhook empty body
```
webhook_handler import failed
```

## FULL RESULTS

### Cat 1

- [PASS] Cat 1: Import db_manager
- [PASS] Cat 1: Import tier_config
- [PASS] Cat 1: Import subscription_manager
- [PASS] Cat 1: Import brand_ui
- [PASS] Cat 1: Import sample_brand_data
- [PASS] Cat 1: Import prompt_builder
- [WARN] Cat 1: Import webhook_handler — Import failed (likely FastAPI/uvicorn dependency): No module named 'fastapi'
- [PASS] Cat 1: Import logic
- [PASS] Cat 1: Import visual_audit
### Cat 2

- [PASS] Cat 2: Schema creation
- [PASS] Cat 2: Users table columns
- [PASS] Cat 2: Profiles table columns
- [PASS] Cat 2: Activity log table
- [PASS] Cat 2: Usage tracking table
- [PASS] Cat 2: Organizations table
- [PASS] Cat 2: Admin audit log table
- [PASS] Cat 2: Platform settings table
### Cat 3

- [PASS] Cat 3: Solo tier
- [PASS] Cat 3: Agency tier
- [PASS] Cat 3: Enterprise tier
- [PASS] Cat 3: Free/default tier fallback
- [PASS] Cat 3: Tier casing consistency
- [PASS] Cat 3: Tier ordering (agency > solo)
### Cat 4

- [PASS] Cat 4: Create user
- [PASS] Cat 4: Duplicate user
- [PASS] Cat 4: Get user by username
- [PASS] Cat 4: Get non-existent user
- [PASS] Cat 4: Set super_admin
- [PASS] Cat 4: Set beta_tester
- [PASS] Cat 4: Suspend user
- [PASS] Cat 4: Unsuspend user
- [PASS] Cat 4: Suspend super_admin
- [PASS] Cat 4: Check login (valid)
- [PASS] Cat 4: Check login (nonexistent)
### Cat 5

- [PASS] Cat 5: Create brand
- [PASS] Cat 5: Retrieve brand
- [PASS] Cat 5: Update brand
- [PASS] Cat 5: Delete brand
- [PASS] Cat 5: List brands
- [PASS] Cat 5: Sample brand excludes from count
- [PASS] Cat 5: Load sample brand
- [PASS] Cat 5: Load sample brand twice
- [PASS] Cat 5: Delete sample brand
- [PASS] Cat 5: Reload sample brand
- [PASS] Cat 5: Is profile sample
### Cat 6

- [PASS] Cat 6: Weights sum to 100%
- [PASS] Cat 6: Empty brand = 0%
- [PASS] Cat 6: Strategy only = 10%
- [PASS] Cat 6: Strategy + full MH >= 33%
- [PASS] Cat 6: Full brand >= 90%
- [PASS] Cat 6: Hard ceiling (no MH) cap at 55
- [PASS] Cat 6: Partial MH removes ceiling
- [PASS] Cat 6: Brand promise weight
- [PASS] Cat 6: Voice cluster empty
- [PASS] Cat 6: Voice cluster partial (UNSTABLE)
- [PASS] Cat 6: Voice cluster fortified
- [PASS] Cat 6: 3 clusters full, 2 empty
- [PASS] Cat 6: Social scoring
- [PASS] Cat 6: Social all platforms
- [PASS] Cat 6: Sample brand score >= 90
### Cat 7

- [PASS] Cat 7: Record usage event
- [PASS] Cat 7: Usage with detail
- [PASS] Cat 7: Usage count (no activity)
- [PASS] Cat 7: Org-level usage
- [PASS] Cat 7: Activity log creation
- [PASS] Cat 7: Activity log order
- [PASS] Cat 7: Activity log scoping
### Cat 8

- [PASS] Cat 8: Suspension fields
- [PASS] Cat 8: Unsuspension clears fields
- [PASS] Cat 8: Suspension survives status update
- [PASS] Cat 8: Admin audit log
### Cat 9

- [PASS] Cat 9: Full brand context
- [PASS] Cat 9: Empty brand context
- [PASS] Cat 9: MH no voice
- [PASS] Cat 9: Voice no MH
- [PASS] Cat 9: Content type cluster mapping
- [PASS] Cat 9: Social context
- [PASS] Cat 9: No None injection
- [PASS] Cat 9: Cluster filtering
- [PASS] Cat 9: Voice cluster status
- [PASS] Cat 9: MH builder
### Cat 10

- [WARN] Cat 10: Valid signature — webhook_handler import failed
- [WARN] Cat 10: Invalid signature — webhook_handler import failed
- [WARN] Cat 10: Missing secret (dev mode) — webhook_handler import failed
- [PASS] Cat 10: Variant ID mapping
- [WARN] Cat 10: Find user by email — webhook_handler import failed
- [WARN] Cat 10: Subscription created — webhook_handler import failed
- [WARN] Cat 10: Subscription cancelled — webhook_handler import failed
- [WARN] Cat 10: Non-existent user — webhook_handler import failed
### Cat 11

- [PASS] Cat 11: No 'Brand Governance Engine'
- [PASS] Cat 11: No 'brand governance'
- [PASS] Cat 11: No 'publishing perimeter'
- [PASS] Cat 11: No 'authoritative signal'
- [PASS] Cat 11: No 'Voice DNA' in strings
- [PASS] Cat 11: No 'gold-standard'
- [PASS] Cat 11: No 'signal degradation'
- [PASS] Cat 11: No 'Signal Integrity Score'
- [PASS] Cat 11: No 'algorithmic fidelity'
- [PASS] Cat 11: No 'hallucination' (user-facing)
- [WARN] Cat 11: FORTIFIED/UNSTABLE/EMPTY labels — Found 25 string-literal occurrences of FORTIFIED/UNSTABLE/EMPTY. These appear in calibration logic code. Verify they are
### Cat 12

- [PASS] Cat 12: config.toml exists
- [PASS] Cat 12: primaryColor = #ab8f59
- [PASS] Cat 12: backgroundColor = #24363b
- [PASS] Cat 12: secondaryBackgroundColor = #1b2a2e
- [PASS] Cat 12: textColor = #f5f5f0
- [PASS] Cat 12: start.sh exists with uvicorn+streamlit
- [PASS] Cat 12: brand_ui.py Castellan palette
- [WARN] Cat 12: Missing ANTHROPIC_API_KEY handling — ANTHROPIC_API_KEY is set — cannot test missing key behavior
### Cat 13

- [PASS] Cat 13: Brand name
- [PASS] Cat 13: Archetype
- [PASS] Cat 13: Tone keywords
- [PASS] Cat 13: Mission statement
- [PASS] Cat 13: Core values
- [PASS] Cat 13: Guardrails
- [PASS] Cat 13: Hex palette
- [PASS] Cat 13: Brand promise
- [PASS] Cat 13: Message pillars
- [PASS] Cat 13: Founder positioning
- [PASS] Cat 13: POV statement
- [PASS] Cat 13: Boilerplate
- [PASS] Cat 13: Messaging guardrails
- [PASS] Cat 13: Voice cluster samples
- [PASS] Cat 13: Social samples
- [PASS] Cat 13: No empty fields
### Cat 14

- [PASS] Cat 14: Empty brand name
- [PASS] Cat 14: Long brand name
- [PASS] Cat 14: Corrupted calibration data
- [PASS] Cat 14: Legacy profile format
- [PASS] Cat 14: Usage missing brand_id
- [PASS] Cat 14: Activity log empty
- [PASS] Cat 14: Long prompt builder input
- [PASS] Cat 14: ColorScorer edge cases
- [WARN] Cat 14: Webhook empty body — webhook_handler import failed
- [PASS] Cat 14: Platform settings CRUD
- [PASS] Cat 14: Table row counts

## MODULE INVENTORY

### brand_ui
- `BRAND_COLORS` (constant)
- `HELP_CONTENT_GENERATOR` (constant)
- `HELP_COPY_EDITOR` (constant)
- `HELP_EXPANDER_CSS` (constant)
- `HELP_SOCIAL_ASSISTANT` (constant)
- `HELP_VISUAL_AUDIT` (constant)
- `SHIELD_ALIGNED` (constant)
- `SHIELD_DEGRADATION` (constant)
- `SHIELD_DRIFT` (constant)
- `inject_button_css` (function)
- `inject_typography_css` (function)
- `render_module_help` (function)
- `render_severity` (function)

### db_manager
- `DB_FOLDER` (constant)
- `DB_NAME` (constant)
- `PasswordHasher` (function)
- `SEAT_LIMITS` (constant)
- `VerifyMismatchError` (function)
- `check_login` (function)
- `check_seat_availability` (function)
- `count_user_brands` (function)
- `create_organization` (function)
- `create_user` (function)
- `create_user_admin` (function)
- `datetime` (function)
- `delete_organization_full` (function)
- `delete_profile` (function)
- `delete_sample_brand` (function)
- `delete_user_full` (function)
- `get_admin_audit_log` (function)
- `get_all_organizations` (function)
- `get_all_users_full` (function)
- `get_brand_owner_info` (function)
- `get_daily_usage_platform` (function)
- `get_monthly_usage` (function)
- `get_monthly_usage_all` (function)
- `get_monthly_usage_trend` (function)
- `get_monthly_usage_user` (function)
- `get_org_logs` (function)
- `get_org_tier` (function)
- `get_organization` (function)
- `get_platform_setting` (function)
- `get_profiles` (function)
- `get_table_row_counts` (function)
- `get_usage_analytics` (function)
- `get_user_by_email` (function)
- `get_user_count` (function)
- `get_user_full` (function)
- `get_user_status` (function)
- `get_users_by_org` (function)
- `has_sample_brand` (function)
- `init_db` (function)
- `is_profile_sample` (function)
- `is_user_suspended` (function)
- `json` (constant)
- `load_sample_brand` (function)
- `log_admin_action` (function)
- `log_event` (function)
- `logging` (constant)
- `os` (constant)
- `ph` (constant)
- `record_usage_action` (function)
- `record_usage_action_impersonated` (function)
- `remove_org_member` (function)
- `reset_user_password` (function)
- `run_migrations` (function)
- `save_profile` (function)
- `set_platform_setting` (function)
- `set_user_subscription` (function)
- `shutil` (constant)
- `sqlite3` (constant)
- `suspend_user` (function)
- `unsuspend_user` (function)
- `update_last_login` (function)
- `update_organization_fields` (function)
- `update_user_fields` (function)
- `update_user_status` (function)

### logic
- `ColorScorer` (function)
- `Counter` (function)
- `Image` (constant)
- `KMeans` (function)
- `SignetLogic` (function)
- `anthropic` (constant)
- `api_key` (constant)
- `base64` (constant)
- `client` (constant)
- `extract_dominant_colors` (function)
- `hex_to_rgb` (function)
- `image_to_base64` (function)
- `io` (constant)
- `json` (constant)
- `load_dotenv` (function)
- `math` (constant)
- `np` (constant)
- `os` (constant)
- `re` (constant)
- `rgb_to_hex` (function)
- `sanitize_user_input` (function)
- `time` (constant)

### prompt_builder
- `CONTENT_TYPE_TO_CLUSTER` (constant)
- `VOICE_CLUSTER_NAMES` (constant)
- `annotations` (constant)
- `build_brand_context` (function)
- `build_mh_context` (function)
- `build_social_context` (function)
- `get_cluster_status` (function)
- `json` (constant)
- `parse_voice_clusters` (function)
- `re` (constant)

### sample_brand_data
- `SAMPLE_BRAND` (constant)
- `annotations` (constant)
- `json` (constant)

### subscription_manager
- `LS_API_KEY` (constant)
- `LS_CACHE_TTL_SECONDS` (constant)
- `LS_STORE_ID` (constant)
- `PROTECTED_TIERS` (constant)
- `TIER_CONFIG` (constant)
- `annotations` (constant)
- `check_brand_limit` (function)
- `check_seat_limit` (function)
- `check_usage_limit` (function)
- `datetime` (function)
- `db` (constant)
- `get_tier_from_variant_id` (function)
- `get_usage_nudge_message` (function)
- `logger` (constant)
- `logging` (constant)
- `os` (constant)
- `record_ai_action` (function)
- `requests` (constant)
- `resolve_tier_from_ls_variant` (function)
- `resolve_user_tier` (function)
- `st` (constant)
- `sync_user_status` (function)
- `time` (constant)

### tier_config
- `PROTECTED_TIERS` (constant)
- `TIER_CONFIG` (constant)
- `annotations` (constant)
- `get_tier_config` (function)
- `get_tier_from_variant_id` (function)

### visual_audit
- `ColorScorer` (function)
- `VOICE_CLUSTER_NAMES` (constant)
- `annotations` (constant)
- `client` (constant)
- `datetime` (function)
- `extract_dominant_colors` (function)
- `get_cluster_status` (function)
- `image_to_base64` (function)
- `json` (constant)
- `logger` (constant)
- `logging` (constant)
- `re` (constant)
- `run_color_compliance` (function)
- `run_copy_compliance` (function)
- `run_full_audit` (function)
- `run_visual_identity_check` (function)
- `sanitize_user_input` (function)

## SCHEMA INVENTORY

### activity_log
| Column | Type | PK | Not Null | Default |
|--------|------|-----|----------|---------|
| id | INTEGER | YES |  |  |
| org_id | TEXT |  |  |  |
| username | TEXT |  |  |  |
| timestamp | TEXT |  |  |  |
| activity_type | TEXT |  |  |  |
| asset_name | TEXT |  |  |  |
| score | INTEGER |  |  |  |
| verdict | TEXT |  |  |  |
| metadata_json | TEXT |  |  |  |
| created_at | DATETIME |  |  | CURRENT_TIMESTAMP |

### admin_audit_log
| Column | Type | PK | Not Null | Default |
|--------|------|-----|----------|---------|
| id | INTEGER | YES |  |  |
| admin_username | TEXT |  | YES |  |
| action_type | TEXT |  | YES |  |
| target_type | TEXT |  | YES |  |
| target_id | TEXT |  | YES |  |
| details | TEXT |  |  |  |
| timestamp | TIMESTAMP |  |  | CURRENT_TIMESTAMP |

### organizations
| Column | Type | PK | Not Null | Default |
|--------|------|-----|----------|---------|
| org_id | TEXT | YES |  |  |
| org_name | TEXT |  | YES |  |
| subscription_tier | TEXT |  | YES | 'agency' |
| owner_username | TEXT |  | YES |  |
| created_at | TIMESTAMP |  |  | CURRENT_TIMESTAMP |

### platform_settings
| Column | Type | PK | Not Null | Default |
|--------|------|-----|----------|---------|
| key | TEXT | YES |  |  |
| value | TEXT |  |  |  |
| updated_at | TIMESTAMP |  |  | CURRENT_TIMESTAMP |
| updated_by | TEXT |  |  |  |

### profiles
| Column | Type | PK | Not Null | Default |
|--------|------|-----|----------|---------|
| id | INTEGER | YES |  |  |
| org_id | TEXT |  |  |  |
| name | TEXT |  |  |  |
| data | TEXT |  |  |  |
| created_at | TEXT |  |  |  |
| updated_by | TEXT |  |  |  |
| is_sample_brand | BOOLEAN |  |  | 0 |

### usage_tracking
| Column | Type | PK | Not Null | Default |
|--------|------|-----|----------|---------|
| id | INTEGER | YES |  |  |
| username | TEXT |  | YES |  |
| org_id | TEXT |  |  |  |
| module | TEXT |  | YES |  |
| action_weight | INTEGER |  |  | 1 |
| timestamp | TIMESTAMP |  |  | CURRENT_TIMESTAMP |
| billing_month | TEXT |  | YES |  |
| is_impersonated | BOOLEAN |  |  | 0 |
| action_detail | TEXT |  |  | NULL |

### users
| Column | Type | PK | Not Null | Default |
|--------|------|-----|----------|---------|
| username | TEXT | YES |  |  |
| email | TEXT |  |  |  |
| password_hash | TEXT |  |  |  |
| is_admin | BOOLEAN |  |  | 0 |
| org_id | TEXT |  |  |  |
| subscription_status | TEXT |  |  | 'trial' |
| created_at | TEXT |  |  |  |
| subscription_tier | TEXT |  |  | 'solo' |
| org_role | TEXT |  |  | 'member' |
| lemon_squeezy_subscription_id | TEXT |  |  | NULL |
| lemon_squeezy_variant_id | TEXT |  |  | NULL |
| last_subscription_sync | TEXT |  |  | NULL |
| last_login | TIMESTAMP |  |  | NULL |
| comp_expires_at | TIMESTAMP |  |  | NULL |
| comp_reason | TEXT |  |  | NULL |
| subscription_override_until | TIMESTAMP |  |  | NULL |
| is_beta_tester | BOOLEAN |  |  | 0 |
| is_suspended | BOOLEAN |  |  | 0 |
| suspended_at | TIMESTAMP |  |  | NULL |
| suspended_reason | TEXT |  |  | NULL |
| suspended_by | TEXT |  |  | NULL |

## MANUAL TESTING REQUIRED

The following aspects cannot be tested programmatically:

1. **Streamlit UI Rendering** — Verify all pages render without visual errors:
   - Dashboard, Brand Architect, Visual Compliance, Copy Editor, Content Generator, Social Media Assistant
   - Sidebar navigation and module routing
   - Calibration dial and progress bars render correctly
   - Gold button text is legible (not gold-on-gold)

2. **AI API Calls** — Requires valid ANTHROPIC_API_KEY:
   - Content Generator produces brand-aligned output
   - Copy Editor audits drafts against brand profile
   - Social Media Assistant generates posts with web search
   - Visual Audit completes 3-layer analysis

3. **Visual Appearance** — Browser inspection required:
   - Castellan color palette renders correctly (dark teal bg, gold accents, cream text)
   - Montserrat typography loads and applies globally
   - Expander backgrounds are cream (#f5f5f0)
   - Audit findings text is legible (not white-on-white)
   - Reference Anchors / severity indicators have proper contrast
   - Shield SVGs render inline in all browsers

4. **Lemon Squeezy Integration** — Requires live webhook delivery:
   - Webhook HTTP endpoint accepts POST requests
   - HMAC signature validation with real LS_WEBHOOK_SECRET
   - Full lifecycle: subscription_created → updated → cancelled → resumed

5. **Admin Panel** — Requires super_admin login:
   - User management (impersonation, suspension, tier changes)
   - Organization management
   - Usage analytics and audit log viewing
   - Password reset functionality
