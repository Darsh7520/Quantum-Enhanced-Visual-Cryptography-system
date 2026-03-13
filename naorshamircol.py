import numpy as np
from PIL import Image,ImageOps
import requests

# --- Optional Quantum Randomness ---
def get_quantum_random_bits(n_bits=1024):
    url = f"https://qrng.anu.edu.au/API/jsonI.php?length={n_bits}&type=uint8"
    response = requests.get(url).json()
    return np.array(response['data'], dtype=np.uint8)

# --- Naor-Shamir for one channel ---
def ns_channel(channel_matrix, quantum_bits=None):
    h, w = channel_matrix.shape
    share1 = np.zeros((h*2, w*2), dtype=np.uint8)
    share2 = np.zeros((h*2, w*2), dtype=np.uint8)

    bit_index = 0

    for i in range(h):
        for j in range(w):
            pixel = channel_matrix[i, j]
            # Correct mapping: black=1, white=0
            bit = 1 if pixel < 128 else 0

            # Random pattern choice
            if quantum_bits is not None and bit_index < len(quantum_bits):
                pattern = quantum_bits[bit_index] % 2
                bit_index += 1
            else:
                pattern = np.random.randint(0, 2)

            if bit == 0:  # white pixel → identical blocks
                if pattern == 0:
                    block1 = np.array([[1,0],[0,1]])
                    block2 = np.array([[1,0],[0,1]])
                else:
                    block1 = np.array([[0,1],[1,0]])
                    block2 = np.array([[0,1],[1,0]])
            else:  # black pixel → complementary blocks
                if pattern == 0:
                    block1 = np.array([[1,0],[0,1]])
                    block2 = np.array([[0,1],[1,0]])
                else:
                    block1 = np.array([[0,1],[1,0]])
                    block2 = np.array([[1,0],[0,1]])

            share1[i*2:(i+1)*2, j*2:(j+1)*2] = block1
            share2[i*2:(i+1)*2, j*2:(j+1)*2] = block2

    return share1, share2

# --- Full Color Naor-Shamir ---
def generate_ns_color_shares(image_path, use_quantum=False):
    img = Image.open(image_path).convert('RGB')
    r, g, b = img.split()

    quantum_bits = None
    if use_quantum:
        quantum_bits = get_quantum_random_bits(img.size[0] * img.size[1])

    r1, r2 = ns_channel(np.array(r), quantum_bits)
    g1, g2 = ns_channel(np.array(g), quantum_bits)
    b1, b2 = ns_channel(np.array(b), quantum_bits)

    share1 = np.stack([r1*255, g1*255, b1*255], axis=-1).astype(np.uint8)
    share2 = np.stack([r2*255, g2*255, b2*255], axis=-1).astype(np.uint8)

    return share1, share2

def reconstruct_color(share1, share2):
    return np.bitwise_or(share1, share2)

# --- Example Run ---
if __name__ == "__main__":
    s1, s2 = generate_ns_color_shares("/Users/darshpatel/Desktop/python/256_Superman.png", use_quantum=False)
    Image.fromarray(s1).save("share1_color.png")
    Image.fromarray(s2).save("share2_color.png")

    reconstructed = reconstruct_color(s1, s2)
    img = Image.fromarray(reconstructed)
    ImageOps.invert(img).save("reconstructed_color.png")

