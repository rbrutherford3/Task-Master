# Task Master

[![standard-readme compliant](https://img.shields.io/badge/readme%20style-standard-brightgreen.svg?style=flat-square)](https://github.com/RichardLitt/standard-readme)

![TaskMaster logo](TaskMaster0.png "TaskMaster logo")

Task Master is a task management software created by Spiff Industries for standard desktop browsers available at [https://masteroftasks.com/](https://masteroftasks.com/).  It allows the user to easily create, edit, and check off tasks that can be optionally descriptive.  The level of detail is up to the user.  It employs the principles of importance and urgency as described in [*The 7 Habits of Highly Effective People&#174;*](https://www.franklincovey.com/the-7-habits/) by Steven Covey.  Each category can be selected as low, medium, or high. This software attempts to bring that system of efficiency to the 21st century.

## Table of Contents

- [Install](#install)
- [Usage](#usage)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgments)

## Install

#### 1. Install Python 3, pip, and venv if they are not already available

On Ubuntu or Debian:

```
sudo apt-get install -y python3 python3-pip python3-venv
```

Use the equivalent package manager or installer for your operating system if you are not on Ubuntu or Debian.

#### 2. Clone the project and change into the repository directory:

```
git clone https://github.com/rbrutherford3/Task-Master.git
cd Task-Master
```

#### 3. Create and activate a virtual environment:

```
python3 -m venv .venv
source .venv/bin/activate
```

#### 4. Install Python dependencies from the project requirements file:

```
pip3 install -r requirements.txt
```

#### 5. Create a [Resend](https://resend.com/) account and get an API key

#### 6. Create Google reCAPTCHAv3 site key and secret keys, making sure your reCAPTCHA configuration allows `localhost` and `127.0.0.1`

#### 7. Create a [neon](https://neon.com/) account and get a connection URL like the own shown below in step 8

#### 8. Configure `local_settings.py`

The project reads local secrets and database settings from `local_settings.py` if the file exists. Create it in the project root and define the values your environment needs.

```python
RESEND_API_KEY = "your-resend-api-key"
RECAPTCHA_SITE_KEY = "your-recaptcha-site-key"
RECAPTCHA_SECRET_KEY = "your-recaptcha-secret-key"
DATABASE_URL = "postgresql://user:password@localhost:5432/taskmaster"
```

`DATABASE_URL` can point to PostgreSQL or MySQL. If it is omitted, the project falls back to SQLite for local development. PostgreSQL support uses psycopg2-binary; if you use MySQL, install the appropriate MySQL driver for your environment.

If you deploy on Vercel, the same values from `local_settings.py` should be entered as environment variables in the Vercel project settings.

#### 9. Finish the Django setup

Run the Django database setup commands and start the development server:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

Open your browser and navigate to `http://127.0.0.1:8000/`.

If you want to use a different timezone, update `TIME_ZONE` in `taskmaster_site/settings.py`. The project currently defaults to `America/New_York`.

#### 10. Optional: when you are done using the app, deactivate the virtual environment:
```
deactivate
```

## Usage

Go to Task Master in your browser, register a new account using your email address, and log in. You may then view, create, edit, and delete tasks. The site is accessible across all devices, including mobile. Through the settings page, you may change your password, change your email address, or delete your account altogether. Deleting your account does indeed purge all records from the database.

## Contributing

Contributions are welcome, including any feedback.  Please contact rbrutherford3 on GitHub.

## License

[MIT © Robert Rutherford](../LICENSE)

## Acknowledgments

* Thanks to my parents for everything
* Thanks to my sister for this computer
* Thanks to Colby Sainato for actually looking at this
* Thanks to Kendall Griffith for also actually looking at this :)
