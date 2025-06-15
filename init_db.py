# init_db.py
from db import db

# Create sample users
db.create_user('analyst1', 'analystpass', 'analyst')
db.create_user('investor1', 'investorpass', 'investor', 'analyst1')
db.create_user('investor2', 'investorpass', 'investor', 'analyst1')

print("Database initialized successfully!")