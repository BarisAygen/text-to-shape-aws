# app.py
import os
import time
import streamlit as st
from shape_engine import parse_command, draw_shape, SHAPES

os.makedirs("outputs", exist_ok=True)

st.set_page_config(page_title="Text → Shape (Local Demo)", page_icon="🎨", layout="wide")
st.title("🎨 Text → Shape Generator (Local)")
st.caption("Strict vs Creative mode, fuzzy matching and composite shapes")

with st.sidebar:
    st.header("⚙️ Settings")
    mode = st.radio("Mode", ["creative", "strict"], index=0)
    width = st.slider("Width (px)", 100, 1024, 300, step=50)
    height = st.slider("Height (px)", 100, 1024, 300, step=50)
    stroke = st.slider("Stroke width (px)", 1, 15, 3, step=1)
    color = st.selectbox("Line color", ["black", "white", "red", "green", "blue", "purple"])
    bg = st.selectbox("Background color", ["white", "black", "lightgray", "beige"])
    st.divider()
    st.markdown("**Supported commands:** " + ", ".join(SHAPES))
    st.caption("Creative mode: fuzzy & synonyms. Examples: `sqare`→square, `box`→square")

cmd = st.text_input("Enter a shape command (e.g., circle / tree / sqare / box / house):", "")
col1, col2 = st.columns([1, 1])

with col1:
    if st.button("Draw!", use_container_width=True):
        if not cmd.strip():
            st.warning("Please enter a command.")
        else:
            parsed = parse_command(cmd, mode=mode)
            if not parsed:
                st.error("Command not recognized. Try strict mode with valid commands or use creative mode.")
            else:
                out_name = f"outputs/{int(time.time())}-{parsed}.png"
                path = draw_shape(parsed, size=(width, height), stroke=stroke, color=color, bg=bg, filename=out_name)
                st.success(f"Generated: {parsed}")
                st.image(path, caption=os.path.basename(path), use_container_width=True)

with col2:
    st.info("📎 Tip: `tree` and `house` are composite shapes.")
    st.code(
        "Examples:\n"
        "  circle\n"
        "  triangle\n"
        "  line\n"
        "  tree\n"
        "  house\n"
        "  sqare   # misspelling → square\n"
        "  box     # synonym → square"
    )
