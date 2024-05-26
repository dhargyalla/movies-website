from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,FloatField
from wtforms.validators import DataRequired,NumberRange
import requests


'''
Red underlines? Install the required packages first: 
Open the Terminal in PyCharm (bottom left). 

On Windows type:
python -m pip install -r requirements.txt

On MacOS type:
pip3 install -r requirements.txt

This will install the packages from requirements.txt for this project.
'''

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap5(app)

MOVIE_DB_API_KEY = "a2953317eb06bd57673ec3c87228c375"
MOVIE_DB_SEARCH_URL ="https://api.themoviedb.org/3/search/movie"
MOVIE_DB_IMAGE_URL = "http://image.tmdb.org/t/p/original"
MOVIE_DB_INFO_URL =  "https://api.themoviedb.org/3/movie"


class UpdateMovie(FlaskForm):
    rating = FloatField('Rating', validators=[DataRequired(), NumberRange(min=0, max=10, message="Rating must be between 0 and 10")])
    review = StringField('Review', validators=[DataRequired()])
    submit = SubmitField('Done')

class AddMovie(FlaskForm):
    title = StringField('Movie Title', validators=[DataRequired()])
    submit = SubmitField('Add movie')


# CREATE DB
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movie-collection.db'
class Base(DeclarativeBase):
    pass
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# CREATE TABLE
class Movie(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(250), unique=True, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    description: Mapped[str] = mapped_column(String(250), nullable=False)
    rating: Mapped[float] = mapped_column(Float, nullable=True)
    ranking: Mapped[int] = mapped_column(Integer,nullable=True)
    review: Mapped[str] = mapped_column(String, nullable=True)
    img_url: Mapped[str] = mapped_column(String, nullable=False)

with app.app_context():
    db.create_all()
    # CREATE NEW RECORD
    # new_movie = Movie(
    #     title="Phone Booth",
    #     year=2002,
    #     description="Publicist Stuart Shepard finds himself trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside help, Stuart's negotiation with the caller leads to a jaw-dropping climax.",
    #     rating=7.3,
    #     ranking=10,
    #     review="My favourite character was the caller.",
    #     img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg"
    #     )
    # db.session.add(new_movie)
    # db.session.commit()

#CREATE SECOND RECORD

# second_movie = Movie(
#     title="Avatar The Way of Water",
#     year=2022,
#     description="Set more than a decade after the events of the first film, learn the story of the Sully family (Jake, Neytiri, and their kids), the trouble that follows them, the lengths they go to keep each other safe, the battles they fight to stay alive, and the tragedies they endure.",
#     rating=7.3,
#     ranking=9,
#     review="I liked the water.",
#     img_url="https://image.tmdb.org/t/p/w500/t6HIqrRAclMCA60NsSmeqe9RmNV.jpg"
# )
# with app.app_context():
#     db.session.add(second_movie)
#     db.session.commit()

@app.route("/")
def home():
    # all_movies = db.session.execute(db.select(Movie).order_by(desc(Movie.ranking))).scalars()
    result = db.session.execute(db.select(Movie).order_by(Movie.ranking))
    all_movies = result.scalars().all()

    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", movies=all_movies)

@app.route("/edit/<int:movie_id>", methods = ['GET', 'POST'])
def edit(movie_id):
    form = UpdateMovie()
    #we can fetch the id like this also, instead of passing the id via url
    # movie_id = request.args.get("id")
    movie_selected = db.get_or_404(Movie, movie_id)
    if form.validate_on_submit():
        rating = form.rating.data
        review = form.review.data
        movie_to_update = db.session.execute(db.select(Movie).where(Movie.id == movie_id)).scalar()
        movie_to_update.rating = rating
        movie_to_update.review = review
        db.session.commit()
        return redirect(url_for('home'))
    return render_template("edit.html", form = form, movie=movie_selected)

@app.route("/delete", methods = ['GET', 'POST'])
def delete():
    movie_id = request.args.get("movie_id")
    book_to_delete = db.get_or_404(Movie, movie_id)
    db.session.delete(book_to_delete)
    db.session.commit()
    return redirect(url_for('home'))

@app.route("/add", methods = ['GET', 'POST'])
def add():
    form = AddMovie()
    if form.validate_on_submit():
        movie_title = form.title.data
        response = requests.get(MOVIE_DB_SEARCH_URL, params={"api_key": MOVIE_DB_API_KEY, "query": movie_title})
        response.raise_for_status()
        data = response.json()
        movies_data = data['results']

        return render_template("select.html", data = movies_data)
    return render_template("add.html", form = form)

@app.route("/find")
def findMovie():
    movie_api_id = request.args.get("movie_id")
    if movie_api_id:
        movie_api_url = f"{MOVIE_DB_INFO_URL}/{movie_api_id}"
        response = requests.get(movie_api_url, params={"api_key": MOVIE_DB_API_KEY})
        data = response.json()
        new_movie = Movie(
            title= data["title"],
            # The data in release_date includes month and day, we will want to get rid of.
            year=data["release_date"].split("-")[0],
            img_url=f"{MOVIE_DB_IMAGE_URL}{data['poster_path']}",
            description=data["overview"]

        )

        db.session.add(new_movie)
        db.session.commit()

    return redirect(url_for("edit", movie_id=new_movie.id))

if __name__ == '__main__':
    app.run(debug=True)
