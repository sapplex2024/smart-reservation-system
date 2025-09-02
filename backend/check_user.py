from app.models.database import SessionLocal, User
from app.api.auth import verify_password

db = SessionLocal()
try:
    user = db.query(User).filter(User.username == 'admin').first()
    print('User found:', user is not None)
    if user:
        print('Username:', user.username)
        print('Email:', user.email)
        print('Full name:', user.full_name)
        print('Role:', user.role)
        print('Is active:', user.is_active)
        print('Password verification with "admin123":', verify_password('admin123', user.hashed_password))
    else:
        print('Admin user not found in database')
finally:
    db.close()