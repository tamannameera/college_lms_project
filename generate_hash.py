from werkzeug.security import generate_password_hash

# Replace 'yourpassword' with your actual desired password
hashed = generate_password_hash("yourpassword")
print("Hashed password:", hashed)
