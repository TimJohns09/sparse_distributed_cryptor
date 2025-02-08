import random

class SDM:
    def __init__(self, p, block_size_bytes):
        """
        p: number of hard locations (addresses)
        block_size_bytes: number of bytes in each data block
        """
        self.p = p
        self.block_size_bytes = block_size_bytes
        self.bits_per_byte = 8
        self.pattern_length = block_size_bytes * self.bits_per_byte  # e.g., 32 bytes * 8 bits = 256 bits

        # Generate deterministic addresses (each a binary vector of length pattern_length)
        self.addresses = [self._generate_deterministic_address(i) for i in range(p)]

        # Initialize the SDM counters.
        self.data = [[0]*self.pattern_length for _ in range(p)]

        # Set the Hamming radius (e.g., 30% of the pattern length)
        self.radius = int(0.1 * self.pattern_length)

    def _generate_deterministic_address(self, index):
        random.seed(index)
        return [random.randint(0, 1) for _ in range(self.pattern_length)]

    def hamming_distance(self, a, b):
        return sum(x != y for x, y in zip(a, b))

    def enter(self, addressVector, pattern):
        """
        Enter a binary pattern (list of 0/1) into the SDM.
        For each hard location within radius of addressVector, increment counters where pattern bit=1,
        and decrement counters where pattern bit=0.
        """
        for i, stored_addr in enumerate(self.addresses):
            if self.hamming_distance(addressVector, stored_addr) <= self.radius:
                for bit_index, bit_val in enumerate(pattern):
                    if bit_val == 1:
                        self.data[i][bit_index] += 1
                    else:
                        self.data[i][bit_index] -= 1

    def retrieve(self, addressVector):
        """
        Retrieve a pattern from the SDM given an addressVector.
        Find all addresses within radius, sum their counters bit-by-bit,
        and threshold to produce a reconstructed pattern.
        """
        sum_counters = [0]*self.pattern_length
        for i, stored_addr in enumerate(self.addresses):
            if self.hamming_distance(addressVector, stored_addr) <= self.radius:
                for bit_index in range(self.pattern_length):
                    sum_counters[bit_index] += self.data[i][bit_index]

        # Threshold: if sum of counters for a bit is > 0, bit=1; else bit=0
        reconstructed = [1 if x > 0 else 0 for x in sum_counters]
        return reconstructed

def file_to_byte_blocks(file_path, block_size_bytes):
    """
    Read the file in binary mode and split it into blocks of size block_size_bytes.
    Returns a list of byte strings (each block_size_bytes long, except possibly the last one).
    """
    with open(file_path, 'rb') as f:
        file_bytes = f.read()

    # Split into fixed-size byte blocks
    return [file_bytes[i:i+block_size_bytes] for i in range(0, len(file_bytes), block_size_bytes)]

def byte_blocks_to_file(blocks, output_path):
    """
    Write the list of byte blocks back into a binary file.
    """
    with open(output_path, 'wb') as f:
        for block in blocks:
            f.write(block)

def bytes_to_bits(byte_block):
    """
    Convert a block of bytes into a list of bits (0/1).
    block_size_bytes * 8 = total bits.
    """
    bits = []
    for byte in byte_block:
        for i in range(8):
            bit = (byte >> (7 - i)) & 1
            bits.append(bit)
    return bits

def bits_to_bytes(bits):
    """
    Convert a list of bits (0/1) into a bytes object.
    len(bits) should be a multiple of 8.
    """
    byte_array = bytearray()
    for i in range(0, len(bits), 8):
        byte_val = 0
        for j in range(8):
            byte_val = (byte_val << 1) | bits[i+j]
        byte_array.append(byte_val)
    return bytes(byte_array)

def main():
    # Example usage: store and then reconstruct "malware.txt"
    # Change this to your desired file.
    files = ["malware.txt"]  
    block_size_bytes = 32  # Size of each block in bytes
    p = 10000  # number of addresses

    # Initialize the SDM
    sdm = SDM(p=p, block_size_bytes=block_size_bytes)

    keys = []
    file_names = []

    # Store each file
    for file in files:
        byte_blocks = file_to_byte_blocks(file, block_size_bytes)

        # Create a random address vector (key) for each block
        address_vectors = []
        for _ in byte_blocks:
            addr_vec = [random.randint(0, 1) for _ in range(sdm.pattern_length)]
            address_vectors.append(addr_vec)

        keys.append(address_vectors)
        file_names.append(file)

        print(f"Storing file: {file}")

        # Store each block in the SDM
        for byte_block, addr_vec in zip(byte_blocks, address_vectors):
            pattern = bytes_to_bits(byte_block)
            sdm.enter(addr_vec, pattern)

    # Reconstruct the first file as an example
    if files:
        print("Reconstructing file from SDM...")
        reconstructed_blocks = []
        for addr_vec in keys[0]:
            pattern = sdm.retrieve(addr_vec)
            block_bytes = bits_to_bytes(pattern)
            reconstructed_blocks.append(block_bytes)

        byte_blocks_to_file(reconstructed_blocks, "reconstructed.bin")
        print("File successfully reconstructed as 'reconstructed.bin'.")

if __name__ == "__main__":
    main()
