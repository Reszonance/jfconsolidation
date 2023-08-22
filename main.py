import os
from website import create_app

app = create_app()

# without conditional check
# any file that imports website will do app.run()
# debug=True will update web server when code changes
if __name__ == '__main__':
    app.run(debug=True)
    
else:
    gunicorn_app = create_app()
    port = int(os.getenv("PORT", 10000))
    from gunicorn.app.wsgiapp import WSGIApplication
    WSGIApplication("%(prog)s [OPTIONS] [APP_MODULE]").run()