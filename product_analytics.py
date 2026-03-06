"""
product_analytics.py — Investor-ready product analytics dashboard.

Super-admin only. Styled with the Castellan brand system.
Each section header IS an investor question.
"""

import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta

import db_manager as db
from tier_config import TIER_CONFIG
import brand_ui

# ── Castellan palette constants ───────────────────────────────────────────────
GOLD = "#ab8f59"
TEAL = "#24363b"
COPPER = "#a6784d"
CHARCOAL = "#3d3d3d"
CREAM = "#f5f5f0"
SAGE = "#5c6b61"
TEAL_DARK = "#1b2a2e"


# ── Dashboard CSS ─────────────────────────────────────────────────────────────

def _inject_analytics_css():
    st.markdown("""
    <style>
    .analytics-section h2 {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
        color: """ + TEAL + """ !important;
        border-bottom: 2px solid """ + GOLD + """;
        padding-bottom: 8px;
        margin-top: 32px;
    }
    .analytics-section h3 {
        font-family: 'Montserrat', sans-serif !important;
        font-weight: 700 !important;
        letter-spacing: 0.03em !important;
        color: """ + CHARCOAL + """ !important;
    }
    .metric-card {
        background: """ + CREAM + """;
        border: 1px solid """ + GOLD + """;
        padding: 16px;
        text-align: center;
    }
    .metric-card .value {
        font-family: 'Montserrat', sans-serif;
        font-size: 1.8rem;
        font-weight: 700;
        line-height: 1.2;
    }
    .metric-card .label {
        font-family: 'Montserrat', sans-serif;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: """ + SAGE + """;
        margin-top: 4px;
    }
    .funnel-row {
        display: flex;
        align-items: center;
        gap: 12px;
        margin: 6px 0;
        font-family: 'Montserrat', sans-serif;
        font-size: 0.85rem;
    }
    .funnel-bar {
        height: 20px;
        background: """ + GOLD + """;
        min-width: 2px;
    }
    .funnel-label {
        min-width: 220px;
        color: """ + CHARCOAL + """;
    }
    .funnel-stat {
        color: """ + SAGE + """;
        font-size: 0.8rem;
        min-width: 100px;
    }
    .status-retained { border-left: 4px solid """ + GOLD + """; }
    .status-at-risk  { border-left: 4px solid """ + COPPER + """; }
    .status-churned  { border-left: 4px solid """ + CHARCOAL + """; }
    .status-new      { border-left: 4px solid """ + SAGE + """; }
    .distro-bar {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 4px 0;
        font-family: 'Montserrat', sans-serif;
        font-size: 0.82rem;
        color: """ + CHARCOAL + """;
    }
    .distro-fill {
        height: 16px;
        background: """ + GOLD + """;
    }
    .cost-table {
        width: 100%;
        border-collapse: collapse;
        font-family: 'Montserrat', sans-serif;
        font-size: 0.85rem;
    }
    .cost-table th {
        background: """ + TEAL + """;
        color: """ + CREAM + """;
        padding: 8px 12px;
        text-align: left;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.04em;
        font-size: 0.75rem;
    }
    .cost-table td {
        background: """ + CREAM + """;
        color: """ + CHARCOAL + """;
        padding: 8px 12px;
        border-bottom: 1px solid #ddd;
    }
    .definition-note {
        font-size: 0.75rem;
        color: """ + SAGE + """;
        font-style: normal;
        margin-top: 8px;
        font-family: 'Montserrat', sans-serif;
    }
    </style>
    """, unsafe_allow_html=True)


def _metric_card(value, label, color=TEAL):
    return f"""
    <div class="metric-card">
        <div class="value" style="color:{color};">{value}</div>
        <div class="label">{label}</div>
    </div>
    """


def _html_table(headers, rows):
    """Renders an HTML table with Castellan styling."""
    html = '<table class="cost-table"><thead><tr>'
    for h in headers:
        html += f'<th>{h}</th>'
    html += '</tr></thead><tbody>'
    for row in rows:
        html += '<tr>'
        for cell in row:
            html += f'<td>{cell}</td>'
        html += '</tr>'
    html += '</tbody></table>'
    return html


# ══════════════════════════════════════════════════════════════════════════════
# MAIN RENDER
# ══════════════════════════════════════════════════════════════════════════════

def render_product_analytics():
    """Render the full product analytics dashboard. Super-admin only."""
    brand_ui.inject_typography_css()
    brand_ui.inject_button_css()
    _inject_analytics_css()

    st.markdown('<div class="analytics-section">', unsafe_allow_html=True)

    _section_1_who_is_using()
    _section_2_do_they_come_back()
    _section_3_what_do_they_do()
    _section_4_cost_to_serve()
    _section_5_platform_investment()
    _section_6_onboarding_funnel()
    _section_7_acquisition()
    _section_8_revenue()

    st.divider()
    _section_exports()

    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 1: WHO IS USING SIGNET?
# ══════════════════════════════════════════════════════════════════════════════

def _section_1_who_is_using():
    st.markdown("## Who Is Using Signet?")

    total_users = db.get_user_count()
    active_7d = db.get_active_users(7)
    active_30d = db.get_active_users(30)
    avg_sessions = db.get_user_sessions_per_week()

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(_metric_card(total_users, "Total Users", TEAL), unsafe_allow_html=True)
    with c2:
        pct_7d = round(active_7d / total_users * 100) if total_users > 0 else 0
        color = GOLD if pct_7d >= 30 else (COPPER if pct_7d < 10 else CHARCOAL)
        st.markdown(_metric_card(active_7d, "Active (7d)", color), unsafe_allow_html=True)
    with c3:
        pct_30d = round(active_30d / total_users * 100) if total_users > 0 else 0
        color = GOLD if pct_30d >= 30 else (COPPER if pct_30d < 10 else CHARCOAL)
        st.markdown(_metric_card(active_30d, "Active (30d)", color), unsafe_allow_html=True)
    with c4:
        st.markdown(_metric_card(avg_sessions, "Avg Sessions/Week", GOLD), unsafe_allow_html=True)

    st.markdown('<p class="definition-note">Active = performed at least one module action in the period.</p>',
                unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 2: DO THEY COME BACK?
# ══════════════════════════════════════════════════════════════════════════════

def _section_2_do_they_come_back():
    st.markdown("## Do They Come Back?")

    total_users = db.get_user_count()
    user_data = db.get_user_return_table()

    if total_users <= 30:
        # View A — Per-user table
        if not user_data:
            st.info("No user data available yet.")
            return

        now = datetime.now()
        rows = []
        for u in user_data:
            last_active = u.get('last_active')
            signed_up = u.get('signed_up', '')

            # Determine status
            if last_active:
                try:
                    la_dt = datetime.fromisoformat(last_active.replace('Z', ''))
                    days_since = (now - la_dt).days
                except (ValueError, TypeError):
                    days_since = 999
            else:
                days_since = 999

            try:
                su_dt = datetime.fromisoformat(signed_up.replace('Z', '')) if signed_up else now
                days_since_signup = (now - su_dt).days
            except (ValueError, TypeError):
                days_since_signup = 999

            if days_since_signup <= 7:
                status = "New"
                css_class = "status-new"
            elif days_since <= 7:
                status = "Retained"
                css_class = "status-retained"
            elif days_since <= 30:
                status = "At risk"
                css_class = "status-at-risk"
            else:
                status = "Churned"
                css_class = "status-churned"

            # Calculate weeks active
            total_weeks = max(days_since_signup // 7, 1)
            weeks_active = u.get('weeks_active', 0)

            rows.append({
                "User": u['username'],
                "Signed Up": (signed_up or "Unknown")[:10],
                "Last Active": (last_active or "Never")[:10],
                "Total Actions": u.get('total_actions', 0),
                "Weeks Active": f"{weeks_active}/{total_weeks}",
                "Status": status,
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("Cohort view available when user base exceeds 30. "
                "Individual user tracking is more informative at current scale.")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 3: WHAT DO THEY ACTUALLY DO?
# ══════════════════════════════════════════════════════════════════════════════

def _section_3_what_do_they_do():
    st.markdown("## What Do They Actually Do?")

    engagement = db.get_module_engagement()
    this_week = db.get_module_engagement_week(0)
    last_week = db.get_module_engagement_week(1)

    MODULE_LABELS = {
        "content_generator": "Content Generator",
        "copy_editor": "Copy Editor",
        "social_assistant": "Social Assistant",
        "visual_audit": "Visual Audit",
    }

    if engagement:
        rows = []
        for e in engagement:
            module = e.get('module', '')
            total = e.get('total_actions', 0)
            unique = e.get('unique_users', 0)
            apu = round(total / unique, 1) if unique > 0 else 0

            tw = this_week.get(module, 0)
            lw = last_week.get(module, 0)
            if lw > 0:
                change = round((tw - lw) / lw * 100)
                change_str = f"+{change}%" if change >= 0 else f"{change}%"
            elif tw > 0:
                change_str = "New"
            else:
                change_str = "--"

            rows.append({
                "Module": MODULE_LABELS.get(module, module),
                "Total Actions": total,
                "Unique Users": unique,
                "Actions/User": apu,
                "This Week vs Last": change_str,
            })

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No module action data yet. Will populate after first user actions.")

    # Actions per session distribution
    st.markdown("### Actions Per Session Distribution")
    buckets, total_sessions = db.get_session_action_distribution()

    if total_sessions > 0:
        for label, count in buckets.items():
            pct = round(count / total_sessions * 100) if total_sessions > 0 else 0
            bar_width = max(pct * 3, 2)
            is_work = label in ("2-3", "4+")
            bar_color = GOLD if is_work else CHARCOAL
            st.markdown(
                f'<div class="distro-bar">'
                f'<span style="min-width:180px;">{label} actions:</span>'
                f'<div class="distro-fill" style="width:{bar_width}px; background:{bar_color};"></div>'
                f'<span>{pct}%</span>'
                f'</div>',
                unsafe_allow_html=True
            )
        work_pct = 0
        if total_sessions > 0:
            work_pct = round((buckets.get("2-3", 0) + buckets.get("4+", 0)) / total_sessions * 100)
        if work_pct >= 50:
            st.markdown(f'<p class="definition-note" style="color:{GOLD};">Users are doing real work: '
                        f'{work_pct}% of sessions have 2+ actions.</p>', unsafe_allow_html=True)
    else:
        st.info("No session data yet.")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 4: WHAT DOES IT COST TO SERVE A USER?
# ══════════════════════════════════════════════════════════════════════════════

def _section_4_cost_to_serve():
    st.markdown("## What Does It Cost To Serve A User?")

    costs = db.get_api_costs(30)
    total_cost = costs['total_cost'] or 0
    total_actions = costs['total_actions'] or 0
    active_users = db.get_active_user_count(30)

    avg_cost_per_action = round(total_cost / total_actions, 4) if total_actions > 0 else 0
    avg_cost_per_user = round(total_cost / active_users, 2) if active_users > 0 else 0

    solo_price = TIER_CONFIG['solo']['price_monthly_usd']
    agency_price = TIER_CONFIG['agency']['price_monthly_usd']
    agency_seats = TIER_CONFIG['agency']['max_seats']
    per_seat = round(agency_price / agency_seats, 2)

    solo_margin = round((1 - avg_cost_per_user / solo_price) * 100, 1) if solo_price > 0 and avg_cost_per_user > 0 else 0
    agency_margin = round((1 - avg_cost_per_user / per_seat) * 100, 1) if per_seat > 0 and avg_cost_per_user > 0 else 0

    # Summary table
    summary_rows = [
        ["Total API cost (this month)", f"${total_cost:,.2f}"],
        ["Avg cost per action", f"${avg_cost_per_action:.4f}"],
        ["Avg cost per active user (monthly)", f"${avg_cost_per_user:.2f}"],
        ["Gross margin at Solo (${:.0f})".format(solo_price),
         f"{solo_margin}%" if avg_cost_per_user > 0 else "--"],
        ["Gross margin at Agency per seat (${:.0f}/seat)".format(per_seat),
         f"{agency_margin}%" if avg_cost_per_user > 0 else "--"],
    ]
    st.markdown(_html_table(["Metric", "Value"], summary_rows), unsafe_allow_html=True)

    # Cost per module
    if costs['per_module']:
        st.markdown("### Cost Per Module")
        module_rows = []
        MODULE_LABELS = {
            "content_generator": "Content Generator",
            "copy_editor": "Copy Editor",
            "social_assistant": "Social Assistant",
            "visual_audit": "Visual Audit",
        }
        for m in costs['per_module']:
            module = m.get('module', '')
            cost = m.get('cost', 0) or 0
            actions = m.get('actions', 0) or 0
            cpa = round(cost / actions, 4) if actions > 0 else 0
            module_rows.append([
                MODULE_LABELS.get(module, module),
                f"${cpa:.3f}/action",
                f"{actions} actions",
                f"${cost:,.2f} total"
            ])
        st.markdown(_html_table(["Module", "Cost/Action", "Volume", "Total"], module_rows),
                    unsafe_allow_html=True)

    # Daily cost trend
    if costs['daily']:
        st.markdown("### Daily API Spend (Last 30 Days)")
        daily_df = pd.DataFrame(costs['daily'])
        daily_df.columns = ['Day', 'Cost']
        daily_df = daily_df.set_index('Day')
        st.line_chart(daily_df, color=GOLD)

    if total_actions == 0:
        st.info("API cost tracking active. Will populate after first module actions with instrumented code.")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 5: ARE USERS INVESTING IN THE PLATFORM?
# ══════════════════════════════════════════════════════════════════════════════

def _section_5_platform_investment():
    st.markdown("## Are Users Investing In The Platform?")

    view_tabs = st.tabs(["Current Distribution", "Confidence Over Time", "Profile Completion"])

    with view_tabs[0]:
        buckets, scores = db.get_calibration_distribution()
        labels = {
            "0-25": ("Not Calibrated", COPPER),
            "26-50": ("Partially", CHARCOAL),
            "51-75": ("Calibrated", TEAL),
            "76-100": ("Fully Calibrated", GOLD),
        }
        total = sum(buckets.values())
        if total > 0:
            for key, count in buckets.items():
                label, color = labels[key]
                pct = round(count / total * 100)
                bar_width = max(pct * 3, 2)
                st.markdown(
                    f'<div class="distro-bar">'
                    f'<span style="min-width:200px;">{label} ({key}%):</span>'
                    f'<div class="distro-fill" style="width:{bar_width}px; background:{color};"></div>'
                    f'<span>{count} brands</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.info("No brand profiles yet.")

    with view_tabs[1]:
        trend = db.get_avg_calibration_trend(8)
        if trend:
            trend_df = pd.DataFrame(trend)
            trend_df.columns = ['Week', 'Avg Confidence']
            trend_df = trend_df.set_index('Week')
            st.line_chart(trend_df, color=GOLD)
        else:
            st.info("Calibration trend data will populate as users modify their brand profiles.")

    with view_tabs[2]:
        completion = db.get_profile_completion_stats()
        if completion:
            comp_labels = {
                "strategy_fields": "Strategy fields",
                "voice_samples": "At least 1 voice sample",
                "voice_3plus": "3+ samples (any cluster)",
                "message_house": "Message house started",
                "visual_identity": "Visual identity",
                "social_samples": "Social samples",
            }
            for key, label in comp_labels.items():
                pct = completion.get(key, 0)
                bar_width = max(pct * 3, 2)
                color = GOLD if pct >= 50 else (COPPER if pct < 25 else CHARCOAL)
                st.markdown(
                    f'<div class="distro-bar">'
                    f'<span style="min-width:250px;">{label}:</span>'
                    f'<div class="distro-fill" style="width:{bar_width}px; background:{color};"></div>'
                    f'<span>{pct}% of brands</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
        else:
            st.info("No brand profiles yet.")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 6: WHERE DO USERS DROP OFF?
# ══════════════════════════════════════════════════════════════════════════════

def _section_6_onboarding_funnel():
    st.markdown("## Where Do Users Drop Off?")

    funnel, total_users = db.get_onboarding_funnel()

    STEP_LABELS = {
        "account_created": "Signed up",
        "first_brand_created": "Created first brand",
        "first_voice_sample": "Uploaded first voice sample",
        "first_module_run": "Ran first module",
        "message_house_started": "Started message house",
        "calibration_crossed_60": "Reached 60% confidence",
        "calibration_crossed_90": "Reached 90% confidence",
    }

    if total_users > 0:
        for step_key, label in STEP_LABELS.items():
            count = funnel.get(step_key, 0)
            pct = round(count / total_users * 100) if total_users > 0 else 0
            bar_width = max(pct * 3, 2)
            st.markdown(
                f'<div class="funnel-row">'
                f'<span class="funnel-label">{label}:</span>'
                f'<span class="funnel-stat">{pct}%</span>'
                f'<div class="funnel-bar" style="width:{bar_width}px;"></div>'
                f'<span class="funnel-stat">{count}</span>'
                f'</div>',
                unsafe_allow_html=True
            )

        # Inactive user diagnostics
        st.markdown("### Inactive User Diagnostics")
        st.caption("Users inactive for 14+ days.")
        diagnostics = db.get_inactive_user_diagnostics(14)
        if diagnostics:
            diag_rows = []
            for d in diagnostics[:20]:
                diag_rows.append({
                    "User": d['username'],
                    "Last Active": (d['last_active'] or "Never")[:10],
                    "Actions": d['total_actions'],
                    "Confidence": f"{d['confidence']}%",
                    "Missing": d['missing'],
                })
            st.dataframe(pd.DataFrame(diag_rows), use_container_width=True, hide_index=True)
        else:
            st.success("No inactive users to diagnose.")
    else:
        st.info("Onboarding funnel will populate as users register and interact with the platform.")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 7: WHERE DO USERS COME FROM?
# ══════════════════════════════════════════════════════════════════════════════

def _section_7_acquisition():
    st.markdown("## Where Do Users Come From?")

    sources = db.get_acquisition_sources()
    if sources:
        total = sum(s['count'] for s in sources)
        for s in sources:
            pct = round(s['count'] / total * 100) if total > 0 else 0
            bar_width = max(pct * 3, 2)
            source_label = (s.get('source') or 'unknown').title()
            st.markdown(
                f'<div class="distro-bar">'
                f'<span style="min-width:120px;">{source_label}:</span>'
                f'<div class="distro-fill" style="width:{bar_width}px;"></div>'
                f'<span>{pct}%</span>'
                f'</div>',
                unsafe_allow_html=True
            )
    else:
        st.info("Acquisition tracking active. Will populate after first user registrations with instrumented code.")


# ══════════════════════════════════════════════════════════════════════════════
# SECTION 8: WHAT'S THE REVENUE PATH?
# ══════════════════════════════════════════════════════════════════════════════

def _section_8_revenue():
    st.markdown("## What's The Revenue Path?")

    rev = db.get_revenue_metrics()
    tier_counts = rev.get('tier_counts', {})

    # Tier breakdown
    tier_labels = {
        'solo': f"Solo (${TIER_CONFIG['solo']['price_monthly_usd']})",
        'agency': f"Agency (${TIER_CONFIG['agency']['price_monthly_usd']})",
        'enterprise': f"Enterprise (${TIER_CONFIG['enterprise']['price_monthly_usd']})",
    }
    # Combine non-paying tiers
    free_trial = sum(v for k, v in tier_counts.items() if k not in ('solo', 'agency', 'enterprise', 'retainer'))
    tier_rows = [["Free / trial", f"{free_trial} users"]]
    for key, label in tier_labels.items():
        count = tier_counts.get(key, 0)
        tier_rows.append([label, f"{count} {'users' if key == 'solo' else 'orgs'}"])

    st.markdown(_html_table(["Tier", "Count"], tier_rows), unsafe_allow_html=True)

    # MRR calculation
    solo_count = tier_counts.get('solo', 0)
    agency_count = tier_counts.get('agency', 0)
    enterprise_count = tier_counts.get('enterprise', 0)
    mrr = (solo_count * TIER_CONFIG['solo']['price_monthly_usd'] +
           agency_count * TIER_CONFIG['agency']['price_monthly_usd'] +
           enterprise_count * TIER_CONFIG['enterprise']['price_monthly_usd'])

    st.markdown(f"**MRR:** ${mrr:,.2f}")

    # Conversion metrics
    conversion_rows = [
        ["Free to paid conversion", f"{rev['conversion_rate']}%" if rev['paying_users'] > 0
         else "--"],
        ["Avg days from signup to payment",
         f"{rev['avg_days_to_conversion']}" if rev['avg_days_to_conversion'] else "--"],
    ]
    st.markdown(_html_table(["Metric", "Value"], conversion_rows), unsafe_allow_html=True)

    if rev['paying_users'] == 0:
        st.markdown(
            f'<p class="definition-note">Conversion tracking active. Will populate when first '
            f'subscription is processed.</p>',
            unsafe_allow_html=True
        )


# ══════════════════════════════════════════════════════════════════════════════
# EXPORTS
# ══════════════════════════════════════════════════════════════════════════════

def _section_exports():
    st.markdown("## Data Export")

    c1, c2 = st.columns(2)

    with c1:
        st.markdown("### Investor Summary")
        st.caption("Narrative report for pitch meetings.")
        if st.button("Generate Investor Summary", key="pa_generate_summary"):
            report = _generate_investor_summary()
            st.download_button(
                "Download Summary (Markdown)",
                report,
                file_name=f"signet_investor_summary_{datetime.now().strftime('%Y%m%d')}.md",
                mime="text/markdown",
                key="pa_download_summary"
            )
            st.text_area("Preview", report, height=400, key="pa_summary_preview")

    with c2:
        st.markdown("### Raw Events Export")
        st.caption("Full product_events dump for due diligence.")
        if st.button("Export Raw Events (CSV)", key="pa_export_csv"):
            csv_data = db.get_product_events_csv()
            st.download_button(
                "Download CSV",
                csv_data,
                file_name=f"signet_product_events_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                key="pa_download_csv"
            )


def _generate_investor_summary():
    """Generate a markdown investor summary report."""
    now = datetime.now()
    billing_month = now.strftime("%Y-%m")

    total_users = db.get_user_count()
    active_30d = db.get_active_users(30)
    active_pct = round(active_30d / total_users * 100) if total_users > 0 else 0
    avg_sessions = db.get_user_sessions_per_week()

    engagement = db.get_module_engagement()
    top_module = engagement[0]['module'].replace('_', ' ').title() if engagement else "N/A"
    total_actions = sum(e.get('total_actions', 0) for e in engagement) if engagement else 0
    actions_per_session = round(total_actions / max(active_30d, 1), 1)

    # Retention
    user_data = db.get_user_return_table()
    users_14d_ago = [u for u in user_data
                     if u.get('signed_up') and
                     (now - datetime.fromisoformat(u['signed_up'].replace('Z', ''))).days > 14]
    retained = sum(1 for u in users_14d_ago
                   if u.get('last_active') and
                   (now - datetime.fromisoformat(u['last_active'].replace('Z', ''))).days <= 7)
    retention_pct = round(retained / len(users_14d_ago) * 100) if users_14d_ago else 0

    # Calibration
    buckets, scores = db.get_calibration_distribution()
    avg_confidence = round(sum(scores) / len(scores)) if scores else 0
    completion = db.get_profile_completion_stats()
    voice_pct = completion.get('voice_samples', 0)
    mh_pct = completion.get('message_house', 0)

    # Costs
    costs = db.get_api_costs(30)
    total_cost = costs['total_cost'] or 0
    avg_cost_per_user = round(total_cost / active_30d, 2) if active_30d > 0 else 0
    solo_price = TIER_CONFIG['solo']['price_monthly_usd']
    gross_margin = round((1 - avg_cost_per_user / solo_price) * 100, 1) if solo_price > 0 and avg_cost_per_user > 0 else 0

    # Funnel
    funnel, funnel_total = db.get_onboarding_funnel()
    brand_pct = round(funnel.get('first_brand_created', 0) / funnel_total * 100) if funnel_total > 0 else 0
    voice_funnel_pct = round(funnel.get('first_voice_sample', 0) / funnel_total * 100) if funnel_total > 0 else 0
    module_pct = round(funnel.get('first_module_run', 0) / funnel_total * 100) if funnel_total > 0 else 0

    # Find largest dropoff
    steps = ['account_created', 'first_brand_created', 'first_voice_sample',
             'first_module_run', 'message_house_started']
    step_labels = {
        'account_created': 'Signup',
        'first_brand_created': 'First brand',
        'first_voice_sample': 'First voice sample',
        'first_module_run': 'First module',
        'message_house_started': 'Message house',
    }
    max_drop = 0
    drop_from = drop_to = ""
    for i in range(len(steps) - 1):
        a = funnel.get(steps[i], 0)
        b = funnel.get(steps[i + 1], 0)
        drop = a - b
        if drop > max_drop:
            max_drop = drop
            drop_from = step_labels[steps[i]]
            drop_to = step_labels[steps[i + 1]]

    # Revenue
    rev = db.get_revenue_metrics()
    mrr_val = sum(
        rev['tier_counts'].get(k, 0) * TIER_CONFIG[k]['price_monthly_usd']
        for k in ('solo', 'agency', 'enterprise')
    )

    # Acquisition
    sources = db.get_acquisition_sources()
    primary_source = sources[0]['source'].title() if sources else "Direct"
    primary_pct = round(sources[0]['count'] / sum(s['count'] for s in sources) * 100) if sources else 100

    report = f"""# Signet — Product Metrics Summary
Period: Launch to {now.strftime('%B %d, %Y')}
Generated: {now.strftime('%Y-%m-%d %H:%M')}

## Users & Engagement
{total_users} registered. {active_30d} active in the last 30 days ({active_pct}%).
Active users average {avg_sessions} sessions per week and {actions_per_session} module actions per session.
Most-used module: {top_module} ({round(engagement[0]['total_actions'] / total_actions * 100) if engagement and total_actions > 0 else 0}% of all actions).

## Retention
Of {len(users_14d_ago)} users who signed up more than 14 days ago, {retained} ({retention_pct}%) returned
and performed at least one action in the last 7 days.

## Product Depth
Average Engine Confidence across active brands: {avg_confidence}%.
{voice_pct}% of brands have voice samples. {mh_pct}% have started a message house.

## Unit Economics
Average API cost per active user per month: ${avg_cost_per_user:.2f}.
At Solo pricing (${solo_price}/month), estimated gross margin: {gross_margin}%.
Total platform API cost this month: ${total_cost:,.2f}.

## Onboarding
{brand_pct}% create a brand. {voice_funnel_pct}% upload first voice sample.
{module_pct}% run first module. Largest drop-off: between {drop_from} and {drop_to}.

## Revenue
Current MRR: ${mrr_val:,.2f} across {rev['paying_users']} subscribers.
Free-to-paid conversion: {rev['conversion_rate']}%{'' if rev['paying_users'] > 0 else ' (No conversions yet — tracking active)'}.

## Acquisition
Primary channel: {primary_source} ({primary_pct}% of signups).
"""
    return report
