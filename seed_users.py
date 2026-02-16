from app import app, ONA_CENTERS
from models import db, User

def seed_center_users():
    with app.app_context():
        # 1. Admin
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin', role='admin', email='admin@ona.dz')
            admin.set_password('admin123')
            db.session.add(admin)
            print("Admin created: admin / admin123")
        
        # 2. Centers
        print("\nCreating center manager accounts...")
        
        for center_id, data in ONA_CENTERS.items():
            username = f"manager_{center_id}"
            password = f"ona_{center_id}_2024"
            
            existing_user = User.query.filter_by(username=username).first()
            if not existing_user:
                user = User(
                    username=username,
                    role='center_manager',
                    center_id=center_id,
                    email=f"{center_id}@ona.dz"
                )
                user.set_password(password)
                db.session.add(user)
                print(f"Created user for ID: {center_id}")
            else:
                print(f"Already exists: {username}")
        
        db.session.commit()
        print("Done.")

if __name__ == "__main__":
    seed_center_users()
