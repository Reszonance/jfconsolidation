# website is a python package
# when you put an __init__.py inside a folder it becomes a python package
from website import create_app

app = create_app()

# without conditional check
# any file that imports website will do app.run()
# debug=True will update web server when code changes
if __name__ == '__main__':
    app.run(debug = True)
else:
    gunicorn_app = create_app()