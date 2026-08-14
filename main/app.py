import streamlit as st
from supabase import create_client, Client
import time
import pandas as pd
from datetime import datetime
import plotly.express as px # NEW FOR ROUNDED BARS

# ========== CONFIG ==========
st.set_page_config(
    layout="wide",
    page_icon="🗳️",
    page_title="BSK ICT Club | Electronic Polling Station",
    initial_sidebar_state="expanded"
)

# YOUR SUPABASE CREDENTIALS
SUPABASE_URL = "https://vxdizbiaucutdutafuxv.supabase.co"
SUPABASE_KEY = "sb_publishable_KwmVUTPjMdLlwDbiesqUVw_CTI2cpqX"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# PASSWORDS
DEFAULT_STUDENT_PASSWORD = "BSKICTCLUB@2026"
ADMIN_PASSWORD = "ADMINICTCLUB@2026"

# CLUB POSTS
POSITIONS = [
    "President",
    "Secretary",
    "Treasurer",
    "Speaker",
    "Projects Manager",
    "Mobiliser/Coordinator"
]

# VOTING PERIOD - CHANGE THESE
VOTING_START = datetime(2026, 8, 6, 8, 0) # 8am
VOTING_END = datetime(2026, 8, 6, 17, 0) # 5pm

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
        return False, f"You have already voted for {position}"

    supabase.table("votes").insert({
        "username": username,
        "candidate_id": candidate_id,
        "candidate_name": candidate_name,
        "position": position,
        "voted_at": datetime.now().isoformat()
    }).execute()

    supabase.rpc('increment_vote', {'candidate_id': candidate_id}).execute()
    return True, f"Vote for {candidate_name} as {position} cast successfully!"

def check_all_voted(username):
    votes = supabase.table("votes").select("position").eq("username", username).execute()
    voted_positions = [v['position'] for v in votes.data]
    return set(voted_positions) == set(POSITIONS)

def get_results():
    res = supabase.table("candidates").select("*").execute() # removed order, we sort per position
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
    return True

# ========== PLOTLY CHART FUNCTION ==========
def plot_horizontal_bars(df, position):
    # df must have columns: name, votes
    fig = px.bar(
        df,
        x="votes",
        y="name",
        orientation='h', # HORIZONTAL
        text="votes",
        color="name",
        color_discrete_sequence=px.colors.qualitative.Pastel # Soft colors like photo
    )
    fig.update_traces(
        textposition='outside',
        marker=dict(line=dict(width=0), cornerradius=15) # ROUND CORNERS
    )
    fig.update_layout(
        title=f"<b>Results for: {position}</b>",
        xaxis_title="Votes",
        yaxis_title="",
        showlegend=False,
        height=300 + 50 * len(df), # auto height
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="white"),
        margin=dict(l=20, r=20, t=40, b=20)
    )
    fig.update_xaxes(showgrid=True, gridcolor='rgba(255,255,255,0.1)')
    fig.update_yaxes(categoryorder='total ascending') # highest on top
    return fig

# ========== SESSION STATE ==========
if 'user' not in st.session_state:
    st.session_state.user = None
if 'vote_receipt' not in st.session_state:
    st.session_state.vote_receipt = []

# ========== HEADER ==========
col1, col2 = st.columns([3,1])
with col1:
    st.title("🗳️ BSK ICT Club Online Voting System")
with col2:
    now = datetime.now()
    if now < VOTING_START: st.error(f"Voting Starts: {VOTING_START.strftime('%d %b %H:%M')}")
    elif now > VOTING_END: st.error("Voting CLOSED")
    else: st.success(f"Voting OPEN - Ends {VOTING_END.strftime('%H:%M')}")

st.caption("Secure. Transparent. One vote per post. Powered by BSK ICT Club")

# ========== LOGIN PAGE ==========
if st.session_state.user is None:
    st.subheader("Member Login")
    st.info(f"Username = Your Lastname in lowercase. Example: mpoza | Password: {DEFAULT_STUDENT_PASSWORD}")
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

    # ========== MEMBER VOTING PAGE ==========
    if user['role'] == 'student':
        if datetime.now() < VOTING_START or datetime.now() > VOTING_END:
            st.error("Voting is currently closed")

        # CHECK IF FINISHED VOTING FOR ALL
        all_voted = check_all_voted(user['username'])

        if all_voted:
            st.success("✅ You have voted for all positions. Thank you!")
            st.subheader("Your Vote Receipt")
            for r in st.session_state.vote_receipt:
                st.write(f"- Voted for: **{r['candidate']}** - Position: **{r['position']}**")

            st.divider()
            st.header("📊 Live Results") # NOW SHOW RESULTS
            results = get_results()
            df = pd.DataFrame(results)
            if not df.empty:
                for pos in POSITIONS:
                    pos_df = df[df['position'] == pos].sort_values('votes', ascending=True) # ascending for plotly
                    if not pos_df.empty:
                        st.plotly_chart(plot_horizontal_bars(pos_df, pos), use_container_width=True)
            else:
                st.info("No candidates added yet.")

        else: # STILL VOTING
            st.subheader("Cast Your Vote")
            st.warning(f"You must vote for all {len(POSITIONS)} positions. You can vote 1 position at a time.")
            st.info("You will see live results only after voting for all positions.")

            for pos in POSITIONS:
                st.divider()
                st.write(f"### {pos}")
                candidates = get_candidates(pos)

                already_voted = supabase.table("votes").select("*").eq("username", user['username']).eq("position", pos).execute()

                if already_voted.data:
                    st.success(f"✅ Already voted for {pos}")
                elif candidates:
                    cols = st.columns(min(3, len(candidates)))
                    for i, c in enumerate(candidates):
                        with cols[i % 3]:
                            st.metric(label=c['name'], value=f"{c['votes']} votes")
                            if st.button(f"Vote {c['name']}", key=f"{pos}_{c['id']}", use_container_width=True):
                                success, msg = cast_vote(user['username'], c['id'], c['name'], pos)
                                if success:
                                    st.session_state.vote_receipt.append({"candidate": c['name'], "position": pos})
                                    st.success(msg)
                                    time.sleep(0.5)
                                    st.rerun()
                                else: st.error(msg)
                else:
                    st.warning(f"No candidates added for {pos} yet")

    # ========== ADMIN PANEL ==========
    if user['role'] in ['patron', 'president']:
        st.sidebar.markdown("---")
        st.sidebar.subheader("Admin Controls")

        tab1, tab2, tab3, tab4 = st.tabs(["➕ Add Candidate", "📊 Live Results", "🔄 Restore Voter", "⚠️ Reset Election"])

        with tab1:
            st.subheader("Add New Candidate")
            with st.form("add_candidate"):
                name = st.text_input("Candidate Full Name")
                position = st.selectbox("Position", POSITIONS)
                if st.form_submit_button("Add Candidate"):
                    supabase.table("candidates").insert({"name": name, "position": position}).execute()
                    st.success(f"{name} added for {position}")

        with tab2:
            st.subheader("Live Results Dashboard - Admin View")
            results = get_results()
            df = pd.DataFrame(results)
            if not df.empty:
                for pos in POSITIONS:
                    pos_df = df[df['position'] == pos].sort_values('votes', ascending=True)
                    if not pos_df.empty:
                        st.plotly_chart(plot_horizontal_bars(pos_df, pos), use_container_width=True)

                csv = df.to_csv(index=False)
                st.download_button("📥 Download Results CSV", csv, "bsk_ict_results.csv", "text/csv")
            else:
                st.info("No candidates added yet.")

            st.divider()
            st.subheader("Audit Log")
            audit = get_audit_log()
            audit_df = pd.DataFrame(audit)
            if not audit_df.empty:
                st.dataframe(audit_df[['username','candidate_name','position','voted_at']], use_container_width=True, hide_index=True)
            else:
                st.info("No votes cast yet")

        with tab3:
            st.subheader("Restore Voter Access")
            st.warning("Use this if a member claims someone voted using their credentials. This deletes all their votes.")
            username_to_reset = st.text_input("Enter Username to Reset - lastname lowercase")
            if st.button("Reset This Voter", type="secondary"):
                reset_voter(username_to_reset)
                st.success(f"{username_to_reset} can now vote again for all positions.")

        with tab4:
            st.subheader("Danger Zone")
            st.error("This will delete ALL votes and reset vote counts to 0")
            if st.button("RESET ENTIRE ELECTION", type="primary"):
                reset_election()
                st.success("Election has been reset. All members can vote again.")

st.markdown("---")
st.markdown("#### :green-background[Developed by Mpoza Christopher | BSK ICT Club]")
