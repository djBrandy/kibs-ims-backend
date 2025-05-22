# KIBS Inventory Management System Backend

Backend API for the KIBS Inventory Management System.

## Deployment

This backend is configured to be deployed on [Render](https://render.com).

### Deployment Steps

1. Create a new PostgreSQL database on Render
2. Create a new Web Service on Render
3. Connect your GitHub repository
4. Use the following settings:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn wsgi:app`
5. Add the following environment variables:
   - `DATABASE_URL`: Will be automatically set if using Render's PostgreSQL
   - `SECRET_KEY`: Generate a secure random string
   - `FLASK_APP`: wsgi.py
   - `FLASK_ENV`: production
   - `FRONTEND_URL`: https://kibs-ims.netlify.app

## Local Development

1. Clone the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - Unix/MacOS: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Create a `.env` file based on `.env.example`
6. Run migrations: `flask db upgrade`
7. Start the development server: `flask run`

## API Documentation

The API is available at the following base URL:

- Production: https://your-render-app-name.onrender.com/api
- Development: http://localhost:5000/api

### Authentication

Authentication is handled via Basic Auth or session cookies.

### Endpoints

- `/api/auth/login` - User login
- `/api/products` - Product management
- `/api/suppliers` - Supplier management
- `/api/role-data` - Role-based data access