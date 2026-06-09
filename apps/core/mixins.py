"""
Core mixins for views.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages


class HRProLoginRequiredMixin(LoginRequiredMixin):
    """
    Login required mixin with custom redirect.
    """
    login_url = '/accounts/login/'
    redirect_field_name = 'next'


class SuccessMessageMixin:
    """
    Mixin to add success message after form submission.
    """
    success_message = ""

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.success_message:
            messages.success(self.request, self.success_message)
        return response


class HTMXMixin:
    """
    Mixin for HTMX partial responses.

    Usage:
        class MyView(HTMXMixin, TemplateView):
            template_name = 'full_page.html'
            htmx_template_name = '_partial.html'
    """
    htmx_template_name = None

    def get_template_names(self):
        if self.request.headers.get('HX-Request') and self.htmx_template_name:
            return [self.htmx_template_name]
        return super().get_template_names()


class AuditMixin:
    """
    Mixin to track who created/updated records.

    Requires model to have:
        - created_by (ForeignKey to User)
        - updated_by (ForeignKey to User)
    """

    def form_valid(self, form):
        if not form.instance.pk:
            # Creating new record
            form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
