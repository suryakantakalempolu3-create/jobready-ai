"""Load sample data: demo student account + job listings into MySQL.
Usage:  python seed.py          (add missing sample data)
        python seed.py --reset  (delete all rows first)
"""
import sys
from app import create_app
from app.seed_data import seed_all

if __name__ == "__main__":
    app = create_app(seed=False)
    with app.app_context():
        seed_all(reset="--reset" in sys.argv)
    print("Seeded. Demo login -> demo@jobready.ai / Demo@1234")
