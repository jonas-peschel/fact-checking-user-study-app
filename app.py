import streamlit as st
from streamlit.components.v1 import iframe
from uuid import uuid4

# create participant ID 
if "participant_id" not in st.session_state:
    st.session_state.participant_id = str(uuid4())

pid = st.session_state.participant_id



st.title("Fact-checking User Study")

iframe(f"https://jonas-peschel.github.io/fact-checking-surveys/test_survey/?pid={pid}", height=1000)