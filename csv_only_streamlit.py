import streamlit as st
import pandas as pd
import io

# Set page config for a modern look
st.set_page_config(
    page_title="CSV Editor",
    page_icon="📊",
    layout="wide"
)

# Custom CSS for modern styling
st.markdown("""
    <style>
    .stApp {
        max-width: 1200px;
        margin: 0 auto;
    }
    .stButton>button {
        background-color: #4CAF50;
        color: white;
        border-radius: 5px;
        padding: 0.5rem 1rem;
        border: none;
    }
    .stButton>button:hover {
        background-color: #45a049;
    }
    .css-1d391kg {
        padding: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Title and description
st.title("📊 CSV Editor")
st.markdown("Upload a CSV file to view and edit its contents.")

# File uploader
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    # Read the CSV file
    df = pd.read_csv(uploaded_file)
    
    # Display the dataframe with editing capabilities
    st.subheader("Edit Data")
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        use_container_width=True,
        height=400
    )
    
    # Add a download button for the edited data
    if st.button("Save Changes"):
        # Convert the edited dataframe to CSV
        csv = edited_df.to_csv(index=False)
        st.download_button(
            label="Download edited CSV",
            data=csv,
            file_name="edited_data.csv",
            mime="text/csv"
        )
    
    # Display some basic statistics
    st.subheader("Data Overview")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Rows", len(edited_df))
    with col2:
        st.metric("Total Columns", len(edited_df.columns))
    with col3:
        st.metric("Memory Usage", f"{edited_df.memory_usage(deep=True).sum() / 1024:.2f} KB")
    
    # Display data types
    st.subheader("Column Information")
    st.dataframe(
        pd.DataFrame({
            'Column': edited_df.columns,
            'Data Type': edited_df.dtypes,
            'Non-Null Count': edited_df.count()
        }),
        use_container_width=True
    )
else:
    st.info("👆 Please upload a CSV file to begin editing.") 