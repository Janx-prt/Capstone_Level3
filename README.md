<<<<<<< HEAD
# Capstone_Level3
=======
## SCOOP — Newsroom & API (Django)

A small newsroom app for your capstone. It ships with:
A public landing page that previews Articles (with cover images).
Auth (login, logout, signup) and a modal signup on the landing page.
Roles on the custom User model: Reader, Journalist, Editor (+ admin).
Editorial workflow (journalists write; editors approve).
A REST API (DRF) for Article and Publisher.
Management commands to seed roles and demo data.

## Tech Stack

Python 3.11+ (works on 3.13 in your env)
Django 4.2
Django REST Framework
SQLite (default)
Tailwind (CDN) for quick styling
django-widget-tweaks for nicer form rendering

## Requirements 

Install dependencies:

```bash
pip install -r requirements.txt
```

asgiref==3.9.1
black==25.1.0
certifi==2025.8.3
charset-normalizer==3.4.3
click==8.2.1
colorama==0.4.6
Django==4.2.24
django-widget-tweaks==1.5.0
djangorestframework==3.16.1
flake8==7.3.0
idna==3.10
mccabe==0.7.0
mypy_extensions==1.1.0
packaging==25.0
pathspec==0.12.1
pillow==11.3.0
platformdirs==4.4.0
pycodestyle==2.14.0
pyflakes==3.4.0
python-dotenv==1.1.1
requests==2.32.5
sqlparse==0.5.3
tzdata==2025.2
urllib3==2.5.0


## Project Structure
news_project/
├─ capostone/
│  ├─ __init__.py
│  ├─ asgi.py
│  ├─ settings.py            # AUTH_USER_MODEL = 'newsroom.User'
│  ├─ urls.py                # includes accounts, API, and newsroom urls (namespaced)
│  └─ wsgi.py
├─ newsroom/
│  ├─ __init__.py
│  ├─ admin.py
│  ├─ apps.py
│  ├─ emails.py
│  ├─ forms.py               # SignUpForm etc.
│  ├─ models.py              # User, Article, Publisher, etc.
│  ├─ signals.py
│  ├─ tests.py
│  ├─ test_api.py
│  ├─ urls.py                # web routes (app_name = "articles")
│  ├─ views.py               # LandingView, ArticleDetailView, SignUpView, CRUD views…
│  ├─ permissions.py         # DRF permission classes (IsJournalist, IsEditor, etc.)
│  ├─ management/
│  │  └─ commands/
│  │     ├─ seed_roles.py            # create Reader/Journalist/Editor roles
│  │     ├─ bootstrap_roles.py       # optional bootstrap
│  │     └─ seed_demo_articles.py    # create 2–3 sample articles with covers
│  ├─ migrations/
│  ├─ templates/
│  │  └─ articles/  
│  │  |   └─ tasks/     
│  │  |     └─ tasks/ 
│  │  |   │  ├─ detail.html
│  │  |   │  ├─ form.html
│  │  ├─ base.html
│  │  ├─ landing.html
│  │  ├─ registration/
│  │  │  ├─ login.html
│  │  │  └─ signup.html                
│  ├─ static/
│  │  └─ tasks/     
│  └─ api/
│     ├─ __init__.py
│     ├─ serializers.py
│     ├─ views.py              # DRF viewsets: ArticleViewSet, PublisherViewSet
│     ├─ urls.py               # /api/ mounted here from project urls
│     └─ permissions.py        # (if present) usually move to newsroom/permissions.py
├─ static/
├─ staticfiles/
└─ db.sqlite3

## Quick Start

1) Create & activate a virtual env (you already have myenv)
python -m venv .venv
.\.venv\Scripts\activate

2) Install deps
pip install django==4.2.* djangorestframework django-widget-tweaks

3) Migrate database
python manage.py migrate

4) Create a superuser
python manage.py createsuperuser

5) Seed roles and demo articles (optional but nice)
python manage.py seed_roles
python manage.py seed_demo_articles

6) Run the dev server
python manage.py runserver


## URLs (Web)
| Path                      | Name                       | Notes                                                    |
| ------------------------- | -------------------------- | -------------------------------------------------------- |
| `/`                       | `articles:landing`         | Public landing page with article previews (cover images) |
| `/articles/<pk>/`         | `articles:article-detail`  | **Login required**; shows full article                   |
| `/articles/new/`          | `articles:article-create`  | Journalist-only                                          |
| `/articles/<pk>/edit/`    | `articles:article-edit`    | Author or Editor                                         |
| `/articles/<pk>/delete/`  | `articles:article-delete`  | Author or Editor                                         |
| `/review/`                | `articles:review`          | Editors’ review queue                                    |
| `/articles/<pk>/approve/` | `articles:article-approve` | Editor-only                                              |
| `/signup/`                | `articles:signup`          | Sign up (also used by landing modal)                     |
| `/accounts/login/`        | `login`                    | Django auth                                              |
| `/accounts/logout/`       | `logout`                   | Django auth                                              |
| `/admin/`                 | —                          | Django admin                                             |

## Settings hooks
LOGIN_REDIRECT_URL = 'articles:landing'
LOGOUT_REDIRECT_URL = 'articles:landing'

## API (DRF)
The project registers a DRF router under /api/:
| Endpoint                | Methods                 | Description                |
| ----------------------- | ----------------------- | -------------------------- |
| `/api/articles/`        | GET, POST               | List / create articles     |
| `/api/articles/{id}/`   | GET, PUT, PATCH, DELETE | Retrieve / update / delete |
| `/api/publishers/`      | GET, POST               | List / create publishers   |
| `/api/publishers/{id}/` | GET, PUT, PATCH, DELETE | Retrieve / update / delete |

## Auth for Postman
Enabled: BasicAuthentication and SessionAuthentication.
Easiest in Postman: choose Basic Auth and use a Django user’s username/password.
Set Content-Type: application/json for POST/PUT/PATCH.

Example: Create an Article
POST /api/articles/
Authorization: Basic <base64 creds>
Content-Type: application/json

{
  "title": "Inside the Atelier",
  "body": "Long-form content…",
  "cover_url": "https://picsum.photos/id/237/800/1000",
  "publisher": 1            // if your serializer expects an ID
}
Object-level permissions (see below) ensure only authors/editors/admins can mutate content.

## Roles & Permissions

Custom User has helpers: is_reader(), is_journalist(), is_editor().
DRF permission classes (from newsroom/permissions.py):
- IsReader, IsJournalist, IsEditor (role gates)
- ReadOnly (SAFE methods)
- IsAuthorOrEditor (object-level: author can edit their own; editors/admins can edit anything)
- IsEditorOrReadOnly (anyone can read; only editors/admins can modify)
Typical usage
    - ArticleViewSet
        - List/Retrieve: any authenticated user.
        - Create: IsJournalist (or editor/admin).
        - Update/Delete: IsAuthorOrEditor (plus admin).
    - PublisherViewSet
        - List/Retrieve: any authenticated user.
        - Create/Update/Delete: IsEditor (or admin).

## CRUD Matrix

Articles (Web & API)
Legend: ✅ allowed, 🔒 object-level (must be the author) or role, ❌ not allowed
|  Action | Reader | Journalist | Editor | Admin |
| ------: | :----: | :--------: | :----: | :---: |
|  Create |    ❌   |      ✅     |    ✅   |   ✅   |
|    Read |   ✅\*  |      ✅     |    ✅   |   ✅   |
|  Update |    ❌   |  🔒 (own)  |    ✅   |   ✅   |
|  Delete |    ❌   |  🔒 (own)  |    ✅   |   ✅   |
| Approve |    ❌   |      ❌     |    ✅   |   ✅   |
* Landing list is public. Full article detail requires login (any role).

Publishers (API)
| Action | Reader | Journalist | Editor | Admin |
| -----: | :----: | :--------: | :----: | :---: |
| Create |    ❌   |      ❌     |    ✅   |   ✅   |
|   Read |    ✅   |      ✅     |    ✅   |   ✅   |
| Update |    ❌   |      ❌     |    ✅   |   ✅   |
| Delete |    ❌   |      ❌     |    ✅   |   ✅   |


## Seeding Demo Content

python manage.py seed_roles           # creates Reader/Journalist/Editor roles
python manage.py seed_demo_articles   # adds 2–3 example articles with images

## Running Tests

python manage.py test


## Troubleshooting

NoReverseMatch: 'signup'
Make sure the link uses the namespace:

In newsroom/urls.py: app_name = "articles" and path("signup/", SignUpView.as_view(), name="signup")

In templates: {% url 'articles:signup' %}

In project capostone/urls.py:

path("", include(("newsroom.urls", "articles"), namespace="articles")),


'tasks' is not a registered namespace when rendering auth pages
Your base.html should not reference {% url 'tasks:...' %} unless you actually have a tasks app with app_name = 'tasks'. Remove those links or replace them with newsroom links.

ModuleNotFoundError: newsroom.permissions
Keep permissions.py at newsroom/permissions.py and import with from newsroom.permissions import .... Avoid duplicate files under newsroom/api/permissions.py.

403 / CSRF errors in Postman
Use Basic Auth for DRF endpoints, or obtain a CSRF token and session cookie when using SessionAuth.

## Developer Notes

Static & Styling: landing.html uses Tailwind via CDN for simple cards.
Images: Articles display cover_url (string URL). Swap to ImageField if you want uploads.
Settings:
    REST_FRAMEWORK enables BasicAuthentication and SessionAuthentication.
    AUTH_USER_MODEL = 'newsroom.User'.

>>>>>>> 992d4d2 (Initial commit: Django project with requirements and .gitignore)
