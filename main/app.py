import streamlit as st
from supabase import create_client, Client
import time
import pandas as pd
import plotly.express as px
from datetime import datetime

# ========== CONFIG ==========
st.set_page_config(layout="wide", page_icon="🗳️", page_title="BSK ICT Club | Online Voting System", initial_sidebar_state="collapsed")

# ========== SUPABASE CREDENTIALS ==========
SUPABASE_URL = "https://vxdizbiaucutdutafuxv.supabase.co"
SUPABASE_KEY = "sb_publishable_KwmVUTPjMdLlwDbiesqUVw_CTI2cpqX"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========== PASSWORDS ==========
DEFAULT_STUDENT_PASSWORD = "BSKICTCLUB@2026"
ADMIN_PASSWORD = "ADMINICTCLUB@2026"

POSITIONS = ["President", "Secretary", "Treasurer", "Speaker", "Projects Manager", "Mobiliser/Coordinator"]
VOTING_START = datetime(2026, 8, 8, 0, 0)
VOTING_END = datetime(2026, 8, 18, 17, 0) # CHANGED TO 18TH 5PM
CAN_VOTE_ROLES = ['student', 'candidate', 'president', 'patron']
ADMIN_ROLES = ['patron', 'president']

# ========== PLOTLY CHART FUNCTION ==========
def plot_horizontal_bars(df, position):
    fig = px.bar(
        df,
        x="votes",
        y="name",
        orientation='h', # HORIZONTAL
        text="votes",
        color="votes",
        color_continuous_scale=px.colors.sequential.Blues # Like your photo
    )
    fig.update_traces(
        textposition='outside',
        marker=dict(cornerradius=12) # ROUND CORNERS
    )
    fig.update_layout(
        title=f"<b>Results for: {position}</b>",
        xaxis_title="Votes",
        yaxis_title="",
        showlegend=False,
        height=100 + 50 * len(df), # auto height
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(size=14),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    fig.update_xaxes(showgrid=True, gridcolor='rgba(0,0,0,0.1)')
    fig.update_yaxes(categoryorder='total ascending') # highest on top
    return fig

# ========== DB FUNCTIONS ==========
def get_election_status():
    try:
        res = supabase.table("settings").select("is_active").eq("id", 1).execute()
        if res.data: return res.data[0]['is_active']
        else:
            supabase.table("settings").insert({"id": 1, "is_active": True}).execute()
            return True
    except: return True

def set_election_status(status: bool):
    supabase.table("settings").update({"is_active": status}).eq("id", 1).execute()

def login(username, password):
    res = supabase.table("students").select("*").eq("username", username.lower()).execute()
    if not res.data: return None
    user = res.data[0]
    if user['role'] in ADMIN_ROLES:
        if password == ADMIN_PASSWORD: return user
    else:
        if password == DEFAULT_STUDENT_PASSWORD: return user
    return None

def register_student(name, username, role="student"):
    check = supabase.table("students").select("*").eq("username", username.lower()).execute()
    if check.data: return False, "Username already exists"
    password = ADMIN_PASSWORD if role in ADMIN_ROLES else DEFAULT_STUDENT_PASSWORD
    supabase.table("students").insert({"name": name, "username": username.lower(), "password": password, "role": role}).execute()
    return True, f"{role.title()} {name} registered successfully"

def get_candidates(position):
    res = supabase.table("candidates").select("*").eq("position", position).order("name").execute()
    return res.data

def cast_vote(username, candidate_id, candidate_name, position):
    check = supabase.table("votes").select("*").eq("username", username).eq("position", position).execute()
    if check.data: return False, f"You have already voted for {position}"
    supabase.table("votes").insert({"username": username, "candidate_id": candidate_id, "candidate_name": candidate_name, "position": position, "voted_at": datetime.now().isoformat()}).execute()
    supabase.rpc('increment_vote', {'candidate_id': candidate_id}).execute()
    return True, f"Vote for {candidate_name} as {position} cast successfully!"

def check_all_voted(username):
    votes = supabase.table("votes").select("position").eq("username", username).execute()
    voted_positions = [v['position'] for v in votes.data]
    return set(voted_positions) == set(POSITIONS)

def get_results():
    res = supabase.table("candidates").select("*").execute()
    return res.data

def get_audit_log():
    res = supabase.table("votes").select("*").order("voted_at", desc=True).execute()
    return res.data

def reset_voter(username):
    votes = supabase.table("votes").select("*").eq("username", username).execute()
    for v in votes.data:
        supabase.rpc('decrement_vote', {'candidate_id': v['candidate_id']}).execute()
    supabase.table("votes").delete().eq("username", username).execute()
    return True

def reset_election():
    supabase.table("votes").delete().neq("id", 0).execute()
    supabase.table("candidates").update({"votes": 0}).neq("id", 0).execute()
    set_election_status(True)
    return True

# ========== SESSION ==========
if 'user' not in st.session_state: st.session_state.user = None
if 'vote_receipt' not in st.session_state: st.session_state.vote_receipt = []

# ========== HEADER ==========
col1, col2 = st.columns([3,1])
with col1: st.title("🗳️ BSK ICT Club Online Voting System")
with col2:
    now = datetime.now()
    election_active_db = get_election_status()
    voting_open = VOTING_START <= now <= VOTING_END and election_active_db
    if not election_active_db: st.error("Voting MANUALLY STOPPED")
    elif now < VOTING_START: st.warning(f"Starts: {VOTING_START.strftime('%d %b %H:%M')}")
    elif now > VOTING_END: st.error(f"Voting CLOSED - Ended {VOTING_END.strftime('%d %b %H:%M')}")
    else: st.success(f"Voting OPEN - Ends {VOTING_END.strftime('%d %b %H:%M')}")

# ========== LOGIN ==========
if st.session_state.user is None:
    st.subheader("Member Login")
    st.info(f"Students & Candidates: Use password `{DEFAULT_STUDENT_PASSWORD}`")
    st.warning("Patron & President: Use your admin password")
    with st.form("login_form"):
        username = st.text_input("Username - Lastname lowercase")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login", type="primary", use_container_width=True):
            user = login(username, password)
            if user:
                st.session_state.user = user
                st.rerun()
            else:
                st.error("Invalid Username or Password")
else:
    user = st.session_state.user
    st.sidebar.success(f"Logged in as: **{user['name']}**")
    st.sidebar.caption(f"Username: {user['username']} | Role: {user['role'].title()}")
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.user = None; st.session_state.vote_receipt = []; st.rerun()

    now = datetime.now()
    election_active_db = get_election_status()
    voting_open = VOTING_START <= now <= VOTING_END and election_active_db

    # ========== VOTING ==========
    if user['role'] in CAN_VOTE_ROLES:
        all_voted = check_all_voted(user['username'])

        if not voting_open and not all_voted:
            st.error("Voting is currently closed")
            if user['role'] in ADMIN_ROLES: show_results_to_all = True # Admin can see
            else: show_results_to_all = False
        elif all_voted:
            st.success("✅ You have voted for all positions. Thank you!")
            st.subheader("Your Vote Receipt")
            for r in st.session_state.vote_receipt: st.write(f"- **{r['candidate']}** - {r['position']}")
            st.divider(); st.header("📊 Live Results"); show_results_to_all = True
        else:
            show_results_to_all = False
            st.subheader("Cast Your Vote")
            st.info("You will see live results only after voting for all 6 positions.")
            for pos in POSITIONS:
                st.divider(); st.write(f"### {pos}")
                candidates = get_candidates(pos)
                already_voted = supabase.table("votes").select("*").eq("username", user['username']).eq("position", pos).execute()
                if already_voted.data: st.success(f"✅ Already voted for {pos}")
                elif candidates:
                    cols = st.columns(min(2, len(candidates)))
                    for i, c in enumerate(candidates):
                        with cols[i % 2]:
                            st.metric(label=c['name'], value=f"{c['votes']} votes")
                            if st.button(f"Vote {c['name']}", key=f"{pos}_{c['id']}", use_container_width=True):
                                success, msg = cast_vote(user['username'], c['id'], c['name'], pos)
                                if success:
                                    st.session_state.vote_receipt.append({"candidate": c['name'], "position": pos})
                                    st.success(msg)
                                    time.sleep(0.3)
                                    st.rerun()
                                else:
                                    st.error(msg)
                else: st.warning(f"No candidates for {pos}")

    # ========== ADMIN ==========
    if user['role'] in ADMIN_ROLES:
        st.sidebar.markdown("---"); st.sidebar.subheader("Admin Controls")
        tab0, tab1, tab2, tab3, tab4, tab5 = st.tabs(["👤 Register", "➕ Candidate", "📊 Results", "⏹️ Control", "🔄 Restore", "⚠️ Reset"])

        with tab0:
            st.subheader("Register New Person")
            with st.form("register_member"):
                name = st.text_input("Full Name"); username = st.text_input("Username lowercase")
                role = st.selectbox("Role", ["student", "candidate", "president", "patron"])
                if st.form_submit_button("Register", use_container_width=True):
                    if name and username:
                        success, msg = register_student(name, username, role)
                        st.success(msg) if success else st.error(msg)
                    else:
                        st.error("Fill all fields")

        with tab1:
            st.subheader("Add New Candidate")
            with st.form("add_candidate"):
                name = st.text_input("Candidate Name"); position = st.selectbox("Position", POSITIONS)
                if st.form_submit_button("Add", use_container_width=True):
                    supabase.table("candidates").insert({"name": name, "position": position, "votes": 0}).execute()
                    st.success(f"{name} added")

        with tab2: st.subheader("Live Results Dashboard - Admin View"); show_results_to_all = True

        with tab3:
            st.subheader("Election Control Panel")
            current_status = "ACTIVE" if election_active_db else "STOPPED"
            st.write(f"Current Status: **{current_status}**")
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🟢 START ELECTION", use_container_width=True, disabled=election_active_db):
                    set_election_status(True); st.success("Election Started"); st.rerun()
            with col_b:
                if st.button("🔴 STOP ELECTION NOW", type="primary", use_container_width=True, disabled=not election_active_db):
                    set_election_status(False); st.error("Election Stopped Manually"); st.rerun()

        if 'show_results_to_all' in locals() and show_results_to_all:
            results = get_results(); df = pd.DataFrame(results)
            if not df.empty:
                for pos in POSITIONS:
                    pos_df = df[df['position'] == pos].sort_values('votes', ascending=True)
                    if not pos_df.empty:
                        st.plotly_chart(plot_horizontal_bars(pos_df, pos), use_container_width=True)
                st.download_button("📥 Download CSV", df.to_csv(index=False), "bsk_ict_results.csv")
            else: st.info("No candidates yet.")

            st.divider(); st.subheader("Audit Log")
            audit = get_audit_log(); audit_df = pd.DataFrame(audit)
            if not audit_df.empty: st.dataframe(audit_df[['username','candidate_name','position','voted_at']], use_container_width=True, hide_index=True)
            else: st.info("No votes yet")

        with tab4:
            st.subheader("Restore Voter"); username_to_reset = st.text_input("Username to Reset")
            if st.button("Reset Voter", use_container_width=True):
                reset_voter(username_to_reset)
                st.success(f"{username_to_reset} reset")

        with tab5:
            st.subheader("Danger Zone"); st.error("Deletes ALL votes")
            if st.button("RESET ENTIRE ELECTION", type="primary", use_container_width=True):
                reset_election()
                st.success("Election Reset")

st.markdown("---")
st.markdown("<center>🗳️ <b>Developed by Mpoza Christopher</b> | BSK ICT Club 2026</center>", unsafe_allow_html=True)
