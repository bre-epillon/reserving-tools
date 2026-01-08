import streamlit as st
from presentation.state.session_state_manager import initialize_session_state
from shared.narratives import USAGE, DETAILS, NAVIGATION, DISCLAIMER

import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--debug", type=bool, default=False)
args = parser.parse_args()


def main():
    initialize_session_state(debug=args.debug)

    st.title("Navigation")
    st.markdown(NAVIGATION)

    st.title("Usage Instructions")
    st.markdown(USAGE)

    st.title("Details")
    st.markdown(DETAILS)

    st.title("Disclaimer")
    st.markdown(DISCLAIMER)


if __name__ == "__main__":
    main()
