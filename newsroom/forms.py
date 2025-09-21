# newsroom/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import get_user_model

from .models import Article

User = get_user_model()
CSS = "w-full rounded-xl border border-gray-300 px-4 py-3"


class SignUpForm(UserCreationForm):
    role = forms.ChoiceField(choices=User.Roles.choices)

    class Meta(UserCreationForm.Meta):
        model = User
        # password1/password2 are added by UserCreationForm
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["email"].required = True
        self.fields["role"].initial = User.Roles.READER
        # Optional: hide Django’s long default help text for username
        self.fields["username"].help_text = ""
        # Add Tailwind classes
        for f in self.fields.values():
            f.widget.attrs.setdefault("class", CSS)
        # Nice-to-have UX
        self.fields["username"].widget.attrs.setdefault(
            "autocomplete", "username")
        self.fields["email"].widget.attrs.setdefault("autocomplete", "email")
        self.fields["password1"].widget.attrs.setdefault(
            "autocomplete", "new-password")
        self.fields["password2"].widget.attrs.setdefault(
            "autocomplete", "new-password")

    # Optional: enforce unique emails; remove if you don’t want this rule
    def clean_email(self):
        email = (self.cleaned_data.get("email") or "").strip().lower()
        if email and User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)  # sets username + hashed password
        user.email = self.cleaned_data["email"]
        user.role = self.cleaned_data["role"]
        if commit:
            user.save()  # your User.save() assigns the correct group
        return user


class StyledAuthForm(AuthenticationForm):
    """Login form with Tailwind-friendly widgets (no |add_class needed)."""

    def __init__(self, *args, **kwargs):
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
    class Meta:
        model = Article
        fields = ["title", "body", "cover_url", "publisher"]
        widgets = {
            "title": forms.TextInput(attrs={"class": CSS}),
            "body": forms.Textarea(attrs={"class": CSS, "rows": 8}),
            "cover_url": forms.URLInput(attrs={"class": CSS}),
            "publisher": forms.Select(attrs={"class": CSS}),
        }
