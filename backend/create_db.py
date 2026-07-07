from .init import create_app, create_default_admin, db


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        create_default_admin()
    print("SQLite database schema created successfully.")


if __name__ == "__main__":
    main()
