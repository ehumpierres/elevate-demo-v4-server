import base64

# Load the original private key from a file
with open('rsa_key.p8', 'rb') as key_file:
    private_key = key_file.read()

# Encode the private key to base64
encoded_key = base64.b64encode(private_key).decode('utf-8')

# Write the base64 encoded key to a new file
with open('encoded_rsa_key.txt', 'w') as encoded_file:
    encoded_file.write(encoded_key)

print("Base64 encoded key has been written to encoded_rsa_key.txt")