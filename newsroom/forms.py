"""
Forms for the Newsroom application.

This module defines form classes for user authentication, registration,
and article submission, with TailwindCSS-friendly widget styling.
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model

from .models import Article

User = get_user_model()
CSS = "w-full rounded-xl border border-gray-300 px-4 py-3"


class SignUpForm(UserCreationForm):
    """
    Form for registering a new user with role selection.

    Extends Django’s :class:`~django.contrib.auth.forms.UserCreationForm`
    to include a ``role`` field and enforce unique email addresses.

    Attributes
    ----------
    role : forms.ChoiceField
        Field for selecting the user role, based on :class:`~newsroom.models.User.Roles`.

    Meta
    ----
    model : User
        The custom user model retrieved via :func:`django.contrib.auth.get_user_model`.
    fields : tuple[str]
        Fields included in the form (``username``, ``email``). Passwords are
        handled by :class:`UserCreationForm`.
    """

    role = forms.ChoiceField(choices=User.Roles.choices)

    class Meta(UserCreationForm.Meta):
        model = User
        # password1/password2 are added by UserCreationForm
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        """
        Initialize the signup form with custom styling and field behavior.

        - Makes ``email`` required.
        - Sets default ``role`` to *READER*.
        - Removes default Django help text for username.
        - Adds TailwindCSS classes to all widgets.
        - Adds autocomplete attributes for better UX.
        """
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        self.fields["role"].initial = User.Roles.READER
        self.fields["username"].help_text = ""  # remove long default help text
        for f in self.fields.values():
            f.widget.attrs.setdefault("class", CSS)

        self.fields["username"].widget.attrs.setdefault(
            "autocomplete", "username")
        self.fields["email"].widget.attrs.setdefault("autocomplete", "email")
        self.fields["password1"].widget.attrs.setdefault(
            "autocomplete", "new-password")
        self.fields["password2"].widget.attrs.setdefault(
            "autocomplete", "new-password")

    def clean_email(self):
        """
        Validate that the provided email is unique.

        Returns
        -------
        str
            A cleaned, lowercase version of the email.

        Raises
        ------
        forms.ValidationError
            If the email is already registered.
        """
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        """
        Save the user instance with email and role fields.

        Parameters
        ----------
        commit : bool, optional
            Whether to save the object to the database immediately,
            by default ``True``.

        Returns
        -------
        User
            The created user instance.
        """
        user = super().save(commit=False)  # sets username + hashed password
        user.email = self.cleaned_data["email"]
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()  # User.save() assigns the correct group
        return user


class StyledAuthForm(AuthenticationForm):
    """
    Login form with TailwindCSS-friendly widget styling.

    Extends :class:`~django.contrib.auth.forms.AuthenticationForm` and
    adds utility classes and placeholders so no ``|add_class`` template
    filter is required.
    """

    def __init__(self, *args, **kwargs):
        """
        Initialize the login form with TailwindCSS classes and placeholders.

        - Adds CSS classes to all fields.
        - Sets placeholders for username and password.
        - Sets autocomplete attributes for smoother login experience.
        """
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs.setdefault("class", CSS)
        self.fields["username"].widget.attrs.setdefault(
            "placeholder", "Username")
        self.fields["password"].widget.attrs.setdefault(
            "placeholder", "Password")
        self.fields["username"].widget.attrs.setdefault(
            "autocomplete", "username")
        self.fields["password"].widget.attrs.setdefault(
            "autocomplete", "current-password")


class ArticleForm(forms.ModelForm):
    """
    Form for creating or editing an :class:`~newsroom.models.Article`.

    Provides TailwindCSS widget styling for all fields.

    Meta
    ----
    model : Article
        The :class:`~newsroom.models.Article` model.
    fields : list[str]
        ``title``, ``body``, ``cover_url``, ``publisher``.
    widgets : dict
        Mapping of fields to styled form widgets.
    """

    class Meta:
        model = Article
        fields = ["title", "body", "cover_url", "publisher"]
        widgets = {
            "title": forms.TextInput(attrs={"class": CSS}),
            "body": forms.Textarea(attrs={"class": CSS, "rows": 8}),
            "cover_url": forms.URLInput(attrs={"class": CSS}),
            "publisher": forms.Select(attrs={"class": CSS}),
        }
