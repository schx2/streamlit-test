import streamlit as st
import pandas as pd

def initialize_filter_state():
    """Initialize all filter-related session state variables."""
    # Initialize main filter values with defaults
    if 'property_types' not in st.session_state:
        st.session_state.property_types = []
    elif st.session_state.property_types is None:
        st.session_state.property_types = []
        
    if 'states' not in st.session_state:
        st.session_state.states = []
    elif st.session_state.states is None:
        st.session_state.states = []
        
    if 'year_built_range' not in st.session_state:
        st.session_state.year_built_range = (1800, 2023)
    elif st.session_state.year_built_range is None:
        st.session_state.year_built_range = (1800, 2023)
        
    if 'beds_range' not in st.session_state:
        st.session_state.beds_range = (0, 10)
    elif st.session_state.beds_range is None:
        st.session_state.beds_range = (0, 10)
        
    if 'baths_range' not in st.session_state:
        st.session_state.baths_range = (0.0, 10.0)
    elif st.session_state.baths_range is None:
        st.session_state.baths_range = (0.0, 10.0)
        
    if 'sqft_range' not in st.session_state:
        st.session_state.sqft_range = (0, 10000)
    elif st.session_state.sqft_range is None:
        st.session_state.sqft_range = (0, 10000)
        
    if 'sale_date_range' not in st.session_state:
        st.session_state.sale_date_range = (1900, 2023)
    elif st.session_state.sale_date_range is None:
        st.session_state.sale_date_range = (1900, 2023)
        
    if 'sale_price_range' not in st.session_state:
        st.session_state.sale_price_range = (0, 2000000)
    elif st.session_state.sale_price_range is None:
        st.session_state.sale_price_range = (0, 2000000)
        
    if 'permit_year_range' not in st.session_state:
        st.session_state.permit_year_range = (1950, 2024)
    elif st.session_state.permit_year_range is None:
        st.session_state.permit_year_range = (1950, 2024)
        
    if 'sale_to_permit_years_range' not in st.session_state:
        st.session_state.sale_to_permit_years_range = (-20, 20)
    elif st.session_state.sale_to_permit_years_range is None:
        st.session_state.sale_to_permit_years_range = (-20, 20)

def render_all_filters(builder):
    """Render all filters in the sidebar."""
    st.header("Filters")
    
    # Initialize session state
    initialize_filter_state()
    
    # Property Types filter
    property_types = sorted([pt for pt in builder.properties_df['propertyType'].unique() if pd.notna(pt)])
    st.multiselect(
        "Property Types",
        options=property_types,
        default=st.session_state.property_types,
        key="property_types",
        help="Select property types to include"
    )

    # States filter
    states = sorted([s for s in builder.properties_df['state'].unique() if pd.notna(s)])
    st.multiselect(
        "States",
        options=states,
        default=st.session_state.states,
        key="states"
    )

    # Year Built filter
    st.slider(
        "Year Built Range",
        min_value=1800,
        max_value=2023,
        value=st.session_state.year_built_range,
        key="year_built_range"
    )

    # Beds filter
    st.slider(
        "Bedrooms Range",
        min_value=0,
        max_value=10,
        value=st.session_state.beds_range,
        key="beds_range"
    )

    # Baths filter
    st.slider(
        "Bathrooms Range",
        min_value=0.0,
        max_value=10.0,
        value=st.session_state.baths_range,
        step=0.5,
        key="baths_range"
    )

    # Square Footage filter
    st.slider(
        "Square Footage Range",
        min_value=0,
        max_value=10000,
        value=st.session_state.sqft_range,
        step=100,
        key="sqft_range"
    )

    # Sale Date filter
    st.slider(
        "Sale Year Range",
        min_value=1900,
        max_value=2023,
        value=st.session_state.sale_date_range,
        key="sale_date_range"
    )

    # Sale Price filter
    st.slider(
        "Sale Price Range",
        min_value=0,
        max_value=2000000,
        value=st.session_state.sale_price_range,
        step=10000,
        format="$%d",
        key="sale_price_range"
    )

    # Permit Year filter
    st.slider(
        "Permit Year Range",
        min_value=1950,
        max_value=2023,
        value=st.session_state.permit_year_range,
        key="permit_year_range"
    )
    
    # Time between sale and permit filter
    st.slider(
        "Years Between Sale and Permit",
        min_value=-20,
        max_value=20,
        value=st.session_state.sale_to_permit_years_range,
        help="Negative values mean permit before sale, positive values mean permit after sale",
        key="sale_to_permit_years_range"
    )

    # Add Apply Filters button
    st.divider()
    col1, col2 = st.columns([3, 1])
    with col1:
        if st.button("Apply Filters", type="primary"):
            st.rerun()
    with col2:
        if st.button("Reset"):
            initialize_filter_state()
            st.rerun() 