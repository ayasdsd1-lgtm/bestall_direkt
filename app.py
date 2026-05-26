# används import email?
import email
# används from sqlite3 import Cursor?
from sqlite3 import Cursor
import traceback
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import psycopg2
import os
import re      # Används för formatvalidering vid registrering
from flask import jsonify
# används import json?
import json
# orderbekräftelse funktion
import smtplib
from email.message import EmailMessage
# funktion för verksamhet att lägga ut bilder
from werkzeug.utils import secure_filename
import uuid
from datetime import timedelta


load_dotenv() # laddar in .env-filen som innehåller databas-info

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")  # Hämtar hemlig nyckel från .env
app.permanent_session_lifetime = timedelta(days=30)

# funktion för verksamhet att lägga ut bilder 
UPLOAD_FOLDER = "static/uploads"
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Databasanslutning via miljövariabel - Supabase kräver SSL
conn = psycopg2.connect(os.getenv("DATABASE_URL"), sslmode="require")


# -------------------------------------------------------
# STARTSIDAN
# -------------------------------------------------------

@app.route("/")
def home():
    """
    Startsidan. Renderar index.html
    HTML-sida: index.html
    """
    return render_template("index.html")

# -------------------------------------------------------
# SÖK
# -------------------------------------------------------

@app.route("/search")
def search():  # route behålls /search — redan engelska
    """
    Sökfunktion för startsidan.

    Denna route:
    1. Hämtar sökordet från URL:en (t.ex. /search?q=brunch)
    2. Söker i databasen efter företag som matchar sökordet
    3. Skickar resultatet till search.html för visning
    """
    
    # behöver ändra försiktigt med databas

    query = request.args.get("q", "").strip()

    cursor = conn.cursor()

    try:
        cursor.execute(
            """
           SELECT DISTINCT v.company_business_id, v.company_name, v.category
            FROM public.company_business v
            LEFT JOIN public.menu_item m ON m.company_business_id = v.company_business_id
            WHERE v.company_name ILIKE %s
                OR v.category    ILIKE %s
                OR v.description ILIKE %s
                OR m.item_name   ILIKE %s
                OR m.description ILIKE %s
            """,
            (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%")
        )

        results = cursor.fetchall()

    except Exception as e:
        print("Fel vid sökning:", e)
        results = []

    return render_template("search.html", results=results, query=query)

# -------------------------------------------------------
# KATEGORIER
# -------------------------------------------------------

@app.route("/category/<category_name>")
def category(category_name):
    """
    Visar alla företag som tillhör en viss kategori.
    """

    # behöver ändra försiktigt med databas

    categories = {
    "Brunch": "Brunch",
    "Smatt-och-mingel": "Smått & mingel",
    "Middag-och-festmat": "Middag & festmat",
    "Buffe": "Buffé",
    "Bakverk-och-sott": "Bakverk & sött",
    "Vegetariskt": "Vegetariskt"
}

    display_name = categories.get(category_name, category_name.replace("-", " "))

    cursor = conn.cursor()

    try:
        cursor.execute(
            "SELECT * FROM public.company_business WHERE category = %s",
            (display_name,)
        )

        companies = cursor.fetchall()

    except Exception as e:
        conn.rollback()
        print("Fel vid kategori:", e)
        companies = []

    return render_template("category.html", name=display_name, companies=companies)

# -------------------------------------------------------
# VIEW
# -------------------------------------------------------

@app.route("/view/<int:company_id>") 
def view_company(company_id):
    """
    Visar företagssidan för ett specifikt företag baserat på company_id i URL:en.
    HTML-sida: view.html
    """

    # behöver ändra försiktigt med databas

    cursor = conn.cursor()

    try:

        # Hämta verksamhetsinformation
        cursor.execute("""
            SELECT
                company_name,
                address,
                phone,
                description,
                category,
                email,
                logo_url
            FROM public.company_business
            WHERE company_business_id = %s
        """, (company_id,))

        company_data = cursor.fetchone()
        print("Resultat från databasen:", company_data)
        print("company_business_id från URL:", company_id)

        print("Verksamhet:", company_data)  

        # Om verksamheten inte finns
        if not company_data:
            return "Verksamheten hittades inte", 404

        # Gör om databassvaret till dictionary
        company = {
            "name": company_data[0],
            "address": company_data[1],
            "phone": company_data[2],
            "description": company_data[3],
            "category": company_data[4],
            "email": company_data[5],
            "logo_url": company_data[6],
            "services": []
        }

        # Hämta tjänster/meny
        cursor.execute("""
            SELECT
                item_name,
                description,
                price,
                image_url
            FROM public.menu_item
            WHERE company_business_id = %s
        """, (company_id,))

        menu_items = cursor.fetchall()

        # Lägg till tjänster i listan
        for item in menu_items:

            company["services"].append({
                "name": item[0],
                "description": item[1],
                "price": item[2],
                "image_url": item[3]
            })

        return render_template(
            "view.html",
            company=company
        )

    except Exception as e:

        conn.rollback()

        print("Fel vid hämtning av verksamhet:", e)

        return "Ett fel uppstod", 500

def send_order_confirmation_email(to_email, customer_name):
    """
    Skickar ett orderbekräftelse via mejl efter en kund har lagt en beställning
    """

    sender_email = os.getenv("MAIL_USERNAME")
    sender_password = os.getenv("MAIL_PASSWORD")

    message = EmailMessage()
    message["Subject"] = "Bekräftelse på din beställning"
    message["From"] = sender_email
    message["To"] = to_email

    message.set_content(
        f"Hej {customer_name}!\n"
        "Tack för din beställning hos Beställ Direkt.\n"
        "Vi har tagit emot din beställning och verksamheten kommer att hantera den så snart som möjligt.\n\n"
        "Vänliga hälsningar,\n"
        "Beställ Direkt"
    )

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login(sender_email, sender_password)
        smtp.send_message(message)


@app.route('/create-order', methods=['POST'])
def create_order():
    """
    Tar emot kundens uppgifter och orderdetaljer via POST och sparar dem i tabellen 'bestallningar'.
    Returnerar JSON med success: True vid lyckad beställning, annars success: False och statuskod 500.
    Formuläret i HTML ska ha method="POST" och action="{{ url_for('create_order') }}".
    HTML-sida: view.html
    """
    
    name = request.form.get('customer_name')
    email = request.form.get('email')
    phone = request.form.get('phone')

    cursor = conn.cursor()

    try:
        # skapa kund
        cursor.execute("""
            INSERT INTO public.customer (name, email, phone)
            VALUES (%s, %s, %s)
            RETURNING customer_id
        """, (name, email, phone))

        customer_id = cursor.fetchone()[0]

        # skapa beställlning 
        cursor.execute("""
            INSERT INTO public.orders (customer_id, company_business_id, status)
            VALUES (%s, %s, %s)
            RETURNING order_id
        """, (customer_id, 5, 'pending'))

        order_id = cursor.fetchone()[0]
        
        conn.commit()

        send_order_confirmation_email(email, name)

        return jsonify({
            "success": True,
            "message": f"Tack för din beställning, {name}! En bekräftelse har skickats till {email}."
        })
    
    except Exception as e:
        conn.rollback()
        print("Fel vid beställning:", e)

        return jsonify({
            "success": False,
            "message": "Beställningen gick inte igenom."
        }), 500

# -------------------------------------------------------
# INLOGGNING
# -------------------------------------------------------

@app.route("/login-page")
def login_page():
    """
    Visar inloggningssidan för företagare
    Länken i HTML ska se ut: {{ url_for('login_page') }}
    HTML-sida: log_in.html
    """
    return render_template("log_in.html")


@app.route("/login", methods=["POST"])
def login():
    """
    Hanterar inloggning
    """

    email = request.form["email"]
    password = request.form["password"]

    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT 
                v.company_business_id,
                f.password
             FROM public.company_owner f
             LEFT JOIN public.company_business v
                ON f.company_id = v.company_id
            WHERE f.email = %s
        """, (email,))

        user = cursor.fetchone()

        print(user)

        if user:

            company_id = user[0]
            stored_password = user[1]

            if check_password_hash(stored_password, password):

                # Sparar användaren i session
                session.permanent = True  # Gör sessionen permanent (varar i 30 dagar)
                session["user"] = email

                # Skicka företagaren till dashboard/profile
                return redirect(url_for("profile"))
            
            else:
                return render_template(
                    "log_in.html",
                    error ="Fel lösenord"
                )
        else:
            return render_template(
                "log_in.html",
                error="Användare finns inte"
            )
        
    except Exception as e:
        conn.rollback()
        print("FEL:", e)
        return render_template(
            "log_in.html",
            error="Något gick fel, försök igen"
        )
    
# -------------------------------------------------------
# REGISTRERING
# -------------------------------------------------------

@app.route("/register-page")
def register_page():
    """
    Visar registreringssidan för företagare.
    Länken i HTML ska se ut: {{ url_for('registrera_sig') }}
    HTML-sida: register.html
    """
    return render_template("register.html")


@app.route("/register", methods=["POST"])
def register():
    """
    Registrerar en ny företagare i databasen.
    Tar emot namn, email och lösenord via POST.
    Kollar först om emailen redan finns i databasen.
    Lösenordet hashas innan det sparas.
    Efter lyckad registrering skickas användaren till inloggningssidan.
    Formuläret i HTML ska ha method="POST" och action="{{ url_for('register') }}".
    HTML-sida: register.html
    """

    name = request.form.get("name", "").strip()
    personal_identity_number  = request.form.get("personal_identity_number", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    password = request.form.get("password", "")

    # Samla alla fältfel i en ordbok så HTML kan visa dem per fält
    errors = {}

    # Namn
    if not name:
        errors["name"] = "Namn är obligatoriskt."
    elif len(name) < 2:
        errors["name"] = "Namnet är för kort."

    # Personnummer – format YYYYMMDD-XXXX eller YYYYMMDDXXXX
    if not personal_identity_number:
        errors["personal_identity_number"] = "Personnummer är obligatoriskt."
    elif not re.fullmatch(r"\d{8}-?\d{4}", personal_identity_number):
        errors["personal_identity_number"] = "Ange personnummer i format YYYYMMDD-XXXX."

    # E-post
    if not email:
        errors["email"] = "E-postadress är obligatorisk."
    elif not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        errors["email"] = "Ange en giltig e-postadress."

    # Mobilnummer – 10 siffror, får börja med +46
    if not phone:
        errors["phone"] = "Mobilnummer är obligatoriskt."
    elif not re.fullmatch(r"(\+46|0)\d{9}", phone.replace(" ", "").replace("-", "")):
        errors["phone"] = "Ange ett giltigt mobilnummer (t.ex. 0701234567)."

    # Lösenord
    if not password:
        errors["password"] = "Lösenord är obligatoriskt."
    elif len(password) < 8:
        errors["password"] = "Lösenordet måste vara minst 8 tecken."

    # Om valideringsfel finns – returnera sidan med alla felmeddelanden
    if errors:
        return render_template(
            "register.html",
            errors=errors,
            # Skicka tillbaka ifyllda värden så användaren inte behöver skriva om allt
            prev={"name": name, "personal_identity_number": personal_identity_number, "email": email, "phone": phone}
        )

    cursor = conn.cursor()

    try:
        # Kolla om emailen redan är registrerad
        cursor.execute(
            "SELECT company_id FROM public.company_owner WHERE email = %s",
            (email,)
        )
        if cursor.fetchone():
            errors["email"] = "Den här e-postadressen är redan registrerad."
            return render_template(
                "register.html",
                errors=errors,
                prev={"name": name, "personal_identity_number": personal_identity_number, "email": email, "phone": phone}
            )

        # Hasha lösenordet innan det sparas i databasen
        hashed_password = generate_password_hash(password)

        cursor.execute(
            """INSERT INTO public.company_owner
               (company_name, personal_identity_number, email, phone, password)
               VALUES (%s, %s, %s, %s, %s)""",
            (name, personal_identity_number, email, phone, hashed_password)
        )
        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Fel vid registrering: {e}")
        return render_template(
            "register.html",
            errors={"general": "Något gick fel, försök igen."},
            prev={"name": name, "personal_identity_number": personal_identity_number, "email": email, "phone": phone}
        )

    # Skicka användaren till inloggningssidan efter lyckad registrering
    return render_template("register.html", success="Ditt konto har skapats! Du kan nu logga in.")

# -------------------------------------------------------
# UTLOGGNING
# -------------------------------------------------------

@app.route("/logout")
def logout():
    """
    Loggar ut den inloggade användaren genom att rensa sessionen.
    Skickar användaren tillbaka till startsidan.
    Länken i HTML ska se ut: {{ url_for('logout') }}
    """
    session.clear()      # Raderar minneslappen - användaren är ut utloggad
    return redirect(url_for("home"))


@app.route("/delete-account", methods=["POST"])
def delete_account():
    """
    Raderar företagarens konto och all kopplad data permanent ur databasen.
    Kräver POST-anrop (bekräftelse från formulär) för att förhindra oavsiktlig radering.
    Kopplade tabeller som raderas: bestallningsrad, bestallningar, meny, verksamhet, company_owner.
    """
    if "user" not in session:
        return redirect(url_for("login_page"))

    email = session["user"]
    cursor = conn.cursor()

    try:
        # Hämta company_id och verksamhet_id för kaskadradering
        cursor.execute(
            "SELECT company_id FROM public.company_owner WHERE email = %s",
            (email,)
        )
        row = cursor.fetchone()
        if not row:
            session.clear()
            return redirect(url_for("home"))

        company_id = row[0]

        cursor.execute(
            "SELECT company_business_id FROM public.company_business WHERE company_id = %s",
            (company_id,)
        )
        business_row = cursor.fetchone()

        if business_row:
            company_business_id = business_row[0]

            # Radera beställningsrader
            cursor.execute("""
                DELETE FROM public.order_item
                WHERE order_id IN (
                    SELECT order_id FROM public.orders
                    WHERE company_business_id = %s
                )
            """, (company_business_id,))

            # Radera beställningar
            cursor.execute(
                "DELETE FROM public.orders WHERE company_business_id = %s",
                (company_business_id,)
            )

            # Radera meny
            cursor.execute(
                "DELETE FROM public.menu_item WHERE company_business_id = %s",
                (company_business_id,)
            )

            # Radera verksamhet
            cursor.execute(
                "DELETE FROM public.company_business WHERE company_business_id = %s",
                (company_business_id,)
            )

        # Radera företagaren
        cursor.execute(
            "DELETE FROM public.company_owner WHERE company_id = %s",
            (company_id,)
        )

        conn.commit()

    except Exception as e:
        conn.rollback()
        print(f"Fel vid radering av konto: {e}")
        return "Kunde inte radera kontot, försök igen.", 500

    session.clear()
    return redirect(url_for("home"))

# -------------------------------------------------------
# Info sidan
# -------------------------------------------------------

@app.route("/info")
def info():
    """
    Visar info sidan för besökare
    Länken i HTML ska se ut: {{ url_for('info') }}
    HTML-sidan: info.html
    """
    return render_template("info.html")


# -------------------------------------------------------
# Profile sidan
# -------------------------------------------------------
@app.route("/profile")
def profile():
    """
    Visar profilsidan för inloggad företagare.
    Kontrollerar att användaren är inloggad via sessionen.
    Hämtar företagarens inkomna beställningar från databasen och skickar dem till profile.html.
    Länken i HTML ska se ut: {{ url_for('profile') }}
    HTML-sida: profile.html
    """
    if "user" not in session:
        return redirect(url_for("login_page"))
    
    email = session["user"]
    cursor = conn.cursor()

    try:
        query = """
            SELECT
                b.order_id,
                b.date,
                k.name AS customer_name,
                k.phone,
                m.item_name,
                br.amount
            FROM public.company_owner f
            JOIN public.company_business v ON f.company_id = v.company_id
            JOIN public.orders b ON v.company_business_id = b.company_business_id
            JOIN public.customer k ON b.customer_id = k.customer_id
            JOIN public.order_item br ON b.order_id = br.order_id
            JOIN public.menu_item m ON br.menu_item_id = m.menu_item_id
            WHERE f.email = %s
            ORDER BY b.date DESC
        """

        cursor.execute(query, (email, ))
        bookings = cursor.fetchall()

        # Hämta verksamhetsinformation
        cursor.execute("""
            SELECT
                v.company_business_id,
                v.company_name,
                v.phone,
                v.description,
                v.category,
                v.email,
                v.logo_url,
                v.address,
                v.company_id,
                f.is_active 
            FROM public.company_business v
            JOIN public.company_owner f ON v.company_id = f.company_id   
            WHERE f.email = %s
        """, (email,))

        business = cursor.fetchone()
        if business:
            cursor.execute("""
                SELECT
                    menu_item_id,
                    item_name,
                    description,
                    price,
                    image_url
                FROM public.menu_item
                WHERE company_business_id = %s
                ORDER BY menu_item_id DESC
            """, (business[0],))

            services = cursor.fetchall()
            print("Services:", services)        
            print("business =", business)

            return render_template(
                "profile.html", 
                bookings=bookings, 
                business=business,
                services=services,
                company_id=business[0],
                is_active=business[8]
                )
        else:
            return render_template(
                "profile.html", 
                bookings=bookings, 
                business=None,
                company_id=None,
                is_active=True
            )
        
    except Exception as e:
        print(f"Gick inte att ladda upp profilsidan: {e}")
        return "Ett fel uppstod", 500
    

@app.route('/toggle-status', methods=['POST'])
def toggle_status():
    """
    Är till för att företag ska kunna aktivera/avaktivera sina verksamheter
    """
    user_email = session.get('user')
    if not user_email:
        return redirect(url_for('login_page'))
    
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE public.company_owner
            SET is_active = NOT is_active
            WHERE email = %s
        """, (user_email,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Det gick inte att ändra status. Vänligen försök senare")

    return redirect(url_for('profile'))



@app.route("/upload-profile-image", methods=["POST"])
def upload_profile_image():
    if "user" not in session:
        return redirect(url_for("login_page"))

    image = request.files.get("profile_image")

    if not image or image.filename == "":
        return redirect(url_for("profile"))

    if not allowed_file(image.filename):
        return "Endast JPG, JPEG och PNG är tillåtna.", 400

    original_filename = secure_filename(image.filename)
    file_extension = original_filename.rsplit(".", 1)[1].lower()
    unique_filename = f"{uuid.uuid4()}.{file_extension}"

    image.save(os.path.join(app.config["UPLOAD_FOLDER"], unique_filename))

    image_path = url_for("static", filename=f"uploads/{unique_filename}")

    email = session["user"]
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE public.company_business v
            SET logo_url = %s
            FROM public.company_owner f
            WHERE v.company_id = f.company_id
              AND f.email = %s
        """, (image_path, email))

        conn.commit()

    except Exception as e:
        conn.rollback()
        print("Fel vid bilduppladdning:", e)

    return redirect(url_for("profile"))
    
@app.route("/update-business", methods=["POST"])
def update_business():

    if "user" not in session:
        return redirect(url_for("login_page"))

    session_email = session["user"]

    company_name = request.form.get("company_name")
    description = request.form.get("description")
    phone = request.form.get("phone")
    category = request.form.get("category")
    email = request.form.get("email")
    address = request.form.get("address")

    cursor = conn.cursor()

    try:
        # Hämta company_id för inloggad användare (SÄ-S-02)
        cursor.execute("""
            SELECT company_id
            FROM public.company_owner
            WHERE email = %s
        """, (session_email,))

        company_owner = cursor.fetchone()
        
        if not company_owner:
            return "Obehörig åtkomst", 403

        company_id = company_owner[0]

        # Verifiera att en verksamhet faktiskt tillhör den inloggade företagaren
        # innan UPDATE körs — förhindrar att session-manipulation når annan data (SÄ-S-02)
        cursor.execute("""
            UPDATE public.company_business
            SET
               company_name = %s,
                description = %s,
                phone = %s,
                category = %s,
                email = %s,
                address = %s
            WHERE company_id = %s
        """, (
            company_name,
            description,
            phone,
            category,
            email,
            address,
            company_id
        ))

        conn.commit()

        return redirect(url_for("profile"))

    except Exception as e:
        conn.rollback()
        print("Fel vid uppdatering:", e)
        return "Kunde inte uppdatera verksamheten", 500
    
    
@app.route("/create-business", methods=["GET", "POST"])
def create_business():
    """
    Visar sidan där företagaren kan skapa en verksamhet.
    """

    if "user" not in session:
        return redirect(url_for("login_page"))

    if request.method == "POST":

        company_name = request.form.get("company_name")
        address = request.form.get("address")
        phone = request.form.get("phone")
        description = request.form.get("description")
        category = request.form.get("category")
        email = request.form.get("email")

        cursor = conn.cursor()

        try:

            # Hämta company_id från inloggad användare

            session_email = session["user"]
            cursor.execute("""
                SELECT company_id
                FROM public.company_owner
                WHERE email = %s
            """, (session_email,))

            owner = cursor.fetchone()

            if not owner:
                return "Ingen företagare kopplad till kontot", 403
            company_id = owner[0]

            # Skapa verksamheten
            cursor.execute("""
                INSERT INTO public.company_business
                (
                    company_id,
                    company_name,
                    address,
                    phone,
                    description,
                    category,
                    email
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING company_business_id
            """, (
                company_id,
                company_name,
                address,
                phone,
                description,
                category,
                email
            ))

            company_id = cursor.fetchone()[0]

            conn.commit()

            return redirect(
                url_for(
                    "profile",
                    company_id=company_id
                )
            )

        except Exception as e:

            conn.rollback()

            import traceback
            traceback.print_exc()

            print("Fel vid skapande av verksamhet:", e)

            return render_template(
                "create_business.html",
                error="Kunde inte skapa verksamheten"
            )

    return render_template("create_business.html")


@app.route("/create-service", methods=["POST"])
def create_service():

    if "user" not in session:
        return redirect(url_for("login_page"))

    email = session["user"]

    item_name = request.form.get("item_name")
    description = request.form.get("description")
    price = request.form.get("price")

    service_image = request.files.get("service_image")
    image_path = None

    if service_image and service_image.filename != "" and allowed_file(service_image.filename):

        original_filename = secure_filename(service_image.filename)

        file_extension = original_filename.rsplit(".", 1)[1].lower()

        unique_filename = f"{uuid.uuid4()}.{file_extension}"

        service_image.save(
            os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
        )

        image_path = url_for(
            "static",
            filename=f"uploads/{unique_filename}"
        )

    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT company_business_id
            FROM public.company_business
            WHERE company_id = (
                SELECT company_id
                FROM public.company_owner
                WHERE email = %s
            )
        """, (email,))

        business_row = cursor.fetchone()
        if not business_row:
            return "Ingen verksamhet kopplad till kontot", 403
        company_id = business_row[0]

        cursor.execute("""
            INSERT INTO public.menu_item
            (
                company_business_id,
                item_name,
                description,
                price,
                image_url
            )
            VALUES (%s, %s, %s, %s, %s)
        """, (
            company_id,
            item_name,
            description,
            price,
            image_path
        ))

        conn.commit()

        return redirect(url_for("profile"))

    except Exception as e:

        conn.rollback()

        print(e)

        return "Kunde inte skapa tjänst", 500
    

@app.route("/update-service/<int:service_id>", methods=["POST"])
def update_service(service_id):

    if "user" not in session:
        return redirect(url_for("login_page"))

    item_name = request.form.get("item_name")
    description = request.form.get("description")
    price = request.form.get("price")

    service_image = request.files.get("service_image")

    cursor = conn.cursor()

    try:

        image_path = None

        if (
            service_image
            and service_image.filename != ""
            and allowed_file(service_image.filename)
        ):

            original_filename = secure_filename(service_image.filename)

            file_extension = original_filename.rsplit(".", 1)[1].lower()

            unique_filename = f"{uuid.uuid4()}.{file_extension}"

            service_image.save(
                os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    unique_filename
                )
            )

            image_path = url_for(
                "static",
                filename=f"uploads/{unique_filename}"
            )

            cursor.execute("""
                UPDATE public.menu_item
                SET
                    item_name = %s,
                    description = %s,
                    price = %s,
                    image_url = %s
                WHERE menu_item_id = %s
            """, (
                item_name,
                description,
                price,
                image_path,
                service_id
            ))

        else:

            cursor.execute("""
                UPDATE public.menu_item
                SET
                    item_name = %s,
                    description = %s,
                    price = %s
                WHERE menu_item_id = %s
            """, (
                item_name,
                description,
                price,
                service_id
            ))

        conn.commit()

        return redirect(url_for("profile"))

    except Exception:
        conn.rollback()
        traceback.print_exc()
        return "Kunde inte uppdatera tjänst", 500
    
@app.route("/delete-service/<int:service_id>")
def delete_service(service_id):

    if "user" not in session:
        return redirect(url_for("login_page"))

    cursor = conn.cursor()

    try:

        cursor.execute("""
            DELETE FROM public.menu_item
            WHERE menu_item_id = %s
        """, (service_id,))

        conn.commit()

        return redirect(url_for("profile"))

    except Exception as e:

        conn.rollback()

        print("Fel vid radering:", e)

        return "Kunde inte radera tjänst", 500




# -------------------------------------------------------
# Admin
# -------------------------------------------------------
ADMIN_USER = os.getenv("ADMIN_USER")
ADMIN_PASS = os.getenv("ADMIN_PASS")

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        
        if email == ADMIN_USER and password == ADMIN_PASS:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        else:
            return render_template("admin_login.html", error="Felaktiga admin-uppgifter")
            
    return render_template("admin_login.html")

@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    
    cursor = conn.cursor()
    cursor.execute("SELECT company_id, company_name, email, blocked FROM public.company_owner ORDER BY company_id DESC")
    company_owner = cursor.fetchall()
    return render_template("admin_dashboard.html", company_owner=company_owner)

@app.route("/admin/blocked/<int:id>")
def toggle_company_status(id):
    if not session.get("admin_logged_in"): return redirect(url_for("admin_login"))
    
    cursor = conn.cursor()
    cursor.execute("UPDATE public.company_owner SET blocked = NOT blocked WHERE company_id = %s", (id,))
    conn.commit()
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/delete/<int:id>")
def delete_company(id):
    if not session.get("admin_logged_in"): return redirect(url_for("admin_login"))
    
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM public.company_business WHERE company_id = %s", (id,))
        cursor.execute("DELETE FROM public.company_owner WHERE company_id = %s", (id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"Fel vid radering: {e}")
        
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/logout")
def admin_logout():
    session.pop("admin_logged_in", None)
    return redirect(url_for("home"))


# -------------------------------------------------------
# STARTA SERVERN
# -------------------------------------------------------
if __name__ == "__main__":
    app.run(debug=True, port=5001)

