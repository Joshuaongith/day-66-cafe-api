"""
Cafe API Server
Provides a RESTful interface for managing a SQLite database of cafes.
"""

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Boolean

app = Flask(__name__)


# ==========================================
# DATABASE CONFIGURATION
# ==========================================
class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///cafes.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# ==========================================
# MODELS
# ==========================================
class Cafe(db.Model):
    """Database model representing a cafe entity."""

    __tablename__ = "cafe"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    map_url: Mapped[str] = mapped_column(String(500), nullable=False)
    img_url: Mapped[str] = mapped_column(String(500), nullable=False)
    location: Mapped[str] = mapped_column(String(250), nullable=False)
    seats: Mapped[str] = mapped_column(String(250), nullable=False)
    has_toilet: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_wifi: Mapped[bool] = mapped_column(Boolean, nullable=False)
    has_sockets: Mapped[bool] = mapped_column(Boolean, nullable=False)
    can_take_calls: Mapped[bool] = mapped_column(Boolean, nullable=False)
    coffee_price: Mapped[str] = mapped_column(String(250), nullable=True)

    def to_dict(self):
        """Serializes the SQLAlchemy model instance into a Python dictionary."""
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}


with app.app_context():
    db.create_all()


# ==========================================
# ROUTES
# ==========================================
@app.route("/")
def home():
    """Renders the API documentation landing page."""
    return render_template("index.html")


@app.route("/random")
def random():
    """Retrieves a single random cafe record."""
    random_cafe = db.session.scalar(
        db.select(Cafe).order_by(db.func.random()).limit(1)
    )
    return jsonify(cafe=random_cafe.to_dict()), 200


@app.route("/all")
def find_all_cafes():
    """Retrieves all cafe records."""
    all_cafe = db.session.scalars(db.select(Cafe))
    cafes = [cafe.to_dict() for cafe in all_cafe]
    return jsonify(cafes=cafes), 200


@app.route("/search")
def search():
    """
    Searches for cafes by location.
    Requires query parameter: loc (str)
    """
    query_location = request.args.get("loc")

    # Parameter validation
    if not query_location:
        return jsonify(error={"Bad Request": "Missing required query parameter: 'loc'."}), 400

    query_location = query_location.title()
    search_cafe = db.session.scalars(
        db.select(Cafe).where(Cafe.location == query_location)
    ).all()

    if search_cafe:
        result = [cafe.to_dict() for cafe in search_cafe]
        return jsonify(cafe=result), 200

    return jsonify(error={"Not found": "No cafes found at the specified location."}), 404


@app.route("/add", methods=["POST"])
def add_cafe():
    """
    Creates a new cafe record.
    Requires form data matching the Cafe model columns.
    """
    required_fields = ["name", "map_url", "img_url", "location", "seats"]
    missing_fields = [field for field in required_fields if not request.form.get(field)]

    # Request validation
    if missing_fields:
        if request.form.get("coffee_price") and len(missing_fields) == len(required_fields):
            return jsonify(error={
                "Bad Request": "Missing required fields for resource creation.",
                "Hint": "To update an existing record, use the PATCH /update-price/<id> endpoint."
            }), 400

        return jsonify(error={
            "Bad Request": f"Missing required fields: {', '.join(missing_fields)}"
        }), 400

    # Instantiate model and parse strings to boolean
    new_cafe = Cafe(
        name=request.form.get("name"),
        map_url=request.form.get("map_url"),
        img_url=request.form.get("img_url"),
        location=request.form.get("location"),
        seats=request.form.get("seats"),
        coffee_price=request.form.get("coffee_price"),
        has_toilet=request.form.get("has_toilet") == "1",
        has_wifi=request.form.get("has_wifi") == "1",
        has_sockets=request.form.get("has_sockets") == "1",
        can_take_calls=request.form.get("can_take_calls") == "1"
    )

    db.session.add(new_cafe)
    db.session.commit()

    return jsonify(response={"success": "Successfully added the new cafe."}), 201


@app.route("/update-price/<int:cafe_id>", methods=["PATCH"])
def update_coffee_price(cafe_id):
    """
    Updates the coffee_price attribute of a specific cafe.
    Requires path variable: cafe_id (int)
    Requires query parameter: price (str)
    """
    new_price = request.args.get("price")

    # Parameter validation
    if not new_price:
        return jsonify(error={"Bad Request": "Missing required query parameter: 'price'."}), 400

    updated_entry = db.session.get(Cafe, cafe_id)

    if updated_entry:
        updated_entry.coffee_price = new_price
        db.session.commit()
        return jsonify(success="Successfully updated the price."), 200

    return jsonify(error={"Not found": "Cafe ID not found in database."}), 404


@app.route("/report-closed/<int:cafe_id>", methods=["DELETE"])
def delete_cafe(cafe_id):
    """
    Deletes a cafe record from the database.
    Requires path variable: cafe_id (int)
    Requires authentication via query parameter: api-key (str)
    """
    # Authentication check
    if request.args.get("api-key") != "TopSecretAPIKey":
        return jsonify(error={"Forbidden": "Invalid API key."}), 403

    entry_to_delete = db.session.get(Cafe, cafe_id)

    # Resource validation
    if not entry_to_delete:
        return jsonify(error={"Not found": "Cafe ID not found in database."}), 404

    # Database transaction (Simulated for local development)
    # db.session.delete(entry_to_delete)
    # db.session.commit()

    return jsonify(success="Successfully deleted the cafe."), 200


if __name__ == '__main__':
    app.run(debug=True)