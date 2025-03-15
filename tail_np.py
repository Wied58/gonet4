import subprocess
import numpy as np

def is_saturated(file_path):

    num_bytes = 18711040

    # Execute the 'tail' command to get the last 'num_bytes' of the file
    result = subprocess.run(
        ['tail', '-c', str(num_bytes), file_path],
        capture_output=True,
        check=True
    )
    
    # Capture the output bytes
    output_bytes = result.stdout
    
    # Convert the bytes to a NumPy array
    array = np.frombuffer(output_bytes, dtype=np.uint8)
    
    # Step 1: Create a boolean mask where elements > 4095 are True
    mask = array > 4095
     
    # Step 2: Count the number of True values in the mask
    count = np.count_nonzero(mask)
     
    # Step 3: Check if the count exceeds 100
    if count > 100:
        print("More than 100 elements are greater than 4095.")
    else:
        print("100 or fewer elements are greater than 4095.")


# Example usage:
# Assuming 'example.bin' is the file and we want the last 18711040 bytes
file_path = '249_250315_154645_1742053607.jpg'
#array = tail_to_numpy(file_path)
is_saturated(file_path)
#print(array)


