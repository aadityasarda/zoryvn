import asyncio
import random
from datetime import date, timedelta

from src.database import async_session, init_db
from src.models.user import User
from src.models.record import FinancialRecord
from src.utils.security import hash_password


USERS = [
    {
        "name": "Admin User",
        "email": "admin@finance.com",
        "password": hash_password("password123"),
        "role": "admin",
        "status": "active",
    },
    {
        "name": "Analyst User",
        "email": "analyst@finance.com",
        "password": hash_password("password123"),
        "role": "analyst",
        "status": "active",
    },
    {
        "name": "Viewer User",
        "email": "viewer@finance.com",
        "password": hash_password("password123"),
        "role": "viewer",
        "status": "active",
    },
]

INCOME_CATEGORIES = [
    ("salary", "Monthly salary payment"),
    ("freelance", "Freelance project income"),
    ("investment", "Investment returns"),
    ("rental", "Rental income"),
    ("bonus", "Performance bonus"),
]

EXPENSE_CATEGORIES = [
    ("rent", "Office/home rent payment"),
    ("utilities", "Electricity, water, internet bills"),
    ("groceries", "Food and grocery shopping"),
    ("transport", "Fuel and transportation"),
    ("software", "Software subscriptions"),
    ("insurance", "Health/life insurance premium"),
    ("marketing", "Marketing and advertising"),
    ("equipment", "Office equipment purchase"),
    ("dining", "Restaurant and dining expenses"),
    ("healthcare", "Medical expenses"),
]


async def seed_database():
    await init_db()

    async with async_session() as session:
        # Check if already seeded
        from sqlalchemy import select, func

        count = await session.execute(select(func.count(User.id)))
        if count.scalar() > 0:
            print("Database already has data. Skipping seed.")
            print("To re-seed, drop all tables in PostgreSQL and run again.")
            return

        # Create users
        user_objects = []
        for user_data in USERS:
            user = User(**user_data)
            session.add(user)
            user_objects.append(user)

        await session.flush()

        print(f"[OK] Created {len(user_objects)} users:")
        for u in user_objects:
            print(f"> {u.email} (role: {u.role}, password: password123)")

        records_created = 0
        today = date.today()

        for user in user_objects:
            num_records = random.randint(15, 20)

            for i in range(num_records):
                days_ago = random.randint(0, 180)
                record_date = today - timedelta(days=days_ago)

                if random.random() < 0.4:
                    record_type = "income"
                    category, desc = random.choice(INCOME_CATEGORIES)
                    amount = round(random.uniform(500, 10000), 2)
                else:
                    record_type = "expense"
                    category, desc = random.choice(EXPENSE_CATEGORIES)
                    amount = round(random.uniform(20, 3000), 2)

                record = FinancialRecord(
                    user_id=user.id,
                    amount=amount,
                    type=record_type,
                    category=category,
                    date=record_date,
                    description=f"{desc} - Record #{i + 1}",
                )
                session.add(record)
                records_created += 1

        await session.commit()

        print(f"[OK] Created {records_created} financial records")
        print()
        print("Login credentials:")
        print("Admin: admin@finance.com / password123")
        print("Analyst: analyst@finance.com / password123")
        print("Viewer: viewer@finance.com / password123")
        print()
        print("Start the server: uvicorn src.main:app --reload")
        print("API docs: http://localhost:8000/docs")


if __name__ == "__main__":
    asyncio.run(seed_database())
