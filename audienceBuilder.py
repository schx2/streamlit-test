import pandas as pd
import json
from typing import Dict, List, Optional
from datetime import datetime

class AudienceBuilder:
    def __init__(self, matches_files: Dict[str, str]):
        """Initialize the AudienceBuilder with paths to matches files."""
        self.matches_files = matches_files
        self.properties_df = None
        self.permits_df = None
    
    def load_data(self):
        """Load and process property and permit data from matches files."""
        properties_list = []
        permits_list = []
        
        # Initialize property-permit mappings
        self.property_permit_map = {}  # property_id -> list of permit_ids
        self.permit_property_map = {}  # permit_id -> property_id
        
        # Load and process each matches file
        for state, file_path in self.matches_files.items():
            try:
                with open(file_path, 'r') as f:
                    matches = json.load(f)
                
                for match in matches:
                    if 'property' in match and 'permit' in match:
                        property_id = match['property'].get('id')
                        permit_id = match['permit'].get('permit_id')
                        if property_id and permit_id:
                            # Store property-permit mapping
                            if property_id not in self.property_permit_map:
                                self.property_permit_map[property_id] = []
                            self.property_permit_map[property_id].append(permit_id)
                            self.permit_property_map[permit_id] = property_id
                    
                    if 'property' in match:
                        property_data = match['property']
                        property_data['state'] = state  # Ensure state is included
                        # Ensure all required fields exist with default values
                        property_data.setdefault('yearBuilt', None)
                        property_data.setdefault('bedrooms', None)  # Changed from 'beds' to 'bedrooms'
                        property_data.setdefault('bathrooms', None)
                        property_data.setdefault('squareFootage', None)
                        property_data.setdefault('propertyType', 'Unknown')
                        properties_list.append(property_data)
                    
                    if 'permit' in match:
                        permit_data = match['permit']
                        permit_data['state'] = state  # Ensure state is included
                        permit_data.setdefault('file_date', None)
                        permits_list.append(permit_data)
            
            except Exception as e:
                print(f"Error loading {file_path}: {str(e)}")
        
        if not properties_list:
            raise ValueError("No data loaded from any of the matches files")
        
        # Convert to DataFrames
        self.properties_df = pd.DataFrame(properties_list)
        self.permits_df = pd.DataFrame(permits_list)
        
        # Process property data - handle missing values gracefully
        self.properties_df['yearBuilt'] = pd.to_numeric(self.properties_df['yearBuilt'], errors='coerce')
        self.properties_df['bedrooms'] = pd.to_numeric(self.properties_df['bedrooms'], errors='coerce')  # Changed from 'beds'
        self.properties_df['bathrooms'] = pd.to_numeric(self.properties_df['bathrooms'], errors='coerce')
        self.properties_df['squareFootage'] = pd.to_numeric(self.properties_df['squareFootage'], errors='coerce')
        
        # Rename columns for consistency
        self.properties_df = self.properties_df.rename(columns={
            'bedrooms': 'beds',  # Rename after conversion
            'bathrooms': 'baths',
            'squareFootage': 'buildingSize'
        })
        
        # Process permit data and sale dates - ensure timezone consistency
        self.permits_df['file_date'] = pd.to_datetime(self.permits_df['file_date'], errors='coerce', utc=True)
        self.properties_df['lastSaleDate'] = pd.to_datetime(self.properties_df['lastSaleDate'], errors='coerce', utc=True)
        
        # Set index for both DataFrames
        self.properties_df.set_index('id', inplace=True)
        self.permits_df.set_index('permit_id', inplace=True)
        
        print(f"Loaded {len(self.properties_df)} properties and {len(self.permits_df)} permits")
        print(f"Found {len(self.property_permit_map)} properties with permits")
        print(f"Found {len(self.permit_property_map)} permit-property mappings")
        
        # Print data quality information
        print("\nData quality check:")
        for col in ['yearBuilt', 'beds', 'baths', 'buildingSize']:
            if col in self.properties_df.columns:
                null_count = self.properties_df[col].isna().sum()
                print(f"{col}: {null_count} null values ({null_count/len(self.properties_df)*100:.1f}%)")
            else:
                print(f"{col}: Column not found in dataset")
    
    def filter_properties(self, **kwargs) -> pd.DataFrame:
        """Filter properties based on various criteria."""
        try:
            if self.properties_df is None:
                raise ValueError("Data not loaded. Call load_data() first.")
            
            total_properties = len(self.properties_df)
            print(f"\n[Property Filtering] Starting with {total_properties:,} total properties")
            
            mask = pd.Series(True, index=self.properties_df.index)
            
            try:
                # Year filters
                if kwargs.get('min_year_built') is not None or kwargs.get('max_year_built') is not None:
                    # Only include properties with non-null year built when filtering
                    year_mask = self.properties_df['yearBuilt'].notna()
                    if kwargs.get('min_year_built') is not None:
                        year_mask = year_mask & (self.properties_df['yearBuilt'] >= kwargs['min_year_built'])
                    if kwargs.get('max_year_built') is not None:
                        year_mask = year_mask & (self.properties_df['yearBuilt'] <= kwargs['max_year_built'])
                    mask = mask & year_mask
                    print(f"[Property Filtering] After year built filters: {mask.sum():,} properties")
            except Exception as e:
                print(f"Error in year built filter: {str(e)}")
                raise
            
            try:
                # Sale year filters
                if kwargs.get('min_sale_year') is not None or kwargs.get('max_sale_year') is not None:
                    # Sale dates are already datetime objects with UTC timezone
                    sale_dates = self.properties_df['lastSaleDate']
                    # Only include properties with non-null sale date when filtering
                    sale_mask = sale_dates.notna()
                    if kwargs.get('min_sale_year') is not None:
                        sale_mask = sale_mask & (sale_dates.dt.year >= kwargs['min_sale_year'])
                    if kwargs.get('max_sale_year') is not None:
                        sale_mask = sale_mask & (sale_dates.dt.year <= kwargs['max_sale_year'])
                    mask = mask & sale_mask
                    print(f"[Property Filtering] After sale year filters: {mask.sum():,} properties")
            except Exception as e:
                print(f"Error in sale year filter: {str(e)}")
                raise
            
            try:
                # Sale price filters
                if kwargs.get('min_sale_price') is not None or kwargs.get('max_sale_price') is not None:
                    # Only include properties with non-null sale price when filtering
                    price_mask = self.properties_df['lastSalePrice'].notna()
                    if kwargs.get('min_sale_price') is not None:
                        price_mask = price_mask & (self.properties_df['lastSalePrice'] >= kwargs['min_sale_price'])
                    if kwargs.get('max_sale_price') is not None:
                        price_mask = price_mask & (self.properties_df['lastSalePrice'] <= kwargs['max_sale_price'])
                    mask = mask & price_mask
                    print(f"[Property Filtering] After sale price filters: {mask.sum():,} properties")
            except Exception as e:
                print(f"Error in sale price filter: {str(e)}")
                raise
            
            try:
                # Numeric filters
                numeric_filters = [
                    ('min_beds', 'max_beds', 'beds'),
                    ('min_baths', 'max_baths', 'baths'),
                    ('min_sqft', 'max_sqft', 'buildingSize')
                ]
                
                for min_param, max_param, field in numeric_filters:
                    if ((kwargs.get(min_param) is not None or kwargs.get(max_param) is not None) and 
                        field in self.properties_df.columns):
                        # Only include properties with non-null values when filtering
                        num_mask = self.properties_df[field].notna()
                        if kwargs.get(min_param) is not None:
                            num_mask = num_mask & (self.properties_df[field] >= kwargs[min_param])
                        if kwargs.get(max_param) is not None:
                            num_mask = num_mask & (self.properties_df[field] <= kwargs[max_param])
                        mask = mask & num_mask
                        print(f"[Property Filtering] After {field} filters: {mask.sum():,} properties")
            except Exception as e:
                print(f"Error in numeric filters: {str(e)}")
                raise
            
            try:
                # List filters
                if kwargs.get('property_types') is not None and len(kwargs['property_types']) > 0:
                    # Only include properties with non-null and non-Unknown property types when filtering
                    type_mask = (
                        self.properties_df['propertyType'].notna() &
                        (self.properties_df['propertyType'] != 'Unknown') &
                        self.properties_df['propertyType'].isin(kwargs['property_types'])
                    )
                    mask = mask & type_mask
                    print(f"[Property Filtering] After property_types {kwargs['property_types']}: {mask.sum():,} properties")
            except Exception as e:
                print(f"Error in property types filter: {str(e)}")
                raise
            
            try:
                if kwargs.get('states') is not None and len(kwargs['states']) > 0:
                    state_mask = self.properties_df['state'].isin(kwargs['states'])
                    mask = mask & state_mask
                    print(f"[Property Filtering] After states {kwargs['states']}: {mask.sum():,} properties")
            except Exception as e:
                print(f"Error in states filter: {str(e)}")
                raise
            
            try:
                # Time between sale and permit filter
                if (kwargs.get('min_sale_to_permit_years') is not None or 
                    kwargs.get('max_sale_to_permit_years') is not None):
                    
                    # Create a mask for properties with valid time differences
                    time_mask = pd.Series(False, index=self.properties_df.index)
                    
                    # Get properties with permits and valid sale dates
                    valid_properties = set(self.property_permit_map.keys())
                    sale_dates = self.properties_df['lastSaleDate']
                    properties_with_sales = set(sale_dates[sale_dates.notna()].index)
                    valid_properties = valid_properties.intersection(properties_with_sales)
                    
                    # Calculate time differences for each property
                    for property_id in valid_properties:
                        sale_date = self.properties_df.loc[property_id, 'lastSaleDate']
                        property_valid = False
                        
                        for permit_id in self.property_permit_map[property_id]:
                            try:
                                permit_date = self.permits_df.at[permit_id, 'file_date']
                                if isinstance(permit_date, pd.Series):
                                    print(f"Warning: Multiple permit dates found for permit {permit_id}")
                                    continue
                                
                                if pd.isna(permit_date):
                                    continue
                                
                                time_diff = (permit_date - sale_date).days / 365.25
                                
                                # Check if time difference is within range
                                within_range = True
                                if kwargs.get('min_sale_to_permit_years') is not None:
                                    within_range = within_range and (time_diff >= kwargs['min_sale_to_permit_years'])
                                if kwargs.get('max_sale_to_permit_years') is not None:
                                    within_range = within_range and (time_diff <= kwargs['max_sale_to_permit_years'])
                                
                                if within_range:
                                    property_valid = True
                                    break
                            except Exception as e:
                                print(f"Warning: Error processing permit {permit_id} for property {property_id}: {str(e)}")
                                continue
                        
                        if property_valid:
                            time_mask.loc[property_id] = True
                    
                    mask = mask & time_mask
                    print(f"[Property Filtering] After sale-to-permit time filter: {mask.sum():,} properties")
            except Exception as e:
                print(f"Error in time between sale and permit filter: {str(e)}")
                raise
            
            filtered_df = self.properties_df[mask]
            print(f"[Property Filtering] Final property count: {len(filtered_df):,}")
            return filtered_df
            
        except Exception as e:
            import traceback
            print(f"Error in filter_properties: {str(e)}")
            print("Traceback:")
            print(traceback.format_exc())
            raise
    
    def filter_permits(self, **kwargs) -> pd.DataFrame:
        """Filter permits based on year criteria."""
        if self.permits_df is None:
            raise ValueError("Data not loaded. Call load_data() first.")
        
        total_permits = len(self.permits_df)
        print(f"\n[Permit Filtering] Starting with {total_permits:,} total permits")
        
        # Create a copy of the DataFrame at the start
        filtered_df = self.permits_df.copy()
        
        # Year filters with null handling
        if kwargs.get('min_permit_year'):
            year_mask = (filtered_df['file_date'].notna() & 
                        (filtered_df['file_date'].dt.year >= kwargs['min_permit_year']))
            filtered_df = filtered_df[year_mask]
            print(f"[Permit Filtering] After min_permit_year ({kwargs['min_permit_year']}): {len(filtered_df):,} permits")
        
        if kwargs.get('max_permit_year'):
            year_mask = (filtered_df['file_date'].notna() & 
                        (filtered_df['file_date'].dt.year <= kwargs['max_permit_year']))
            filtered_df = filtered_df[year_mask]
            print(f"[Permit Filtering] After max_permit_year ({kwargs['max_permit_year']}): {len(filtered_df):,} permits")
        
        print(f"[Permit Filtering] Final permit count: {len(filtered_df):,}")
        return filtered_df
    
    def build_audience(self, property_filters: Dict = None, permit_filters: Dict = None,
                      exclude_properties: List = None) -> Dict:
        """Build audience by applying property and permit filters."""
        if property_filters is None:
            property_filters = {}
        if permit_filters is None:
            permit_filters = {}
        if exclude_properties is None:
            exclude_properties = []
        
        print("\n[Build Audience] Starting audience build")
        print(f"[Build Audience] Property filters: {property_filters}")
        print(f"[Build Audience] Permit filters: {permit_filters}")
        print(f"[Build Audience] Excluded properties: {len(exclude_properties):,}")
        
        # Calculate total available properties first
        total_available = len(self.properties_df)
        available_properties = self.properties_df[~self.properties_df.index.isin(exclude_properties)].copy()
        print(f"[Build Audience] Total available properties: {len(available_properties):,}")
        
        # Apply property filters
        filtered_properties = self.filter_properties(**property_filters)
        
        # Remove excluded properties after filtering
        if exclude_properties:
            filtered_properties = filtered_properties[~filtered_properties.index.isin(exclude_properties)]
            print(f"[Build Audience] Properties after exclusion: {len(filtered_properties):,}")
        
        # Apply permit filters
        filtered_permits = self.filter_permits(**permit_filters)
        
        # Create property-permit mappings
        property_permit_map = {}
        permit_property_map = {}
        for state, file_path in self.matches_files.items():
            with open(file_path, 'r') as f:
                matches = json.load(f)
                for match in matches:
                    if 'property' in match and 'permit' in match:
                        property_id = match['property'].get('id')
                        permit_id = match['permit'].get('permit_id')
                        if property_id and permit_id:
                            if property_id not in property_permit_map:
                                property_permit_map[property_id] = []
                            property_permit_map[property_id].append(permit_id)
                            permit_property_map[permit_id] = property_id
        
        # Add property_id to filtered permits
        filtered_permits = filtered_permits.copy()
        filtered_permits.loc[:, 'property_id'] = filtered_permits.index.map(lambda x: permit_property_map.get(x))
        
        # Get properties with matching permits
        matching_property_ids = set()
        for permit_id in filtered_permits.index:
            property_id = permit_property_map.get(permit_id)
            if property_id:
                matching_property_ids.add(property_id)
        
        # Get final intersection of properties
        final_properties = filtered_properties[filtered_properties.index.isin(matching_property_ids)]
        print(f"[Build Audience] Properties with matching permits: {len(final_properties):,}")
        
        result = {
            'total_properties': len(available_properties),
            'matching_properties': len(filtered_properties),
            'matching_permits': len(filtered_permits),
            'final_matches': len(final_properties),
            'results': final_properties,
            'filtered_permits': filtered_permits
        }
        
        print("\n[Build Audience] Final results:")
        print(f"- Total available properties: {result['total_properties']:,}")
        print(f"- Properties matching filters: {result['matching_properties']:,}")
        print(f"- Permits matching filters: {result['matching_permits']:,}")
        print(f"- Final matched properties: {result['final_matches']:,}")
        
        return result
    
    def get_safe_year(self, series: pd.Series, default: int) -> int:
        """Safely get a year value from a datetime series, handling empty or all-null cases."""
        if series is None:
            return default
        if len(series) == 0 or series.isna().all():
            return default
        return int(series.dt.year.min())

    def get_safe_max_year(self, series: pd.Series, default: int) -> int:
        """Safely get a maximum year value from a datetime series, handling empty or all-null cases."""
        if series is None:
            return default
        if len(series) == 0 or series.isna().all():
            return default
        return int(series.dt.year.max())

    def get_safe_numeric_value(self, series: pd.Series, default: float) -> float:
        """Safely get a numeric value from a series, handling empty or all-null cases."""
        if series is None:
            return default
        clean_series = pd.to_numeric(series, errors='coerce')
        if len(clean_series) == 0 or clean_series.isna().all():
            return default
        return float(clean_series.min())
    
    def get_safe_max_value(self, series: pd.Series, default: float) -> float:
        """Safely get a maximum numeric value from a series, handling empty or all-null cases."""
        if series is None:
            return default
        clean_series = pd.to_numeric(series, errors='coerce')
        if len(clean_series) == 0 or clean_series.isna().all():
            return default
        return float(clean_series.max())
    
    def get_column_if_exists(self, column_name: str) -> pd.Series:
        """Safely get a column from properties_df, returning None if it doesn't exist."""
        return self.properties_df[column_name] if column_name in self.properties_df.columns else None