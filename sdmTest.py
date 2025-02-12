"""
Class that impliments the Sparse Distributed Memory 
algorithm as a proof of concept.

Author: Tim Johns
Last Modified: 10/24/24
"""
import numpy as np


class SDM:

    def __init__(self, p, n):
        """
        Constructor that initializes the SDM with random addresses and zeroed data storage.
        """
        # Initialize the number of addresses:
        self.p = p
        # Initialize the length of addresses dynamically:
        self.n = n
        # Initialize array of random addresses:
        self.addresses = np.random.randint(0, 2, (p, n))
        # Initialize array of data storage with zeros:
        self.data = np.zeros((p, n))
        # Initialize value for the radius:
        self.radius = 0.451 * n

    def enter(self, addressVector):
        """
        This method 'enters' the info in an address vector into the sdm's data array
        by finding all the addresses within the radius of the given address vector, and then writing 
        the given address's info to the physical address's data by adding or subtracting 1
        based on the value in the addressVector.
        """
        #Loop through the sdm's array of addresses:
        for i in range(self.p):

            #Compute the Hamming distance between the address vector and the current physical address:
            hdist = hamming_distance(self.addresses[i], addressVector)

            #Check if the Hamming distance is within the radius:
            if hdist <= self.radius:
                #Update the data vector at this physical address by looping through its bits:
                for j in range(self.n):
                    if addressVector[j] == 1:
                        #If the bit in the address vector is 1, add 1 to the data vector:
                        self.data[i][j] += 1
                    else:
                        #If the bit in the address vector is 0, subtract 1 from the data vector:
                        self.data[i][j] -= 1


    def lookup(self, addressVector):
        """
        This method 'looks up' the information stored in the data vector
        of the sdm finding all the addresses within the neighborhood of the
        given address vector, and then adding each bit in the data to the retrieved data vector.
        The information stored in that retrieved vector is then converted to 
        ones and zeros for output.
        """
        #Initialze array of 0s for retrieved data:
        retrieved_data = np.zeros(self.n)

        #Loop through the addresses:
        for i in range(self.p):

            #Compute the Hamming distance between the address vector and the current physical address:
            hdist = hamming_distance(self.addresses[i], addressVector)

            #Check if the Hamming distance is within the radius:
            if hdist <= self.radius:
                #If within the neighborhood, add the data at the current address to our retrieved data vector:
                for j in range(self.n):
                    retrieved_data[j] += self.data[i][j]

        #Convert the retrieved data to ones and zeros:
        for j in range(self.n):
            #If positive set to 1
            if retrieved_data[j] >= 0:
                retrieved_data[j] = 1
            #If negative set to zero:
            else:
                retrieved_data[j] = 0

        return retrieved_data
    

    def learn(self, iterations, probability):
        """
        This method enters a specified number of noisy rings into
        the sdm. Each ring is as noisy as is specified by the
        probability parameter.
        """
        #Enter a pattern for each desired iteration:
        for x in range(iterations):
            #Get a noisy ring:
            data = noisy_copy(ring(), probability)
            plot(data, 16)
            print()
            #Enter the ring into the sdm:
            self.enter(data)


#-----------------------FUNCTIONS-----------------------

def hamming_distance(vector1, vector2):
    """
    Function that computes the Hamming distance.
    """
    #Initialize the distance:
    distance = 0
    #Loop through the vectors:
    for i in range(len(vector1)):
        #Add 1 to the hamming distance where the vectors are not the same:
        if vector1[i] != vector2[i]:
            distance += 1
    return distance

#-------------------------------------------------------

def file2NPArray(file_path):
    """
    Converts the content of a file to a binary string.
    
    Parameters:
        file_path (str): The path to the file to be converted.
    
    Returns:
        str: A binary string representing the file's content.
    """
    with open(file_path, 'rb') as file:
        # Read the file content as bytes
        file_bytes = file.read()
        # Convert each byte to its binary representation and join them as a string
        binary_string = ''.join(format(byte, '08b') for byte in file_bytes)
    return np.array([int(bit) for bit in binary_string])

#-------------------------------------------------------

def Array2File(np_array, output_path):
    """
    Converts a NumPy array of binary data back into a file.
    
    Parameters:
        np_array (numpy.ndarray): A NumPy array containing binary data (0s and 1s).
        output_path (str): The path where the file will be saved.
    """
    # Ensure the array contains only 0s and 1s
    np_array = np.round(np_array).astype(int)
    
    # Convert the NumPy array back into a binary string
    binary_string = ''.join(map(str, np_array))
    
    # Convert the binary string into bytes (in chunks of 8 bits)
    byte_data = bytearray()
    for i in range(0, len(binary_string), 8):
        byte = binary_string[i:i+8]
        
        # Ensure the byte is exactly 8 bits, if it's not, pad it with leading zeros
        byte = byte.zfill(8)
        
        byte_data.append(int(byte, 2))  # Convert to integer and append to byte_data
    
    # Write the byte data to a file
    with open(output_path, 'wb') as file:
        file.write(byte_data)

#-------------------------------------------------------

def main():
    input_file = "test_text2bin.txt"  # File path to the input file
    binary = file2Array(input_file)  # Convert the file to binary
    print(f"Binary data length: {len(binary)}")  # Display the length of the binary data

    # Initialize SDM with p=2000 and n equal to the length of the binary data
    sdm = SDM(2000, len(binary))
    
    # Use the binary data as the key for entering and looking up
    key = binary
    print(key)
    print()
    print(sdm.data)
    print()
    sdm.enter(key)
    print("\nRetrieved:")
    retrieved_data = sdm.lookup(key)
    print(retrieved_data)

    # Optionally, save the retrieved data to a file
    Array2File(retrieved_data, "retrieved_output.bin")


    """
    print("\nPart 1: Plotting randomized data: -------------------------------------")
    testpat = np.random.randint(0, 2, 256)
    plot(testpat, 16)


    print("\nPart 2: Generating a ring: --------------------------------------------")
    r = ring()
    plot(r, 16)

    print("\nPart 3: Testing Enter and Lookup: -------------------------------------")
    print("\nKey:")
    key = ring()
    plot(r, 16)
    sdm = SDM(2000, 256)
    sdm.enter(key)
    print("\nRetrieved:")
    retrieved_data = sdm.lookup(key)
    plot(retrieved_data, 16)

    print("\nPart 4: Recover pattern after 25% noise added: ------------------------")
    print("\nKey:")
    key2 = noisy_copy(key, 0.25)
    plot(key2, 16)
    print("\nRetrieved:")
    retrieved_data = sdm.lookup(key2)
    plot(retrieved_data, 16)

    print("\nPart 5: Learn with the following five noisy examples --------------------")
    sdm2 = SDM(2000, 256)
    sdm2.learn(5, 0.1)
    key3 = noisy_copy(ring(), 0.1)
    print("\nTest with the following probe:")
    plot(key3, 16)
    print("\nResult:")
    plot(sdm2.test(key3), 16)
    """
    

if __name__ == '__main__':
    main()
