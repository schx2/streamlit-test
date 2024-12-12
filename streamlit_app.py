import streamlit as st
from utils import (
    initialize_session_state,
    load_data,
    build_property_filters,
    build_permit_filters,
    display_distributions
)
from filters import render_all_filters, initialize_filter_state, reset_filters
import json
import os
import pandas as pd
import numpy as np

st.set_page_config(page_title="Demo Audience Builder", page_icon="🏡", layout="wide")

def save_audience(properties, name):
    """Save a set of properties as a named audience."""
    # Create audiences directory if it doesn't exist
    os.makedirs('audiences', exist_ok=True)
    
    # Convert properties to a list of strings if they aren't already
    properties_list = [str(p) for p in properties]
    
    # Save the audience
    with open(f'audiences/{name}.json', 'w') as f:
        json.dump({
            'name': name,
            'properties': properties_list
        }, f)

def load_saved_audiences():
    """Load all saved audiences."""
    audiences = {}
    if os.path.exists('audiences'):
        for filename in os.listdir('audiences'):
            if filename.endswith('.json'):
                with open(f'audiences/{filename}', 'r') as f:
                    audience = json.load(f)
                    # Convert properties back to the original type if needed
                    audiences[audience['name']] = set(audience['properties'])
    return audiences

def delete_audience(name):
    """Delete an audience file and remove it from session state."""
    try:
        os.remove(f'audiences/{name}.json')
        del st.session_state.saved_audiences[name]
        return True
    except Exception as e:
        print(f"Error deleting audience {name}: {str(e)}")
        return False

def delete_all_audiences():
    """Delete all saved audience files and clear from session state."""
    try:
        if os.path.exists('audiences'):
            for filename in os.listdir('audiences'):
                if filename.endswith('.json'):
                    os.remove(os.path.join('audiences', filename))
        st.session_state.saved_audiences = {}
        return True
    except Exception as e:
        print(f"Error deleting all audiences: {str(e)}")
        return False

def get_audience_summary(properties_df, property_ids):
    """Generate a summary of audience properties."""
    audience_df = properties_df[properties_df.index.isin(property_ids)]
    
    summary = {
        'Total Properties': len(audience_df),
        'Average Square Footage': f"{audience_df['buildingSize'].mean():.0f}",
        'Average Year Built': f"{audience_df['yearBuilt'].mean():.0f}",
        'Average Beds': f"{audience_df['beds'].mean():.1f}",
        'Average Baths': f"{audience_df['baths'].mean():.1f}",
        'Property Types': audience_df['propertyType'].value_counts().to_dict(),
        'States': audience_df['state'].value_counts().to_dict()
    }
    return summary

def display_audience_details(builder, properties, name=None, filtered_permits=None, key_prefix=""):
    """Display comprehensive details about an audience, including charts."""
    # Create a DataFrame for just this audience
    audience_df = builder.properties_df[builder.properties_df.index.isin(properties)].copy()
    
    # Create audience results for charts
    audience_results = {
        'results': audience_df,
        'total_properties': len(audience_df),
        'filtered_permits': filtered_permits
    }
    
    class JSONEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (pd.Timestamp, pd.DatetimeIndex)):
                return obj.strftime('%Y-%m-%d %H:%M:%S')
            if isinstance(obj, (np.int64, np.int32)):
                return int(obj)
            if isinstance(obj, (np.float64, np.float32)):
                return float(obj)
            if pd.isna(obj):
                return None
            return super().default(obj)
    
    if name:
        st.subheader(f"Audience: {name}")
    
    # Add download button
    col1, col2 = st.columns([3, 1])
    with col1:
        if name and st.button("📥 Download Properties as CSV", key=f"download_{key_prefix}"):
            # Only process permit data when download is clicked
            if filtered_permits is not None:
                # Get the filtered permit IDs set for faster lookup
                filtered_permit_ids = set(filtered_permits.index)
                
                # Add permit columns using the existing mappings from builder
                audience_df['permit_ids'] = audience_df.index.map(
                    lambda x: ','.join(str(pid) for pid in builder.property_permit_map.get(x, []) 
                                     if pid in filtered_permit_ids)
                )
                
                audience_df['permit_data'] = audience_df.index.map(
                    lambda x: json.dumps(
                        [filtered_permits.loc[pid].to_dict() 
                         for pid in builder.property_permit_map.get(x, [])
                         if pid in filtered_permit_ids],
                        cls=JSONEncoder
                    )
                )
            
            # Convert DataFrame to CSV
            csv = audience_df.to_csv()
            st.download_button(
                label="⬇️ Click to Download",
                data=csv,
                file_name=f"{name or 'audience'}_properties.csv",
                mime="text/csv",
                key=f"actual_download_{key_prefix}"
            )
    
    with col2:
        if name:  # Only show delete button for saved audiences
            if st.button("🗑️ Delete Audience", key=f"delete_{key_prefix}_{name}"):
                if delete_audience(name):
                    st.success(f"Deleted audience '{name}'")
                    st.rerun()
                else:
                    st.error(f"Failed to delete audience '{name}'")
    
    # Display summary metrics
    summary = get_audience_summary(builder.properties_df, properties)
    
    # Display key metrics in columns
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Properties", f"{summary['Total Properties']:,}")
    with col2:
        st.metric("Avg Square Footage", summary['Average Square Footage'])
    with col3:
        st.metric("Avg Year Built", summary['Average Year Built'])
    with col4:
        st.metric("Avg Beds/Baths", f"{summary['Average Beds']}/{summary['Average Baths']}")
    
    # Display distribution charts
    display_distributions(audience_results, builder, filtered_permits, key_prefix=key_prefix)
    
    # Display sample properties
    st.subheader("Sample Properties")
    st.dataframe(audience_df.head(), use_container_width=True)

def main():
    st.title("🏡 Property Audience Builder")
    
    try:
        # Initialize session state and load data
        initialize_session_state()
        initialize_filter_state()
        matches_files = {
            'MD': 'MD/MD_matches.json',
            'VA': 'VA/VA_matches.json'
        }
        builder = load_data(matches_files)
        
        # Load saved audiences
        if 'saved_audiences' not in st.session_state:
            st.session_state.saved_audiences = load_saved_audiences()
        
        # Add delete all audiences button if there are any saved audiences
        if st.session_state.saved_audiences:
            if st.button("🗑️ Delete All Audiences"):
                if delete_all_audiences():
                    st.toast("All audiences have been deleted")
                    st.rerun()
                else:
                    st.error("Failed to delete all audiences")
        
        # Create tabs for builder and saved audiences
        tabs = ["Audience Builder"]
        if st.session_state.saved_audiences:
            tabs.extend(list(st.session_state.saved_audiences.keys()))
        
        current_tab = st.tabs(tabs)
        
        # Remove properties that are already in saved audiences
        excluded_properties = set()
        for properties in st.session_state.saved_audiences.values():
            excluded_properties.update(properties)
        
        # Render filters in sidebar
        with st.sidebar:
            render_all_filters(builder)
        
        # Build audience with current filters
        results = builder.build_audience(
            property_filters=build_property_filters(),
            permit_filters=build_permit_filters(),
            exclude_properties=list(excluded_properties)
        )
        
        # Display content for current tab
        with current_tab[0]:  # Audience Builder tab
            # Display metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Available Properties", 
                         f"{results['total_properties']:,}",
                         f"-{len(excluded_properties):,} in saved audiences" if excluded_properties else None)
            with col2:
                st.metric("Properties Matching Filters", f"{results['matching_properties']:,}",
                          help="Properties that have non-null values for all filters")
            with col3:
                st.metric("Permits Matching Filters", f"{results['matching_permits']:,}")
            st.divider()


            # Add save audience button and name input
            st.subheader("Create an audience")
            st.write("Apply filters to create a new audience")
            audience_name = st.text_input("Audience Name", key="audience_name")
            if st.button("Save as Audience"):
                if not audience_name:
                    st.error("Please enter an audience name")
                elif audience_name in st.session_state.saved_audiences:
                    st.error("An audience with this name already exists")
                else:
                    try:
                        # Get current results and save
                        current_properties = results['results'].index.astype(str).tolist()
                        save_audience(current_properties, audience_name)
                        st.session_state.saved_audiences[audience_name] = set(current_properties)
                        
                        # Reset filters and clear audience name input
                        reset_filters()
                        
                        st.toast(f"Audience '{audience_name}' created. Filters were reset.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Failed to save audience: {str(e)}")

            # Display current selection details
            if len(results['results']) > 0:
                display_audience_details(builder, results['results'].index, filtered_permits=results['filtered_permits'], key_prefix="main")
            else:
                st.warning("No properties match the selected criteria.")
        
        # Display saved audience tabs
        for i, (name, properties) in enumerate(st.session_state.saved_audiences.items(), 1):
            with current_tab[i]:
                # For saved audiences, we need to rebuild their results with current filters
                saved_results = builder.build_audience(
                    property_filters=build_property_filters(),
                    permit_filters=build_permit_filters(),
                    exclude_properties=[p for p in excluded_properties if p not in properties]
                )
                display_audience_details(builder, properties, name, filtered_permits=saved_results['filtered_permits'], key_prefix=f"saved_{i}")
            
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.error("Please check if all required data files are in the correct location.")

if __name__ == "__main__":
    main() 