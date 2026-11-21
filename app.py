
from flask import Flask, render_template, request, redirect, session, jsonify, flash
from database import get_db_connection, create_tables
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import date, datetime

app = Flask(__name__)
app.secret_key = "healthbridge_dev_secret_change_later"


@app.route("/")
def home():
    return render_template("index.html")



@app.route("/doctor-login", methods=["GET", "POST"])
def doctor_login():
    if request.method == "POST":
        doctor_id = request.form.get("doctor_id", "").strip()
        password = request.form.get("password", "")

        conn = get_db_connection()
        doctor = conn.execute(
            "SELECT * FROM doctors WHERE doctor_id = ?",
            (doctor_id,)
        ).fetchone()
        conn.close()

        if doctor and check_password_hash(doctor["password"], password):
            session.clear()
            session["doctor_id"] = doctor["doctor_id"]

            if not doctor["specialization"]:
                return redirect("/doctor-specialization")

            return redirect("/doctor-dashboard")

        return render_template(
            "doctor_login.html",
            error="Invalid Doctor ID or Password."
        )

    return render_template("doctor_login.html")

@app.route("/doctor-register", methods=["GET", "POST"])
def doctor_register():

    if request.method == "POST":
        full_name = request.form["full_name"]
        specialization = request.form["specialization"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match!")
            return redirect("/doctor-register")

        conn = get_db_connection()

        try:
            doctor_count = conn.execute(
                "SELECT COUNT(*) FROM doctors"
            ).fetchone()[0]

            doctor_id = f"HB-DOC-{doctor_count + 1:04d}"

            hashed_password = generate_password_hash(password)

            conn.execute("""
                INSERT INTO doctors
                (doctor_id, full_name, specialization, password)
                VALUES (?, ?, ?, ?)
            """, (doctor_id, full_name, specialization, hashed_password))

            conn.commit()

            flash(f"Registration successful! Your Doctor ID is {doctor_id}")
            return redirect("/doctor-login")

        except sqlite3.IntegrityError:
            flash("Registration failed. Please try again.")

        finally:
            conn.close()

    return render_template("doctor_register.html")


@app.route("/doctor-specialization", methods=["GET", "POST"])
def doctor_specialization():
    if "doctor_id" not in session:
        return redirect("/doctor-login")

    if request.method == "POST":
        doctor_name = request.form.get("doctor_name", "").strip()
        specialization = request.form.get("specialization", "")

        conn = get_db_connection()
        conn.execute("""
            UPDATE doctors
            SET full_name = ?, specialization = ?
            WHERE doctor_id = ?
        """, (doctor_name, specialization, session["doctor_id"]))

        conn.commit()
        conn.close()

        return redirect("/doctor-dashboard")
    
    conn = get_db_connection()
    doctor = conn.execute(
        "SELECT * FROM doctors WHERE doctor_id = ?",
        (session["doctor_id"],)
    ).fetchone()
    conn.close()

    return render_template("doctor_specialization.html", doctor=doctor)



@app.route("/doctor-dashboard")
def doctor_dashboard():
    if "doctor_id" not in session:
        return redirect("/doctor-login")

    conn = get_db_connection()

    doctor = conn.execute(
        "SELECT * FROM doctors WHERE doctor_id = ?",
        (session["doctor_id"],)
    ).fetchone()

    recent_patients = conn.execute("""
        SELECT patient_id, name, created_at
        FROM patients
        ORDER BY created_at DESC
        LIMIT 5
    """).fetchall()

    doctor_appointments = conn.execute("""
        SELECT
            appointments.*,
            patients.name AS patient_name,
            patients.mobile AS patient_mobile
        FROM appointments
        JOIN patients
        ON appointments.patient_id = patients.patient_id
        WHERE appointments.doctor_id = ?
        ORDER BY appointments.appointment_date DESC,
                 appointments.appointment_time DESC
    """, (session["doctor_id"],)).fetchall()

    conn.close()

    if not doctor:
        session.clear()
        return redirect("/doctor-login")

    return render_template(
        "doctor_dashboard.html",
        doctor=doctor,
        recent_patients=recent_patients,
        doctor_appointments=doctor_appointments
    )


@app.route("/update-appointment-status/<int:appointment_id>", methods=["POST"])
def update_appointment_status(appointment_id):
    if "doctor_id" not in session:
        return redirect("/doctor-login")

    new_status = request.form.get("status")

    allowed_statuses = ["Waiting", "Confirmed", "Completed", "Cancelled"]

    if new_status not in allowed_statuses:
        return redirect("/doctor-dashboard")

    conn = get_db_connection()

    conn.execute("""
        UPDATE appointments
        SET status = ?
        WHERE id = ? AND doctor_id = ?
    """, (new_status, appointment_id, session["doctor_id"]))

    conn.commit()
    conn.close()

    return redirect("/doctor-dashboard")



@app.route("/today-patients")
def today_patients():
    if "doctor_id" not in session:
        return redirect("/doctor-login")

    conn = get_db_connection()

    appointments = conn.execute("""
        SELECT
            appointments.*,
            patients.name AS patient_name
        FROM appointments
        JOIN patients
        ON appointments.patient_id = patients.patient_id
        WHERE appointments.doctor_id = ?
        AND appointments.appointment_date = ?
        ORDER BY appointments.token_number
    """, (session["doctor_id"], date.today().isoformat())).fetchall()

    conn.close()

    return render_template(
        "today_patients.html",
        appointments=appointments
    )

@app.route("/call-staff", methods=["GET", "POST"])
def call_staff():
    if "doctor_id" not in session:
        return redirect("/doctor-login")

    conn = get_db_connection()

    if request.method == "POST":
        staff_role = request.form.get("staff_role")
        message = request.form.get("message")

        conn.execute("""
            INSERT INTO staff_requests
            (doctor_id, staff_role, message)
            VALUES (?, ?, ?)
        """, (
            session["doctor_id"],
            staff_role,
            message
        ))

        conn.commit()

    requests = conn.execute("""
        SELECT * FROM staff_requests
        WHERE doctor_id = ?
        ORDER BY created_at DESC
    """, (session["doctor_id"],)).fetchall()

    conn.close()

    return render_template(
        "call_staff.html",
        requests=requests
    )

@app.route("/revisit-patients")
def revisit_patients():
    if "doctor_id" not in session:
        return redirect("/doctor-login")

    conn = get_db_connection()

    patients = conn.execute("""
        SELECT
            patients.patient_id,
            patients.name,
            patients.mobile,
            COUNT(appointments.id) AS visit_count,
            MAX(appointments.appointment_date) AS last_visit
        FROM appointments
        JOIN patients
        ON appointments.patient_id = patients.patient_id
        WHERE appointments.doctor_id = ?
        GROUP BY patients.patient_id
        HAVING COUNT(appointments.id) > 1
        ORDER BY last_visit DESC
    """, (session["doctor_id"],)).fetchall()

    conn.close()

    return render_template(
        "revisit_patients.html",
        patients=patients
    )

@app.route("/patient-history")
def patient_history():
    if "doctor_id" not in session:
        return redirect("/doctor-login")

    conn = get_db_connection()

    patients = conn.execute("""
        SELECT DISTINCT
            patients.patient_id,
            patients.name,
            patients.mobile
        FROM patients
        JOIN appointments
        ON patients.patient_id = appointments.patient_id
        WHERE appointments.doctor_id = ?
        ORDER BY patients.name
    """, (session["doctor_id"],)).fetchall()

    conn.close()

    return render_template(
        "patient_history.html",
        patients=patients
    )

@app.route("/manage-availability", methods=["GET", "POST"])
def manage_availability():
    if "doctor_id" not in session:
        return redirect("/doctor-login")

    conn = get_db_connection()

    if request.method == "POST":
        slot_date = request.form["slot_date"]
        slot_time = request.form["slot_time"]

        try:
            conn.execute("""
                INSERT INTO doctor_slots
                (doctor_id, slot_date, slot_time)
                VALUES (?, ?, ?)
            """, (
                session["doctor_id"],
                slot_date,
                slot_time
            ))

            conn.commit()
        except sqlite3.IntegrityError:
            pass

    slots = conn.execute("""
        SELECT * FROM doctor_slots
        WHERE doctor_id = ?
        ORDER BY slot_date, slot_time
    """, (session["doctor_id"],)).fetchall()

    conn.close()

    return render_template(
        "manage_availability.html",
        slots=slots
    )

@app.route("/get-available-slots")
def get_available_slots():
    if "patient_id" not in session:
        return jsonify([]), 401

    doctor_id = request.args.get("doctor_id")
    slot_date = request.args.get("date")

    conn = get_db_connection()

    slots = conn.execute("""
        SELECT slot_time
        FROM doctor_slots
        WHERE doctor_id = ?
        AND slot_date = ?
        AND status = 'Available'
        ORDER BY slot_time
    """, (doctor_id, slot_date)).fetchall()

    conn.close()

    return jsonify([slot["slot_time"] for slot in slots])


@app.route("/my-appointments")
def my_appointments():
    if "patient_id" not in session:
        return redirect("/patient-login")

    conn = get_db_connection()

    appointments = conn.execute("""
        SELECT
            appointments.*,
            doctors.full_name,
            doctors.specialization
        FROM appointments
        JOIN doctors
        ON appointments.doctor_id = doctors.doctor_id
        WHERE appointments.patient_id = ?
        ORDER BY appointments.appointment_date DESC,
                 appointments.appointment_time DESC
    """, (session["patient_id"],)).fetchall()

    conn.close()

    today = date.today().isoformat()

    upcoming_appointments = []
    previous_appointments = []

    for appointment in appointments:
        if appointment["appointment_date"] >= today and appointment["status"] not in ("Cancelled", "Completed"):
            upcoming_appointments.append(appointment)
        else:
            previous_appointments.append(appointment)

    return render_template(
        "my_appointments.html",
        upcoming_appointments=upcoming_appointments,
        previous_appointments=previous_appointments
    )


@app.route("/cancel-appointment/<int:appointment_id>", methods=["POST"])
def cancel_appointment(appointment_id):
    if "patient_id" not in session:
        return redirect("/patient-login")

    conn = get_db_connection()

    appointment = conn.execute("""
        SELECT *
        FROM appointments
        WHERE id = ? AND patient_id = ?
    """, (appointment_id, session["patient_id"])).fetchone()

    if not appointment:
        conn.close()
        return redirect("/my-appointments")

    today = date.today().isoformat()

    if (
        appointment["appointment_date"] < today
        or appointment["status"] in ("Completed", "Cancelled")
    ):
        conn.close()
        return redirect("/my-appointments")

    conn.execute("""
        UPDATE appointments
        SET status = 'Cancelled'
        WHERE id = ? AND patient_id = ?
    """, (appointment_id, session["patient_id"]))

    conn.execute("""
        UPDATE doctor_slots
        SET status = 'Available'
        WHERE doctor_id = ?
          AND slot_date = ?
          AND slot_time = ?
    """, (
        appointment["doctor_id"],
        appointment["appointment_date"],
        appointment["appointment_time"]
    ))

    conn.commit()
    conn.close()

    return redirect("/my-appointments")




@app.route("/book-appointment", methods=["GET", "POST"])
def book_appointment():
    if "patient_id" not in session:
        return redirect("/patient-login")

    conn = get_db_connection()

    doctors = conn.execute("""
        SELECT doctor_id, full_name, specialization
        FROM doctors
        WHERE specialization IS NOT NULL
        ORDER BY full_name
    """).fetchall()

    if request.method == "POST":
        doctor_id = request.form.get("doctor_id")
        appointment_date = request.form.get("appointment_date")
        appointment_time = request.form.get("appointment_time")

        # Check whether the selected slot exists and is available
        slot = conn.execute("""
            SELECT * FROM doctor_slots
            WHERE doctor_id = ?
            AND slot_date = ?
            AND slot_time = ?
            AND status = 'Available'
        """, (doctor_id, appointment_date, appointment_time)).fetchone()

        if not slot:
            conn.close()
            return render_template(
                "book_appointment.html",
                doctors=doctors,
                error="This slot is not available. Please choose another."
            )

        selected_datetime = datetime.strptime(
            appointment_date + " " + appointment_time,
            "%Y-%m-%d %H:%M"
        )

        if selected_datetime <= datetime.now():
            conn.close()
            return render_template(
                "book_appointment.html",
                doctors=doctors,
                error="Please select a future slot."
            )

        last_token = conn.execute("""
            SELECT MAX(token_number) AS last_token
            FROM appointments
            WHERE doctor_id = ? AND appointment_date = ?
        """, (doctor_id, appointment_date)).fetchone()

        token_number = (last_token["last_token"] or 0) + 1

        conn.execute("""
            INSERT INTO appointments
            (patient_id, doctor_id, appointment_date,
             appointment_time, token_number)
            VALUES (?, ?, ?, ?, ?)
        """, (
            session["patient_id"],
            doctor_id,
            appointment_date,
            appointment_time,
            token_number
        ))

        conn.execute("""
            UPDATE doctor_slots
            SET status = 'Booked'
            WHERE id = ?
        """, (slot["id"],))

        conn.commit()
        conn.close()

        return render_template(
            "appointment_success.html",
            token_number=token_number,
            appointment_date=appointment_date,
            appointment_time=appointment_time
        )

    conn.close()

    return render_template(
        "book_appointment.html",
        doctors=doctors
    )



@app.route("/staff-login", methods=["GET", "POST"])
def staff_login():

    if request.method == "POST":

        staff_id = request.form.get("staff_id", "").strip()
        password = request.form.get("password", "")

        conn = get_db_connection()

        staff = conn.execute("""
            SELECT * FROM staff
            WHERE staff_id = ?
        """, (staff_id,)).fetchone()

        conn.close()

        if staff and check_password_hash(staff["password"], password):
            session.clear()
            session["staff_id"] = staff["staff_id"]
            session["staff_name"] = staff["full_name"]
            session["staff_role"] = staff["role"]

            return redirect("/staff-dashboard")

        return render_template(
            "staff_login.html",
            error="Invalid Staff ID or Password."
        )

    return render_template("staff_login.html")

@app.route("/staff-dashboard")
def staff_dashboard():

    if "staff_id" not in session:
        return redirect("/staff-login")

    return render_template(
        "staff_dashboard.html",
        staff_name=session["staff_name"],
        staff_role=session["staff_role"]
    )

@app.route("/staff-attendance", methods=["GET", "POST"])
def staff_attendance():

    if "staff_id" not in session:
        return redirect("/staff-login")

    conn = get_db_connection()

    today = date.today().isoformat()
    now = datetime.now().strftime("%H:%M:%S")

    if request.method == "POST":

        existing = conn.execute("""
            SELECT * FROM staff_attendance
            WHERE staff_id = ? AND attendance_date = ?
        """, (session["staff_id"], today)).fetchone()

        if not existing:
            conn.execute("""
                INSERT INTO staff_attendance
                (staff_id, attendance_date, check_in)
                VALUES (?, ?, ?)
            """, (session["staff_id"], today, now))

            conn.commit()

        conn.close()
        return redirect("/staff-attendance")

    attendance = conn.execute("""
        SELECT * FROM staff_attendance
        WHERE staff_id = ? AND attendance_date = ?
    """, (session["staff_id"], today)).fetchone()

    conn.close()

    return render_template(
        "staff_attendance.html",
        attendance=attendance,
        today=today
    )

@app.route("/billing", methods=["GET", "POST"])
def billing():

    if "staff_id" not in session:
        return redirect("/staff-login")

    if session.get("staff_role") != "Billing Staff":
        return "Access Denied: Billing Staff Only", 403

    conn = get_db_connection()

    if request.method == "POST":

        patient_id = request.form.get("patient_id", "").strip()

        patient = conn.execute("""
            SELECT * FROM patients
            WHERE patient_id = ?
        """, (patient_id,)).fetchone()

        if not patient:
            conn.close()
            return render_template(
                "billing.html",
                error="Patient ID not found."
            )

        consultation = float(request.form.get("consultation_charge") or 0)
        lab = float(request.form.get("lab_charge") or 0)
        other = float(request.form.get("other_charge") or 0)

        total = consultation + lab + other
        status = request.form.get("payment_status", "Pending")

        conn.execute("""
            INSERT INTO bills
            (patient_id, staff_id, consultation_charge,
             lab_charge, other_charge, total_amount, payment_status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            patient_id,
            session["staff_id"],
            consultation,
            lab,
            other,
            total,
            status
        ))

        conn.commit()

    bills = conn.execute("""
        SELECT bills.*, patients.name AS patient_name
        FROM bills
        JOIN patients ON bills.patient_id = patients.patient_id
        ORDER BY bills.id DESC
    """).fetchall()

    conn.close()

    return render_template("billing.html", bills=bills)

@app.route("/doctor-attendance", methods=["GET", "POST"])
def doctor_attendance():

    if "doctor_id" not in session:
        return redirect("/doctor-login")

    conn = get_db_connection()

    today = date.today().isoformat()
    now = datetime.now().strftime("%H:%M:%S")

    if request.method == "POST":

        existing = conn.execute("""
            SELECT * FROM doctor_attendance
            WHERE doctor_id = ? AND attendance_date = ?
        """, (session["doctor_id"], today)).fetchone()

        if not existing:
            conn.execute("""
                INSERT INTO doctor_attendance
                (doctor_id, attendance_date, check_in)
                VALUES (?, ?, ?)
            """, (session["doctor_id"], today, now))

            conn.commit()

        conn.close()
        return redirect("/doctor-attendance")

    attendance = conn.execute("""
        SELECT * FROM doctor_attendance
        WHERE doctor_id = ? AND attendance_date = ?
    """, (session["doctor_id"], today)).fetchone()

    conn.close()

    return render_template(
        "doctor_attendance.html",
        attendance=attendance,
        today=today
    )

@app.route("/patient-login", methods=["GET", "POST"])
def patient_login():

    if request.method == "POST":

        login_id = request.form.get("login_id", "").strip()
        password = request.form.get("password", "")

        conn = get_db_connection()

        patient = conn.execute("""
            SELECT * FROM patients
            WHERE patient_id = ? OR mobile = ?
        """, (login_id, login_id)).fetchone()

        conn.close()

        if patient and check_password_hash(patient["password"], password):
            session.clear()
            session["patient_id"] = patient["patient_id"]
            return redirect("/patient-dashboard")

        return render_template(
            "patient_login.html",
            error="Invalid Patient ID or Password."
        )

    return render_template("patient_login.html")


@app.route("/patient-register", methods=["GET", "POST"])
def patient_register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        dob = request.form.get("dob", "")
        gender = request.form.get("gender", "")
        mobile = request.form.get("mobile", "").strip()
        email = request.form.get("email", "").strip()
        address = request.form.get("address", "").strip()
        password = request.form.get("password", "")

        if not all([name, dob, gender, mobile, address, password]):
            return render_template(
                "patient_register.html",
                error="Please fill all required fields."
            )

        if not mobile.isdigit() or len(mobile) != 10:
            return render_template(
                "patient_register.html",
                error="Enter a valid 10-digit mobile number."
            )

        if len(password) < 8:
            return render_template(
                "patient_register.html",
                error="Password must contain at least 8 characters."
            )

        conn = get_db_connection()

        try:
            cursor = conn.execute("""
                INSERT INTO patients
                (name, dob, gender, mobile, email, address, password)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                name, dob, gender, mobile, email, address,
                generate_password_hash(password)
            ))

            patient_id = f"HB-PAT-{cursor.lastrowid:04d}"

            conn.execute("""
                UPDATE patients
                SET patient_id = ?
                WHERE id = ?
            """, (patient_id, cursor.lastrowid))

            conn.commit()

            return render_template(
                "registration_success.html",
                patient_id=patient_id,
                name=name
            )

        except sqlite3.IntegrityError:
            return render_template(
                "patient_register.html",
                error="This mobile number is already registered."
            )

        finally:
            conn.close()

    return render_template("patient_register.html")


@app.route("/patient-dashboard")
def patient_dashboard():

    if "patient_id" not in session:
        return redirect("/patient-login")

    conn = get_db_connection()

    patient = conn.execute("""
        SELECT * FROM patients WHERE patient_id = ?
    """, (session["patient_id"],)).fetchone()

    conn.close()

    if not patient:
        session.clear()
        return redirect("/patient-login")

    return render_template(
        "patient_dashboard.html",
        patient=patient
    )


@app.route("/my-bills")
def my_bills():
    if "patient_id" not in session:
        return redirect("/patient-login")

    conn = get_db_connection()

    bills = conn.execute("""
        SELECT *
        FROM bills
        WHERE patient_id = ?
        ORDER BY created_at DESC
    """, (session["patient_id"],)).fetchall()

    conn.close()

    return render_template(
        "my_bills.html",
        bills=bills
    )


@app.route("/hospital-map")
def hospital_map():
    return render_template("hospital_map.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


if __name__ == "__main__":
    create_tables()
    app.run(debug=True)
