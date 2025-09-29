import streamlit as st
from presentation.state.session_state_manager import initialize_session_state
from shared.narratives import USAGE, DETAILS, NAVIGATION, DISCLAIMER

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--debug", type=bool, default=False)
args = parser.parse_args()


def main():
    initialize_session_state(debug=args.debug)

    st.sidebar.title("Navigation")
    st.sidebar.markdown(NAVIGATION)

    st.sidebar.title("Usage Instructions")
    st.sidebar.markdown(USAGE)

    st.sidebar.title("Details")
    st.sidebar.markdown(DETAILS)

    st.sidebar.title("Disclaimer")
    st.sidebar.markdown(DISCLAIMER)


if __name__ == "__main__":
    main()
