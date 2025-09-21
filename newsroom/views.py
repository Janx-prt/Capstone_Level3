# newsroom/views.py
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from django.urls import reverse, reverse_lazy          # <-- add reverse
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.views.generic import (
    ListView, DetailView, TemplateView, CreateView, UpdateView, DeleteView
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
    template_name = "registration/login.html"
    authentication_form = _StyledAuthForm


class SignUpView(CreateView):
    form_class = SignUpForm
    template_name = "registration/signup.html"
    success_url = reverse_lazy("articles:landing")     # <-- namespaced


class LandingView(ListView):
    template_name = "landing.html"
    model = Article
    context_object_name = "articles"
    queryset = (
        Article.objects.filter(status=Article.Status.APPROVED)
        .select_related("author", "publisher")
        .order_by("-approved_at", "-created_at")
    )

    def get_context_data(self, **kwargs):
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
    template_name = "articles/detail.html"
    model = Article
    login_url = "login"


class ArticleCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Article
    form_class = ArticleForm
    permission_required = "newsroom.add_article"
    template_name = "articles/form.html"

    def form_valid(self, form):
        form.instance.author = self.request.user
        form.instance.status = Article.Status.PENDING
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("articles:article-detail", kwargs={"pk": self.object.pk})


class ArticleUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Article
    form_class = ArticleForm
    permission_required = "newsroom.change_article"
    template_name = "articles/form.html"

    def get_success_url(self):
        return reverse("articles:article-detail", kwargs={"pk": self.object.pk})


class ArticleDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Article
    permission_required = "newsroom.delete_article"
    template_name = "articles/confirm_delete.html"
    success_url = reverse_lazy("articles:landing")     # <-- namespaced


class ReviewQueueView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Article
    template_name = "articles/review.html"
    context_object_name = "articles"
    permission_required = "newsroom.can_approve"

    def get_queryset(self):
        return (
            Article.objects.filter(status=Article.Status.PENDING)
            .select_related("author", "publisher")
            .order_by("created_at")
        )


@login_required
@permission_required("newsroom.can_approve", raise_exception=True)
def approve_article(request, pk):
    a = get_object_or_404(Article, pk=pk)
    a.status = Article.Status.APPROVED
    if not a.approved_at:
        a.approved_at = timezone.now()
    a.save(update_fields=["status", "approved_at"])
    return redirect("articles:review")                 # <-- namespaced


class DashboardView(TemplateView):
    template_name = "tasks/dashboard.html"

    def get_context_data(self, **kwargs):
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
