import streamlit as st
from streamlit.components.v1 import iframe
from uuid import uuid4

# create participant ID 
if "participant_id" not in st.session_state:
    st.session_state.participant_id = str(uuid4())

pid = st.session_state.participant_id



st.title("Fact-checking User Study")


st.write("Pre-study Survey")
iframe(f"https://jonas-peschel.github.io/fact-checking-surveys/pre/?pid={pid}&claim_id=pre", height=1000)

st.write("Per-claim Survey")
iframe(f"https://jonas-peschel.github.io/fact-checking-surveys/claim/?pid={pid}&claim_id={100}", height=1000)

st.write("Post-study Survey")
iframe(f"https://jonas-peschel.github.io/fact-checking-surveys/post/?pid={pid}&claim_id=post", height=1000)