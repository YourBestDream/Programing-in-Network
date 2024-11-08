from app import create_app, db

my_app = create_app()

with my_app.app_context():
    db.create_all()

if __name__ == "__main__":
    my_app.run(host="0.0.0.0", port=5000, debug=True)
