import streamlit as st
import pandas as pd

def initialize_filter_state(force_reset=False):
    """Initialize all filter-related session state variables.
    
    Args:
        force_reset (bool): If True, reset all values to defaults regardless of current state
    """
    # Initialize main filter values with defaults
    if 'property_types' not in st.session_state or force_reset:
        st.session_state.property_types = ['Single Family', 'Condo', 'Townhouse', 'Multi-Family']
        
    if 'states' not in st.session_state or force_reset:
        st.session_state.states = ['VA', 'MD']
        
    if 'year_built_range' not in st.session_state or force_reset:
        st.session_state.year_built_range = (1800, 2024)
        
    if 'beds_range' not in st.session_state or force_reset:
        st.session_state.beds_range = (0, 10)
        
    if 'baths_range' not in st.session_state or force_reset:
        st.session_state.baths_range = (0.0, 10.0)
        
    if 'sqft_range' not in st.session_state or force_reset:
        st.session_state.sqft_range = (0, 10000)
        
    if 'sale_date_range' not in st.session_state or force_reset:
        st.session_state.sale_date_range = (1900, 2024)
        
    if 'sale_price_range' not in st.session_state or force_reset:
        st.session_state.sale_price_range = (0, 2000000)
        
    if 'permit_year_range' not in st.session_state or force_reset:
        st.session_state.permit_year_range = (1950, 2024)
        
    if 'sale_to_permit_years_range' not in st.session_state or force_reset:
        st.session_state.sale_to_permit_years_range = (-20, 20)

    # Initialize include null checkboxes - all default to True
    if 'include_null_property_type' not in st.session_state or force_reset:
        st.session_state.include_null_property_type = True
    if 'include_null_year_built' not in st.session_state or force_reset:
        st.session_state.include_null_year_built = True
    if 'include_null_beds' not in st.session_state or force_reset:
        st.session_state.include_null_beds = True
    if 'include_null_baths' not in st.session_state or force_reset:
        st.session_state.include_null_baths = True
    if 'include_null_sqft' not in st.session_state or force_reset:
        st.session_state.include_null_sqft = True
    if 'include_null_sale_date' not in st.session_state or force_reset:
        st.session_state.include_null_sale_date = True
    if 'include_null_sale_price' not in st.session_state or force_reset:
        st.session_state.include_null_sale_price = True
    if 'include_null_sale_to_permit' not in st.session_state or force_reset:
        st.session_state.include_null_sale_to_permit = True

def reset_filters():
    """Reset all filter-related session state variables to defaults."""
    # First clear all filter keys from session state
    for key in [
        'property_types', 'states', 'year_built_range', 'beds_range',
        'baths_range', 'sqft_range', 'sale_date_range', 'sale_price_range',
        'permit_year_range', 'sale_to_permit_years_range',
        'include_null_property_type', 'include_null_year_built', 'include_null_beds', 'include_null_baths',
        'include_null_sqft', 'include_null_sale_date', 'include_null_sale_price',
        'include_null_sale_to_permit'
    ]:
        if key in st.session_state:
            del st.session_state[key]

def render_all_filters(builder):
    """Render all filters in the sidebar."""
    st.header("Filters")
    
    # Initialize session state
    initialize_filter_state()
    
    # Property Types filter
    property_types = sorted([pt for pt in builder.properties_df['propertyType'].unique() if pd.notna(pt) and pt != 'Unknown'])
    st.multiselect(
        "Property Types",
        options=property_types,
        default=st.session_state.property_types,
        key="property_types",
        help="Select property types to include"
    )
    st.checkbox("Include properties with unknown or missing property type", key="include_null_property_type")

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
        max_value=2024,
        value=st.session_state.year_built_range,
        key="year_built_range"
    )
    st.checkbox("Include properties with no year built data", key="include_null_year_built")

    # Beds filter
    st.slider(
        "Bedrooms Range",
        min_value=0,
        max_value=10,
        value=st.session_state.beds_range,
        key="beds_range"
    )
    st.checkbox("Include properties with no bedroom data", key="include_null_beds")

    # Baths filter
    st.slider(
        "Bathrooms Range",
        min_value=0.0,
        max_value=10.0,
        value=st.session_state.baths_range,
        step=0.5,
        key="baths_range"
    )
    st.checkbox("Include properties with no bathroom data", key="include_null_baths")

    # Square Footage filter
    st.slider(
        "Square Footage Range",
        min_value=0,
        max_value=10000,
        value=st.session_state.sqft_range,
        step=100,
        key="sqft_range"
    )
    st.checkbox("Include properties with no square footage data", key="include_null_sqft")

    # Sale Date filter
    st.slider(
        "Sale Year Range",
        min_value=1900,
        max_value=2024,
        value=st.session_state.sale_date_range,
        key="sale_date_range"
    )
    st.checkbox("Include properties with no sale date data", key="include_null_sale_date")

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
    st.checkbox("Include properties with no sale price data", key="include_null_sale_price")

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
    st.checkbox("Include properties with no sale-to-permit data", key="include_null_sale_to_permit")

    # Add Apply Filters button
    st.divider()
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Apply Filters", type="primary"):
            st.rerun()
    with col2:
        if st.button("Reset"):
            reset_filters()
            st.rerun() 