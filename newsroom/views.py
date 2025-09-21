"""
Views for the Newsroom app.

This module defines class-based and function-based views
for user authentication, article management, editorial review,
and the dashboard.
"""

from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from django.urls import reverse, reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import (
    ListView, DetailView, TemplateView, CreateView, UpdateView, DeleteView,
)
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.forms import AuthenticationForm

from .models import Article

try:
    from .forms import SignUpForm, StyledAuthForm as _StyledAuthForm, ArticleForm
except Exception:
    SignUpForm = None
    ArticleForm = None
    _StyledAuthForm = AuthenticationForm


class LoginView(DjangoLoginView):
    """
    Custom login view using a styled authentication form.

    Attributes
    ----------
    template_name : str
        Template for the login page.
    authentication_form : Form
        The form class used for authentication.
    """

    template_name = "registration/login.html"
    authentication_form = _StyledAuthForm


class SignUpView(CreateView):
    """
    User registration view.

    Attributes
    ----------
    form_class : Form
        The form used for signup.
    template_name : str
        Template for the signup page.
    success_url : str
        Redirect URL after successful signup.
    """

    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("articles:landing")


class LandingView(ListView):
    """
    Landing page view displaying approved articles.

    Attributes
    ----------
    template_name : str
        Template for the landing page.
    model : Model
        The model queried (Article).
    context_object_name : str
        Context variable name for the articles.
    queryset : QuerySet
        Approved articles ordered by approval/creation time.
    """

    template_name = "landing.html"
    model = Article
    context_object_name = "articles"
    queryset = (
        Article.objects.filter(status=Article.Status.APPROVED)
        .select_related("author", "publisher")
        .order_by("-approved_at", "-created_at")
    )

    def get_context_data(self, **kwargs):
        """
        Add login and signup forms to the context.
        """
        ctx = super().get_context_data(**kwargs)
        try:
            from .forms import SignUpForm as _SignUpForm
            from .forms import StyledAuthForm as _Styled
            ctx["login_form"] = _Styled(self.request)
            ctx["signup_form"] = _SignUpForm()
        except Exception:
            ctx["login_form"] = AuthenticationForm(self.request)
            ctx["signup_form"] = None
        return ctx


class ArticleDetailView(LoginRequiredMixin, DetailView):
    """
    Article detail view (requires login).

    Attributes
    ----------
    template_name : str
        Template for the article detail.
    model : Model
        The model queried (Article).
    login_url : str
        Redirect URL for unauthenticated users.
    """

    template_name = "articles/detail.html"
    model = Article
    login_url = "login"


class ArticleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """
    Article creation view for journalists.

    Attributes
    ----------
    model : Model
        The model (Article).
    form_class : Form
        The form for creating articles.
    permission_required : str
        Required permission (``newsroom.add_article``).
    template_name : str
        Template for the form.
    """

    model = Article
    form_class = ArticleForm
    permission_required = "newsroom.add_article"
    template_name = "articles/form.html"

    def form_valid(self, form):
        """
        Assign author and set status to PENDING before saving.
        """
        form.instance.author = self.request.user
        form.instance.status = Article.Status.PENDING
        return super().form_valid(form)

    def get_success_url(self):
        """
        Redirect to the article detail page after creation.
        """
        return reverse("articles:article-detail", kwargs={"pk": self.object.pk})


class ArticleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """
    Article update view.

    Attributes
    ----------
    model : Model
        The model (Article).
    form_class : Form
        The form for updating articles.
    permission_required : str
        Required permission (``newsroom.change_article``).
    template_name : str
        Template for the form.
    """

    model = Article
    form_class = ArticleForm
    permission_required = "newsroom.change_article"
    template_name = "articles/form.html"

    def get_success_url(self):
        """
        Redirect to the article detail page after update.
        """
        return reverse("articles:article-detail", kwargs={"pk": self.object.pk})


class ArticleDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    """
    Article delete view.

    Attributes
    ----------
    model : Model
        The model (Article).
    permission_required : str
        Required permission (``newsroom.delete_article``).
    template_name : str
        Template for the delete confirmation.
    success_url : str
        Redirect URL after deletion.
    """

    model = Article
    permission_required = "newsroom.delete_article"
    template_name = "articles/confirm_delete.html"
    success_url = reverse_lazy("articles:landing")


class ReviewQueueView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Review queue view for editors.

    Attributes
    ----------
    model : Model
        The model (Article).
    template_name : str
        Template for the review queue.
    context_object_name : str
        Context variable name for the articles.
    permission_required : str
        Required permission (``newsroom.can_approve``).
    """

    model = Article
    template_name = "articles/review.html"
    context_object_name = "articles"
    permission_required = "newsroom.can_approve"

    def get_queryset(self):
        """
        Return all pending articles for review.
        """
        return (
            Article.objects.filter(status=Article.Status.PENDING)
            .select_related("author", "publisher")
            .order_by("created_at")
        )


@login_required
@permission_required("newsroom.can_approve", raise_exception=True)
def approve_article(request, pk):
    """
    Approve a pending article.

    Parameters
    ----------
    request : HttpRequest
        The incoming request.
    pk : int
        Primary key of the article.

    Returns
    -------
    HttpResponseRedirect
        Redirects to the review queue.
    """
    a = get_object_or_404(Article, pk=pk)
    a.status = Article.Status.APPROVED
    if not a.approved_at:
        a.approved_at = timezone.now()
    a.save(update_fields=["status", "approved_at"])
    return redirect("articles:review")


class DashboardView(TemplateView):
    """
    Dashboard view showing article statistics.

    Attributes
    ----------
    template_name : str
        Template for the dashboard.
    """

    template_name = "tasks/dashboard.html"

    def get_context_data(self, **kwargs):
        """
        Add pending and draft articles to the context.
        """
        ctx = super().get_context_data(**kwargs)
        ctx["pending_articles"] = (
            Article.objects.filter(status=Article.Status.PENDING)
            .select_related("author", "publisher")
            .order_by("-created_at")
        )
        ctx["draft_articles"] = (
            Article.objects.filter(status=Article.Status.DRAFT)
            .select_related("author", "publisher")
            .order_by("-updated_at")
        )
        return ctx
