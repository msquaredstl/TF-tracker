from app.db.session import init_db


def main():
    init_db()
    print("Database ready. Use seed_from_yaml or seed_from_csvs to populate.")


if __name__ == "__main__":
    main()
