from db_manager import init_db, insert_token

init_db()
insert_token("TEST123")
print("✅ Token 'TEST123' inserted successfully!")
