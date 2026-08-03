from app.db.base_metadata import Base
from app.db.session import engine


def main() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database tables created from SQLAlchemy metadata.")


if __name__ == "__main__":
    main()
