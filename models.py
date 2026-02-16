from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, current_user
from datetime import datetime
from cryptography.fernet import Fernet
import os

db = SQLAlchemy()

# مفتاح التشفير (يجب أن يكون ثابتاً في .env)
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
if not ENCRYPTION_KEY:
    # مفتاح احتياطي صالح بصيغة base64 (32 بايت)
    ENCRYPTION_KEY = 'wbUgP_K0FAiLxwMtbx-I_VvGhff5ztHSCnoz8tiRb-4='

cipher = Fernet(ENCRYPTION_KEY.encode() if isinstance(ENCRYPTION_KEY, str) else ENCRYPTION_KEY)

class User(UserMixin, db.Model):
    """نموذج المستخدمين (المسؤولون)"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=True)
    role = db.Column(db.String(50), nullable=False)  # 'admin' أو 'center_manager'
    center_id = db.Column(db.String(50), nullable=True)  # المركز المعني (للمدير)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime, nullable=True)
    
    def set_password(self, password):
        """تحديث كلمة المرور بتجزئة آمنة"""
        self.password_hash = generate_password_hash(password, method='pbkdf2:sha256')
    
    def check_password(self, password):
        """التحقق من كلمة المرور"""
        return check_password_hash(self.password_hash, password)

class Complaint(db.Model):
    """نموذج الشكاوى"""
    __tablename__ = 'complaints'
    
    id = db.Column(db.Integer, primary_key=True)
    tracking_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    
    # بيانات المواطن (مشفرة)
    name_encrypted = db.Column(db.String(255), nullable=False)
    phone_encrypted = db.Column(db.String(255), nullable=False)
    birth_date_encrypted = db.Column(db.String(255), nullable=True)
    birth_place_encrypted = db.Column(db.String(255), nullable=True)
    address_encrypted = db.Column(db.String(255), nullable=True)
    id_card_encrypted = db.Column(db.String(255), nullable=True)
    
    # معلومات الشكوى
    commune = db.Column(db.String(100), nullable=False, index=True)
    complaint_type = db.Column(db.String(100), nullable=False)
    problem_description = db.Column(db.Text, nullable=False)
    
    # الحالة والمتابعة
    status = db.Column(db.String(50), default='جديد', index=True)  # جديد / قيد المعالجة / حل
    assigned_to = db.Column(db.String(100), nullable=True)  # من تم إسناد الشكوى له
    notes = db.Column(db.Text, nullable=True)  # ملاحظات المسؤول
    
    # الوقت والتتبع
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    resolved_at = db.Column(db.DateTime, nullable=True)
    
    # بيانات المركز المعني
    center_id = db.Column(db.String(50), nullable=False, index=True)
    
    def encrypt_data(self, name, phone, birth_date=None, birth_place=None, address=None, id_card=None):
        """تشفير بيانات المواطن"""
        self.name_encrypted = cipher.encrypt(name.encode()).decode()
        self.phone_encrypted = cipher.encrypt(phone.encode()).decode()
        if birth_date:
            self.birth_date_encrypted = cipher.encrypt(birth_date.encode()).decode()
        if birth_place:
            self.birth_place_encrypted = cipher.encrypt(birth_place.encode()).decode()
        if id_card:
            self.id_card_encrypted = cipher.encrypt(id_card.encode()).decode()
        if address:
            self.address_encrypted = cipher.encrypt(address.encode()).decode()
    
    def decrypt_name(self):
        """فك تشفير الاسم"""
        try:
            return cipher.decrypt(self.name_encrypted.encode()).decode()
        except:
            return "***مشفر***"
    
    def decrypt_phone(self):
        """فك تشفير الهاتف"""
        try:
            return cipher.decrypt(self.phone_encrypted.encode()).decode()
        except:
            return "***مشفر***"

    def decrypt_birth_date(self):
        """فك تشفير تاريخ الميلاد"""
        try:
            return cipher.decrypt(self.birth_date_encrypted.encode()).decode() if self.birth_date_encrypted else "-"
        except:
            return "***مشفر***"

    def decrypt_birth_place(self):
        """فك تشفير مكان الميلاد"""
        try:
            return cipher.decrypt(self.birth_place_encrypted.encode()).decode() if self.birth_place_encrypted else "-"
        except:
            return "***مشفر***"

    def decrypt_id_card(self):
        """فك تشفير رقم بطاقة التعريف"""
        try:
            return cipher.decrypt(self.id_card_encrypted.encode()).decode() if self.id_card_encrypted else "-"
        except:
            return "***مشفر***"

    def decrypt_address(self):
        """فك تشفير العنوان"""
        try:
            return cipher.decrypt(self.address_encrypted.encode()).decode() if self.address_encrypted else "-"
        except:
            return "***مشفر***"

    def decrypt_all(self):
        """فك تشفير جميع البيانات الشخصية"""
        return {
            'name': self.decrypt_name(),
            'phone': self.decrypt_phone(),
            'birth_date': self.decrypt_birth_date(),
            'birth_place': self.decrypt_birth_place(),
            'address': self.decrypt_address(),
            'id_card': self.decrypt_id_card()
        }

class AuditLog(db.Model):
    """نموذج سجلات التدقيق الأمنية"""
    __tablename__ = 'audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(255), nullable=False)
    entity_type = db.Column(db.String(50), nullable=False)  # 'complaint', 'user', ...
    entity_id = db.Column(db.Integer, nullable=True)
    changes = db.Column(db.Text, nullable=True)  # تفاصيل التغييرات
    ip_address = db.Column(db.String(45), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f'<AuditLog {self.action} by {self.user_id} at {self.timestamp}>'
