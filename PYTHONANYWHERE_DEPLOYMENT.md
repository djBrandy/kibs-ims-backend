# PythonAnywhere Flask Deployment Guide

## Step 1: Prepare Your Files

1. Run the deployment script:
   ```bash
   python deploy_to_pythonanywhere.py
   ```
   This creates `kibs_backend_deployment.zip`

## Step 2: Upload to PythonAnywhere

1. Log into your PythonAnywhere account
2. Go to the **Files** tab
3. Upload `kibs_backend_deployment.zip` to your home directory
4. Extract the zip file:
   ```bash
   unzip kibs_backend_deployment.zip
   mv deployment_package kibs-ims-backend
   ```

## Step 3: Install Dependencies

1. Open a **Bash console** in PythonAnywhere
2. Navigate to your project:
   ```bash
   cd ~/kibs-ims-backend
   ```
3. Install requirements:
   ```bash
   pip3.10 install --user -r requirements_pythonanywhere.txt
   ```

## Step 4: Configure Web App

1. Go to the **Web** tab in PythonAnywhere
2. Click **"Add a new web app"**
3. Choose **"Manual configuration"**
4. Select **Python 3.10**
5. In the **Code** section:
   - **Source code**: `/home/djbrandy67/kibs-ims-backend`
   - **Working directory**: `/home/djbrandy67/kibs-ims-backend`
   - **WSGI configuration file**: `/var/www/djbrandy67_pythonanywhere_com_wsgi.py`

## Step 5: Configure WSGI File

1. Click on the WSGI configuration file link
2. Replace the entire content with:

```python
import sys
import os

# Add your project directory to the Python path
project_home = '/home/djbrandy67/kibs-ims-backend'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variables
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('DEBUG', 'False')

# Import your Flask application
from app import app as application

# Initialize database
with application.app_context():
    try:
        from app.database import db
        db.create_all()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Database initialization error: {e}")
```

## Step 6: Set Up Database

1. In a Bash console, run:
   ```bash
   cd ~/kibs-ims-backend
   python3.10 migrate_pythonanywhere.py
   ```

## Step 7: Configure Static Files (Optional)

If you have static files:
1. In the **Web** tab, scroll to **Static files**
2. Add:
   - **URL**: `/static/`
   - **Directory**: `/home/djbrandy67/kibs-ims-backend/static/`

## Step 8: Reload and Test

1. Click the **"Reload"** button in the Web tab
2. Visit your app at: `https://djbrandy67.pythonanywhere.com`

## Troubleshooting

### Check Error Logs
- Go to **Web** tab → **Log files**
- Check both **Error log** and **Server log**

### Common Issues
1. **Import errors**: Check that all dependencies are installed
2. **Database errors**: Verify MySQL connection settings
3. **Path issues**: Ensure all paths use `/home/djbrandy67/kibs-ims-backend`

### Test Database Connection
```python
# In a Python console
from app import app
with app.app_context():
    from app.database import db
    print(db.engine.execute("SELECT 1").fetchone())
```

## Production Checklist

- [ ] All dependencies installed
- [ ] Database connection working
- [ ] WSGI file configured correctly
- [ ] Static files serving (if needed)
- [ ] Error logs checked
- [ ] App accessible via browser
- [ ] Admin user created (admin/admin123)

## Environment Variables (Optional)

For better security, set these in your WSGI file:
```python
os.environ['SECRET_KEY'] = 'your-secret-key-here'
os.environ['JWT_SECRET_KEY'] = 'your-jwt-secret-here'
```