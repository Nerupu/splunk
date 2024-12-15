import string
import random
import os
import argparse

parser = argparse.ArgumentParser(description='Generate a random password')
parser.add_argument('-l', '--length', type=int, default=32, help='Length of the password')
parser.add_argument('-f', '--file', type=str, default='password.txt', help='File to save the password to')

args = parser.parse_args()

def generate_password(length):
    chars = string.ascii_letters + string.ascii_letters.capitalize() + string.digits + '!@#$%^&*()'
    random.seed = (os.urandom(1024)) #in short, this gives more randomness to the password
    return ''.join(random.choice(chars) for i in range(length))

if __name__ == '__main__':
    print("Generating password")
    password = generate_password(args.length)
    print(f"Password: {password}")
    print(f"Saving password to file.")
    with open(args.file, 'w') as f:
        f.write(password)
    print("Done")

