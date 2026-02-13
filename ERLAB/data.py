import os
import glob
import pandas as pd
import xarray as xr
import numpy as np

def load_ses_spectra(directory_path, file_pattern="S313_MgB2_*.txt"):
    """
    Loads and combines multiple ARPES spectra files from a specified directory
    into a single xarray dataset with correct physical coordinates.

    Args:
        directory_path (str): The path to the directory containing the data files.
        file_pattern (str): The file pattern to match (e.g., "S313_MgB2_*.txt").

    Returns:
        xarray.DataArray: A single DataArray containing the combined ARPES data,
                          with coordinates labeled 'energy', 'kx', and 'ky'.
    """
    file_list = sorted(glob.glob(os.path.join(directory_path, file_pattern)))

    if not file_list:
        raise FileNotFoundError(f"No files found in the directory: {directory_path} with pattern {file_pattern}")

    datasets = []
    
    for file_path in file_list:
        with open(file_path, 'r') as f:
            lines = f.readlines()
        
        data_start_line = None
        angle_value = None
        for i, line in enumerate(lines):
            # Find the line where the [Data] section begins
            if "[Data]" in line:
                data_start_line = i + 1
                
                # We know the angle value is 3 lines before the [Data] line.
                # Use a more robust check to find the correct line with a float value.
                try:
                    angle_value = float(lines[i - 3].strip())
                except (ValueError, IndexError):
                    # If parsing fails, fall back to the next line which also contains a float value
                    try:
                        angle_value = float(lines[i - 4].strip())
                    except (ValueError, IndexError):
                        print(f"Warning: Could not parse angle in {os.path.basename(file_path)}. Skipping.")
                        angle_value = None
                break
        
        if data_start_line is None or angle_value is None:
            continue

        df = pd.read_csv(file_path, sep='\t', header=None, skiprows=data_start_line)
        
        data_array = xr.DataArray(
            data=df.iloc[:, 1:],
            dims=('energy', 'y_pixel'),
            coords={
                'energy': df.iloc[:, 0],
                'angle': angle_value,
            }
        ).expand_dims('angle')
        
        datasets.append(data_array)

    if not datasets:
        raise ValueError("No valid datasets were created. Check file format.")

    combined_data = xr.concat(datasets, dim='angle', join='outer')
    
    combined_data = combined_data.rename({'angle': 'kx'})
    
    first_pixel_momentum = -1.0 # REPLACE THIS WITH YOUR REAL VALUE
    last_pixel_momentum = 1.0   # REPLACE THIS WITH YOUR REAL VALUE
    
    ky_values = np.linspace(first_pixel_momentum, last_pixel_momentum, combined_data.sizes['y_pixel'])
    combined_data = combined_data.assign_coords(ky=('y_pixel', ky_values))
    
    return combined_data

# Example of how to use your new function:
if __name__ == '__main__':
    data_folder = "C:/Users/mdram/SolidStatePhysics1/dataverse_files"
    
    try:
        arpes_data = load_ses_spectra(data_folder)
        print("Successfully created the combined ARPES dataset:")
        print(arpes_data)

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")