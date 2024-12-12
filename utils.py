import streamlit as st
import pandas as pd
import plotly.express as px
import json

# Configuration constants
OUTLIER_QUANTILES = {
    'lower': 0.01,  # 5th percentile
    'upper': 0.99   # 95th percentile
}

# Default ranges
DEFAULT_RANGES = {
    'year_built': (1900, 2023),
    'beds': (0, 10),
    'baths': (0.0, 10.0),
    'sqft': (0.0, 10000.0),
    'sale_year': (2000, 2023),
    'sale_price': (0.0, 2000000.0),
    'permit_year': (2000, 2023)
}

# Field mappings for alternative names
FIELD_MAPPINGS = {
    'sale_amount': ['lastSaleAmount', 'lastSalePrice', 'saleAmount', 'salePrice'],
    'sale_date': ['lastSaleDate', 'saleDate'],
    'permit_date': ['file_date', 'fileDate', 'permitDate', 'issueDate', 'issue_date']
}

# Slider steps
SLIDER_STEPS = {
    'price': 10000.0,  # $10k steps
    'sqft': 100.0,     # 100 sqft steps
    'baths': 0.5       # 0.5 bath steps
}

def initialize_session_state():
    """Initialize all session state variables if they don't exist."""
    if 'initialized' not in st.session_state:
        st.session_state.initialized = False
        st.session_state.builder = None
        st.session_state.ranges = None

def load_data(matches_files):
    """Load data into the builder if not already loaded."""
    from audienceBuilder import AudienceBuilder
    
    if not st.session_state.initialized:
        # st.info("Loading data... please wait.")
        builder = AudienceBuilder(matches_files=matches_files)
        builder.load_data()
        st.session_state.builder = builder
        st.session_state.initialized = True
        # st.success("Data loaded successfully!")
    
    return st.session_state.builder

def get_safe_range(data: pd.DataFrame | pd.Series, 
                  field_key: str = None,
                  default_min: float = 0.0, 
                  default_max: float = 1.0,
                  remove_outliers: bool = True,
                  as_int: bool = False,
                  is_date: bool = False) -> tuple:
    """
    Get min/max range for data, handling various data types and edge cases.
    """
    try:
        # Handle DataFrame with field mapping
        if isinstance(data, pd.DataFrame) and field_key:
            possible_fields = FIELD_MAPPINGS.get(field_key, [field_key])
            for field in possible_fields:
                if field in data.columns:
                    series = data[field]
                    if not series.isna().all():
                        break
            else:  # No valid field found
                return (default_min, default_max)
        else:
            series = data
        
        # Handle empty or all-null series
        if series is None or len(series) == 0 or series.isna().all():
            return (default_min, default_max)
        
        # Handle dates
        if is_date:
            if not pd.api.types.is_datetime64_any_dtype(series):
                series = pd.to_datetime(series, errors='coerce')
            valid_values = series.dropna()
            if len(valid_values) == 0:
                return (default_min, default_max)
            return (
                int(valid_values.dt.year.min()),
                int(valid_values.dt.year.max())
            )
        
        # Handle numeric data
        clean_series = pd.to_numeric(series, errors='coerce')
        valid_values = clean_series.dropna()
        if len(valid_values) == 0:
            return (default_min, default_max)
        
        if remove_outliers:
            lower = valid_values.quantile(OUTLIER_QUANTILES['lower'])
            upper = valid_values.quantile(OUTLIER_QUANTILES['upper'])
        else:
            lower = valid_values.min()
            upper = valid_values.max()
        
        # Round to step size if it's a price
        if field_key == 'sale_amount':
            step = SLIDER_STEPS['price']
            lower = round(float(lower) / step) * step
            upper = round(float(upper) / step) * step
        
        if as_int:
            return (int(lower), int(upper))
        return (float(lower), float(upper))
        
    except Exception as e:
        print(f"Error in get_safe_range: {str(e)}")
        return (default_min, default_max)

def create_distribution_chart(data: pd.DataFrame, field: str, title: str, 
                            is_date: bool = False, is_price: bool = False,
                            alt_fields: list = None, remove_outliers: bool = False):
    """Create a distribution chart for a given field."""
    try:
        # Try alternative field names if provided
        if alt_fields:
            for alt_field in alt_fields:
                if alt_field in data.columns and not data[alt_field].isna().all():
                    field = alt_field
                    break
        
        if field not in data.columns:
            return None
        
        total_properties = len(data)
        
        # Get valid data
        valid_data = data[data[field].notna()].copy()
        valid_count = len(valid_data)
        if valid_count == 0:
            return None
        
        # Handle dates
        if is_date:
            valid_data[field] = pd.to_datetime(valid_data[field], errors='coerce')
            valid_data = valid_data[valid_data[field].notna()]
            if len(valid_data) == 0:
                return None
        
        # Remove outliers if requested
        outlier_count = 0
        if remove_outliers and not is_date:
            if pd.api.types.is_numeric_dtype(valid_data[field]) or is_price:
                values = pd.to_numeric(valid_data[field], errors='coerce')
                lower = values.quantile(OUTLIER_QUANTILES['lower'])
                upper = values.quantile(OUTLIER_QUANTILES['upper'])
                valid_data = valid_data[(values >= lower) & (values <= upper)]
                outlier_count = valid_count - len(valid_data)
                title += f" ({OUTLIER_QUANTILES['lower']*100:.0f}th-{OUTLIER_QUANTILES['upper']*100:.0f}th percentile)"
        
        # Update title with counts
        missing_count = total_properties - valid_count
        title = f"{title}<br>Total: {total_properties:,} | Valid: {valid_count:,}"
        if missing_count > 0:
            title += f" | Missing: {missing_count:,}"
        if outlier_count > 0:
            title += f" | Outliers: {outlier_count:,}"
        
        # Create and customize histogram
        fig = px.histogram(valid_data, x=field, title=title)
        fig.update_xaxes(
            title=title.split('<br>')[0],  # Use original title without counts
            tickformat="%Y-%m-%d" if is_date else "$,.0f" if is_price else None
        )
        fig.update_layout(
            showlegend=False,
            yaxis_title="Count",
            height=400,  # Increased height
            margin=dict(l=20, r=20, t=60, b=20),  # Increased top margin for multi-line title
            bargap=0.1  # Reduced gap between bars
        )
        
        return fig
        
    except Exception as e:
        print(f"Error creating chart for {field}: {str(e)}")
        return None

def update_filter_ranges(builder):
    """Update all filter ranges based on current selections."""
    try:
        # Build audience with current filters
        results = builder.build_audience(
            property_filters=build_property_filters(),
            permit_filters=build_permit_filters()
        )
        return results
        
    except Exception as e:
        print(f"Error updating filter ranges: {str(e)}")
        return None

def build_property_filters():
    """Build the property filters dictionary from current session state."""
    filters = {}
    
    # Property types and states
    if st.session_state.property_types:
        filters['property_types'] = st.session_state.property_types
    if st.session_state.states:
        filters['states'] = st.session_state.states
    
    # Numeric range filters
    if st.session_state.year_built_range:
        filters['min_year_built'] = st.session_state.year_built_range[0]
        filters['max_year_built'] = st.session_state.year_built_range[1]
    
    if st.session_state.beds_range:
        filters['min_beds'] = st.session_state.beds_range[0]
        filters['max_beds'] = st.session_state.beds_range[1]
    
    if st.session_state.baths_range:
        filters['min_baths'] = st.session_state.baths_range[0]
        filters['max_baths'] = st.session_state.baths_range[1]
    
    if st.session_state.sqft_range:
        filters['min_sqft'] = st.session_state.sqft_range[0]
        filters['max_sqft'] = st.session_state.sqft_range[1]
    
    if st.session_state.sale_date_range:
        filters['min_sale_year'] = st.session_state.sale_date_range[0]
        filters['max_sale_year'] = st.session_state.sale_date_range[1]
    
    if st.session_state.sale_price_range:
        filters['min_sale_price'] = st.session_state.sale_price_range[0]
        filters['max_sale_price'] = st.session_state.sale_price_range[1]
    
    if st.session_state.sale_to_permit_years_range:
        filters['min_sale_to_permit_years'] = st.session_state.sale_to_permit_years_range[0]
        filters['max_sale_to_permit_years'] = st.session_state.sale_to_permit_years_range[1]
    
    return filters

def build_permit_filters():
    """Build the permit filters dictionary from current session state."""
    filters = {}
    
    if st.session_state.permit_year_range:
        filters['min_permit_year'] = st.session_state.permit_year_range[0]
        filters['max_permit_year'] = st.session_state.permit_year_range[1]
    
    return filters

def display_data_quality(results):
    """Display data quality information for the results."""
    quality_data = []
    for col in ['yearBuilt', 'beds', 'baths', 'buildingSize']:
        if col in results['results'].columns:
            null_count = results['results'][col].isna().sum()
            quality_data.append({
                'Field': col,
                'Null Count': null_count,
                'Null Percentage': f"{null_count/len(results['results'])*100:.1f}%"
            })
        else:
            quality_data.append({
                'Field': col,
                'Null Count': 'Column not found',
                'Null Percentage': 'N/A'
            })
    st.dataframe(pd.DataFrame(quality_data))

def create_permit_year_distribution(builder, property_ids, filtered_permits=None):
    """Create a distribution chart showing permits by year for the given properties."""
    try:
        print("\n[Chart: Permits by Year] Creating distribution")
        if filtered_permits is None:
            print("[Chart: Permits by Year] No permits provided")
            return None
            
        print(f"[Chart: Permits by Year] Starting with {len(filtered_permits):,} filtered permits")
        
        # Only keep permits for the selected properties
        permits_df = filtered_permits[filtered_permits['property_id'].isin(property_ids)].copy()
        print(f"[Chart: Permits by Year] After property filter: {len(permits_df):,} permits")
        
        if len(permits_df) == 0:
            print("[Chart: Permits by Year] No permits to display")
            return None
            
        permits_df['file_date'] = pd.to_datetime(permits_df['file_date'], errors='coerce')
        permits_df['year'] = permits_df['file_date'].dt.year
        
        # Create year distribution
        year_counts = permits_df['year'].value_counts().sort_index()
        print(f"[Chart: Permits by Year] Year distribution: {dict(year_counts)}")
        
        # Create bar chart
        fig = px.bar(
            x=year_counts.index,
            y=year_counts.values,
            title=f'Permits by Year (Total: {len(permits_df):,})',
            labels={'x': 'Year', 'y': 'Number of Permits'}
        )
        
        fig.update_layout(
            showlegend=False,
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
            bargap=0.1
        )
        
        return fig
    
    except Exception as e:
        print(f"[Chart: Permits by Year] Error: {str(e)}")
        return None

def create_sale_to_permit_distribution(builder, property_ids, filtered_permits=None):
    """Create a distribution chart showing time between sale and permit dates."""
    try:
        if filtered_permits is None:
            return None
        
        # Calculate time differences
        time_diffs = []
        for property_id in property_ids:
            if property_id in builder.property_permit_map:
                sale_date = builder.properties_df.loc[property_id, 'lastSaleDate']
                if pd.notna(sale_date):
                    permit_dates = []
                    for permit_id in builder.property_permit_map[property_id]:
                        if permit_id in filtered_permits.index:
                            permit_date = filtered_permits.loc[permit_id, 'file_date']
                            if pd.notna(permit_date):
                                # Both dates are already timezone-aware (UTC)
                                time_diff = (permit_date - sale_date).days / 365.25
                                time_diffs.append(time_diff)
        
        if not time_diffs:
            return None
        
        # Create DataFrame for the distribution
        df = pd.DataFrame({'years_between': time_diffs})
        
        # Create histogram
        fig = px.histogram(
            df,
            x='years_between',
            title=f'Distribution of Years Between Sale and Permit (n={len(time_diffs):,})',
            labels={'years_between': 'Years (negative = permit before sale)'},
            nbins=int(max(time_diffs) - min(time_diffs)) + 1,  # One bin per year
            range_x=(int(min(time_diffs)), int(max(time_diffs)) + 1)  # Align to integer years
        )
        
        fig.update_layout(
            showlegend=False,
            yaxis_title="Count",
            height=400,
            margin=dict(l=20, r=20, t=40, b=20),
            bargap=0.1
        )
        
        return fig
    
    except Exception as e:
        print(f"Error creating sale-to-permit distribution: {str(e)}")
        return None

def display_distributions(results, builder=None, filtered_permits=None, key_prefix="main"):
    """Display distribution charts for various fields."""
    print("\n[Charts] Starting to display distributions")
    
    # Use filtered permits from results if available
    if 'filtered_permits' in results:
        filtered_permits = results['filtered_permits']
        print(f"[Charts] Using filtered permits from results: {len(filtered_permits):,} permits")
    elif filtered_permits is not None:
        print(f"[Charts] Using provided filtered permits: {len(filtered_permits):,} permits")
    else:
        print("[Charts] No filtered permits available")
    
    # Add outlier removal toggle
    remove_outliers = st.checkbox("Remove Outliers", value=False, 
                                help="Remove data points below 1st percentile and above 99th percentile",
                                key=f"{key_prefix}_remove_outliers")
    
    # Create two columns for charts with more width
    col1, col2 = st.columns([1, 1])
    
    # Square Footage Distribution
    with col1:
        fig = create_distribution_chart(
            results['results'], 
            'buildingSize', 
            'Distribution by Square Footage',
            remove_outliers=remove_outliers
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    # Year Built Distribution
    with col2:
        fig = create_distribution_chart(
            results['results'], 
            'yearBuilt', 
            'Distribution by Year Built',
            remove_outliers=remove_outliers
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    # Bedrooms and Bathrooms Distribution
    col3, col4 = st.columns([1, 1])
    with col3:
        fig = create_distribution_chart(
            results['results'], 
            'beds', 
            'Distribution by Bedrooms',
            remove_outliers=remove_outliers
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    with col4:
        fig = create_distribution_chart(
            results['results'], 
            'baths', 
            'Distribution by Bathrooms',
            remove_outliers=remove_outliers
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    # Sale Date and Price Distributions
    col5, col6 = st.columns([1, 1])
    with col5:
        fig = create_distribution_chart(
            results['results'], 
            'lastSaleDate', 
            'Distribution by Sale Date',
            is_date=True,
            alt_fields=['lastSaleDate', 'saleDate'],
            remove_outliers=remove_outliers
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    with col6:
        fig = create_distribution_chart(
            results['results'], 
            'lastSaleAmount', 
            'Distribution by Sale Price',
            is_price=True,
            alt_fields=['lastSaleAmount', 'lastSalePrice', 'saleAmount', 'salePrice'],
            remove_outliers=remove_outliers
        )
        if fig:
            st.plotly_chart(fig, use_container_width=True)
    
    # Permit Year Distribution
    if builder is not None and filtered_permits is not None:
        print("\n[Charts] Creating permit year distribution")
        fig = create_permit_year_distribution(builder, results['results'].index, filtered_permits)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            print("[Charts] No permit year chart created")
        
        # Sale to Permit Time Distribution
        print("\n[Charts] Creating sale-to-permit time distribution")
        fig = create_sale_to_permit_distribution(builder, results['results'].index, filtered_permits)
        if fig:
            st.plotly_chart(fig, use_container_width=True)
        else:
            print("[Charts] No sale-to-permit time distribution created")

def reset_invalid_ranges():
    """Reset any filter ranges that are outside their valid bounds."""
    range_checks = [
        ('year_built_range', 'year_built'),
        ('beds_range', 'beds'),
        ('baths_range', 'baths'),
        ('sqft_range', 'sqft'),
        ('sale_date_range', 'sale_date'),
        ('sale_price_range', 'sale_price'),
        ('permit_year_range', 'permit_year')
    ]
    
    for state_key, range_key in range_checks:
        current_range = getattr(st.session_state, state_key, None)
        if isinstance(current_range, tuple) and len(current_range) == 2:
            min_val, max_val = st.session_state.ranges[range_key]
            if (current_range[0] < min_val or current_range[1] > max_val):
                setattr(st.session_state, state_key, None)