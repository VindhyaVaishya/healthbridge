# HealthBridge 🏥
### Hospital Management System

HealthBridge is a web-based Hospital Management System designed to simplify hospital operations and improve patient management through a user-friendly interface.

The system provides separate portals for patients, doctors, and hospital staff, helping manage appointments, patient records, hospital services, and administrative activities.

## ✨ Features

### 👤 Patient Portal
- Patient registration and login
- Automatic Patient ID generation
- Patient dashboard
- Book doctor appointments
- View appointment details and token numbers
- Hospital map and facility information

### 🩺 Doctor Portal
- Doctor registration and login
- Doctor dashboard
- View patient appointments
- Manage doctor availability
- View patient-related information

### 🏥 Staff Portal
- Staff management
- Staff attendance
- Doctor attendance
- Patient billing management
- Staff service requests

### 📅 Appointment Management
- Appointment booking
- Doctor availability and time slots
- Automatic token number generation
- Appointment records

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend programming |
| Flask | Web framework |
| HTML5 | Page structure |
| CSS3 | Styling and design |
| JavaScript | Interactive functionality |
| SQLite | Database management |
| VS Code | Development environment |
| Git & GitHub | Version control |

## 📂 Project Structure

```text
healthbridge/
│
├── app.py
├── database.py
├── requirements.txt
├── .gitignore
│
├── static/
│   └── style.css
│
└── templates/
    ├── index.html
    ├── patient_login.html
    ├── doctor_login.html
    ├── doctor_dashboard.html
    └── other HTML pages
```

## ⚙️ Installation and Setup

### 1. Clone the Repository

```bash
git clone https://github.com/VindhyaVaishya/healthbridge.git
```

### 2. Open the Project Folder

```bash
cd healthbridge
```

### 3. Create a Virtual Environment

```bash
python -m venv venv
```

### 4. Activate the Virtual Environment

For Windows PowerShell:

```bash
venv\Scripts\Activate
```

### 5. Install Dependencies

```bash
pip install -r requirements.txt
```

### 6. Run the Application

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000/
```

## 🗄️ Database

HealthBridge uses SQLite for storing application data.

The database handles information related to patients, doctors, appointments, staff, attendance, and billing.

## 🎯 Project Objective

The main objective of HealthBridge is to provide a centralized and easy-to-use platform for hospital management, reduce manual administrative work, and improve coordination between patients, doctors, and hospital staff.

## 👩‍💻 Developed By

**Vindhya Vaishya**

B.Tech – Computer Science and Engineering (Artificial Intelligence)

## 📌 Project Information

- Project Name: HealthBridge
- Project Type: Hospital Management System
- Development Status: Academic Project
- Backend: Python Flask
- Database: SQLite

---

**HealthBridge – Your Health, Our Priority.** 💛
