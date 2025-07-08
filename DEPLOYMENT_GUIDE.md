# KIBS IMS Backend Deployment Guide for PythonAnywhere

## Prerequisites
- PythonAnywhere account with MySQL database
- Database: `djbrandy67$kibs_ims_db`
- Database user: `djbrandy67`
- Database password: `Brandon`

## Step 1: Upload Files
Upload all backend files to `/home/djbrandy67/kibs-ims-backend/`

## Step 2: Install Dependencies
In PythonAnywhere Bash console:
```bash
cd /home/djbrandy67/kibs-ims-backend
pip3.10 install --user -r requirements_minimal.txt
```

## Step 3: Setup Database
1. Go to PythonAnywhere MySQL console
2. Select database: `djbrandy67$kibs_ims_db`
3. Run the SQL script from `create_tables.sql`

## Step 4: Configure Web App
1. Go to PythonAnywhere Web tab
2. Create new web app (Flask, Python 3.10)
3. Set source code: `/home/djbrandy67/kibs-ims-backend`
4. Set WSGI file: `/home/djbrandy67/kibs-ims-backend/wsgi.py`

## Step 5: Update WSGI Configuration
Edit the WSGI file to point to your app:
```python
import sys
import os

project_home = '/home/djbrandy67/kibs-ims-backend'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

from app import app as application
```

## Step 6: Test the Application
1. Reload the web app
2. Visit your PythonAnywhere URL
3. Test API endpoints

## Default Admin Credentials
- Username: `admin`
- Password: `admin123`

## API Endpoints
- `/api/auth/login` - Login
- `/api/products` - Products management
- `/api/audit/scan/<barcode>` - Product scanning
- `/api/routines` - Routine management
- `/api/suggestions` - Suggestions system

## Mobile Interface Features
All desktop features are available in mobile interface:
- Product management
- Audit system with messages
- Routine scheduling
- Suggestion system
- Stock alerts with audit messages
- QR code generation
- Analytics dashboard

## Troubleshooting
1. Check error logs in PythonAnywhere
2. Verify database connection
3. Ensure all dependencies are installed
4. Check file permissions