# 🔐 دليل الأمان - ONA

## سياسات الأمان والحماية

هذا النظام مصمم بمعايير أمان عالية جداً لحماية خصوصية المواطنين والبيانات الحساسة.

---

## 🛡️ طبقات الحماية

### 1️⃣ تشفير البيانات (Data Encryption)

```python
# جميع الأسماء والهواتف مشفرة باستخدام Fernet
from cryptography.fernet import Fernet

complaint.encrypt_data(name, phone)
# الآن الاسم والهاتف مشفران في قاعدة البيانات
```

**كيفية الفك:**
```python
name = complaint.decrypt_name()  # فك التشفير
phone = complaint.decrypt_phone()
```

### 2️⃣ تجزئة كلمات المرور (Password Hashing)

```python
# كلمات المرور محفوظة بـ PBKDF2:SHA256
from werkzeug.security import generate_password_hash

user.set_password('mypassword')
# تُحفظ محققهة وليست كلمة المرور الأصلية
```

### 3️⃣ حماية الجلسات (Session Security)

```python
app.config['SESSION_COOKIE_SECURE'] = True      # HTTPS فقط
app.config['SESSION_COOKIE_HTTPONLY'] = True    # منع JavaScript
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'   # CSRF Protection
```

### 4️⃣ حماية CSRF

```html
<!-- في كل نموذج -->
<form method="POST">
    {{ csrf_token() }}
    <!-- البيانات -->
</form>
```

### 5️⃣ حماية XSS

```python
# Flask يستخدم Jinja2 الذي يهرب HTML تلقائياً
{{ user_input }}  # آمن من هجمات XSS
```

---

## 🔑 إدارة المفاتيح السرية

### إنشاء مفاتيح آمنة:

```python
import os
from cryptography.fernet import Fernet

# مفتاح Encryption
encryption_key = Fernet.generate_key()
print(encryption_key.decode())

# Secret Key
secret_key = os.urandom(32).hex()
print(secret_key)
```

### حفظ المفاتيح:
```bash
# في ملف .env (محلي فقط، لا تضفه على GitHub)
SECRET_KEY=your-generated-key-here
ENCRYPTION_KEY=your-generated-key-here
```

### في الإنتاج:
```bash
# استخدم متغيرات البيئة من النظام
export SECRET_KEY=$(python -c 'import os; print(os.urandom(32).hex())')
export ENCRYPTION_KEY=$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')
```

---

## 👤 إدارة المستخدمين والصلاحيات

### أنواع المستخدمين:

1. **Admin** (الإدارة)
   - عرض جميع الشكاوى
   - تحديث أي شكوى
   - عرض سجل التدقيق
   - إدارة المستخدمين

2. **Center Manager** (مدير المركز)
   - عرض شكاوى مركزه فقط
   - تحديث شكاوى مركزه فقط

### إضافة مستخدم جديد:

```python
from app import app, db, User

with app.app_context():
    # إضافة مدير مركز
    user = User(
        username='mila_manager',
        email='manager@mila.ona.dz',
        role='center_manager',
        center_id='mila'
    )
    user.set_password('SecurePassword123!')
    db.session.add(user)
    db.session.commit()
    print("تم إضافة المستخدم بنجاح!")
```

### تغيير كلمة المرور:

```python
with app.app_context():
    user = User.query.filter_by(username='mila_manager').first()
    user.set_password('NewSecurePassword456!')
    db.session.commit()
    print("تم تحديث كلمة المرور")
```

---

## 📝 سجل التدقيق (Audit Logs)

كل عملية في النظام تُسجل:

```
[2026-02-08 12:30:45] Admin تسجيل دخول | IP: 192.168.1.100
[2026-02-08 12:31:10] عرض شكوى ONA-20260208123040
[2026-02-08 12:32:25] تحديث حالة من "جديد" إلى "قيد المعالجة"
[2026-02-08 12:33:15] تسجيل خروج
```

### مراجعة السجلات:
```python
from app import db, AuditLog

# آخر 100 عملية
logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(100).all()

for log in logs:
    print(f"{log.timestamp} - {log.action} - {log.ip_address}")
```

### البحث عن أنشطة مريبة:
```python
# محاولات تسجيل دخول فاشلة
failed_logins = AuditLog.query.filter_by(action='محاولة تسجيل دخول فاشلة').all()

# آخر 24 ساعة
from datetime import datetime, timedelta
recent = AuditLog.query.filter(
    AuditLog.timestamp > datetime.utcnow() - timedelta(hours=24)
).all()
```

---

## 🚀 نشر آمن على الإنترنت

### 1. استخدام HTTPS (مجاني):

```python
# مع Let's Encrypt
from flask_talisman import Talisman

Talisman(app)

# في الإنتاج
app.run(ssl_context='adhoc')  # أو شهادة SSL حقيقية
```

### 2. جدار الحماية (Firewall):
```bash
# السماح فقط بـ HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### 3. قاعدة بيانات منفصلة:

```python
# استخدم PostgreSQL بدل SQLite
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://user:pass@secure-db.example.com/ona'
```

### 4. متغيرات البيئة الآمنة:

```bash
# استخدم مدير الأسرار (Secrets Manager)
# مثل AWS Secrets Manager أو HashiCorp Vault

export SECRET_KEY=$(aws secretsmanager get-secret-value --secret-id ona/secret-key)
export DATABASE_URL=$(aws secretsmanager get-secret-value --secret-id ona/db-url)
```

---

## 🔍 الفحص الأمني الدوري

### كل يوم:
- [ ] تفقد سجل التدقيق
- [ ] ابحث عن محاولات دخول فاشلة
- [ ] تحقق من وجود عمليات غير عادية

### كل أسبوع:
- [ ] تحديث البرامج (`pip install --upgrade`)
- [ ] مراجعة قائمة المستخدمين النشطين
- [ ] نسخ احتياطية من قاعدة البيانات

### كل شهر:
- [ ] مراجعة شاملة لسياسات الأمان
- [ ] اختبار استرجاع النسخ الاحتياطية
- [ ] تحديث كلمات المرور للحسابات الإدارية

---

## ⚠️ تحذيرات أمنية

### ❌ DO NOT:
- ❌ لا تشارك المفاتيح السرية عبر البريد
- ❌ لا تكتب المفاتيح في الكود مباشرة
- ❌ لا تستخدم كلمات مرور ضعيفة (مثل 123456)
- ❌ لا تضف .env على GitHub
- ❌ لا تثق بأي طلب غريب

### ✅ DO:
- ✅ استخدم متغيرات البيئة
- ✅ استخدم HTTPS دائماً
- ✅ غيّر الحسابات الافتراضية فوراً
- ✅ راقب سجلات التدقيق
- ✅ نفذ تحديثات الأمان سريعاً

---

## 🆘 الإجراءات الطارئة

### إذا تم اختراق الحساب:

1. **فوراً:**
   ```bash
   # غيّر كلمة المرور للجميع
   python reset_passwords.py
   ```

2. **تحقق من السجلات:**
   ```python
   # أي بيانات تم الوصول إليها؟
   suspicious_logs = AuditLog.query.filter_by(user_id=hacked_user_id).all()
   ```

3. **بلّغ:**
   - أخبر الإدارة فوراً
   - وثّق الحادثة
   - ارسل تقرير للجهات المعنية

### إذا تسرّبت البيانات:

1. **أغلق الموقع مؤقتاً:**
   ```python
   @app.before_request
   def maintenance():
       return "تحت الصيانة الأمنية", 503
   ```

2. **تحقق من النطاق:**
   ```python
   # كم شكوى تأثرت؟
   affected = Complaint.query.all()
   ```

3. **أعلم المستخدمين:**
   - أرسل بريد لجميع من أرسلوا شكاوى
   - اشرح ماحصل
   - أخبرهم بالخطوات المتخذة

---

## 📞 التواصل الأمني

للإبلاغ عن ثغرة أمنية:
- **البريد:** security@ona.dz
- **الهاتف:** 0770971700
- **لا تشاركها بأي مكان آخر!**

---

**تم آخر تحديث: 2026-02-08**
