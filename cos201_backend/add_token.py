from db_manager import init_db, insert_token

init_db()
insert_token("TEST456")
print("✅ Token 'TEST456' inserted successfully!")
