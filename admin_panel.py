"""
admin_panel.py — Super Admin Panel ("God Mode")

Only accessible to users where subscription_tier == 'super_admin'.
Renders as a page within the main Streamlit app via app_mode routing.
"""

import streamlit as st
import pandas as pd
import json
import os
import time
from datetime import datetime, timedelta

import db_manager as db
import subscription_manager as sub_manager
from tier_config import TIER_CONFIG


# ── Access check ─────────────────────────────────────────────────────────────

def _is_admin():
    """Returns True if current session is a super_admin (tier-based or NICK_ADMIN)."""
    tier_key = st.session_state.get('tier', {}).get('_tier_key', '')
    raw_user = (st.session_state.get('username') or '').upper()
    return tier_key == 'super_admin' or raw_user == 'NICK_ADMIN'


def _admin_user():
    """Returns the real admin username (even during impersonation)."""
    admin_session = st.session_state.get('admin_session')
    if admin_session:
        return admin_session.get('username', 'admin')
    return st.session_state.get('username', 'admin')


# ── Main render ──────────────────────────────────────────────────────────────

def render_admin_panel():
    """Top-level render function. Called from app.py routing."""
    if not _is_admin():
        st.session_state['app_mode'] = 'DASHBOARD'
        st.rerun()
        return

    st.title("ADMIN PANEL")
    st.caption("Super Admin Control Center")

    tabs = st.tabs([
        "USERS", "ORGANIZATIONS", "SUBSCRIPTIONS",
        "IMPERSONATION", "ANALYTICS", "AUDIT LOG",
        "SYSTEM"
    ])

    with tabs[0]:
        _render_user_management()
    with tabs[1]:
        _render_org_management()
    with tabs[2]:
        _render_subscription_overrides()
    with tabs[3]:
        _render_impersonation()
    with tabs[4]:
        _render_usage_analytics()
    with tabs[5]:
        _render_audit_log()
    with tabs[6]:
        _render_system_health()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: USER MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

def _render_user_management():
    st.subheader("User Management")

    # --- User Table ---
    users = db.get_all_users_full()
    billing_month = datetime.now().strftime("%Y-%m")

    rows = []
    for u in users:
        org_id = u.get('org_id') or u['username']
        brand_count = db.count_user_brands(org_id, exclude_sample=True)
        usage = db.get_monthly_usage_user(u['username'], billing_month)
        tier_key = u.get('subscription_tier', 'solo')
        tier_display = TIER_CONFIG.get(tier_key, {}).get('display_name', tier_key)
        org_name = u.get('org_id') or 'Solo'
        flags = []
        if u.get('is_beta_tester'):
            flags.append("BETA")
        if u.get('is_suspended'):
            flags.append("SUSPENDED")
        rows.append({
            "Username": u['username'],
            "Email": u.get('email', ''),
            "Tier": tier_display,
            "Org": org_name,
            "Role": u.get('org_role', 'member'),
            "Status": u.get('subscription_status', 'inactive'),
            "Flags": " | ".join(flags) if flags else "",
            "Brands": brand_count,
            "Actions (Mo)": usage,
            "Last Login": (u.get('last_login') or 'Never')[:16],
            "Created": (u.get('created_at') or 'Unknown')[:10],
        })

    if rows:
        df = pd.DataFrame(rows)

        # Search filter
        search = st.text_input("Search users", key="admin_user_search", placeholder="Filter by username or email...")
        if search:
            mask = df['Username'].str.contains(search, case=False, na=False) | \
                   df['Email'].str.contains(search, case=False, na=False)
            df = df[mask]

        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No users found.")

    st.divider()

    col_create, col_edit, col_delete = st.columns(3)

    # --- Create User ---
    with col_create:
        st.markdown("#### Create User")
        with st.form("admin_create_user"):
            new_username = st.text_input("Username", max_chars=64)
            new_email = st.text_input("Email", max_chars=120)
            new_password = st.text_input("Password", type="password", max_chars=64)
            new_tier = st.selectbox("Tier", list(TIER_CONFIG.keys()),
                                    format_func=lambda k: TIER_CONFIG[k]['display_name'])
            orgs = db.get_all_organizations()
            org_options = ["Solo (No Org)"] + [o['org_id'] for o in orgs]
            new_org = st.selectbox("Organization", org_options)
            new_role = st.selectbox("Org Role", ["member", "owner"])

            if st.form_submit_button("Create User"):
                if not new_username or not new_email or not new_password:
                    st.error("Username, email, and password are required.")
                else:
                    org_val = None if new_org == "Solo (No Org)" else new_org
                    ok = db.create_user_admin(new_username, new_email, new_password,
                                              tier=new_tier, org_id=org_val, org_role=new_role)
                    if ok:
                        db.log_admin_action(_admin_user(), "user_created", "user", new_username,
                                            {"tier": new_tier, "org": org_val, "role": new_role})
                        st.success(f"User '{new_username}' created.")
                        st.rerun()
                    else:
                        st.error("Failed — username or email may already exist.")

    # --- Edit User ---
    with col_edit:
        st.markdown("#### Edit User")
        usernames = [u['username'] for u in users]
        if usernames:
            edit_user = st.selectbox("Select user to edit", usernames, key="admin_edit_user_select")
            user_data = db.get_user_full(edit_user)
            if user_data:
                with st.form("admin_edit_user"):
                    edit_email = st.text_input("Email", value=user_data.get('email', ''))
                    edit_tier = st.selectbox("Tier", list(TIER_CONFIG.keys()),
                                            index=list(TIER_CONFIG.keys()).index(
                                                user_data.get('subscription_tier', 'solo')),
                                            format_func=lambda k: TIER_CONFIG[k]['display_name'])
                    edit_status = st.selectbox("Status",
                                              ["active", "inactive", "past_due", "cancelled"],
                                              index=["active", "inactive", "past_due", "cancelled"].index(
                                                  user_data.get('subscription_status', 'inactive')))
                    orgs = db.get_all_organizations()
                    org_options = ["Solo (No Org)"] + [o['org_id'] for o in orgs]
                    current_org = user_data.get('org_id') or "Solo (No Org)"
                    edit_org = st.selectbox("Organization", org_options,
                                           index=org_options.index(current_org) if current_org in org_options else 0)
                    edit_role = st.selectbox("Org Role", ["member", "owner"],
                                            index=["member", "owner"].index(user_data.get('org_role', 'member')))
                    edit_beta = st.checkbox("Beta Tester", value=bool(user_data.get('is_beta_tester', 0)))

                    if st.form_submit_button("Save Changes"):
                        changes = {}
                        old_vals = {}
                        if edit_email != user_data.get('email', ''):
                            changes['email'] = edit_email
                            old_vals['email'] = user_data.get('email', '')
                        if edit_tier != user_data.get('subscription_tier', 'solo'):
                            changes['subscription_tier'] = edit_tier
                            old_vals['subscription_tier'] = user_data.get('subscription_tier', 'solo')
                        if edit_status != user_data.get('subscription_status', 'inactive'):
                            changes['subscription_status'] = edit_status
                            old_vals['subscription_status'] = user_data.get('subscription_status', 'inactive')
                        org_val = None if edit_org == "Solo (No Org)" else edit_org
                        if org_val != user_data.get('org_id'):
                            changes['org_id'] = org_val
                            old_vals['org_id'] = user_data.get('org_id')
                        if edit_role != user_data.get('org_role', 'member'):
                            changes['org_role'] = edit_role
                            old_vals['org_role'] = user_data.get('org_role', 'member')
                        if edit_beta != bool(user_data.get('is_beta_tester', 0)):
                            changes['is_beta_tester'] = 1 if edit_beta else 0
                            old_vals['is_beta_tester'] = user_data.get('is_beta_tester', 0)
                            # Log beta flag change specifically
                            action = "beta_flag_set" if edit_beta else "beta_flag_removed"
                            db.log_admin_action(_admin_user(), action, "user", edit_user,
                                                {"beta_tester": edit_beta})

                        if changes:
                            db.update_user_fields(edit_user, **changes)
                            db.log_admin_action(_admin_user(), "user_edited", "user", edit_user,
                                                {"changes": changes, "old_values": old_vals})
                            st.success(f"User '{edit_user}' updated.")
                            st.rerun()
                        else:
                            st.info("No changes detected.")

        # --- Password Reset (separate from edit form) ---
        st.markdown("#### Reset Password")
        with st.form("admin_reset_password"):
            reset_new_pw = st.text_input("New Password", type="password", max_chars=64,
                                         key="admin_reset_pw_input")
            reset_confirm_pw = st.text_input("Confirm Password", type="password", max_chars=64,
                                             key="admin_reset_pw_confirm")
            if st.form_submit_button("Reset Password"):
                if not reset_new_pw or len(reset_new_pw) < 8:
                    st.error("Password must be at least 8 characters.")
                elif reset_new_pw != reset_confirm_pw:
                    st.error("Passwords do not match.")
                else:
                    db.reset_user_password(edit_user, reset_new_pw)
                    db.log_admin_action(_admin_user(), "password_reset", "user", edit_user,
                                        {"reset_by": _admin_user()})
                    st.success(f"Password reset for '{edit_user}'.")

    # --- Delete User ---
    with col_delete:
        st.markdown("#### Delete User")
        deletable = [u['username'] for u in users if u.get('subscription_tier') != 'super_admin']
        if deletable:
            del_user = st.selectbox("Select user to delete", deletable, key="admin_del_user_select")
            st.warning(f"This will permanently delete **{del_user}** and all their data. This cannot be undone.")
            confirm_name = st.text_input("Type the username to confirm", key="admin_del_confirm")
            if st.button("Delete User", type="primary", key="admin_del_btn"):
                if confirm_name == del_user:
                    result = db.delete_user_full(del_user)
                    if result.get('deleted'):
                        db.log_admin_action(_admin_user(), "user_deleted", "user", del_user,
                                            {"result": result})
                        st.success(f"User '{del_user}' deleted.")
                        st.rerun()
                    else:
                        st.error(f"Delete failed: {result.get('reason', 'Unknown error')}")
                else:
                    st.error("Username does not match. Deletion cancelled.")
        else:
            st.info("No deletable users (super_admin accounts cannot be deleted via UI).")

    # --- Account Suspension ---
    st.divider()
    st.markdown("#### Account Suspension")
    suspendable = [u['username'] for u in users if u.get('subscription_tier') != 'super_admin']
    if suspendable:
        susp_user = st.selectbox("Select user", suspendable, key="admin_susp_user_select")
        susp_data = db.get_user_full(susp_user)
        if susp_data and susp_data.get('is_suspended'):
            st.markdown(
                f'<div style="background:rgba(166,120,77,0.1); border-left:3px solid #a6784d; '
                f'padding:10px; margin:8px 0; font-size:0.85rem;">'
                f'<strong style="color:#a6784d;">SUSPENDED</strong> '
                f'by {susp_data.get("suspended_by", "unknown")} '
                f'on {(susp_data.get("suspended_at") or "")[:16]}<br>'
                f'<em>Reason: {susp_data.get("suspended_reason", "No reason given")}</em></div>',
                unsafe_allow_html=True
            )
            if st.button("Unsuspend Account", key="admin_unsuspend_btn"):
                db.unsuspend_user(susp_user)
                suspended_at = susp_data.get('suspended_at', '')
                db.log_admin_action(
                    _admin_user(), "account_unsuspended", "user", susp_user,
                    {"unsuspended_by": _admin_user(), "was_suspended_at": suspended_at}
                )
                st.success(f"Account '{susp_user}' unsuspended.")
                st.rerun()
        else:
            susp_reason = st.text_input("Suspension reason (required)", key="admin_susp_reason",
                                        placeholder="e.g. 'Abuse detected — 500 actions in 1 hour'")
            if st.button("Suspend Account", type="primary", key="admin_suspend_btn"):
                if not susp_reason.strip():
                    st.error("A reason is required to suspend an account.")
                else:
                    db.suspend_user(susp_user, susp_reason.strip(), _admin_user())
                    db.log_admin_action(
                        _admin_user(), "account_suspended", "user", susp_user,
                        {"reason": susp_reason.strip(), "suspended_by": _admin_user()}
                    )
                    st.success(f"Account '{susp_user}' suspended.")
                    st.rerun()
    else:
        st.info("No suspendable users (super_admin accounts cannot be suspended).")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: ORGANIZATION MANAGEMENT
# ══════════════════════════════════════════════════════════════════════════════

def _render_org_management():
    st.subheader("Organization Management")

    orgs = db.get_all_organizations()
    rows = []
    for o in orgs:
        import sqlite3
        conn = sqlite3.connect(db.DB_NAME)
        member_count = conn.execute("SELECT COUNT(*) FROM users WHERE org_id = ?", (o['org_id'],)).fetchone()[0]
        conn.close()
        brand_count = db.count_user_brands(o['org_id'], exclude_sample=True)
        tier_key = o.get('subscription_tier', 'agency')
        tier = TIER_CONFIG.get(tier_key, TIER_CONFIG['solo'])
        rows.append({
            "Org Name": o.get('org_name', o['org_id']),
            "Org ID": o['org_id'],
            "Tier": tier.get('display_name', tier_key),
            "Owner": o.get('owner_username', ''),
            "Members": f"{member_count}/{tier['max_seats'] if tier['max_seats'] != -1 else 'Unlimited'}",
            "Brands": f"{brand_count}/{tier['max_brands'] if tier['max_brands'] != -1 else 'Unlimited'}",
            "Created": (o.get('created_at') or '')[:10],
        })

    if rows:
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

    st.divider()
    col_create, col_edit, col_delete = st.columns(3)

    # --- Create Org ---
    with col_create:
        st.markdown("#### Create Organization")
        with st.form("admin_create_org"):
            org_name = st.text_input("Org Name", max_chars=100)
            org_tier = st.selectbox("Tier", ["agency", "enterprise", "retainer"],
                                    format_func=lambda k: TIER_CONFIG[k]['display_name'],
                                    key="admin_create_org_tier")
            all_users = db.get_all_users_full()
            owner_options = [u['username'] for u in all_users]
            org_owner = st.selectbox("Owner", owner_options, key="admin_create_org_owner") if owner_options else None

            if st.form_submit_button("Create Organization"):
                if not org_name or not org_owner:
                    st.error("Org name and owner are required.")
                else:
                    org_id = org_name.lower().replace(' ', '_').replace('-', '_')[:50]
                    ok = db.create_organization(org_id, org_name, org_tier, org_owner)
                    if ok:
                        db.update_user_fields(org_owner, org_id=org_id, org_role='owner')
                        db.log_admin_action(_admin_user(), "org_created", "organization", org_id,
                                            {"name": org_name, "tier": org_tier, "owner": org_owner})
                        st.success(f"Organization '{org_name}' created.")
                        st.rerun()
                    else:
                        st.error("Failed — org ID may already exist.")

    # --- Edit Org ---
    with col_edit:
        st.markdown("#### Edit Organization")
        if orgs:
            org_ids = [o['org_id'] for o in orgs]
            edit_org_id = st.selectbox("Select org", org_ids, key="admin_edit_org_select")
            org_data = db.get_organization(edit_org_id)
            if org_data:
                with st.form("admin_edit_org"):
                    edit_org_name = st.text_input("Org Name", value=org_data.get('org_name', ''))
                    edit_org_tier = st.selectbox("Tier", ["agency", "enterprise", "retainer"],
                                                index=["agency", "enterprise", "retainer"].index(
                                                    org_data.get('subscription_tier', 'agency'))
                                                if org_data.get('subscription_tier', 'agency') in ["agency",
                                                                                                    "enterprise",
                                                                                                    "retainer"] else 0,
                                                format_func=lambda k: TIER_CONFIG[k]['display_name'],
                                                key="admin_edit_org_tier")
                    all_users = db.get_all_users_full()
                    owner_options = [u['username'] for u in all_users]
                    current_owner = org_data.get('owner_username', '')
                    edit_owner = st.selectbox("Owner", owner_options,
                                             index=owner_options.index(
                                                 current_owner) if current_owner in owner_options else 0,
                                             key="admin_edit_org_owner")

                    if st.form_submit_button("Save Org Changes"):
                        changes = {}
                        if edit_org_name != org_data.get('org_name', ''):
                            changes['org_name'] = edit_org_name
                        if edit_org_tier != org_data.get('subscription_tier', 'agency'):
                            changes['subscription_tier'] = edit_org_tier
                        if edit_owner != current_owner:
                            changes['owner_username'] = edit_owner
                            # Update roles
                            db.update_user_fields(current_owner, org_role='member')
                            db.update_user_fields(edit_owner, org_id=edit_org_id, org_role='owner')

                        if changes:
                            db.update_organization_fields(edit_org_id, **changes)
                            db.log_admin_action(_admin_user(), "org_edited", "organization", edit_org_id,
                                                {"changes": changes})
                            st.success(f"Organization '{edit_org_id}' updated.")
                            st.rerun()
                        else:
                            st.info("No changes detected.")
        else:
            st.info("No organizations to edit.")

    # --- Delete Org ---
    with col_delete:
        st.markdown("#### Delete Organization")
        if orgs:
            del_org_id = st.selectbox("Select org to delete", [o['org_id'] for o in orgs],
                                      key="admin_del_org_select")
            org_info = db.get_organization(del_org_id)
            if org_info:
                st.warning(
                    f"This will delete **{org_info.get('org_name', del_org_id)}**, "
                    f"disassociate all members, and reassign brands to {org_info.get('owner_username', 'owner')}.")
                confirm_org = st.text_input("Type the org ID to confirm", key="admin_del_org_confirm")
                if st.button("Delete Organization", type="primary", key="admin_del_org_btn"):
                    if confirm_org == del_org_id:
                        result = db.delete_organization_full(del_org_id)
                        if result.get('deleted'):
                            db.log_admin_action(_admin_user(), "org_deleted", "organization", del_org_id,
                                                {"result": result, "name": org_info.get('org_name', '')})
                            st.success(f"Organization '{del_org_id}' deleted.")
                            st.rerun()
                        else:
                            st.error(f"Delete failed: {result.get('reason', 'Unknown error')}")
                    else:
                        st.error("Org ID does not match. Deletion cancelled.")
        else:
            st.info("No organizations to delete.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: SUBSCRIPTION OVERRIDES
# ══════════════════════════════════════════════════════════════════════════════

def _render_subscription_overrides():
    st.subheader("Subscription Overrides")

    users = db.get_all_users_full()
    usernames = [u['username'] for u in users]
    if not usernames:
        st.info("No users.")
        return

    sub_tabs = st.tabs(["Change Tier", "Grant Comp", "Extend Subscription", "Set Retainer"])

    # --- Change User Tier ---
    with sub_tabs[0]:
        st.markdown("#### Change User Tier")
        with st.form("admin_change_tier"):
            tier_user = st.selectbox("Select user", usernames, key="admin_tier_user")
            user_data = db.get_user_full(tier_user) if tier_user else {}
            current_tier = user_data.get('subscription_tier', 'solo') if user_data else 'solo'
            st.caption(f"Current tier: **{TIER_CONFIG.get(current_tier, {}).get('display_name', current_tier)}**")
            new_tier = st.selectbox("New tier", list(TIER_CONFIG.keys()),
                                    format_func=lambda k: TIER_CONFIG[k]['display_name'],
                                    key="admin_new_tier")

            if st.form_submit_button("Apply Tier Change"):
                if new_tier == current_tier:
                    st.info("No change — same tier selected.")
                else:
                    # Check for over-limit on downgrade
                    org_id = user_data.get('org_id') or tier_user
                    new_config = TIER_CONFIG.get(new_tier, TIER_CONFIG['solo'])
                    brand_count = db.count_user_brands(org_id)
                    max_brands = new_config['max_brands']

                    if max_brands != -1 and brand_count > max_brands:
                        st.warning(
                            f"**{tier_user}** currently has {brand_count} brands, which exceeds the "
                            f"{new_config['display_name']} limit of {max_brands}. They won't be able to create "
                            f"new brands until under the limit, but existing brands remain accessible."
                        )

                    db.update_user_fields(tier_user, subscription_tier=new_tier, subscription_status='active')
                    db.log_admin_action(_admin_user(), "tier_changed", "subscription", tier_user,
                                        {"old_tier": current_tier, "new_tier": new_tier})
                    st.success(f"Tier changed: {current_tier} -> {new_tier}")
                    st.rerun()

    # --- Grant Comp Access ---
    with sub_tabs[1]:
        st.markdown("#### Grant Comp Access")
        with st.form("admin_grant_comp"):
            comp_user = st.selectbox("Select user", usernames, key="admin_comp_user")
            comp_tier = st.selectbox("Tier to grant", ["solo", "agency", "enterprise"],
                                     format_func=lambda k: TIER_CONFIG[k]['display_name'],
                                     key="admin_comp_tier")
            comp_duration = st.selectbox("Duration", [
                "1 month", "3 months", "6 months", "12 months", "Indefinite"
            ], key="admin_comp_duration")
            comp_reason = st.text_area("Reason", key="admin_comp_reason",
                                       placeholder="Why is this comp being granted?")

            if st.form_submit_button("Grant Comp Access"):
                expires_at = None
                if comp_duration != "Indefinite":
                    months = int(comp_duration.split()[0])
                    expires_at = (datetime.now() + timedelta(days=months * 30)).isoformat()

                db.update_user_fields(
                    comp_user,
                    subscription_tier=comp_tier,
                    subscription_status='active',
                    comp_expires_at=expires_at,
                    comp_reason=comp_reason
                )
                db.log_admin_action(_admin_user(), "comp_granted", "subscription", comp_user, {
                    "tier": comp_tier,
                    "duration": comp_duration,
                    "expires_at": expires_at,
                    "reason": comp_reason
                })
                st.success(f"Comp access granted to {comp_user}: {TIER_CONFIG[comp_tier]['display_name']} for {comp_duration}.")
                st.rerun()

    # --- Extend Subscription ---
    with sub_tabs[2]:
        st.markdown("#### Extend Subscription")
        st.caption("Override note — prevents platform deactivation even if LS shows expired.")
        with st.form("admin_extend_sub"):
            ext_user = st.selectbox("Select user", usernames, key="admin_ext_user")
            ext_months = st.number_input("Extension (months)", min_value=1, max_value=24, value=1)

            if st.form_submit_button("Apply Extension"):
                override_until = (datetime.now() + timedelta(days=ext_months * 30)).isoformat()
                db.update_user_fields(ext_user, subscription_override_until=override_until)
                db.log_admin_action(_admin_user(), "subscription_extended", "subscription", ext_user, {
                    "months": ext_months,
                    "override_until": override_until
                })
                st.success(f"Subscription override applied for {ext_user} until {override_until[:10]}.")
                st.rerun()

    # --- Set Retainer ---
    with sub_tabs[3]:
        st.markdown("#### Set Retainer Status")
        st.caption("For Castellan PR clients. Bypasses LS entirely.")

        ret_tabs = st.tabs(["User Retainer", "Org Retainer"])
        with ret_tabs[0]:
            with st.form("admin_set_retainer_user"):
                ret_user = st.selectbox("Select user", usernames, key="admin_ret_user")
                if st.form_submit_button("Mark as Retainer"):
                    db.update_user_fields(ret_user, subscription_tier='retainer', subscription_status='active')
                    db.log_admin_action(_admin_user(), "retainer_set", "subscription", ret_user,
                                        {"type": "user"})
                    st.success(f"{ret_user} marked as Retainer.")
                    st.rerun()

        with ret_tabs[1]:
            orgs = db.get_all_organizations()
            if orgs:
                with st.form("admin_set_retainer_org"):
                    ret_org = st.selectbox("Select org", [o['org_id'] for o in orgs], key="admin_ret_org")
                    if st.form_submit_button("Mark Org as Retainer"):
                        db.update_organization_fields(ret_org, subscription_tier='retainer')
                        db.log_admin_action(_admin_user(), "retainer_set", "subscription", ret_org,
                                            {"type": "organization"})
                        st.success(f"Org '{ret_org}' marked as Retainer.")
                        st.rerun()
            else:
                st.info("No organizations.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: IMPERSONATION
# ══════════════════════════════════════════════════════════════════════════════

def _render_impersonation():
    st.subheader("Impersonation (Login-As)")
    st.caption("View the platform exactly as a specific user sees it.")

    # Check if currently impersonating
    if st.session_state.get('admin_session'):
        impersonating = st.session_state.get('username', 'Unknown')
        st.info(f"Currently impersonating: **{impersonating}**")
        if st.button("End Impersonation", type="primary", key="admin_end_impersonation"):
            _end_impersonation()
        return

    users = db.get_all_users_full()
    # Cannot impersonate other super_admins
    impersonatable = [u for u in users if u.get('subscription_tier') != 'super_admin']

    if not impersonatable:
        st.info("No users available for impersonation.")
        return

    target = st.selectbox("Select user to impersonate",
                          [u['username'] for u in impersonatable],
                          key="admin_impersonate_select")

    target_data = db.get_user_full(target) if target else None
    if target_data:
        c1, c2, c3 = st.columns(3)
        c1.metric("Tier", TIER_CONFIG.get(target_data.get('subscription_tier', 'solo'), {}).get('display_name', 'Solo'))
        c2.metric("Status", target_data.get('subscription_status', 'inactive'))
        c3.metric("Org", target_data.get('org_id') or 'Solo')

    st.warning("Impersonation will switch your view to this user's context. "
               "AI actions will be logged under their account but flagged as impersonated and "
               "won't count toward their usage cap.")

    if st.button(f"Login As {target}", type="primary", key="admin_start_impersonation"):
        _start_impersonation(target)


def _start_impersonation(target_username):
    """Saves admin session and switches to target user context."""
    admin_session = {
        'username': st.session_state.get('username'),
        'user_id': st.session_state.get('user_id'),
        'org_id': st.session_state.get('org_id'),
        'is_admin': st.session_state.get('is_admin'),
        'tier': st.session_state.get('tier'),
        'usage': st.session_state.get('usage'),
        'subscription_status': st.session_state.get('subscription_status'),
        'status': st.session_state.get('status'),
        'profiles': st.session_state.get('profiles'),
        '_tier_resolved_at': st.session_state.get('_tier_resolved_at'),
    }
    st.session_state['admin_session'] = admin_session

    # Load target user
    target = db.get_user_full(target_username)
    if not target:
        st.error("User not found.")
        return

    st.session_state['username'] = target['username']
    st.session_state['user_id'] = target['username']
    st.session_state['org_id'] = target.get('org_id') or target['username']
    st.session_state['is_admin'] = bool(target.get('is_admin', 0))
    st.session_state['profiles'] = db.get_profiles(target['username'])
    # Reset active profile to first available (admin's profile name won't exist for target)
    target_profiles = st.session_state['profiles']
    st.session_state['active_profile_name'] = list(target_profiles.keys())[0] if target_profiles else None

    # Resolve tier for target
    tier_config = sub_manager.resolve_user_tier(target['username'])
    st.session_state['tier'] = tier_config
    st.session_state['subscription_status'] = tier_config.get('_subscription_status', 'inactive')
    st.session_state['status'] = st.session_state['subscription_status']
    st.session_state['_tier_resolved_at'] = time.time()
    st.session_state['usage'] = sub_manager.check_usage_limit(target['username'])

    # Log
    db.log_admin_action(admin_session['username'], "impersonation_started", "impersonation",
                        target_username, {"target": target_username})

    st.session_state['app_mode'] = 'DASHBOARD'
    st.rerun()


def _end_impersonation():
    """Restores admin session from stored state."""
    admin_session = st.session_state.get('admin_session', {})
    target_username = st.session_state.get('username', 'unknown')

    if admin_session:
        for key, value in admin_session.items():
            st.session_state[key] = value

    st.session_state.pop('admin_session', None)

    # Log
    db.log_admin_action(admin_session.get('username', 'admin'), "impersonation_ended",
                        "impersonation", target_username, {"target": target_username})

    st.session_state['app_mode'] = 'ADMIN PANEL'
    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5: USAGE ANALYTICS
# ══════════════════════════════════════════════════════════════════════════════

def _render_usage_analytics():
    st.subheader("Usage Analytics")

    billing_month = datetime.now().strftime("%Y-%m")

    # --- Overview Cards ---
    users = db.get_all_users_full()
    orgs = db.get_all_organizations()
    total_brands = sum(db.count_user_brands(u.get('org_id') or u['username']) for u in users
                       if u.get('is_admin', 0) or not u.get('org_id'))
    total_actions = db.get_monthly_usage_all(billing_month)
    # Estimate: $0.025 per action, visual_audit weighted 3x already baked into action_weight
    est_cost = total_actions * 0.025

    tier_breakdown = {}
    for u in users:
        tk = u.get('subscription_tier', 'solo')
        tier_breakdown[tk] = tier_breakdown.get(tk, 0) + 1

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total Users", len(users))
    c2.metric("Organizations", len(orgs))
    c3.metric("Total Brands", total_brands)
    c4.metric("AI Actions (Month)", total_actions)
    c5.metric("Est. API Cost", f"${est_cost:,.2f}")

    # Tier breakdown
    st.caption("Users by tier: " + " | ".join(
        f"**{TIER_CONFIG.get(k, {}).get('display_name', k)}**: {v}" for k, v in sorted(tier_breakdown.items())))

    st.divider()

    # --- Per-User Usage Table ---
    st.markdown("#### Per-User Breakdown")
    analytics = db.get_usage_analytics(billing_month)

    if analytics:
        rows = []
        for a in analytics:
            tk = a.get('subscription_tier', 'solo')
            tier = TIER_CONFIG.get(tk, TIER_CONFIG['solo'])
            limit = tier['monthly_ai_actions']
            used = a.get('actions_this_month', 0)
            pct = (used / limit * 100) if limit > 0 else 0
            rows.append({
                "Username": a['username'],
                "Tier": tier.get('display_name', tk),
                "Actions (This Mo)": used,
                "Actions (Last Mo)": a.get('actions_last_month', 0),
                "Limit": limit if limit > 0 else "Unlimited",
                "% Used": f"{pct:.0f}%" if limit > 0 else "N/A",
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # --- Monthly Trend ---
    st.divider()
    st.markdown("#### Monthly Trend (Last 6 Months)")
    trend = db.get_monthly_usage_trend(6)
    if trend and any(t['actions'] > 0 for t in trend):
        chart_data = pd.DataFrame(trend)
        chart_data = chart_data.rename(columns={"month": "Month", "actions": "AI Actions"})
        chart_data = chart_data.set_index("Month")
        st.bar_chart(chart_data)

        # Cost overlay
        for t in trend:
            t['est_cost'] = f"${t['actions'] * 0.025:,.2f}"
        st.caption("Estimated cost per month: " + " | ".join(f"{t['month']}: {t['est_cost']}" for t in trend))
    else:
        st.info("No usage data yet.")

    # --- Daily Usage (Current Month) ---
    st.divider()
    st.markdown("#### Daily Usage (Current Month)")
    daily_data = db.get_daily_usage_platform(billing_month)
    if daily_data and any(d['actions'] > 0 for d in daily_data):
        daily_df = pd.DataFrame(daily_data)
        daily_df = daily_df.rename(columns={"day": "Day", "actions": "AI Actions"})
        daily_df = daily_df.set_index("Day")
        st.bar_chart(daily_df)

        # Spike detection
        avg_daily = sum(d['actions'] for d in daily_data) / len(daily_data) if daily_data else 0
        spikes = [d for d in daily_data if d['actions'] > avg_daily * 2 and avg_daily > 0]
        if spikes:
            st.markdown(
                f'<div style="border-left:3px solid #a6784d; padding:8px 12px; font-size:0.85rem; color:#3d3d3d;">'
                f'<strong style="color:#a6784d;">Spike detected:</strong> '
                + ", ".join(f"{s['day']} ({s['actions']} actions)" for s in spikes)
                + f' — daily average is {avg_daily:.0f}</div>',
                unsafe_allow_html=True
            )

        # Daily cost estimate
        daily_cost_str = " | ".join(f"{d['day']}: ${d['actions'] * 0.025:,.2f}" for d in daily_data[-7:])
        st.caption(f"Est. daily cost (last 7 days): {daily_cost_str}")
    else:
        st.info("No daily usage data for this month yet.")

    # --- Overage Report ---
    st.divider()
    st.markdown("#### Overage Report")
    beta_usernames = {u['username'] for u in users if u.get('is_beta_tester')}
    overages = []
    for a in (analytics or []):
        tk = a.get('subscription_tier', 'solo')
        if tk in ('super_admin',) or a['username'] in beta_usernames:
            continue
        tier = TIER_CONFIG.get(tk, TIER_CONFIG['solo'])
        limit = tier['monthly_ai_actions']
        used = a.get('actions_this_month', 0)
        if limit > 0 and used > limit:
            overages.append({
                "Username": a['username'],
                "Email": a.get('email', ''),
                "Tier": tier.get('display_name', tk),
                "Used": used,
                "Limit": limit,
                "Over By": used - limit,
            })
    if overages:
        st.dataframe(pd.DataFrame(overages), use_container_width=True, hide_index=True)
    else:
        st.success("No users over their soft cap this month.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6: AUDIT LOG
# ══════════════════════════════════════════════════════════════════════════════

def _render_audit_log():
    st.subheader("Admin Audit Log")
    st.caption("All admin actions are permanently logged and cannot be deleted.")

    # Filters
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        filter_action = st.selectbox("Action Type", ["All", "user_created", "user_deleted", "user_edited",
                                                      "org_created", "org_deleted", "org_edited",
                                                      "tier_changed", "comp_granted",
                                                      "subscription_extended", "retainer_set",
                                                      "impersonation_started", "impersonation_ended"],
                                     key="admin_log_action_filter")
    with fc2:
        filter_target = st.selectbox("Target Type", ["All", "user", "organization", "subscription", "impersonation"],
                                     key="admin_log_target_filter")
    with fc3:
        filter_limit = st.number_input("Show last N entries", min_value=10, max_value=1000, value=100,
                                       key="admin_log_limit")

    logs = db.get_admin_audit_log(
        limit=filter_limit,
        action_type=filter_action if filter_action != "All" else None,
        target_type=filter_target if filter_target != "All" else None,
    )

    if logs:
        rows = []
        for log in logs:
            rows.append({
                "Timestamp": (log.get('timestamp') or '')[:19],
                "Admin": log.get('admin_username', ''),
                "Action": log.get('action_type', ''),
                "Target Type": log.get('target_type', ''),
                "Target": log.get('target_id', ''),
            })
        df = pd.DataFrame(rows)
        selection = st.dataframe(df, use_container_width=True, hide_index=True,
                                 on_select="rerun", selection_mode="single-row")

        # Detail view
        if selection and len(selection.selection.rows) > 0:
            row_idx = selection.selection.rows[0]
            selected = logs[row_idx]
            st.markdown("---")
            st.markdown("**Details:**")
            details = selected.get('details')
            if details:
                try:
                    st.json(json.loads(details) if isinstance(details, str) else details)
                except (json.JSONDecodeError, TypeError):
                    st.code(str(details))
            else:
                st.caption("No additional details.")
    else:
        st.info("No audit log entries found.")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 7: SYSTEM (Health, Bulk Actions, Announcements)
# ══════════════════════════════════════════════════════════════════════════════

def _render_system_health():
    st.subheader("System")

    sys_tabs = st.tabs(["Health Check", "Bulk Actions", "Announcements"])

    # --- Health Check ---
    with sys_tabs[0]:
        st.markdown("#### System Health")

        # DB file size
        db_path = db.DB_NAME
        if os.path.exists(db_path):
            size_mb = os.path.getsize(db_path) / (1024 * 1024)
            st.metric("Database Size", f"{size_mb:.2f} MB")
        else:
            st.metric("Database Size", "N/A")

        # Row counts
        counts = db.get_table_row_counts()
        cols = st.columns(len(counts))
        for i, (table, count) in enumerate(counts.items()):
            cols[i].metric(table, count)

        st.divider()

        # Env var status
        st.markdown("#### Environment Variables")
        env_vars = {
            "ANTHROPIC_API_KEY": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "LEMONSQUEEZY_API_KEY": bool(os.environ.get("LEMONSQUEEZY_API_KEY")),
            "LEMONSQUEEZY_STORE_ID": bool(os.environ.get("LEMONSQUEEZY_STORE_ID")),
            "LEMONSQUEEZY_WEBHOOK_SECRET": bool(os.environ.get("LEMONSQUEEZY_WEBHOOK_SECRET")),
        }
        for name, is_set in env_vars.items():
            icon = "+" if is_set else "x"
            color = "green" if is_set else "red"
            st.markdown(f":{color}[{'Set' if is_set else 'Not set'}] — `{name}`")

    # --- Bulk Actions ---
    with sys_tabs[1]:
        st.markdown("#### Bulk Actions")

        users = db.get_all_users_full()
        usernames = [u['username'] for u in users if u.get('subscription_tier') != 'super_admin']

        selected_users = st.multiselect("Select users", usernames, key="admin_bulk_users")

        if selected_users:
            bc1, bc2 = st.columns(2)
            with bc1:
                bulk_tier = st.selectbox("New tier", list(TIER_CONFIG.keys()),
                                         format_func=lambda k: TIER_CONFIG[k]['display_name'],
                                         key="admin_bulk_tier")
                if st.button("Apply Tier to Selected", key="admin_bulk_tier_btn"):
                    for u in selected_users:
                        old = db.get_user_full(u)
                        old_tier = old.get('subscription_tier', 'solo') if old else 'solo'
                        db.update_user_fields(u, subscription_tier=bulk_tier, subscription_status='active')
                        db.log_admin_action(_admin_user(), "tier_changed", "subscription", u,
                                            {"old_tier": old_tier, "new_tier": bulk_tier, "bulk": True})
                    st.success(f"Tier updated for {len(selected_users)} users.")
                    st.rerun()

            with bc2:
                bulk_status = st.selectbox("New status", ["active", "inactive"],
                                           key="admin_bulk_status")
                if st.button("Apply Status to Selected", key="admin_bulk_status_btn"):
                    for u in selected_users:
                        db.update_user_fields(u, subscription_status=bulk_status)
                    st.success(f"Status updated for {len(selected_users)} users.")
                    st.rerun()

        st.divider()

        # CSV Export
        st.markdown("#### Export Users")
        if st.button("Generate CSV Export", key="admin_export_csv"):
            billing_month = datetime.now().strftime("%Y-%m")
            rows = []
            for u in users:
                usage = db.get_monthly_usage_user(u['username'], billing_month)
                rows.append({
                    "username": u['username'],
                    "email": u.get('email', ''),
                    "tier": u.get('subscription_tier', 'solo'),
                    "org": u.get('org_id') or 'Solo',
                    "status": u.get('subscription_status', 'inactive'),
                    "actions_this_month": usage,
                })
            df = pd.DataFrame(rows)
            csv = df.to_csv(index=False)
            st.download_button("Download CSV", csv, "signet_users_export.csv", "text/csv")

    # --- Announcements ---
    with sys_tabs[2]:
        st.markdown("#### Platform Announcement")
        st.caption("Set a banner that displays on all user pages.")

        current = db.get_platform_setting("announcement") or ""
        new_announcement = st.text_area("Announcement text (leave empty to remove)",
                                        value=current, key="admin_announcement_text")

        if st.button("Update Announcement", key="admin_announcement_btn"):
            if new_announcement.strip():
                db.set_platform_setting("announcement", new_announcement.strip(), _admin_user())
                st.success("Announcement updated.")
            else:
                db.set_platform_setting("announcement", "", _admin_user())
                st.success("Announcement removed.")
            st.rerun()

        if current:
            st.divider()
            st.markdown("**Preview:**")
            st.info(current)
