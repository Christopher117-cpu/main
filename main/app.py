import streamlit as st
from supabase import create_client, Client
import time
import pandas as pd
from datetime import datetime

# ========== CONFIG ==========
st.set_page_config(
    layout="wide",
    page_icon="🗳️",
    page_title="BSK School | Online Voting System",
    initial_sidebar_state="expanded"
)

# YOUR SUPABASE CREDENTIALS
SUPABASE_URL = "https://vxdizbiaucutdutafuxv.supabase.co"
SUPABASE_KEY = "sb_publishable_KwmVUTPjMdLlwDbiesqUVw_CTI2cpqX"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# PASSWORDS
DEFAULT_STUDENT_PASSWORD = "BSKICTCLUB@2026"
ADMIN_PASSWORD = "ADMINICTCLUB@2026"

# VOTING PERIOD
VOTING_START = datetime(2026, 8, 5, 8, 0)
VOTING_END = datetime(2026, 8, 5, 17, 0)

# ========== DATABASE FUNCTIONS ==========
def login(username, password):
    res = supabase.table("students").select("*").eq("username", username.lower()).eq("password", password).execute()
    return res.data[0] if res.data else None

def get_candidates(position):
    res = supabase.table("candidates").select("*").eq("position", position).order("name").execute()
    return res.data

def cast_vote(username, candidate_id, candidate_name, position):
    check = supabase.table("votes").select("*").eq("username", username).eq("position", position).execute()
    if check.data:
        return False, "You have already voted for this position"

    supabase.table("votes").insert({
        "username": username,
        "candidate_id": candidate_id,
        "candidate_name": candidate_name,
        "position": position,
        "voted_at": datetime.now().isoformat()
    }).execute()

    supabase.rpc('increment_vote', {'candidate_id': candidate_id}).execute()
    supabase.table("students").update({"has_voted": True}).eq("username", username).execute()
    return True, f"Vote for {candidate_name} cast successfully!"

def get_results():
    res = supabase.table("candidates").select("*").order("votes", desc=True).execute()
    return res.data

def get_audit_log():
    res = supabase.table("votes").select("*").order("voted_at", desc=True).execute()
    return res.data

def reset_voter(username):
    votes = supabase.table("votes").select("*").eq("username", username).execute()
    for v in votes.data:
        supabase.rpc('decrement_vote', {'candidate_id': v['candidate_id']}).execute()
    supabase.table("votes").delete().eq("username", username).execute()
    supabase.table("students").update({"has_voted": False}).eq("username", username).execute()
    return True

def reset_election():
    supabase.table("votes").delete().neq("id", 0).execute()
    supabase.table("students").update({"has_voted": False}).neq("username", "").execute()
    supabase.table("candidates").update({"votes": 0}).neq("id", 0).execute()
    return True

# ========== SESSION STATE ==========
if 'user' not in st.session_state:
    st.session_state.user = None
if 'vote_receipt' not in st.session_state:
    st.session_state.vote_receipt = []

# ========== HEADER ==========
col1, col2 = st.columns([3,1])
with col1:
    st.title("🗳️ BSK School Online Voting System")
with col2:
    now = datetime.now()
    if now < VOTING_START: st.error(f"Starts: {VOTING_START.strftime('%d %b %H:%M')}")
    elif now > VOTING_END: st.error("Voting CLOSED")
    else: st.success(f"Voting OPEN - Ends {VOTING_END.strftime('%H:%M')}")

# ========== LOGIN PAGE ==========
if st.session_state.user is None:
    st.subheader("Login to Vote")
    st.info(f"Username = Your Lastname in lowercase. Example: mpoza")
    with st.form("login_form"):
        username = st.text_input("Username - Lastname in lowercase")
        password = st.text_input("Password", type="password")
        if st.form_submit_button("Login", type="primary"):
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
    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.session_state.vote_receipt = []
        st.rerun()

    # STUDENT
    if user['role'] == 'student':
        if datetime.now() < VOTING_START or datetime.now() > VOTING_END:
            st.error("Voting is currently closed")
        elif user['has_voted']:
            st.info("✅ You have already voted.")
            for r in st.session_state.vote_receipt:
                st.success(f"Voted for: **{r['candidate']}** - {r['position']}")
        else:
            st.subheader("Cast Your Vote")
            positions = ["Head Prefect", "Deputy Head Prefect", "Girls Prefect", "Sports Prefect"]
            for pos in positions:
                st.divider()
                st.write(f"### {pos}")
                candidates = get_candidates(pos)
                if candidates:
                    for c in candidates:
                        col1, col2 = st.columns([3,1])
                        with col1: st.write(f"**{c['name']}** - Current votes: {c['votes']}")
                        with col2:
                            if st.button(f"Vote", key=f"{pos}_{c['id']}"):
                                success, msg = cast_vote(user['username'], c['id'], c['name'], pos)
                                if success:
                                    st.session_state.vote_receipt.append({"candidate": c['name'], "position": pos})
                                    st.success(msg); time.sleep(1); st.rerun()
                                else: st.error(msg)
                else: st.warning(f"No candidates for {pos}")

    # ADMIN
    if user['role'] in ['patron', 'president']:
        st.sidebar.markdown("---")
        tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Candidate", "📊 Results", "🔄 Restore Voter", "⚠️ Reset Election"])
        with tab1:
            name = st.text_input("Candidate Name")
            position = st.selectbox("Position", ["Head Prefect", "Deputy Head Prefect", "Girls Prefect", "Sports Prefect"])
            if st.button("Add Candidate"):
                supabase.table("candidates").insert({"name": name, "position": position}).execute()
                st.success(f"{name} added")
        with tab2:
            df = pd.DataFrame(get_results())
            if not df.empty:
                for pos in df['position'].unique():
                    st.write(f"#### {pos}")
                    st.dataframe(df[df['position']==pos][['name', 'votes']])
                st.download_button("Download CSV", df.to_csv(index=False), "results.csv")
            st.dataframe(pd.DataFrame(get_audit_log())[["username","candidate_name","position","voted_at"]])
        with tab3:
            username_to_reset = st.text_input("Enter Username to Reset")
            if st.button("Reset Voter"):
                reset_voter(username_to_reset)
                st.success(f"{username_to_reset} can vote again")
        with tab4:
            if st.button("RESET ENTIRE ELECTION", type="primary"):
                reset_election()
                st.success("Election reset")

st.markdown("---")
st.caption("Developed by BSK ICT Club")
