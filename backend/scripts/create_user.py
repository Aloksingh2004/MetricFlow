import argparse
import getpass

from sqlalchemy import select

from app.db.base import Base, SessionLocal, engine
from app.models import User
from app.services.auth import hash_password


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a MetricFlow user without exposing a registration API.")
    parser.add_argument("--email", required=True, help="User email address")
    parser.add_argument("--role", choices=("owner", "member"), default="owner")
    args = parser.parse_args()

    password = getpass.getpass("Password (12+ characters): ")
    if len(password) < 12:
        raise SystemExit("Password must be at least 12 characters.")

    email = args.email.strip().lower()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        if db.scalar(select(User).where(User.email == email)):
            raise SystemExit("A user with that email already exists.")
        db.add(User(email=email, password_hash=hash_password(password), role=args.role, is_active=True))
        db.commit()
    print(f"Created {args.role} account for {email}.")


if __name__ == "__main__":
    main()
