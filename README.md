# Books4U 📖📖📖

## Personalized Book Recommendation System Using Django 🥳🥳

### Setting Up the Project 🌟🌟

- The Project works seamlessly on Python version `3.8.6`

- [Fork](https://docs.github.com/en/github/getting-started-with-github/fork-a-repo#fork-an-example-repository) the Repository

- Clone Your Forked copy -
  `git clone https://github.com/[YOUR-USERNAME]/Books4U.git`

- Navigate to the directory of project -
  `cd Books4U/`

- Create a new branch -
  `git checkout -b [branch_name]`

- If you don't have virtualenv already installed -
  `pip install virtualenv`

- Create a new environment -
  `virtualenv bookenv`

- Activate the environment -
  - For Linux/Unix OS : `source bookenv/bin/activate`
  - For Windows OS: `bookenv\Scripts\activate`

- Install requirements -
  `pip install -r requirements.txt`

- Open `BookRecSystem/settings.py`

- Set `SECRET_KEY = "RANDOM_KEY"`

- Set `ALLOWED_HOSTS = ['127.0.0.1', 'localhost']`

- Make Migrations -
  `python manage.py migrate`

- `python manage.py runserver` - You're good to Go!!

#### Optional

- [Creating Superuser](https://www.geeksforgeeks.org/how-to-create-superuser-in-django/)

