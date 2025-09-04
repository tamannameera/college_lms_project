import mysql.connector
from werkzeug.security import generate_password_hash
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB

# Step 1: Connect to MySQL using config.py
conn = mysql.connector.connect(
    host=MYSQL_HOST,
    user=MYSQL_USER,
    password=MYSQL_PASSWORD,
    database=MYSQL_DB
)
cursor = conn.cursor()

# Step 2: User Data
email = 'student@example.com'
phone = '1234567890'
password = '@12345'  # Plain password

# Step 3: Hash the password
hashed_password = generate_password_hash(password)

# Step 4: Insert query
sql = "INSERT INTO users (email, phone, password_hash, role) VALUES (%s, %s, %s, %s)"
val = (email, phone, hashed_password, 'student')

# Step 5: Execute & save
cursor.execute(sql, val)
conn.commit()
print("✅ User created successfully!")

# Step 6: Clean up
cursor.close()
conn.close()
