# stores standard routes for website
# ie. where users can go to 
from flask import Blueprint, render_template

# blueprint defines a bunch of URLs
# naming it 'views' is optional but simplifies things
views = Blueprint('views', __name__)

# define route for homepage
# home() will run whenever user goes to homepage
# (ie. root directory '/')
@views.route('/')
def home():
    # applies html template to homepage
    return render_template("home.html")