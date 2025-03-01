from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner
from kivy.uix.popup import Popup
from kivy.uix.dropdown import DropDown
from kivy.uix.recycleview import RecycleView
from kivy_garden.calendar import CalendarWidget
from kivy.uix.screenmanager import ScreenManager, Screen
import sqlite3
import qrcode
import random
import os
import cv2
from pyzbar import pyzbar
import pandas as pd
from datetime import datetime, timedelta

# إنشاء مجلدات لتخزين الملفات
if not os.path.exists("students"):
    os.makedirs("students")
if not os.path.exists("reports"):
    os.makedirs("reports")

# إنشاء قاعدة البيانات
DATABASE_FILE = "attendance.db"

def create_database():
    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            time TEXT NOT NULL,
            days TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT NOT NULL,
            group_name TEXT NOT NULL,
            attendance TEXT,
            evaluation TEXT
        )
    ''')
    conn.commit()
    conn.close()

create_database()

class Student:
    def __init__(self, name, phone, group):
        self.id = random.randint(10000, 99999)  # توليد ID عشوائي من 5 أرقام
        self.name = name
        self.phone = phone
        self.group = group
        self.attendance = []  # قائمة لتسجيل الحضور
        self.evaluation = {}  # قاموس لتسجيل التقييمات

    def generate_qr_code(self):
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(str(self.id))
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(f"students/{self.name}_QR.png")

class Group:
    def __init__(self, name, time, days):
        self.name = name
        self.time = time
        self.days = days
        self.students = []  # قائمة الطلاب في المجموعة

    def add_student(self, student):
        self.students.append(student)

    def remove_student(self, student_id):
        for student in self.students:
            if student.id == student_id:
                self.students.remove(student)
                return

class AttendanceSystem:
    def __init__(self):
        self.groups = []
        self.students = []
        self.load_data()

    def load_data(self):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM groups")
        groups = cursor.fetchall()
        for group in groups:
            self.groups.append(Group(group[1], group[2], group[3]))

        cursor.execute("SELECT * FROM students")
        students = cursor.fetchall()
        for student in students:
            new_student = Student(student[1], student[2], student[3])
            new_student.attendance = student[4].split(',') if student[4] else []
            new_student.evaluation = eval(student[5]) if student[5] else {}
            self.students.append(new_student)
        conn.close()

    def save_data(self):
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM groups")
        cursor.execute("DELETE FROM students")
        for group in self.groups:
            cursor.execute("INSERT INTO groups (name, time, days) VALUES (?, ?, ?)", (group.name, group.time, group.days))
        for student in self.students:
            cursor.execute("INSERT INTO students (name, phone, group_name, attendance, evaluation) VALUES (?, ?, ?, ?, ?)",
                           (student.name, student.phone, student.group, ','.join(student.attendance), str(student.evaluation)))
        conn.commit()
        conn.close()

    def add_group(self, name, time, days):
        if any(group.name == name for group in self.groups):
            return "هذه المجموعة موجودة بالفعل!"
        new_group = Group(name, time, days)
        self.groups.append(new_group)
        self.save_data()
        return f"تمت إضافة المجموعة: {name}"

    def add_student(self, name, phone, group_name):
        group = next((g for g in self.groups if g.name == group_name), None)
        if not group:
            return "المجموعة غير موجودة!"
        new_student = Student(name, phone, group_name)
        self.students.append(new_student)
        group.add_student(new_student)
        new_student.generate_qr_code()
        self.save_data()
        return f"تمت إضافة الطالب: {name} (ID: {new_student.id})"

    def delete_student(self, student_id):
        student = next((s for s in self.students if s.id == student_id), None)
        if not student:
            return "الطالب غير موجود!"
        self.students.remove(student)
        self.save_data()
        return f"تم حذف الطالب: {student.name}"

    def delete_group(self, group_name):
        group = next((g for g in self.groups if g.name == group_name), None)
        if not group:
            return "المجموعة غير موجودة!"
        self.groups.remove(group)
        self.save_data()
        return f"تم حذف المجموعة: {group_name}"

    def edit_student(self, student_id, new_name, new_phone, new_group):
        student = next((s for s in self.students if s.id == student_id), None)
        if not student:
            return "الطالب غير موجود!"
        student.name = new_name
        student.phone = new_phone
        student.group = new_group
        self.save_data()
        return f"تم تعديل بيانات الطالب: {student.name}"

    def edit_group(self, group_name, new_name, new_time, new_days):
        group = next((g for g in self.groups if g.name == group_name), None)
        if not group:
            return "المجموعة غير موجودة!"
        group.name = new_name
        group.time = new_time
        group.days = new_days
        self.save_data()
        return f"تم تعديل بيانات المجموعة: {group.name}"

    def record_attendance(self, student_id):
        student = next((s for s in self.students if s.id == student_id), None)
        if not student:
            return "الطالب غير موجود!"
        today = datetime.now().strftime("%Y-%m-%d")
        group = next((g for g in self.groups if g.name == student.group), None)
        if not group:
            return "المجموعة غير موجودة!"
        group_days = group.days.split(',')
        today_name = datetime.now().strftime("%A")
        days_mapping = {
            "Saturday": "السبت",
            "Sunday": "الأحد",
            "Monday": "الاثنين",
            "Tuesday": "الثلاثاء",
            "Wednesday": "الأربعاء",
            "Thursday": "الخميس",
            "Friday": "الجمعة"
        }
        today_name_arabic = days_mapping.get(today_name, today_name)
        if today_name_arabic not in group_days:
            return f"اليوم ({today_name_arabic}) ليس من أيام المجموعة!"
        if today in student.attendance:
            return "تم تسجيل حضور هذا الطالب مسبقًا اليوم!"
        student.attendance.append(today)
        self.save_data()
        return f"تم تسجيل حضور الطالب {student.name} بتاريخ {today}"

    def evaluate_student(self, student_id, stars, notes):
        student = next((s for s in self.students if s.id == student_id), None)
        if not student:
            return "الطالب غير موجود!"
        today = datetime.now().strftime("%Y-%m-%d")
        student.evaluation[today] = {"stars": stars, "notes": notes}
        self.save_data()
        return f"تم تقييم الطالب {student.name} بنجاح!"

    def generate_monthly_report(self, student_id, start_date, end_date):
        student = next((s for s in self.students if s.id == student_id), None)
        if not student:
            return "الطالب غير موجود!"
        group = next((g for g in self.groups if g.name == student.group), None)
        if not group:
            return "المجموعة غير موجودة!"
        group_days = group.days.split(',')
        data = {"التاريخ": [], "اليوم": [], "الحضور": [], "التقييم": [], "الملاحظات": []}
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        current_date = start
        days_mapping = {
            "Saturday": "السبت",
            "Sunday": "الأحد",
            "Monday": "الاثنين",
            "Tuesday": "الثلاثاء",
            "Wednesday": "الأربعاء",
            "Thursday": "الخميس",
            "Friday": "الجمعة"
        }
        while current_date <= end:
            date_str = current_date.strftime("%Y-%m-%d")
            day_name = current_date.strftime("%A")
            day_name_arabic = days_mapping.get(day_name, day_name)
            if day_name_arabic in group_days:
                data["التاريخ"].append(date_str)
                data["اليوم"].append(day_name_arabic)
                if date_str in student.attendance:
                    data["الحضور"].append("حاضر")
                    if date_str in student.evaluation:
                        data["التقييم"].append(student.evaluation[date_str]["stars"])
                        data["الملاحظات"].append(student.evaluation[date_str]["notes"])
                    else:
                        data["التقييم"].append("بدون تقييم")
                        data["الملاحظات"].append("بدون ملاحظات")
                else:
                    data["الحضور"].append("غائب")
                    data["التقييم"].append("بدون تقييم")
                    data["الملاحظات"].append("بدون ملاحظات")
            current_date += timedelta(days=1)
        total_days = len(data["التاريخ"])
        present_days = data["الحضور"].count("حاضر")
        absent_days = total_days - present_days
        attendance_percentage = (present_days / total_days) * 100 if total_days > 0 else 0
        absence_percentage = 100 - attendance_percentage if total_days > 0 else 0
        df = pd.DataFrame(data)
        with pd.ExcelWriter(f"reports/{student.name}_report.xlsx", engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='تقرير الحضور')
            workbook = writer.book
            worksheet = writer.sheets['تقرير الحضور']
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'align': 'center',
                'valign': 'vcenter',
                'fg_color': '#4CAF50',
                'border': 1,
                'font_color': 'white'
            })
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            cell_format_green = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
            cell_format_red = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
            for row_num in range(1, len(df) + 1):
                if df.iloc[row_num - 1]['الحضور'] == 'حاضر':
                    worksheet.set_row(row_num, None, cell_format_green)
                else:
                    worksheet.set_row(row_num, None, cell_format_red)
            worksheet.write(len(df) + 2, 0, f"تقرير الحضور للطالب {student.name} (ID: {student.id})")
            worksheet.write(len(df) + 3, 0, f"نسبة الحضور: {attendance_percentage:.2f}%")
            worksheet.write(len(df) + 4, 0, f"نسبة الغياب: {absence_percentage:.2f}%")
            worksheet.write(len(df) + 5, 0, f"حضر: {present_days} مرة")
            worksheet.write(len(df) + 6, 0, f"غاب: {absent_days} مرة")
        return f"تم تصدير التقرير كـ reports/{student.name}_report.xlsx"

    def scan_qr_code(self):
        cap = cv2.VideoCapture(0)
        while True:
            ret, frame = cap.read()
            if not ret:
                return "تعذر الوصول إلى الكاميرا!"
            barcodes = pyzbar.decode(frame)
            for barcode in barcodes:
                student_id = int(barcode.data.decode("utf-8"))
                self.record_attendance(student_id)
                cap.release()
                cv2.destroyAllWindows()
                return f"تم تسجيل حضور الطالب {student_id}"
            cv2.imshow("QR Code Scanner", frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        cap.release()
        cv2.destroyAllWindows()

    def generate_group_report(self, group_name, start_date, end_date):
        group = next((g for g in self.groups if g.name == group_name), None)
        if not group:
            return "المجموعة غير موجودة!"
        data = {"الطالب": [], "الحضور (%)": [], "الغياب (%)": [], "الحضور (عدد)": [], "الغياب (عدد)": [], "التقييم": []}
        for student in group.students:
            total_days = len(student.attendance)
            total_possible_days = len(group.days.split(',')) * 4
            attendance_percentage = (total_days / total_possible_days) * 100
            absence_percentage = 100 - attendance_percentage
            data["الطالب"].append(student.name)
            data["الحضور (%)"].append(f"{attendance_percentage:.2f}%")
            data["الغياب (%)"].append(f"{absence_percentage:.2f}%")
            data["الحضور (عدد)"].append(total_days)
            data["الغياب (عدد)"].append(total_possible_days - total_days)
            data["التقييم"].append(sum([eval["stars"] for eval in student.evaluation.values()]))
        df = pd.DataFrame(data)
        with pd.ExcelWriter(f"reports/{group.name}_group_report.xlsx", engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='تقرير المجموعة')
            workbook = writer.book
            worksheet = writer.sheets['تقرير المجموعة']
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'align': 'center',
                'valign': 'vcenter',
                'fg_color': '#4CAF50',
                'border': 1,
                'font_color': 'white'
            })
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
            cell_format_green = workbook.add_format({'bg_color': '#C6EFCE', 'font_color': '#006100'})
            cell_format_red = workbook.add_format({'bg_color': '#FFC7CE', 'font_color': '#9C0006'})
            for row_num in range(1, len(df) + 1):
                if float(df.iloc[row_num - 1]['الحضور (%)'].strip('%')) >= 50:
                    worksheet.set_row(row_num, None, cell_format_green)
                else:
                    worksheet.set_row(row_num, None, cell_format_red)
            worksheet.write(len(df) + 2, 0, "تقرير المجموعة")
        return f"تم تصدير التقرير كـ reports/{group.name}_group_report.xlsx"

    def export_students_list(self):
        data = {"الطالب": [], "ID": [], "التقييم": []}
        for student in self.students:
            data["الطالب"].append(student.name)
            data["ID"].append(student.id)
            data["التقييم"].append(sum([eval["stars"] for eval in student.evaluation.values()]))
        df = pd.DataFrame(data)
        with pd.ExcelWriter("reports/students_list.xlsx", engine='xlsxwriter') as writer:
            df.to_excel(writer, index=False, sheet_name='قائمة الطلاب')
            workbook = writer.book
            worksheet = writer.sheets['قائمة الطلاب']
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'align': 'center',
                'valign': 'vcenter',
                'fg_color': '#4CAF50',
                'border': 1,
                'font_color': 'white'
            })
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
        return "تم تصدير قائمة الطلاب كـ reports/students_list.xlsx"

class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.system = AttendanceSystem()
        layout = BoxLayout(orientation='vertical')
        btn_add_group = Button(text="إضافة مجموعة", size_hint=(1, 0.1))
        btn_add_group.bind(on_press=self.add_group)
        layout.add_widget(btn_add_group)
        btn_add_student = Button(text="إضافة طالب", size_hint=(1, 0.1))
        btn_add_student.bind(on_press=self.add_student)
        layout.add_widget(btn_add_student)
        btn_manage_groups = Button(text="إدارة المجموعات", size_hint=(1, 0.1))
        btn_manage_groups.bind(on_press=self.manage_groups)
        layout.add_widget(btn_manage_groups)
        btn_manage_students = Button(text="إدارة الطلاب", size_hint=(1, 0.1))
        btn_manage_students.bind(on_press=self.manage_students)
        layout.add_widget(btn_manage_students)
        btn_record_attendance = Button(text="تسجيل الحضور", size_hint=(1, 0.1))
        btn_record_attendance.bind(on_press=self.record_attendance)
        layout.add_widget(btn_record_attendance)
        btn_generate_report = Button(text="عرض التقرير الشهري", size_hint=(1, 0.1))
        btn_generate_report.bind(on_press=self.generate_report)
        layout.add_widget(btn_generate_report)
        btn_group_report = Button(text="تقرير المجموعة", size_hint=(1, 0.1))
        btn_group_report.bind(on_press=self.group_report)
        layout.add_widget(btn_group_report)
        btn_how_to_use = Button(text="طريقة استخدام البرنامج", size_hint=(1, 0.1))
        btn_how_to_use.bind(on_press=self.how_to_use)
        layout.add_widget(btn_how_to_use)
        btn_exit = Button(text="الخروج", size_hint=(1, 0.1))
        btn_exit.bind(on_press=self.exit_app)
        layout.add_widget(btn_exit)
        self.add_widget(layout)

    def add_group(self, instance):
        self.manager.current = 'add_group'

    def add_student(self, instance):
        self.manager.current = 'add_student'

    def manage_groups(self, instance):
        self.manager.current = 'manage_groups'

    def manage_students(self, instance):
        self.manager.current = 'manage_students'

    def record_attendance(self, instance):
        self.manager.current = 'record_attendance'

    def generate_report(self, instance):
        self.manager.current = 'generate_report'

    def group_report(self, instance):
        self.manager.current = 'group_report'

    def how_to_use(self, instance):
        self.manager.current = 'how_to_use'

    def exit_app(self, instance):
        App.get_running_app().stop()

class AddGroupScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        lbl_name = Label(text="اسم المجموعة:", size_hint=(1, 0.1))
        self.entry_name = TextInput(size_hint=(1, 0.1))
        layout.add_widget(lbl_name)
        layout.add_widget(self.entry_name)
        lbl_time = Label(text="وقت المجموعة:", size_hint=(1, 0.1))
        self.entry_time = TextInput(size_hint=(1, 0.1))
        layout.add_widget(lbl_time)
        layout.add_widget(self.entry_time)
        lbl_days = Label(text="أيام المجموعة:", size_hint=(1, 0.1))
        self.days_listbox = Spinner(text="اختر الأيام", values=["السبت", "الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة"], size_hint=(1, 0.1))
        layout.add_widget(lbl_days)
        layout.add_widget(self.days_listbox)
        btn_add = Button(text="إضافة", size_hint=(1, 0.1))
        btn_add.bind(on_press=self.save_group)
        layout.add_widget(btn_add)
        btn_back = Button(text="رجوع", size_hint=(1, 0.1))
        btn_back.bind(on_press=self.go_back)
        layout.add_widget(btn_back)
        self.add_widget(layout)

    def save_group(self, instance):
        name = self.entry_name.text
        time = self.entry_time.text
        days = self.days_listbox.text
        if not name or not time or not days:
            return "يجب ملء جميع الحقول!"
        system = App.get_running_app().system
        result = system.add_group(name, time, days)
        self.manager.current = 'main'

    def go_back(self, instance):
        self.manager.current = 'main'

class AddStudentScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        lbl_name = Label(text="اسم الطالب:", size_hint=(1, 0.1))
        self.entry_name = TextInput(size_hint=(1, 0.1))
        layout.add_widget(lbl_name)
        layout.add_widget(self.entry_name)
        lbl_phone = Label(text="رقم الهاتف:", size_hint=(1, 0.1))
        self.entry_phone = TextInput(size_hint=(1, 0.1))
        layout.add_widget(lbl_phone)
        layout.add_widget(self.entry_phone)
        lbl_group = Label(text="اسم المجموعة:", size_hint=(1, 0.1))
        self.group_spinner = Spinner(text="اختر المجموعة", size_hint=(1, 0.1))
        layout.add_widget(lbl_group)
        layout.add_widget(self.group_spinner)
        btn_add = Button(text="إضافة", size_hint=(1, 0.1))
        btn_add.bind(on_press=self.save_student)
        layout.add_widget(btn_add)
        btn_back = Button(text="رجوع", size_hint=(1, 0.1))
        btn_back.bind(on_press=self.go_back)
        layout.add_widget(btn_back)
        self.add_widget(layout)

    def save_student(self, instance):
        name = self.entry_name.text
        phone = self.entry_phone.text
        group = self.group_spinner.text
        if not name or not phone or not group:
            return "يجب ملء جميع الحقول!"
        system = App.get_running_app().system
        result = system.add_student(name, phone, group)
        self.manager.current = 'main'

    def go_back(self, instance):
        self.manager.current = 'main'

class ManageGroupsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        lbl_groups = Label(text="المجموعات:", size_hint=(1, 0.1))
        layout.add_widget(lbl_groups)
        self.groups_list = BoxLayout(orientation='vertical', size_hint=(1, 0.8))
        layout.add_widget(self.groups_list)
        btn_back = Button(text="رجوع", size_hint=(1, 0.1))
        btn_back.bind(on_press=self.go_back)
        layout.add_widget(btn_back)
        self.add_widget(layout)

    def on_enter(self):
        self.groups_list.clear_widgets()
        system = App.get_running_app().system
        for group in system.groups:
            group_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
            lbl_group = Label(text=f"المجموعة: {group.name} (الوقت: {group.time}, الأيام: {group.days})", size_hint=(0.7, 1))
            btn_edit = Button(text="تعديل", size_hint=(0.15, 1))
            btn_edit.bind(on_press=lambda instance, g=group.name: self.edit_group(g))
            btn_delete = Button(text="حذف", size_hint=(0.15, 1))
            btn_delete.bind(on_press=lambda instance, g=group.name: self.delete_group(g))
            group_layout.add_widget(lbl_group)
            group_layout.add_widget(btn_edit)
            group_layout.add_widget(btn_delete)
            self.groups_list.add_widget(group_layout)

    def edit_group(self, group_name):
        self.manager.current = 'edit_group'

    def delete_group(self, group_name):
        system = App.get_running_app().system
        result = system.delete_group(group_name)
        self.on_enter()

    def go_back(self, instance):
        self.manager.current = 'main'

class ManageStudentsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        lbl_students = Label(text="الطلاب:", size_hint=(1, 0.1))
        layout.add_widget(lbl_students)
        self.students_list = BoxLayout(orientation='vertical', size_hint=(1, 0.8))
        layout.add_widget(self.students_list)
        btn_back = Button(text="رجوع", size_hint=(1, 0.1))
        btn_back.bind(on_press=self.go_back)
        layout.add_widget(btn_back)
        self.add_widget(layout)

    def on_enter(self):
        self.students_list.clear_widgets()
        system = App.get_running_app().system
        for student in system.students:
            student_layout = BoxLayout(orientation='horizontal', size_hint=(1, 0.1))
            lbl_student = Label(text=f"الطالب: {student.name} (ID: {student.id}, المجموعة: {student.group})", size_hint=(0.7, 1))
            btn_edit = Button(text="تعديل", size_hint=(0.15, 1))
            btn_edit.bind(on_press=lambda instance, s=student.id: self.edit_student(s))
            btn_evaluate = Button(text="تقييم", size_hint=(0.15, 1))
            btn_evaluate.bind(on_press=lambda instance, s=student.id: self.evaluate_student(s))
            btn_delete = Button(text="حذف", size_hint=(0.15, 1))
            btn_delete.bind(on_press=lambda instance, s=student.id: self.delete_student(s))
            student_layout.add_widget(lbl_student)
            student_layout.add_widget(btn_edit)
            student_layout.add_widget(btn_evaluate)
            student_layout.add_widget(btn_delete)
            self.students_list.add_widget(student_layout)

    def edit_student(self, student_id):
        self.manager.current = 'edit_student'

    def evaluate_student(self, student_id):
        self.manager.current = 'evaluate_student'

    def delete_student(self, student_id):
        system = App.get_running_app().system
        result = system.delete_student(student_id)
        self.on_enter()

    def go_back(self, instance):
        self.manager.current = 'main'

class RecordAttendanceScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        btn_scan_qr = Button(text="مسح QR Code", size_hint=(1, 0.1))
        btn_scan_qr.bind(on_press=self.scan_qr)
        layout.add_widget(btn_scan_qr)
        lbl_id = Label(text="ID الطالب:", size_hint=(1, 0.1))
        self.entry_id = TextInput(size_hint=(1, 0.1))
        layout.add_widget(lbl_id)
        layout.add_widget(self.entry_id)
        btn_record = Button(text="تسجيل الحضور", size_hint=(1, 0.1))
        btn_record.bind(on_press=self.record)
        layout.add_widget(btn_record)
        btn_back = Button(text="رجوع", size_hint=(1, 0.1))
        btn_back.bind(on_press=self.go_back)
        layout.add_widget(btn_back)
        self.add_widget(layout)

    def scan_qr(self, instance):
        system = App.get_running_app().system
        result = system.scan_qr_code()
        self.manager.current = 'main'

    def record(self, instance):
        student_id = self.entry_id.text
        if not student_id:
            return "يجب إدخال ID الطالب!"
        system = App.get_running_app().system
        result = system.record_attendance(int(student_id))
        self.manager.current = 'main'

    def go_back(self, instance):
        self.manager.current = 'main'

class GenerateReportScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        lbl_id = Label(text="ID الطالب:", size_hint=(1, 0.1))
        self.entry_id = TextInput(size_hint=(1, 0.1))
        layout.add_widget(lbl_id)
        layout.add_widget(self.entry_id)
        lbl_start = Label(text="تاريخ البداية (YYYY-MM-DD):", size_hint=(1, 0.1))
        self.entry_start = TextInput(size_hint=(1, 0.1))
        layout.add_widget(lbl_start)
        layout.add_widget(self.entry_start)
        lbl_end = Label(text="تاريخ النهاية (YYYY-MM-DD):", size_hint=(1, 0.1))
        self.entry_end = TextInput(size_hint=(1, 0.1))
        layout.add_widget(lbl_end)
        layout.add_widget(self.entry_end)
        btn_generate = Button(text="عرض التقرير", size_hint=(1, 0.1))
        btn_generate.bind(on_press=self.generate)
        layout.add_widget(btn_generate)
        btn_export = Button(text="تصدير Excel", size_hint=(1, 0.1))
        btn_export.bind(on_press=self.export)
        layout.add_widget(btn_export)
        btn_back = Button(text="رجوع", size_hint=(1, 0.1))
        btn_back.bind(on_press=self.go_back)
        layout.add_widget(btn_back)
        self.add_widget(layout)

    def generate(self, instance):
        student_id = self.entry_id.text
        start_date = self.entry_start.text
        end_date = self.entry_end.text
        if not student_id or not start_date or not end_date:
            return "يجب ملء جميع الحقول!"
        system = App.get_running_app().system
        result = system.generate_monthly_report(int(student_id), start_date, end_date)
        self.manager.current = 'main'

    def export(self, instance):
        student_id = self.entry_id.text
        start_date = self.entry_start.text
        end_date = self.entry_end.text
        if not student_id or not start_date or not end_date:
            return "يجب ملء جميع الحقول!"
        system = App.get_running_app().system
        result = system.export_report_excel(int(student_id), start_date, end_date)
        self.manager.current = 'main'

    def go_back(self, instance):
        self.manager.current = 'main'

class GroupReportScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        lbl_group = Label(text="اسم المجموعة:", size_hint=(1, 0.1))
        self.group_spinner = Spinner(text="اختر المجموعة", size_hint=(1, 0.1))
        layout.add_widget(lbl_group)
        layout.add_widget(self.group_spinner)
        lbl_start = Label(text="تاريخ البداية (YYYY-MM-DD):", size_hint=(1, 0.1))
        self.entry_start = TextInput(size_hint=(1, 0.1))
        layout.add_widget(lbl_start)
        layout.add_widget(self.entry_start)
        lbl_end = Label(text="تاريخ النهاية (YYYY-MM-DD):", size_hint=(1, 0.1))
        self.entry_end = TextInput(size_hint=(1, 0.1))
        layout.add_widget(lbl_end)
        layout.add_widget(self.entry_end)
        btn_generate = Button(text="عرض التقرير", size_hint=(1, 0.1))
        btn_generate.bind(on_press=self.generate)
        layout.add_widget(btn_generate)
        btn_export = Button(text="تصدير Excel", size_hint=(1, 0.1))
        btn_export.bind(on_press=self.export)
        layout.add_widget(btn_export)
        btn_back = Button(text="رجوع", size_hint=(1, 0.1))
        btn_back.bind(on_press=self.go_back)
        layout.add_widget(btn_back)
        self.add_widget(layout)

    def generate(self, instance):
        group_name = self.group_spinner.text
        start_date = self.entry_start.text
        end_date = self.entry_end.text
        if not group_name or not start_date or not end_date:
            return "يجب ملء جميع الحقول!"
        system = App.get_running_app().system
        result = system.generate_group_report(group_name, start_date, end_date)
        self.manager.current = 'main'

    def export(self, instance):
        group_name = self.group_spinner.text
        start_date = self.entry_start.text
        end_date = self.entry_end.text
        if not group_name or not start_date or not end_date:
            return "يجب ملء جميع الحقول!"
        system = App.get_running_app().system
        result = system.export_group_report_excel(group_name, start_date, end_date)
        self.manager.current = 'main'

    def go_back(self, instance):
        self.manager.current = 'main'

class HowToUseScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical')
        lbl_instructions = Label(text="""
        طريقة استخدام البرنامج:
        1. إضافة مجموعة: قم بإضافة مجموعة جديدة مع تحديد الوقت والأيام.
        2. إضافة طالب: قم بإضافة طالب جديد واختيار المجموعة المناسبة.
        3. تسجيل الحضور: استخدم الكاميرا لمسح QR Code الطالب أو أدخل ID يدويًا.
        4. إدارة الطلاب: يمكنك تعديل أو حذف الطلاب وإضافة تقييمات لهم.
        5. عرض التقارير: قم بإنشاء تقارير الحضور الشهرية أو تقارير المجموعات.
        6. تصدير البيانات: قم بتصدير قائمة الطلاب أو التقارير كملفات Excel.

        مع تحيات،
        المبرمج
        Pavly Hany
        """, size_hint=(1, 0.9), halign='left', valign='top')
        layout.add_widget(lbl_instructions)
        btn_back = Button(text="رجوع", size_hint=(1, 0.1))
        btn_back.bind(on_press=self.go_back)
        layout.add_widget(btn_back)
        self.add_widget(layout)

    def go_back(self, instance):
        self.manager.current = 'main'

class AttendanceApp(App):
    def build(self):
        self.system = AttendanceSystem()
        sm = ScreenManager()
        sm.add_widget(MainScreen(name='main'))
        sm.add_widget(AddGroupScreen(name='add_group'))
        sm.add_widget(AddStudentScreen(name='add_student'))
        sm.add_widget(ManageGroupsScreen(name='manage_groups'))
        sm.add_widget(ManageStudentsScreen(name='manage_students'))
        sm.add_widget(RecordAttendanceScreen(name='record_attendance'))
        sm.add_widget(GenerateReportScreen(name='generate_report'))
        sm.add_widget(GroupReportScreen(name='group_report'))
        sm.add_widget(HowToUseScreen(name='how_to_use'))
        return sm

if __name__ == "__main__":
    AttendanceApp().run()
