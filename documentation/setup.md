# Local Setup

1. Copy `.env.example` to `.env` and fill in the Neon PostgreSQL connection string.
2. Install Python dependencies with `pip install -r requirements.txt`.
3. Create the database schema with `sql/schema.sql`.
4. Create the Power BI views with `sql/powerbi_views.sql`.
5. Generate sample Excel files by running `python sample_data/generate_sample_excels.py`.
6. Start the app with `python run.py`.

Open `http://127.0.0.1:5000` and log in with the admin credentials from `.env`.