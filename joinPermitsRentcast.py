import pandas as pd
import json
import os
from typing import Dict, List
from multiprocessing import Pool, cpu_count
import numpy as np
from functools import partial
from multiprocessing import Manager

def normalize_address_without_city(street_no: str, street: str, zip_code: str) -> str:
    """Create a normalized address string without city for finding duplicates."""
    return f"{str(street_no).lower()} {str(street).lower()} {str(zip_code)}"

def normalize_address(street_no: str, street: str, city: str, zip_code: str) -> str:
    """Create a normalized address string for comparison with permits."""
    return f"{str(street_no).lower()} {str(street).lower()} {str(city).lower()} {str(zip_code)}"

def is_apartment(prop: Dict) -> bool:
    """Check if a property is an apartment based on multiple criteria."""
    # Check propertyType
    if prop.get('propertyType') == 'Apartment':
        return True
        
    # Check addressLine2 for apartment indicators
    addr_line2 = str(prop.get('addressLine2', ''))  # Convert to string to handle None
    if addr_line2:
        apartment_indicators = ['apt', 'suite', 'ste', 'unit', '#', 'floor', 'fl']
        return any(indicator in addr_line2.lower() for indicator in apartment_indicators)
        
    return False

def process_batch(batch: List[Dict], permits_df: pd.DataFrame) -> List[Dict]:
    """Process a batch of properties and find matches in permits."""
    matches = []
    
    for prop in batch:
        # Skip apartments
        if is_apartment(prop):
            continue
            
        # Extract address components from the direct fields
        address_line1 = prop.get('addressLine1', '')
        if not address_line1:
            continue
        
        # Try to split address line 1 into number and street
        parts = address_line1.strip().split(' ', 1)
        if len(parts) != 2 or not parts[0].isdigit():
            continue
            
        street_no = parts[0]
        street = parts[1]
        city = prop.get('city', '')
        zip_code = prop.get('zipCode', '')
        
        if not (street_no and street and city and zip_code):
            continue
        
        # Create normalized address for comparison
        norm_addr = normalize_address(street_no, street, city, zip_code)
        
        # Look for matches in permits
        permit_matches = permits_df[permits_df['normalized_address'] == norm_addr]
        
        if not permit_matches.empty:
            for _, permit in permit_matches.iterrows():
                matches.append({
                    'property': prop,
                    'permit': permit.to_dict()
                })
    
    return matches

def process_data(state: str):
    """Process permits and property data for a given state."""
    # Read the permits CSV
    print(f"Reading permits.csv...")
    permits_df = pd.read_csv('permits.csv', low_memory=False)
    
    # Filter permits for the specific state
    permits_df = permits_df[permits_df['state'] == state]
    
    # Create normalized addresses for permits
    print("Creating normalized addresses for permits...")
    permits_df['normalized_address'] = permits_df.apply(
        lambda x: normalize_address(x['street_no'], x['street'], x['city'], x['zip_code']), 
        axis=1
    )
    
    # Read the JSON file
    json_file = f"{state}/{state}_merged.json"
    print(f"Reading {json_file}...")
    with open(json_file, 'r') as f:
        properties = json.load(f)
    
    # Group properties by normalized address without city
    print("Identifying duplicate addresses...")
    property_groups = {}
    for prop in properties:
        if is_apartment(prop):
            continue
            
        address_line1 = prop.get('addressLine1', '')
        if not address_line1:
            continue
        
        parts = address_line1.strip().split(' ', 1)
        if len(parts) != 2 or not parts[0].isdigit():
            continue
            
        street_no = parts[0]
        street = parts[1]
        city = prop.get('city', '')
        zip_code = prop.get('zipCode', '')
        
        if not (street_no and street and city and zip_code):
            continue
        
        # Group by address without city
        norm_addr_no_city = normalize_address_without_city(street_no, street, zip_code)
        if norm_addr_no_city not in property_groups:
            property_groups[norm_addr_no_city] = []
        property_groups[norm_addr_no_city].append(prop)
    
    # Process each group to find the best match
    print("Processing property groups...")
    unique_properties = []
    for addr_group in property_groups.values():
        if len(addr_group) == 1:
            # No duplicates, add the property as is
            unique_properties.append(addr_group[0])
        else:
            # Try to find which address variation has a permit match
            found_match = False
            for prop in addr_group:
                street_no = prop['addressLine1'].strip().split(' ', 1)[0]
                street = prop['addressLine1'].strip().split(' ', 1)[1]
                city = prop.get('city', '')
                zip_code = prop.get('zipCode', '')
                
                norm_addr = normalize_address(street_no, street, city, zip_code)
                if permits_df['normalized_address'].eq(norm_addr).any():
                    unique_properties.append(prop)
                    found_match = True
                    break
            
            # If no variation has a permit match, use the first one
            if not found_match:
                unique_properties.append(addr_group[0])
    
    print(f"Reduced {len(properties)} properties to {len(unique_properties)} unique addresses")
    
    # Now process the unique properties in batches
    total_properties = len(unique_properties)
    apartment_count = sum(1 for prop in unique_properties if is_apartment(prop))
    print(f"Processing {total_properties - apartment_count} non-apartment properties...")
    
    # Calculate optimal batch size and number of processes
    num_processes = cpu_count() - 1  # Leave one CPU free
    batch_size = 1000
    num_batches = (len(unique_properties) + batch_size - 1) // batch_size
    
    # Split properties into batches
    batches = [
        unique_properties[i * batch_size:(i + 1) * batch_size]
        for i in range(num_batches)
    ]
    
    # Create a partial function with the permits_df argument fixed
    process_batch_with_permits = partial(process_batch, permits_df=permits_df)
    
    # Process batches in parallel
    print(f"Using {num_processes} processes...")
    with Pool(processes=num_processes) as pool:
        batch_results = []
        for i, batch_matches in enumerate(pool.imap_unordered(process_batch_with_permits, batches)):
            batch_results.extend(batch_matches)
            if (i + 1) % 10 == 0:
                print(f"Processed {(i + 1) * batch_size} properties...")
    
    # Save matches to a file
    output_file = f"{state}_matches.json"
    print(f"Saving {len(batch_results)} matches to {output_file}...")
    with open(output_file, 'w') as f:
        json.dump(batch_results, f, indent=2)

def main():
    # Process both states
    for state in ['VA']:
        if os.path.exists(f"{state}/{state}_merged.json"):
            print(f"\nProcessing {state}...")
            process_data(state)
        else:
            print(f"Skipping {state}: file not found")

if __name__ == "__main__":
    main() 