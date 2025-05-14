import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="CSV Editor", layout="wide")

st.title("CSV Editor")

# File uploader
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

# Initialize session state to store the dataframe and filename
if "dataframe" not in st.session_state:
    st.session_state.dataframe = None
if "filename" not in st.session_state:
    st.session_state.filename = None

if uploaded_file is not None:
    # Read the file and store in session state
    st.session_state.dataframe = pd.read_csv(uploaded_file)
    st.session_state.filename = uploaded_file.name
    
    # Display file information
    st.write(f"Loaded: **{st.session_state.filename}**")
    st.write(f"Rows: {st.session_state.dataframe.shape[0]}, Columns: {st.session_state.dataframe.shape[1]}")

    # Create a new column for row ordering if it doesn't exist
    if "row_order" not in st.session_state.dataframe.columns:
        st.session_state.dataframe.insert(0, "row_order", range(len(st.session_state.dataframe)))
    
    # Configure column display
    column_config = {
        "row_order": st.column_config.NumberColumn(
            "Order",
            help="Change numbers to reorder rows",
            width="small",
            step=1,
            format="%d"
        )
    }
    
    # Data editor with manually editable row ordering
    edited_df = st.data_editor(
        st.session_state.dataframe,
        num_rows="dynamic",
        column_config=column_config,
        use_container_width=True,
        hide_index=True,
        key="data_editor"
    )
    
    # Sort by row_order column after editing
    if st.button("Apply Row Order"):
        edited_df = edited_df.sort_values("row_order").reset_index(drop=True)
        st.session_state.dataframe = edited_df
        st.success("Rows reordered successfully!")
        st.experimental_rerun()
    
    # Line Graph Visualization
    st.subheader("Data Visualization")
    
    # Get numeric columns for plotting
    numeric_columns = edited_df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    
    if numeric_columns:
        # Allow user to select columns for plotting
        selected_columns = st.multiselect(
            "Select columns to plot",
            numeric_columns,
            default=numeric_columns[:2] if len(numeric_columns) >= 2 else numeric_columns
        )
        
        if selected_columns:
            # Create line chart
            st.line_chart(edited_df[selected_columns])
            
            # Add options for customization
            with st.expander("Chart Options"):
                use_index = st.checkbox("Use row numbers as x-axis", value=True)
                if use_index:
                    chart_data = edited_df[selected_columns].reset_index()
                    st.line_chart(chart_data.set_index('index')[selected_columns])
                else:
                    st.line_chart(edited_df[selected_columns])
    else:
        st.info("No numeric columns available for plotting")
    
    # Save button
    col1, col2 = st.columns([1, 5])
    with col1:
        save_name = st.text_input("Save as:", value=f"edited_{st.session_state.filename}")
        include_order = st.checkbox("Include order column", value=False)
    with col2:
        if st.button("Save Changes"):
            save_df = edited_df.copy()
            if not include_order and "row_order" in save_df.columns:
                save_df = save_df.drop(columns=["row_order"])
            save_df.to_csv(save_name, index=False)
            st.success(f"Saved as {save_name}")
            
    # Display data summary
    with st.expander("Data Summary"):
        st.write(edited_df.describe())
else:
    st.info("Please upload a CSV file to get started")
    
    # Display demo information
    if st.checkbox("Show demo data"):
        demo_data = pd.DataFrame({
            'Name': ['John', 'Anna', 'Peter', 'Linda'],
            'Age': [28, 34, 45, 32],
            'City': ['New York', 'Paris', 'Berlin', 'London'],
            'Salary': [75000, 80000, 65000, 70000]
        })
        
        # Add row order column to demo data
        demo_data.insert(0, "row_order", range(len(demo_data)))
        
        # Configure column display for demo
        column_config = {
            "row_order": st.column_config.NumberColumn(
                "Order",
                help="Change numbers to reorder rows",
                width="small",
                step=1,
                format="%d"
            )
        }
        
        # Demo editor with manual row reordering
        edited_demo = st.data_editor(
            demo_data,
            num_rows="dynamic",
            column_config=column_config,
            use_container_width=True,
            hide_index=True,
            key="demo_editor"
        )
        
        # Apply demo ordering
        if st.button("Apply Demo Row Order"):
            edited_demo = edited_demo.sort_values("row_order").reset_index(drop=True)
            st.experimental_rerun()
        
        # Demo visualization
        st.subheader("Demo Data Visualization")
        numeric_columns = edited_demo.select_dtypes(include=['int64', 'float64']).columns.tolist()
        if numeric_columns:
            selected_columns = st.multiselect(
                "Select columns to plot",
                numeric_columns,
                default=numeric_columns[:2] if len(numeric_columns) >= 2 else numeric_columns,
                key="demo_plot"
            )
            if selected_columns:
                st.line_chart(edited_demo[selected_columns])
        
        if st.button("Save Demo Data"):
            # Remove the row_order column before saving unless specified
            if st.checkbox("Include order column in demo", value=False):
                edited_demo.to_csv("demo_data.csv", index=False)
            else:
                edited_demo.drop(columns=["row_order"]).to_csv("demo_data.csv", index=False)
            st.success("Saved as demo_data.csv")
