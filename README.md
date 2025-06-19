# E-Learning Platform

A comprehensive e-learning platform built with Flask and MongoDB, featuring course management, user authentication, and payment integration.

## Features

- User roles (Admin, Instructor, Student)
- Course management
- Payment integration with Stripe
- Quiz system
- Progress tracking
- Contact form
- Responsive design

## Prerequisites

- Python 3.8+
- MongoDB
- Stripe account for payments

## Setup Instructions

1. Create a virtual environment:
```bash
python -m venv .venv
```

2. Activate the virtual environment:
- Windows:
```bash
.venv\Scripts\activate
```
- Unix/MacOS:
```bash
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with:
```
STRIPE_SECRET_KEY=your_stripe_secret_key_here
STRIPE_PUBLIC_KEY=your_stripe_public_key_here
```

5. Start MongoDB service

6. Run the application:
```bash
python app.py
```

The application will be available at http://127.0.0.1:5000

## Directory Structure

```
.
├── app.py              # Main application file
├── requirements.txt    # Python dependencies
├── .env               # Environment variables
├── static/            # Static files (CSS, JS, images)
│   └── images/        # Course and user images
└── templates/         # HTML templates
    ├── admin/         # Admin panel templates
    ├── instructor/    # Instructor dashboard templates
    └── student/       # Student dashboard templates
```

## Initial Setup

1. Start the application
2. Register an admin user
3. Log in and start adding courses
4. Set up Stripe for payments

## Contributing

1. Fork the repository
2. Create a new branch
3. Make your changes
4. Submit a pull request

## License

MIT License