# College LMS Portal

## Setup Instructions

1. Clone the repository:
   git clone <repo_url>

2. Create & activate virtual environment:
   python -m venv venv
   venv\Scripts\activate   # Windows
   source venv/bin/activate  # macOS/Linux

3. Install dependencies:
   pip install -r requirements.txt

4. Copy .env.example → .env and fill credentials

5. Create empty folders:
   uploads/
   video_uploads/

6. Run the app:
   python app.py

7. Open in browser:
   http://127.0.0.1:5000
