import os
import sys
import json
import re
import webbrowser
import threading
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash

# دالة لتحديد المسار الصحيح للموارد عند التشغيل كـ EXE
def resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# تحميل متغيرات البيئة قبل استيراد النماذج
load_dotenv()

from models import db, User, Complaint, AuditLog
from translations import TRANSLATIONS

from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# إنشاء التطبيق
app = Flask(__name__, 
            template_folder=resource_path('templates'),
            static_folder=resource_path('static'))

# تفعيل حماية CSRF
csrf = CSRFProtect(app)

# إعداد محدد السرعة (Rate Limiter) لمنع الإغراق
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)

# تعطيل Jinja2 caching
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0
app.jinja_env.cache = None

# إعداد مسارات قاعدة البيانات بشكل يضمن بقاءها بجانب ملف البرنامج (EXE)
if hasattr(sys, '_MEIPASS'):
    # إذا كان يعمل كملف تنفيذي، نستخدم مسار ملف الـ EXE
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # إذا كان يعمل ككود برمجي، نستخدم مسار الملف الحالي
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))

INSTANCE_DIR = os.path.join(BASE_DIR, 'instance')
os.makedirs(INSTANCE_DIR, exist_ok=True)
DB_PATH = os.path.join(INSTANCE_DIR, 'ona_complaints.db')

# إعدادات الأمان
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-key-for-dev')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['DEBUG'] = os.environ.get('DEBUG', 'True') == 'True'
app.config['SESSION_COOKIE_SECURE'] = False  # تم التعطيل للعمل على HTTP
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# إنشاء مجلد البيانات
os.makedirs('instance', exist_ok=True)

# تهيئة قاعدة البيانات
db.init_app(app)

# إعداد نظام تسجيل الدخول
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'يجب تسجيل الدخول أولاً'

# إدارة اللغات
@app.context_processor
def inject_translations():
    lang = session.get('lang', 'ar')
    return {
        'lang': lang,
        't': lambda key: TRANSLATIONS.get(lang, TRANSLATIONS['ar']).get(key, key),
        'dir': 'rtl' if lang == 'ar' else 'ltr'
    }

@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in ['ar', 'fr']:
        session['lang'] = lang
    return redirect(request.referrer or url_for('index'))

# بيانات المراكز
ONA_CENTERS = {
    'ferdjioua': {'name': 'مركز فرجيوة', 'communes': ['فرجيوة', 'عين البضاء احريش', 'بني قشة']},
    'mila': {'name': 'مركز ميلة', 'communes': ['ميلة', 'سيدي خليفة', 'عين التين']},
    'chelghoum': {'name': 'مركز شلغوم العيد', 'communes': ['شلغوم العيد']},
    'tadjenanet': {'name': 'مركز تاجنانت', 'communes': ['تاجنانت', 'المشيرة', 'واد خلوف']},
    'teleghma': {'name': 'مركز التلاغمة', 'communes': ['التلاغمة', 'واد سقان']},
    'grarem': {'name': 'مركز القرارم قوقة', 'communes': ['القرارم قوقة', 'حمالة']},
    'ouedendja': {'name': 'مركز وادي انجاء', 'communes': ['واد انجاء', 'احمد راشدي']},
    'sidimerouane': {'name': 'مركز سيدي مروان', 'communes': ['سيدي مروان', 'الشيقارة']},
    'terraibainen': {'name': 'مركز ترعي باينان', 'communes': ['ترعي باينان', 'تسالة لمطاعي']}
}

COMPLAINT_TYPES = ['type_leak', 'type_clog', 'type_smell', 'type_cut', 'type_other']
COMPLAINT_STATUSES = ['جديد', 'قيد المعالجة', 'حل']

# منع التخزين المؤقت (Cache) وإضافة رؤوس الأمان
@app.after_request
def add_security_headers(response):
    """إضافة رؤوس أمان مشددة وتعطيل التخزين المؤقت"""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com https://fonts.gstatic.com; img-src 'self' data: https://ona-dz.dz;"
    return response

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def get_center_by_commune(commune):
    """البحث عن المركز بناءً على البلدية"""
    for center_id, center_data in ONA_CENTERS.items():
        if commune in center_data['communes']:
            return center_id
    return None

def log_audit(action, entity_type, entity_id=None, changes=None):
    """تسجيل عملية تدقيق"""
    try:
        log = AuditLog(
            user_id=current_user.id if current_user.is_authenticated else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            changes=json.dumps(changes) if changes else None,
            ip_address=request.remote_addr
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        print(f"خطأ في تسجيل التدقيق: {e}")

def require_role(role):
    """decorator للتحقق من الصلاحيات"""
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.role != role and current_user.role != 'admin':
                flash('لا يوجد صلاحيات كافية', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

@app.route('/')
def index():
    """الشاشة الافتتاحية"""
    return render_template('landing.html')

@app.route('/submit')
def citizen_form():
    """صفحة تقديم الشكاوى للمواطنين"""
    communes = sorted([c for center in ONA_CENTERS.values() for c in center['communes']])
    return render_template('index.html', communes=communes, complaint_types=COMPLAINT_TYPES)

def validate_input(data):
    """تحقق صارم من المدخلات"""
    # التحقق من الاسم (أحرف فقط ومسافات)
    if not re.match(r'^[\u0600-\u06FF\s\w]{3,50}$', data.get('name', '')):
        return "الاسم غير صحيح"
    
    # التحقق من رقم الهاتف الجزائري
    if not re.match(r'^(05|06|07)[0-9]{8}$', data.get('phone', '')):
        return "رقم الهاتف غير صحيح"
    
    # التحقق من رقم التعريف (من 5 إلى 30 حرف/رقم) لزيادة المرونة
    if len(data.get('id_card', '')) < 5:
        return "رقم التعريف غير صحيح"
    
    # التحقق من مكان الازدياد والعنوان (طول أدنى)
    if len(data.get('birth_place', '')) < 2:
        return "مكان الازدياد غير صحيح"
    
    if len(data.get('address', '')) < 5:
        return "العنوان غير صحيح"
    
    return None

@app.route('/api/submit_complaint', methods=['POST'])
@limiter.limit("5 per minute")
def submit_complaint():
    """استقبال الشكوى (API آمن)"""
    try:
        data = request.get_json()
        
        # التحقق من البيانات
        required_fields = ['name', 'phone', 'id_card', 'birth_date', 'birth_place', 'address', 'commune', 'type', 'problem']
        if not all(field in data for field in required_fields):
            return jsonify({'status': 'error', 'message': 'بيانات ناقصة'}), 400
        
        # تحقق أمني إضافي
        validation_error = validate_input(data)
        if validation_error:
            return jsonify({'status': 'error', 'message': validation_error}), 400
        
        # البحث عن المركز
        center_id = get_center_by_commune(data['commune'])
        if not center_id:
            return jsonify({'status': 'error', 'message': 'بلدية غير صحيحة'}), 400
        
        # إنشاء رقم تتبع
        tracking_id = f"ONA-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        # إنشاء الشكوى مع تشفير البيانات
        complaint = Complaint(
            tracking_id=tracking_id,
            commune=data['commune'],
            complaint_type=data['type'],
            problem_description=data['problem'],
            center_id=center_id,
            status='جديد'
        )
        complaint.encrypt_data(
            name=data['name'],
            phone=data['phone'],
            id_card=data.get('id_card'),
            birth_date=data.get('birth_date'),
            birth_place=data.get('birth_place'),
            address=data.get('address')
        )
        
        db.session.add(complaint)
        db.session.commit()
        
        # تسجيل في سجل التدقيق
        log_audit('شكوى جديدة', 'complaint', complaint.id, {
            'commune': data['commune'],
            'type': data['type']
        })
        
        return jsonify({
            'status': 'success',
            'message': 'تم استقبال شكواك بنجاح',
            'tracking_id': tracking_id
        }), 201
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per hour")
def login():
    """صفحة تسجيل الدخول الآمنة"""
    if request.method == 'POST':
        username = request.form.get('u_auth', '').strip()
        password = request.form.get('p_auth', '')
        
        if not username or not password:
            flash('اسم المستخدم وكلمة المرور مطلوبة', 'warning')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user, remember=True)
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            log_audit('تسجيل دخول', 'user', user.id)
            
            return redirect(url_for('dashboard'))
        else:
            flash('بيانات تسجيل الدخول غير صحيحة', 'danger')
            log_audit('محاولة تسجيل دخول فاشلة', 'user', None)
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    """تسجيل الخروج"""
    log_audit('تسجيل خروج', 'user', current_user.id)
    logout_user()
    flash('تم تسجيل الخروج بنجاح', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """لوحة التحكم (مختلفة حسب الدور)"""
    if current_user.role == 'admin':
        return redirect(url_for('admin_dashboard'))
    else:
        return redirect(url_for('center_dashboard', center_id=current_user.center_id))

@app.route('/admin')
@require_role('admin')
def admin_dashboard():
    """لوحة التحكم الإدارية - عرض جميع الشكاوى"""
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('search', '', type=str)
    status_filter = request.args.get('status', '', type=str)
    
    query = Complaint.query
    
    if search_query:
        query = query.filter(
            (Complaint.tracking_id.contains(search_query)) |
            (Complaint.commune.contains(search_query))
        )
    
    if status_filter and status_filter in COMPLAINT_STATUSES:
        query = query.filter_by(status=status_filter)
    
    complaints = query.order_by(Complaint.created_at.desc()).paginate(page=page, per_page=20)
    
    # إحصائيات
    stats = {
        'total': Complaint.query.count(),
        'new': Complaint.query.filter_by(status='جديد').count(),
        'in_progress': Complaint.query.filter_by(status='قيد المعالجة').count(),
        'resolved': Complaint.query.filter_by(status='حل').count()
    }
    
    return render_template('admin_dashboard.html', 
                          complaints=complaints, 
                          stats=stats,
                          centers=ONA_CENTERS,
                          search_query=search_query,
                          status_filter=status_filter)

@app.route('/center/<center_id>')
@login_required
def center_dashboard(center_id):
    """لوحة تحكم مدير المركز - شكاوى المركز فقط"""
    if current_user.role != 'admin' and current_user.center_id != center_id:
        flash('لا يوجد صلاحيات', 'danger')
        return redirect(url_for('dashboard'))
    
    if center_id not in ONA_CENTERS:
        flash('مركز غير موجود', 'danger')
        return redirect(url_for('dashboard'))
    
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '', type=str)
    
    query = Complaint.query.filter_by(center_id=center_id)
    
    if status_filter and status_filter in COMPLAINT_STATUSES:
        query = query.filter_by(status=status_filter)
    
    complaints = query.order_by(Complaint.created_at.desc()).paginate(page=page, per_page=20)
    
    # إحصائيات المركز
    stats = {
        'total': Complaint.query.filter_by(center_id=center_id).count(),
        'new': Complaint.query.filter_by(center_id=center_id, status='جديد').count(),
        'in_progress': Complaint.query.filter_by(center_id=center_id, status='قيد المعالجة').count(),
        'resolved': Complaint.query.filter_by(center_id=center_id, status='حل').count()
    }
    
    return render_template('center_dashboard.html',
                          complaints=complaints,
                          stats=stats,
                          center_id=center_id,
                          center_name=ONA_CENTERS[center_id]['name'],
                          status_filter=status_filter)

def get_t(key):
    lang = session.get('lang', 'ar')
    return TRANSLATIONS.get(lang, TRANSLATIONS['ar']).get(key, key)

@app.route('/track', methods=['GET', 'POST'])
def track_complaint():
    """تتبع حالة الشكوى من قبل المواطن"""
    complaint = None
    tracking_id = request.args.get('tracking_id') or request.form.get('tracking_id')
    
    if tracking_id:
        complaint = Complaint.query.filter_by(tracking_id=tracking_id).first()
        if not complaint:
            flash(get_t('error_tracking_not_found'), 'warning')
            
    return render_template('track.html', complaint=complaint, tracking_id=tracking_id)

@app.route('/api/track/<tracking_id>', methods=['GET'])
@limiter.limit("10 per minute")
def api_track_complaint(tracking_id):
    """تتبع حالة الشكوى (API للموبايل)"""
    try:
        complaint = Complaint.query.filter_by(tracking_id=tracking_id).first()
        if not complaint:
            return jsonify({'status': 'error', 'message': 'رقم التتبع غير موجود'}), 404
        
        return jsonify({
            'status': 'success',
            'tracking_id': complaint.tracking_id,
            'complaint_status': complaint.status,
            'created_at': complaint.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'type': complaint.complaint_type,
            'commune': complaint.commune
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/complaint/<complaint_id>', methods=['GET'])
@login_required
def get_complaint(complaint_id):
    """الحصول على تفاصيل الشكوى"""
    try:
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({'status': 'error', 'message': 'شكوى غير موجودة'}), 404
        
        # التحقق من الصلاحيات
        if current_user.role != 'admin' and current_user.center_id != complaint.center_id:
            return jsonify({'status': 'error', 'message': 'لا توجد صلاحيات'}), 403
        
        log_audit('عرض شكوى', 'complaint', complaint.id)
        
        return jsonify({
            'id': complaint.id,
            'tracking_id': complaint.tracking_id,
            'name': complaint.decrypt_name(),
            'phone': complaint.decrypt_phone(),
            'id_card': complaint.decrypt_id_card(),
            'birth_date': complaint.decrypt_birth_date(),
            'birth_place': complaint.decrypt_birth_place(),
            'address': complaint.decrypt_address(),
            'commune': complaint.commune,
            'type': complaint.complaint_type,
            'problem': complaint.problem_description,
            'status': complaint.status,
            'notes': complaint.notes,
            'created_at': complaint.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': complaint.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/complaint/<complaint_id>/update', methods=['POST'])
@login_required
def update_complaint(complaint_id):
    """تحديث حالة الشكوى"""
    try:
        complaint = Complaint.query.get(complaint_id)
        if not complaint:
            return jsonify({'status': 'error', 'message': 'شكوى غير موجودة'}), 404
        
        # التحقق من الصلاحيات
        if current_user.role != 'admin' and current_user.center_id != complaint.center_id:
            return jsonify({'status': 'error', 'message': 'لا توجد صلاحيات'}), 403
        
        data = request.get_json()
        
        old_status = complaint.status
        new_status = data.get('status')
        notes = data.get('notes', '')
        
        if new_status not in COMPLAINT_STATUSES:
            return jsonify({'status': 'error', 'message': 'حالة غير صحيحة'}), 400
        
        complaint.status = new_status
        complaint.notes = notes
        complaint.assigned_to = current_user.username
        
        if new_status == 'حل':
            complaint.resolved_at = datetime.utcnow()
        
        db.session.commit()
        
        log_audit('تحديث شكوى', 'complaint', complaint.id, {
            'old_status': old_status,
            'new_status': new_status
        })
        
        return jsonify({
            'status': 'success',
            'message': 'تم تحديث الشكوى بنجاح'
        })
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/audit-logs')
@require_role('admin')
def get_audit_logs():
    """الحصول على سجلات التدقيق"""
    page = request.args.get('page', 1, type=int)
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(page=page, per_page=50)
    
    return render_template('audit_logs.html', logs=logs)

@app.route('/admin/users')
@require_role('admin')
def manage_users():
    """إدارة المستخدمين"""
    users = User.query.all()
    return render_template('admin_users.html', users=users, centers=ONA_CENTERS)

@app.route('/api/user/add', methods=['POST'])
@require_role('admin')
def add_user():
    """إضافة مستخدم جديد"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        role = data.get('role')
        center_id = data.get('center_id')
        email = data.get('email')

        if not username or not password or not role:
            return jsonify({'status': 'error', 'message': 'بيانات ناقصة'}), 400

        if User.query.filter_by(username=username).first():
            return jsonify({'status': 'error', 'message': 'اسم المستخدم موجود مسبقاً'}), 400

        new_user = User(
            username=username,
            role=role,
            center_id=center_id if role == 'center_manager' else None,
            email=email
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        log_audit('إضافة مستخدم', 'user', new_user.id, {'username': username, 'role': role})
        
        return jsonify({'status': 'success', 'message': 'تم إضافة المستخدم بنجاح'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/user/change_password', methods=['POST'])
@login_required
def change_password():
    """تغيير كلمة المرور"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        new_password = data.get('new_password')

        if not new_password:
            return jsonify({'status': 'error', 'message': 'كلمة المرور مطلوبة'}), 400

        # التحقق من الصلاحيات: الأدمن يمكنه تغيير أي كلمة مرور، المستخدم يغير لنفسه فقط
        if current_user.role != 'admin' and current_user.id != int(user_id):
            return jsonify({'status': 'error', 'message': 'لا توجد صلاحيات'}), 403

        user = User.query.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': 'المستخدم غير موجود'}), 404

        user.set_password(new_password)
        db.session.commit()
        
        log_audit('تغيير كلمة المرور', 'user', user.id)
        
        return jsonify({'status': 'success', 'message': 'تم تغيير كلمة المرور بنجاح'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/api/user/toggle_status', methods=['POST'])
@require_role('admin')
def toggle_user_status():
    """تفعيل/تعطيل مستخدم"""
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'status': 'error', 'message': 'المستخدم غير موجود'}), 404
        
        if user.username == 'admin':
            return jsonify({'status': 'error', 'message': 'لا يمكن تعطيل حساب المسؤول الرئيسي'}), 400

        user.is_active = not user.is_active
        db.session.commit()
        
        action = 'تفعيل' if user.is_active else 'تعطيل'
        log_audit(f'{action} مستخدم', 'user', user.id)
        
        return jsonify({'status': 'success', 'message': f'تم {action} المستخدم بنجاح'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

# معالج الأخطاء
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return render_template('500.html'), 500

def open_browser():
    """فتح المتصفح بعد قليل من الوقت لضمان عمل السرفر"""
    webbrowser.open_new("http://127.0.0.1:5000")

if __name__ == '__main__':
    # تهيئة قاعدة البيانات والتأكد من وجود المستخدمين
    with app.app_context():
        db.create_all()
        if User.query.filter_by(username='admin').first() is None:
            admin = User(username='admin', email='admin@ona.dz', role='admin')
            admin.set_password('admin123')
            db.session.add(admin)
        
        # إنشاء مستخدم لكل مركز إذا لم يكن موجوداً
        for center_id in ONA_CENTERS.keys():
            if User.query.filter_by(username=center_id).first() is None:
                center_user = User(
                    username=center_id,
                    email=f"{center_id}@ona.dz",
                    role='center_manager',
                    center_id=center_id
                )
                center_user.set_password(f"ona2026{center_id}")
                db.session.add(center_user)
        
        db.session.commit()

    print("\n" + "="*50)
    print("Application ONAMob is running on Desktop Mode")
    print("URL: http://127.0.0.1:5000")
    print("="*50 + "\n")

    # تحديد ما إذا كان التطبيق يعمل كـ EXE
    is_exe = hasattr(sys, '_MEIPASS')
    
    # فتح المتصفح تلقائياً في خيط منفصل
    threading.Timer(1.5, open_browser).start()

    # التشغيل العادي مع تعطيل الـ debug عند التشغيل كـ EXE
    app.run(debug=not is_exe, host='127.0.0.1', port=5000)
