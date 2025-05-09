# IMS KIBS Backend

## Overview
IMS KIBS is a Flask-based application designed to manage inventory and order processing. This project provides a structured approach to handle products, categories, and orders efficiently.

## Project Structure
```
ims-kibs-backend
├── app
│   ├── __init__.py
│   ├── models.py
│   ├── routes.py
│   └── templates
├── config.py
├── requirements.txt
└── README.md
```

## Setup Instructions

1. **Clone the Repository**
   ```bash
   git clone <repository-url>
   cd ims-kibs-backend
   ```

2. **Create a Virtual Environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the Application**
   Update the `config.py` file with your database connection details and any other necessary configurations.

5. **Run the Application**
   ```bash
   flask run
   ```

## Usage
Once the application is running, you can access it at `http://127.0.0.1:5000`. The application provides endpoints to manage products, categories, and orders.

## Contributing
Contributions are welcome! Please submit a pull request or open an issue for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.