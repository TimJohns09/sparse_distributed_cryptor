import numpy as np
import random

class SDM:
    def __init__(self, p, n):
        self.p = p
        self.n = n
        self.addresses = [[[random.randint(0, 1) for _ in range(n)] for _ in range(p)]]
        self.data = [[[0 for _ in range(n)] for _ in range(p)]]
        self.radius = 0.451 * n

    def enter(self, addressVector):
        for i in range(len(self.addresses[0])):
            # Pad the addressVector with zeros if it's shorter than self.addresses[0][i]
            padded_addressVector = addressVector + [0] * (len(self.addresses[0][i]) - len(addressVector))
            hdist = hamming_distance(self.addresses[0][i], padded_addressVector)
            if hdist <= self.radius:
                for j in range(len(self.addresses[0][i])):
                    if self.addresses[0][i][j] == 1:
                        self.data[0][i][j] += 1
                    else:
                        self.data[0][i][j] -= 1

    def lookup(self, addressVector):
        retrieved_data = [0] * len(self.addresses[0][0])  # Initialize with the correct length
        for i in range(len(self.addresses[0])):
            # Pad the addressVector with zeros if it's shorter than self.addresses[0][i]
            padded_addressVector = addressVector + [0] * (len(self.addresses[0][i]) - len(addressVector))
            hdist = hamming_distance(self.addresses[0][i], padded_addressVector)
            if hdist <= self.radius:
                for j in range(len(self.addresses[0][i])):
                    retrieved_data[j] += self.data[0][i][j]
        for i in range(len(retrieved_data)):
            if retrieved_data[i] > 0:
                retrieved_data[i] = 1
            else:
                retrieved_data[i] = 0
        return retrieved_data

def hamming_distance(vector1, vector2):
    distance = 0
    for i in range(len(vector1)):
        if vector1[i] != vector2[i]:
            distance += 1
    return distance

def file_to_binary(filename):
    binary_data = []
    with open(filename, 'r') as file:
        for line in file:
            for char in line:
                ascii_value = ord(char)
                binary_value = bin(ascii_value)[2:].zfill(8)
                binary_data.extend([int(bit) for bit in binary_value])
    return binary_data

def binary_to_file(retrieved_data, filename):
    with open(filename, 'w') as file:
        for i in range(0, len(retrieved_data), 8):
            byte = retrieved_data[i:i+8]
            ascii_value = int(''.join(map(str, byte)), 2)
            char = chr(ascii_value)
            file.write(char)

def main():
    filename = 'test_text2bin.txt'
    sdm = SDM(4000, 256)

    binary_data = file_to_binary(filename)
    chunk_size = 256  # Changed chunk_size to match the length of self.addresses[0][i]
    chunks = [binary_data[i:i+chunk_size] for i in range(0, len(binary_data), chunk_size)]
    for chunk in chunks:
        sdm.enter(chunk)

    retrieved_data = []
    for chunk in chunks:
        retrieved_chunk = sdm.lookup(chunk)
        retrieved_data.extend(retrieved_chunk)

    reconstructed_filename = 'reconstructed_' + filename
    binary_to_file(retrieved_data, reconstructed_filename)

if __name__ == '__main__':
    main()