import os
import random

from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Boolean, Integer, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from dotenv import load_dotenv


load_dotenv()

TOP_SECRET_API_KEY = os.getenv("TOP-SECRET-API-KEY")

app = Flask(__name__)


# CREATE DB
class Base(DeclarativeBase):
    pass

# Connect to Database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///cafes.db"
db = SQLAlchemy(model_class=Base)
db.init_app(app)


# Cafe TABLE Configuration
class Cafe(db.Model):
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
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


with app.app_context():
    db.create_all()


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/random")
def get_random_cafe():
    cafes = db.session.execute(db.select(Cafe)).scalars().all()
    random_cafe = random.choice(cafes).to_dict()
    return jsonify(random_cafe)


@app.route("/all")
def get_all_cafe():
    cafes = db.session.execute(db.select(Cafe)).scalars().all()
    cafe_list = [cafe.to_dict() for cafe in cafes]
    return jsonify(cafe=cafe_list)


@app.route("/search/")
def search_cafe():
    loc = request.args.get("loc")
    cafes = db.session.execute(db.select(Cafe).filter_by(location=loc)).scalars().all()
    cafe_list = [cafe.to_dict() for cafe in cafes]

    if not cafe_list:
        return jsonify(
            error=f"Not Found: Sorry, we don't have a cafe at that location."
        )

    return jsonify(cafe=cafe_list)


@app.route("/add", methods=['POST'])
def add_cafe():
    data = request.form.to_dict()

    # bool field
    bool_field = ["has_toilet", "has_wifi", "has_sockets", "can_take_calls"]
    for field in bool_field:
        data[field] = int(data[field])

    cafe = Cafe(**data)
    db.session.add(cafe)
    db.session.commit()

    return jsonify(response={"success": "Successfully added the new cafe."})


@app.route("/report-closed/<int:cafe_id>", methods=['DELETE'])
def delete_cafe(cafe_id):
    id = cafe_id
    cafe = db.get_or_404(Cafe, cafe_id, description=f"Error: the cafe {id} is not Found. ")

    api_key = request.headers['Authorization']
    if api_key == TOP_SECRET_API_KEY:
        db.session.delete(cafe)
        db.session.commit()
    else:
        return jsonify(response={"Error": f"Failed to delete the cafe {id}. Check Authorization key."}), 403

    return jsonify(response={"success": f"Successfully deleted the cafe {cafe.name}."}), 200


@app.route("/update-price/<int:cafe_id>", methods=['PATCH'])
def update_price(cafe_id):
    try:
        cafe = db.get_or_404(Cafe, cafe_id)
    except:
        return jsonify(response={"failed": f"cafe {cafe_id} is not found."}), 404

    new_cafe_price = request.form["coffee_price"]
    cafe.coffee_price = new_cafe_price
    db.session.commit()

    # return f"{cafe_id}"
    return jsonify(response={"success": f"Successfully updated the cafe price to {new_cafe_price}."}), 200


# HTTP GET - Read Record

# HTTP POST - Create Record

# HTTP PUT/PATCH - Update Record

# HTTP DELETE - Delete Record


if __name__ == "__main__":
    app.run(debug=True)
