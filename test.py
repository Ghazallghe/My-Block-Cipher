from random import shuffle, choice, randint
from calculator import aes_s_box

KEY_SIZE = 32
BLOCK_SIZE = 64  # in bits, Must be dividble by 8
ROUNDS = 12      # Must be Less than KEY_SIZE


KEY = '00001111100000101110111100110110'
IP = [29, 15, 59, 1, 37, 14, 25, 35, 24, 16, 58, 19, 18, 36, 49, 55, 45, 48, 12, 4, 52, 60, 38, 41, 5, 28, 32, 8, 57, 53, 62, 22, 6, 63, 51, 23, 43, 56, 7, 11, 2, 13, 0, 20, 40, 31, 27, 30, 39,
      9, 46, 21, 50, 61, 26, 10, 44, 17, 42, 34, 54, 3, 47, 33]
IP_INV = [42, 3, 40, 61, 19, 24, 32, 38, 27, 49, 55, 39, 18, 41, 5, 1, 9, 57, 12, 11, 43, 51, 31, 35, 8, 6, 54, 46, 25, 0, 47, 45, 26, 63, 59, 7, 13, 4, 22, 48, 44, 23, 58, 36, 56, 16, 50, 62,
          17, 14, 52, 34, 20, 29, 60, 15, 37, 28, 10, 2, 21, 53, 30, 33]
IV = '96f31e9bbe713431'
FP = [8, 12, 14, 5, 0, 25, 20, 27, 9, 6, 10, 3, 21, 17, 28, 22,
      29, 4, 1, 16, 26, 11, 2, 7, 24, 19, 31, 23, 13, 30, 18, 15]


def b2h(x: str, len=BLOCK_SIZE//4) -> str:
    return hex(int(x, 2))[2:].zfill(len)


def h2b(x: str, len=BLOCK_SIZE) -> str:
    return bin(int(x, 16))[2:].zfill(len)


def xor(x: str, y: str, is_hex=False) -> str:
    if is_hex:
        x, y = h2b(x), h2b(y)
    ret = ''
    for i in range(len(x)):
        if x[i] == y[i]:
            ret += '0'

        else:
            ret += '1'
    return b2h(ret) if is_hex else ret


# Inputs 1 byte Binary and Outputs 1 byte Binary:
def s_box(x: str) -> str:
    if len(x) != 8:
        raise ValueError("Input of S_Box must be 1 byte long")

    return bin(int(aes_s_box(int(x, 2)), 16))[2:].zfill(8)


def permute(x: str, permutation: list) -> str:
    ret = ''
    for i in permutation:
        ret += x[i]
    return ret


def sub_key_generator(key: str):
    subs = []
    counter = '1'
    for _ in range(ROUNDS):
        subs.append(xor(key, counter.zfill(len(key))))
        counter += '1'

    return subs


def f(r: str, sub_key: str):

    rs = [r[i:i+8] for i in range(0, len(r), 8)]
    subs = [sub_key[i:i+8] for i in range(0, len(sub_key), 8)]
    # print(rs, subs)
    fs = []
    for i in range(len(rs)):
        fs.append(s_box(xor(s_box(rs[i]), s_box(subs[i]))))

    return permute(''.join(fs), FP)


def feistel(l: str, r: str, key: str) -> str:
    new_r = xor(l, f(r, key))
    return r, new_r


def encrypt(plain_text: str, decrypt=False, inp_binary=False, mode='normal') -> str:

    # __Part1 --> Changit Plain_text form to Hex__

    # If Input is Binary, Change it to Hex:
    if inp_binary:
        inp_len = len(plain_text)
        hex_plain_text = hex(int(plain_text, 2))[2:].zfill(inp_len//4)
    else:
        # If We Are In Encypt Mode encode, English Message to Hex:
        if not decrypt:
            hex_plain_text = plain_text.encode().hex()
        # If We Are Decrypting We Don't need to change Cipher to Hex because it already is Hex
        else:
            hex_plain_text = plain_text

# __Part2 --> Split Message to Different Blocks__
    blocks = [hex_plain_text[i:i+BLOCK_SIZE//4]
              for i in range(0, len(hex_plain_text), BLOCK_SIZE//4)]

    # Ensure that last block hast the same size than others:
    while len(blocks[-1]) < BLOCK_SIZE//4:
        blocks[-1] += '0'


# __Part3 --> Generate SubKeys __

    # If we are in Decrpyt mode we need to reverse sub_keys !!
    sub_keys = sub_key_generator(KEY)
    sub_keys = sub_keys[::-1] if decrypt else sub_keys


# __Part4 --> Encrpyt Each Block

    if mode == 'normal':
        cipher_text = [encrypt_block(i, sub_keys) for i in blocks]
        cipher_text = ''.join(cipher_text)

    elif mode == 'CBC':

        if not decrypt:

            cipher_text, last_encrypted_block = '', IV
            for block in blocks:
                last_encrypted_block = encrypt_block(
                    xor(block, last_encrypted_block, True), sub_keys)
                cipher_text += last_encrypted_block

        else:

            cipher_text = xor(encrypt_block(blocks[0], sub_keys), IV, True)
            for i in range(1, len(blocks)):
                cipher_text += xor(encrypt_block(blocks[i],
                                   sub_keys), blocks[i-1], True)

    return bytes.fromhex(cipher_text).decode() if decrypt else cipher_text


def encrypt_block(inp: str, sub_keys: list[str]) -> str:

    # Change to Binary:
    inp = bin(int(inp, 16))[2:].zfill(len(inp)*4)
    # Perform Initial Permutaion:
    inp = permute(inp, IP)

    # Continue to Feistel Network:
    l, r = inp[:BLOCK_SIZE//2], inp[BLOCK_SIZE//2:]

    for i in range(ROUNDS):
        l, r = feistel(l, r, sub_keys[i])

    # Swap l and r and Perform Final Permutaion:
    out = permute(r+l, IP_INV)

    return format(int(out, 2), f'0{BLOCK_SIZE//4}x')

    # return hex(int(r, 2))[2:]+hex(int(l, 2))[2:]


def diffusion_checker(plain_text_length: int = 256, mode='normal'):

    pl = [choice(('0', '1')) for _ in range(plain_text_length)]
    c1 = encrypt(''.join(pl), inp_binary=True, mode=mode)

    pl2 = pl[::]
    idx = randint(0, plain_text_length-1)
    pl2[idx] = '0' if pl2[idx] == '1' else '1'

    c2 = encrypt(''.join(pl2), inp_binary=True, mode=mode)

    c1, c2 = bin(int(c1, 16)), bin(int(c2, 16))

    pl_diff = 0
    for i in range(len(pl)):
        if pl[i] != pl2[i]:
            pl_diff += 1

    diff = 0
    for i in range(len(c1)):
        try:
            if c1[i] != c2[i]:
                diff += 1
        except:
            diff += 1

    print(f"bit at poisition {idx} changed in plain text")
    print(f"{diff} bit(s) changed in cipher")


if __name__ == "__main__":

    mode = 'CBC'

    print("\t\tAvalanche Effect: ")
    diffusion_checker(mode=mode)
    print("\n")

    plain_text = "Nuclear Weapons will be launched at 5:32 AM October 7, 2024 "
    print(f"Plain Text        :\t{plain_text}")

    print(f"Encoded Plain Text:\t{plain_text.encode().hex()}\n")

    print(f"Key = {hex(int(KEY, 2))}")
    cipher_text = encrypt(plain_text, mode=mode)
    print(f"Cipher Text       :\t{cipher_text}\n")

    decrypted_text = encrypt(cipher_text, decrypt=True, mode=mode)
    print(f"Decrypted         :\t{decrypted_text}")
