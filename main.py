import flet as ft
import webbrowser
import os
import sys
import requests
from datetime import datetime

# قاموس الترجمة المدمج لضمان العمل على جميع الأجهزة
TRANSLATIONS = {
    'ar': {
        'title': 'ONAMob - الديوان الوطني للتطهير',
        'slogan': 'الماء يطهر كل شيء، الديوان يطهر الماء',
        'submit_complaint': 'تقديم شكوى',
        'track_complaint': 'تتبع شكوى',
        'green_number': 'الرقم الأخضر',
        'name': 'الاسم الكامل',
        'id_card': 'رقم بطاقة التعريف الوطنية',
        'birth_date': 'تاريخ الازدياد',
        'birth_place': 'مكان الازدياد',
        'phone': 'رقم الهاتف',
        'address': 'العنوان بالتفصيل',
        'commune': 'البلدية',
        'type': 'نوع المشكلة',
        'problem': 'تفاصيل المشكلة',
        'submit': 'إرسال الشكوى',
        'tracking_id': 'رقم التتبع',
        'status': 'الحالة',
        'created_at': 'تاريخ التقديم',
        'search': 'بحث',
        'fill_all': 'يرجى ملء جميع الحقول المطلوبة',
        'success_msg': 'تم استقبال شكواك بنجاح',
        'error_msg': 'فشل الإرسال، تحقق من الاتصال',
        'error_tracking_not_found': 'رقم التتبع غير موجود',
        'type_leak': 'تسرب مياه',
        'type_clog': 'انسداد بالوعة',
        'type_smell': 'روائح كريهة',
        'type_cut': 'انقطاع المياه',
        'type_other': 'أخرى',
        'complaint_info': 'يرجى إدخال البيانات الشخصية وتفاصيل المشكلة'
    },
    'fr': {
        'title': 'ONAMob - ONA',
        'slogan': "L'eau lave tout, l'ONA épure l'eau",
        'submit_complaint': 'Déposer une plainte',
        'track_complaint': 'Suivre une plainte',
        'green_number': 'Numéro Vert',
        'name': 'Nom Complet',
        'id_card': 'NIN (Carte d\'identité)',
        'birth_date': 'Date de Naissance',
        'birth_place': 'Lieu de Naissance',
        'phone': 'N° de Téléphone',
        'address': 'Adresse Complète',
        'commune': 'Commune',
        'type': 'Type de problème',
        'problem': 'Détails du problème',
        'submit': 'Envoyer la plainte',
        'tracking_id': 'N° de Suivi',
        'status': 'État',
        'created_at': 'Date de dépôt',
        'search': 'Chercher',
        'fill_all': 'Veuillez remplir tous les champs',
        'success_msg': 'Plainte reçue avec succès',
        'error_msg': "Échec de l'envoi, vérifiez la connexion",
        'error_tracking_not_found': 'N° de suivi inexistant',
        'type_leak': "Fuite d'eau",
        'type_clog': 'Obstruction',
        'type_smell': 'Mauvaises odeurs',
        'type_cut': "Coupure d'eau",
        'type_other': 'Autre',
        'complaint_info': 'Veuillez saisir vos données et les détails du problème'
    }
}

# الإعدادات العامة
API_BASE_URL = os.getenv("API_URL", "http://127.0.0.1:5000")
COLOR_PRIMARY = "#008751"
COLOR_SECONDARY = "#006b40"
COLOR_BG = "#F8F9FA"

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# بيانات المراكز
ONA_DATA = [
    {'id': 'ferdjioua', 'name': 'مركز فرجيوة', 'phone': '0666583131', 'communes': ['فرجيوة', 'عين البضاء احريش', 'بني قشة', 'تسدان حدادة', 'العياضي برباس', 'مينار زارزة', 'بوحاتم', 'بن يحي عبد الرحمان']},
    {'id': 'mila', 'name': 'مركز ميلة', 'phone': '0770867866', 'communes': ['ميلة', 'سيدي خليفة', 'عين التين']},
    {'id': 'chelghoum', 'name': 'مركز شلغوم العيد', 'phone': '0770619446', 'communes': ['شلغوم العيد', 'واد العثمانية', 'عين الملوك']},
    {'id': 'tadjenanet', 'name': 'مركز تاجنانت', 'phone': '0770973162', 'communes': ['تاجنانت', 'المشيرة', 'واد خلوف']},
    {'id': 'teleghma', 'name': 'مركز التلاغمة', 'phone': '0664718445', 'communes': ['التلاغمة', 'واد سقان']},
    {'id': 'grarem', 'name': 'مركز القرارم قوقة', 'phone': '0673025681', 'communes': ['القرارم قوقة', 'حمالة']},
    {'id': 'sidimerouane', 'name': 'مركز سيدي مروان', 'phone': '0770943276', 'communes': ['سيدي مروان', 'الشيقارة']},
    {'id': 'ouedendja', 'name': 'مركز وادي انجاء', 'phone': '0770603804', 'communes': ['واد انجاء', 'احمد راشدي', 'تيبرقنت', 'الرواشد', 'زغاية']},
    {'id': 'terraibainen', 'name': 'مركز ترعي باينان', 'phone': '0770278634', 'communes': ['ترعي باينان', 'تسالة لمطاعي', 'اعميرة آراس']}
]

def main(page: ft.Page):
    page.title = "ONAMob"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0
    
    # تحسين العرض للهواتف والحواسب
    if page.platform in [ft.PagePlatform.WINDOWS, ft.PagePlatform.MACOS, ft.PagePlatform.LINUX]:
        page.window_width = 400
        page.window_height = 800
    
    # اللغة الحالية (افتراضياً العربية)
    current_lang = "ar"
    
    def get_text(key):
        return TRANSLATIONS[current_lang].get(key, key)

    def change_lang(e):
        nonlocal current_lang
        current_lang = "fr" if current_lang == "ar" else "ar"
        page.rtl = (current_lang == "ar")
        build_ui()
        page.update()

    # page.fonts = {
    #     "Cairo": "https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap"
    # }
    # page.theme = ft.Theme(font_family="Cairo")

    # عناصر واجهة المستخدم (تُنشأ مرة واحدة ويتم تحديث قيمها)
    name_input = ft.TextField(border_radius=10, prefix_icon=ft.icons.PERSON)
    id_card_input = ft.TextField(border_radius=10, prefix_icon=ft.icons.CREDIT_CARD)
    birth_date_input = ft.TextField(border_radius=10, placeholder="1990-01-01", prefix_icon=ft.icons.CALENDAR_MONTH)
    birth_place_input = ft.TextField(border_radius=10, prefix_icon=ft.icons.LOCATION_CITY)
    phone_input = ft.TextField(border_radius=10, prefix_icon=ft.icons.PHONE_ANDROID)
    address_input = ft.TextField(border_radius=10, prefix_icon=ft.icons.HOME)
    
    all_communes = sorted([com for center in ONA_DATA for com in center['communes']])
    commune_dropdown = ft.Dropdown(options=[ft.dropdown.Option(c) for c in all_communes], border_radius=10)
    
    type_dropdown = ft.Dropdown(border_radius=10)
    problem_input = ft.TextField(multiline=True, min_lines=3, border_radius=10)
    track_input = ft.TextField(border_radius=10, prefix_icon=ft.icons.SEARCH)
    
    submit_btn = ft.ElevatedButton(
        bgcolor=COLOR_PRIMARY, 
        color="white", 
        height=50,
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
    )

    loading_indicator = ft.ProgressBar(visible=False, color=COLOR_PRIMARY)
    track_loading = ft.ProgressBar(visible=False, color=COLOR_PRIMARY)
    track_result = ft.Column(spacing=10)

    # الحاويات الرئيسية
    home_view = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    complaint_view = ft.Column(visible=False, scroll=ft.ScrollMode.AUTO, expand=True)
    track_view = ft.Column(visible=False, scroll=ft.ScrollMode.AUTO, expand=True)
    branches_view = ft.Column(visible=False, scroll=ft.ScrollMode.AUTO, expand=True)

    def show_snack(text, color="green"):
        page.snack_bar = ft.SnackBar(ft.Text(text), bgcolor=color)
        page.snack_bar.open = True
        page.update()

    def handle_submit(e):
        if not all([name_input.value, phone_input.value, id_card_input.value, commune_dropdown.value]):
            show_snack(get_text('fill_all'), "red")
            return

        loading_indicator.visible = True
        submit_btn.disabled = True
        page.update()

        payload = {
            "name": name_input.value,
            "phone": phone_input.value,
            "id_card": id_card_input.value,
            "birth_date": birth_date_input.value or "1900-01-01",
            "birth_place": birth_place_input.value or "-",
            "address": address_input.value or "-",
            "commune": commune_dropdown.value,
            "type": type_dropdown.value,
            "problem": problem_input.value or "..."
        }

        try:
            response = requests.post(f"{API_BASE_URL}/api/submit_complaint", json=payload, timeout=10)
            if response.status_code == 201:
                res = response.json()
                show_snack(f"{get_text('success_msg')}! ID: {res['tracking_id']}")
                for f in [name_input, id_card_input, birth_date_input, birth_place_input, phone_input, address_input, problem_input]:
                    f.value = ""
                commune_dropdown.value = None
            else:
                show_snack(get_text('error_msg'), "red")
        except Exception as ex:
            show_snack(f"Error: {str(ex)}", "red")
        
        loading_indicator.visible = False
        submit_btn.disabled = False
        page.update()

    def handle_search(e):
        if not track_input.value: return
        track_result.controls.clear()
        track_loading.visible = True
        page.update()
        try:
            response = requests.get(f"{API_BASE_URL}/api/track/{track_input.value}", timeout=10)
            if response.status_code == 200:
                data = response.json()
                status_text = data['complaint_status']
                if current_lang == "fr":
                    status_text = {"جديد": "Nouveau", "قيد المعالجة": "En cours", "حل": "Résolu"}.get(status_text, status_text)
                
                track_result.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.ListTile(
                                leading=ft.Icon(ft.icons.TRACK_CHANGES, color=COLOR_PRIMARY),
                                title=ft.Text(f"{get_text('tracking_id')}: {data['tracking_id']}", weight="bold"),
                                subtitle=ft.Text(f"{get_text('created_at')}: {data['created_at']}"),
                            ),
                            ft.Divider(),
                            ft.Padding(
                                padding=ft.padding.only(left=20, right=20, bottom=10),
                                content=ft.Column([
                                    ft.Row([ft.Text(f"{get_text('status')}:", weight="bold"), ft.Badge(text=status_text, bgcolor=COLOR_PRIMARY)]),
                                    ft.Text(f"{get_text('type')}: {data['type']}"),
                                    ft.Text(f"{get_text('commune')}: {data['commune']}"),
                                ], spacing=5)
                            )
                        ]),
                        bgcolor="white", border_radius=15, border=ft.border.all(1, "#EEEEEE")
                    )
                )
            else:
                track_result.controls.append(ft.Text(get_text('error_tracking_not_found'), color="red", text_align="center"))
        except:
            track_result.controls.append(ft.Text("Error", color="red"))
        track_loading.visible = False
        page.update()

    nav_bar = ft.NavigationBar(
        bgcolor="white",
        elevation=10,
        on_change=lambda e: navigate_to(e.control.selected_index)
    )

    def navigate_to(idx):
        nav_bar.selected_index = idx
        home_view.visible = (idx == 0)
        complaint_view.visible = (idx == 1)
        track_view.visible = (idx == 2)
        branches_view.visible = (idx == 3)
        page.update()

    def build_ui():
        lang = current_lang
        page.rtl = (lang == "ar")
        
        # تحديث نصوص المدخلات
        name_input.label = get_text('name')
        id_card_input.label = get_text('id_card')
        birth_date_input.label = get_text('birth_date')
        birth_place_input.label = get_text('birth_place')
        phone_input.label = get_text('phone')
        address_input.label = get_text('address')
        commune_dropdown.label = get_text('commune')
        problem_input.label = get_text('problem')
        track_input.label = get_text('tracking_id')
        submit_btn.text = get_text('submit')
        submit_btn.on_click = handle_submit
        
        type_dropdown.label = get_text('type')
        type_dropdown.options = [
            ft.dropdown.Option("تسرب مياه" if lang=="ar" else "Fuite d'eau", get_text('type_leak')),
            ft.dropdown.Option("انسداد بالوعة" if lang=="ar" else "Obstruction", get_text('type_clog')),
            ft.dropdown.Option("روائح كريهة" if lang=="ar" else "Mauvaises odeurs", get_text('type_smell')),
            ft.dropdown.Option("انقطاع المياه" if lang=="ar" else "Coupure d'eau", get_text('type_cut')),
            ft.dropdown.Option("أخرى" if lang=="ar" else "Autre", get_text('type_other')),
        ]
        type_dropdown.value = type_dropdown.options[0].key

        # تحديث القائمة السفلية
        nav_bar.destinations = [
            ft.NavigationBarDestination(icon=ft.icons.HOME_OUTLINED, selected_icon=ft.icons.HOME, label="الرئيسية" if lang=="ar" else "Accueil"),
            ft.NavigationBarDestination(icon=ft.icons.ADD_COMMENT_OUTLINED, selected_icon=ft.icons.ADD_COMMENT, label=get_text('submit_complaint')),
            ft.NavigationBarDestination(icon=ft.icons.TRACK_CHANGES, label="تتبع" if lang=="ar" else "Suivi"),
            ft.NavigationBarDestination(icon=ft.icons.MAP_OUTLINED, selected_icon=ft.icons.MAP, label="الفروع" if lang=="ar" else "Agences"),
        ]

        # إعادة بناء محتوى الصفحات
        home_view.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Row([ft.TextButton("Français" if lang=="ar" else "العربية", on_click=change_lang, icon=ft.icons.LANGUAGE)], alignment=ft.MainAxisAlignment.END),
                    ft.Image(src="assets/logo.png", height=100),
                    ft.Text(get_text('title'), size=22, weight="bold", color=COLOR_PRIMARY, text_align=ft.TextAlign.CENTER),
                    ft.Text(get_text('slogan'), size=12, italic=True, color="grey700"),
                    ft.Container(height=20),
                    ft.Row([
                        ft.Container(
                            content=ft.Column([ft.Icon(ft.icons.EDIT_NOTE, size=35, color=COLOR_PRIMARY), ft.Text(get_text('submit_complaint'), size=12, weight="bold")], horizontal_alignment="center"),
                            bgcolor="white", padding=15, border_radius=15, expand=True, on_click=lambda _: navigate_to(1),
                            shadow=ft.BoxShadow(blur_radius=10, color="#10000000")
                        ),
                        ft.Container(
                            content=ft.Column([ft.Icon(ft.icons.SEARCH, size=35, color=COLOR_PRIMARY), ft.Text(get_text('track_complaint'), size=12, weight="bold")], horizontal_alignment="center"),
                            bgcolor="white", padding=15, border_radius=15, expand=True, on_click=lambda _: navigate_to(2),
                            shadow=ft.BoxShadow(blur_radius=10, color="#10000000")
                        ),
                    ], spacing=15),
                    ft.Container(height=20),
                    ft.Container(
                        content=ft.Row([ft.Icon(ft.icons.PHONE_IN_TALK, color=COLOR_PRIMARY), ft.Text(f"{get_text('green_number')}: 0770 97 17 00", size=14, weight="bold")], alignment="center"),
                        bgcolor="#F0FFF4", padding=12, border_radius=12, border=ft.border.all(1, COLOR_PRIMARY),
                        on_click=lambda _: webbrowser.open("tel:0770971700")
                    )
                ], horizontal_alignment="center"),
                padding=25
            )
        ]

        complaint_view.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text(get_text('submit_complaint'), size=20, weight="bold", color=COLOR_PRIMARY),
                    ft.Text(get_text('complaint_info'), size=12, color="grey600"),
                    ft.Divider(),
                    loading_indicator,
                    name_input, id_card_input, 
                    ft.Row([birth_date_input, birth_place_input]),
                    phone_input, address_input,
                    commune_dropdown, type_dropdown, problem_input,
                    submit_btn,
                    ft.Container(height=20)
                ], spacing=12),
                padding=20, bgcolor="white", border_radius=20, margin=10
            )
        ]

        track_view.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text(get_text('track_complaint'), size=20, weight="bold", color=COLOR_PRIMARY),
                    ft.Divider(),
                    track_input,
                    ft.ElevatedButton(get_text('search'), on_click=handle_search, bgcolor=COLOR_PRIMARY, color="white", height=45, width=float("inf")),
                    track_loading,
                    track_result
                ], spacing=15),
                padding=20, bgcolor="white", border_radius=20, margin=10
            )
        ]

        branches_list = ft.Column(spacing=10)
        for c in ONA_DATA:
            branches_list.controls.append(
                ft.Container(
                    content=ft.ListTile(
                        leading=ft.Icon(ft.icons.LOCATION_ON, color=COLOR_PRIMARY),
                        title=ft.Text(c['name'], size=14, weight="bold"),
                        subtitle=ft.Text(f"Tél: {c['phone']}", size=12),
                        trailing=ft.IconButton(ft.icons.CALL, icon_size=20, icon_color=COLOR_PRIMARY, on_click=lambda _, p=c['phone']: webbrowser.open(f"tel:{p}")),
                    ),
                    bgcolor="white", border_radius=10, shadow=ft.BoxShadow(blur_radius=5, color="#05000000")
                )
            )
        
        branches_view.controls = [
            ft.Container(
                content=ft.Column([
                    ft.Text("فروعنا" if lang=="ar" else "Nos Agences", size=20, weight="bold", color=COLOR_PRIMARY),
                    ft.Divider(),
                    branches_list
                ]), padding=20
            )
        ]

    build_ui()
    page.add(
        ft.Stack([
            ft.Container(gradient=ft.LinearGradient(begin=ft.alignment.top_left, end=ft.alignment.bottom_right, colors=[COLOR_PRIMARY, COLOR_SECONDARY]), expand=True),
            ft.Column([
                ft.Container(content=ft.Stack([home_view, complaint_view, track_view, branches_view]), expand=True),
                nav_bar
            ], spacing=0, expand=True)
        ], expand=True)
    )

if __name__ == "__main__":
    ft.app(target=main, assets_dir="assets")
