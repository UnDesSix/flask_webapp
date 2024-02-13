from os import environ
from datetime import datetime
from sqlalchemy.sql import func
import xml.etree.ElementTree as ET
from flask_sqlalchemy import SQLAlchemy
from flask import Flask, request, render_template, redirect, url_for


from flask import Flask, request, redirect, url_for, render_template
from flask_sqlalchemy import SQLAlchemy
from os import environ

# Initialize the Flask app
app = Flask(__name__)
# Set the database URI from environment variables
app.config["SQLALCHEMY_DATABASE_URI"] = environ.get("DB_URL")
# Initialize SQLAlchemy with the Flask app
db = SQLAlchemy(app)


# Define the Price model for the SQLAlchemy ORM
class Price(db.Model):
    __tablename__ = "price"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    station_id = db.Column(db.String(20), nullable=False)
    gas_name = db.Column(db.String(50), nullable=False)
    price = db.Column(db.Float, nullable=False)
    last_update = db.Column(db.DateTime, nullable=False)


# Create all tables in the database based on defined models
db.create_all()


@app.route("/", methods=["GET"])
def index():
    # Query the database for distinct gas names
    distinct_gas_names = Price.query.with_entities(Price.gas_name).distinct().all()
    # Render the index.html template with the list of gas names
    return render_template("index.html", gas_names=distinct_gas_names)


@app.route("/upload", methods=["POST"])
def upload_file():
    # Check if the file part is in the request
    if "file" not in request.files:
        print("No file part", flush=True)
        return redirect(url_for("index"))
    file = request.files["file"]
    # Check if a file was selected
    if file.filename == "":
        print("No selected file", flush=True)
        return redirect(url_for("index"))
    if file:
        try:
            # Process the uploaded file and store its prices in the database
            store_prices_from_xml(file)
            print("File processed and data stored in database.", flush=True)
        except Exception as e:
            print(f"Error processing file: {e}", flush=True)
        return redirect(url_for("index"))


@app.route("/mean_price", methods=["GET"])
def mean_price():
    # Get the gas name from query parameters
    gas_name = request.args.get("gas_name")
    if gas_name:
        # Query the database for the average price of the selected gas
        mean_price_result = (
            db.session.query(func.avg(Price.price))
            .filter(Price.gas_name == gas_name)
            .scalar()
        )
        # Format the mean price to 2 decimal places or return "No data"
        mean_price = round(mean_price_result, 2) if mean_price_result else "No data"
        # Query for distinct gas names to update the list
        distinct_gas_names = Price.query.with_entities(Price.gas_name).distinct().all()
        # Render the index.html template with the mean price and gas names
        return render_template(
            "index.html",
            gas_names=distinct_gas_names,
            gas_name=gas_name,
            mean_price=mean_price,
        )
    else:
        # Redirect to the index page if no gas name is provided
        return redirect(url_for("index"))


def store_prices_from_xml(xml_file_path):
    # Parse the XML file
    tree = ET.parse(xml_file_path)
    root = tree.getroot()

    # Iterate through each <pdv> (station) element
    for pdv in root.findall("pdv"):
        station_id = pdv.get("id")

        # Iterate through each <prix> (price) element within <pdv>
        for prix in pdv.findall("prix"):
            gas_name = prix.get("nom")
            value = float(prix.get("valeur"))
            last_update = datetime.strptime(prix.get("maj"), "%Y-%m-%d %H:%M:%S")

            # Store in database
            price_record = Price(
                station_id=station_id,
                gas_name=gas_name,
                price=value,
                last_update=last_update,
            )
            db.session.add(price_record)

    db.session.commit()
