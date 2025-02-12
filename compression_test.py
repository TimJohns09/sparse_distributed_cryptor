import random
import base64

def hamming_distance(a, b):
    """Calculate the Hamming distance between two binary vectors."""
    return sum(x != y for x, y in zip(a, b))

def file_to_binary(file_path):
    """Convert a file to a binary list."""
    with open(file_path, 'rb') as f:
        byte_data = f.read()
    binary_array = []
    for byte in byte_data:
        binary_array.extend([(byte >> i) & 1 for i in range(7, -1, -1)])
    return binary_array

def binary_to_file(binary_array, output_path):
    """Convert a binary list back into a file."""
    byte_data = bytearray()
    for i in range(0, len(binary_array), 8):
        byte = 0
        for bit in binary_array[i:i+8]:
            byte = (byte << 1) | bit
        byte_data.append(byte)
    with open(output_path, 'wb') as f:
        f.write(byte_data)

class SDM:
    def __init__(self, p, n, seed=42):
        self.p = p  # Number of random addresses (keys)
        self.n = n  # Length of each binary vector
        random.seed(seed)  # Set deterministic seed
        self.keys = [[random.randint(0, 1) for _ in range(n)] for _ in range(p)]
        self.data = [[0 for _ in range(n)] for _ in range(p)]
        self.radius = int(0.451 * n)  # Hamming distance threshold

    def enter(self, key_vector, data_vector):
        """Store the data vector in the SDM using the key vector."""
        for i in range(len(self.keys)):
            hdist = hamming_distance(self.keys[i], key_vector)
            if hdist <= self.radius:
                for j in range(len(data_vector)):
                    if data_vector[j] == 1:
                        self.data[i][j] += 1
                    else:
                        self.data[i][j] -= 1

    def lookup(self, key_vector):
        """Retrieve a data vector from the SDM using the key vector."""
        retrieved_data = [0] * len(key_vector)
        for i in range(len(self.keys)):
            hdist = hamming_distance(self.keys[i], key_vector)
            if hdist <= self.radius:
                for j in range(len(key_vector)):
                    retrieved_data[j] += self.data[i][j]
        return [1 if x > 0 else 0 for x in retrieved_data]

def chunk_binary_data(binary_data, chunk_size):
    """Divide binary data into chunks of a specified size."""
    chunks = [binary_data[i * chunk_size:(i + 1) * chunk_size] 
              for i in range(len(binary_data) // chunk_size)]

    # Handle leftover bits by padding with zeros
    remainder = len(binary_data) % chunk_size
    if remainder > 0:
        last_chunk = binary_data[-remainder:] + [0] * (chunk_size - remainder)
        chunks.append(last_chunk)

    return chunks

def generate_key_vectors(num_keys, n, seed=42):
    """Generate a list of random key vectors."""
    random.seed(seed)
    return [[random.randint(0, 1) for _ in range(n)] for _ in range(num_keys)]

def run_length_encode_packed(bits):
    """
    Encode a list of bits or integers using Run-Length Encoding (RLE),
    ensuring that counts do not exceed 255.
    Returns a flat list of counts and values: [count1, value1, count2, value2, ...]
    """
    if not bits:
        return []
    encoded = []
    current_val = bits[0]
    count = 1
    for val in bits[1:]:
        if val == current_val:
            if count < 255:
                count += 1
            else:
                encoded.extend([count, current_val])
                count = 1
        else:
            encoded.extend([count, current_val])
            current_val = val
            count = 1
    encoded.extend([count, current_val])
    return encoded

def run_length_decode_packed(encoded):
    """
    Decode a Run-Length Encoded (RLE) list back to the original list.
    Expects a flat list of counts and values: [count1, value1, count2, value2, ...]
    """
    decoded = []
    if len(encoded) % 2 != 0:
        raise ValueError("Encoded RLE data should have an even number of elements (count, value pairs).")
    for i in range(0, len(encoded), 2):
        count, val = encoded[i], encoded[i+1]
        if not (0 <= val <= 1):
            raise ValueError(f"Invalid value in RLE data: {val}. Expected 0 or 1.")
        decoded.extend([val] * count)
    return decoded

def save_loader_file_no_dependencies(sdm, files_info, chunk_size, output_file):
    """
    Save a loader file containing the SDM's keys (RLE-encoded), data (serialized as signed bytes),
    and a mapping of files to their chunk_keys, all Base64-encoded, along with necessary functions
    and the SDM class.
    """
    with open(output_file, 'w') as f:
        # Write core functions
        f.write("import base64\n\n")
        f.write("def hamming_distance(a, b):\n")
        f.write("    return sum(x != y for x, y in zip(a, b))\n\n")
        
        f.write("def binary_to_file(binary_array, output_path):\n")
        f.write("    byte_data = bytearray()\n")
        f.write("    for i in range(0, len(binary_array), 8):\n")
        f.write("        byte = 0\n")
        f.write("        for bit in binary_array[i:i+8]:\n")
        f.write("            byte = (byte << 1) | bit\n")
        f.write("        byte_data.append(byte)\n")
        f.write("    with open(output_path, 'wb') as f:\n")
        f.write("        f.write(byte_data)\n\n")
        
        # RLE encode SDM keys
        rle_keys = [run_length_encode_packed(key) for key in sdm.keys]
        # Flatten the list of lists into single list
        keys_flat = []
        for rle_key in rle_keys:
            keys_flat.extend(rle_key)
        # Validate all elements are in range(0-255)
        for byte in keys_flat:
            if not (0 <= byte <= 255):
                raise ValueError(f"Value {byte} in keys_flat is out of byte range (0-255).")
        # Convert list of integers to bytes
        keys_bytes = bytes(keys_flat)
        # Base64 encode the bytes
        keys_base64 = base64.b64encode(keys_bytes).decode('utf-8')
        
        # Serialize sdm.data as signed bytes
        flat_data = []
        for data_vector in sdm.data:
            for val in data_vector:
                if val < -128 or val > 127:
                    raise ValueError(f"Vote count {val} is out of range (-128 to 127).")
                if val < 0:
                    flat_data.append(val + 256)  # Convert to two's complement
                else:
                    flat_data.append(val)
        data_bytes = bytes(flat_data)
        data_base64 = base64.b64encode(data_bytes).decode('utf-8')
        
        # Prepare files_info dict for loader script
        # files_info = { 'file_name': { 'chunk_keys': [encoded_key1, encoded_key2, ...], 'original_length': int }, ... }
        serialized_files_info = {}
        for file_name, info in files_info.items():
            serialized_files_info[file_name] = {
                'chunk_keys': info['chunk_keys'],
                'original_length': info['original_length']
            }
        
        # Write the encoded data as variables in the loader script
        f.write(f"keys = '{keys_base64}'\n")
        f.write(f"data = '{data_base64}'\n")
        f.write(f"radius = {sdm.radius}\n")
        f.write(f"chunk_size = {chunk_size}\n\n")
        
        # Write the files_info dict
        f.write("files = {\n")
        for file_name, info in serialized_files_info.items():
            # Convert file_name to a string literal
            # Convert list of chunk_keys to a list of string literals
            chunk_keys_str = ', '.join([f"'{ck}'" for ck in info['chunk_keys']])
            f.write(f"    '{file_name}': {{\n")
            f.write(f"        'chunk_keys': [{chunk_keys_str}],\n")
            f.write(f"        'original_length': {info['original_length']}\n")
            f.write("    },\n")
        f.write("}\n\n")
        
        # SDM class in the loader
        f.write("class SDM:\n")
        f.write("    def __init__(self, keys, data, radius):\n")
        f.write("        self.keys = keys            # list of key vectors\n")
        f.write("        self.data = data            # list of lists of vote counts\n")
        f.write("        self.radius = radius\n\n")
        f.write("    def lookup(self, key_vector):\n")
        f.write("        retrieved_data = [0] * len(key_vector)\n")
        f.write("        for i, key in enumerate(self.keys):\n")
        f.write("            hdist = hamming_distance(key, key_vector)\n")
        f.write("            if hdist <= self.radius:\n")
        f.write("                for j, val in enumerate(self.data[i]):\n")
        f.write("                    retrieved_data[j] += val\n")
        f.write("        return [1 if x > 0 else 0 for x in retrieved_data]\n\n")
        
        # Decoding functions
        f.write("def run_length_decode_packed(encoded):\n")
        f.write("    decoded = []\n")
        f.write("    if len(encoded) % 2 != 0:\n")
        f.write("        raise ValueError(\"Encoded RLE data should have an even number of elements (count, value pairs).\")\n")
        f.write("    for i in range(0, len(encoded), 2):\n")
        f.write("        count, val = encoded[i], encoded[i+1]\n")
        f.write("        if not (0 <= val <= 1):\n")
        f.write("            raise ValueError(f\"Invalid value in RLE data: {val}. Expected 0 or 1.\")\n")
        f.write("        decoded.extend([val] * count)\n")
        f.write("    return decoded\n\n")
        
        # Function to load RLE-encoded keys
        f.write("def load_keys(encoded_keys):\n")
        f.write("    keys_bytes = base64.b64decode(encoded_keys)\n")
        f.write("    keys_list = list(keys_bytes)\n")
        f.write("    decoded_bits = run_length_decode_packed(keys_list)\n")
        f.write("    # Split into individual key vectors\n")
        f.write("    keys = [decoded_bits[i:i+chunk_size] for i in range(0, len(decoded_bits), chunk_size)]\n")
        f.write("    return keys\n\n")
        
        # Function to load signed data
        f.write("def load_data(encoded_data):\n")
        f.write("    data_bytes = base64.b64decode(encoded_data)\n")
        f.write("    data_list = list(data_bytes)\n")
        f.write("    # Convert unsigned bytes back to signed integers\n")
        f.write("    decoded_data = [byte - 256 if byte > 127 else byte for byte in data_list]\n")
        f.write("    # Split into individual data vectors\n")
        f.write("    data = [decoded_data[i:i+chunk_size] for i in range(0, len(decoded_data), chunk_size)]\n")
        f.write("    return data\n\n")
        
        # Function to load and reconstruct a file
        f.write("def reconstruct_file(sdm, chunk_keys, original_length, chunk_size, output_file_name):\n")
        f.write("    binary_data = []\n")
        f.write("    for encoded_ck in chunk_keys:\n")
        f.write("        # Decode Base64 chunk key\n")
        f.write("        decoded_ck_bytes = base64.b64decode(encoded_ck)\n")
        f.write("        ck_list = list(decoded_ck_bytes)\n")
        f.write("        # Decode RLE to get key_vector\n")
        f.write("        key_vector = run_length_decode_packed(ck_list)\n")
        f.write("        # Perform lookup to get chunk_data\n")
        f.write("        reconstructed = sdm.lookup(key_vector)\n")
        f.write("        binary_data.extend(reconstructed)\n")
        f.write("    # Trim to original file length\n")
        f.write("    binary_data = binary_data[:original_length]\n")
        f.write("    # Write to output file\n")
        f.write("    binary_to_file(binary_data, output_file_name)\n\n")
        
        # Main reconstruction logic
        f.write("if __name__ == '__main__':\n")
        f.write("    # Load and decode SDM keys\n")
        f.write("    sdm_keys = load_keys(keys)\n")
        f.write("    # Load and decode SDM data\n")
        f.write("    sdm_data = load_data(data)\n")
        f.write("    # Initialize SDM with keys, data, and radius\n")
        f.write("    sdm = SDM(sdm_keys, sdm_data, radius)\n\n")
        f.write("    # List available files\n")
        f.write("    file_names = list(files.keys())\n")
        f.write("    if not file_names:\n")
        f.write("        print(\"No files available for reconstruction.\")\n")
        f.write("        exit()\n\n")
        f.write("    print(\"Available files for reconstruction:\")\n")
        f.write("    for idx, name in enumerate(file_names, 1):\n")
        f.write("        print(f\"{idx}. {name}\")\n\n")
        f.write("    # Prompt user to select a file\n")
        f.write("    while True:\n")
        f.write("        try:\n")
        f.write("            choice = int(input(\"Enter the number of the file to reconstruct: \"))\n")
        f.write("            if 1 <= choice <= len(file_names):\n")
        f.write("                selected_file = file_names[choice - 1]\n")
        f.write("                break\n")
        f.write("            else:\n")
        f.write("                print(\"Invalid choice. Please enter a valid number.\")\n")
        f.write("        except ValueError:\n")
        f.write("            print(\"Invalid input. Please enter a number.\")\n\n")
        f.write("    # Get file info\n")
        f.write("    file_info = files[selected_file]\n")
        f.write("    chunk_keys = file_info['chunk_keys']\n")
        f.write("    original_length = file_info['original_length']\n\n")
        f.write("    # Reconstruct the file\n")
        f.write("    reconstruct_file(sdm, chunk_keys, original_length, chunk_size, f\"reconstructed_{selected_file}\")\n")
        f.write("    print(f\"File '{selected_file}' has been reconstructed as 'reconstructed_{selected_file}'.\")\n")

def main(file_paths, output_loader_script='sdm_loader_no_deps.py', p=2000, chunk_size=512):
    """
    Main function to process multiple input files, store their data in SDM,
    and generate a loader script for reconstruction.
    
    Parameters:
        file_paths (list): List of input file paths to be processed.
        output_loader_script (str): Name of the loader script to be generated.
        p (int): Number of random addresses (keys) in SDM.
        chunk_size (int): Size of each binary chunk.
    """
    # Initialize the SDM
    sdm = SDM(p, chunk_size)
    
    # Initialize files_info dict
    # files_info = { 'file_name': { 'chunk_keys': [encoded_key1, encoded_key2, ...], 'original_length': int }, ... }
    files_info = {}
    
    for file_path in file_paths:
        try:
            # Extract file name from path
            file_name = file_path.split('/')[-1]
            
            # Convert file to binary
            binary_data = file_to_binary(file_path)
            original_length = len(binary_data)
            
            # Chunk binary data
            chunks = chunk_binary_data(binary_data, chunk_size)
            
            # Generate chunk keys
            chunk_keys = generate_key_vectors(len(chunks), chunk_size)
            
            # Store each chunk in SDM
            for key, chunk in zip(chunk_keys, chunks):
                sdm.enter(key, chunk)
            
            # Encode chunk_keys using RLE and Base64
            encoded_chunk_keys = []
            for key in chunk_keys:
                # RLE encode
                rle_encoded = run_length_encode_packed(key)
                # Convert to bytes
                rle_bytes = bytes(rle_encoded)
                # Base64 encode
                rle_base64 = base64.b64encode(rle_bytes).decode('utf-8')
                encoded_chunk_keys.append(rle_base64)
            
            # Add to files_info
            files_info[file_name] = {
                'chunk_keys': encoded_chunk_keys,
                'original_length': original_length
            }
            
            print(f"Processed and stored file: {file_name}")
        
        except FileNotFoundError:
            print(f"File not found: {file_path}. Skipping.")
        except Exception as e:
            print(f"Error processing file {file_path}: {e}. Skipping.")
    
    if not files_info:
        print("No files were processed. Exiting without creating loader script.")
        return
    
    # Save the loader script
    try:
        save_loader_file_no_dependencies(
            sdm,
            files_info,
            chunk_size,
            output_loader_script
        )
        print(f"Loader script '{output_loader_script}' has been created.")
    except Exception as e:
        print(f"Error creating loader script: {e}")

if __name__ == "__main__":
    # List of input files to be processed
    input_files = [
        "test_text2bin.txt",  # Replace with your actual file paths
        "test_text2bin2.txt",
        # Add more files as needed
    ]
    
    # Output loader script name
    output_loader_script = "sdm_loader_no_deps.py"
    
    # Run the main function
    main(input_files, output_loader_script)
