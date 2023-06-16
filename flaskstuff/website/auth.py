# copied from views.py
# stores standard routes for website
# ie. where users can go to 
from flask import Blueprint, render_template, request, flash

auth = Blueprint('auth', __name__)

@auth.route('/login', methods=['GET', 'POST'])
def login():
    # request stores information sent in form
    data = request.form
    print(data)
        # returns some HTML for /login to render
    # render_template("login.html") fetches the HTML as a template
    # second arg: define any variable; can be used anywhere within login.html template
    return render_template("login.html", 
                           bool=False)

@auth.route('/logout')
def logout():
    return render_template("base.html")

@auth.route('/sign-up', methods=['GET', 'POST'])
def sign_up():
        # request stores information sent in form
    data = request.form
    print(data)

    if request.method == 'POST':
        email = request.form.get('email')
        firstName = request.form.get('firstName')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')

            # base.html will actually show flash messages
        if len(email) < 4:
            flash('Email must be greater than 4 characters', category='error')
        elif len(firstName) < 2:
            flash('Name is too short', category='error')
        elif password1 != password2:
            flash('Passwords don\'t match', category='error')
        elif len(password1) < 7:
            flash('Password must be at least 7 characters', category='error')
        else:
            flash('Account created', category='success')

    return render_template("signup.html")