# QubiPay

A full-stack web application with Python Flask backend and frontend interface.

## Project Structure

```
qubipay/
├── backend/          # Python Flask application
│   ├── app.py
│   ├── database.py
│   ├── models.py
│   └── requirements.txt
├── frontend/         # Web interface
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── app.js
└── .gitignore
```

## Setup

### Backend

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Run the application:
   ```bash
   python app.py
   ```

### Frontend

Open `frontend/index.html` in your web browser to access the frontend interface.

## Requirements

- Python 3.x
- Flask (or dependencies listed in `requirements.txt`)
- Modern web browser

## License

MIT
