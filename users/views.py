

from django.urls import reverse, reverse_lazy
from django.views.generic import TemplateView, DetailView, CreateView
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth import login

from .forms import SignupForm, CustomisedAuthenticationForm
from .models import CustomUser


class SignupView(CreateView):
    form_class = SignupForm
    template_name = 'commons/forms/compact-dynamic-form.html'

    def get(self, request, *args, **kwargs):
        self.object = None
        context = super().get_context_data(**kwargs)
        context['form'] = {
            'title': 'Sign Up',
            'fields': self.form_class(),
            'url': reverse('signup'),
            'type': 'create'
        }

        return self.render_to_response(context)
    
    def form_valid(self, form):
        # Check whether there are free ids ('username#[username_id]')
        user = form.save(commit=False)
        existing_username_ids = CustomUser.objects.filter(
            username=user.username
        ).values_list('username_id', flat=True)
        free_ids = [value for value in range(0, 100) if value not in existing_username_ids]
        if not free_ids:
            form.add_error('username', f'All IDs for username {form} are taken, please choose a different username.')
            return self.form_invalid(form)
        
        user.username_id = free_ids.pop(0)
        user.save()
        login(self.request, user)
        return JsonResponse({'status': 200, 'redirect': reverse('frontpage')})

    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data()})
    

class SigninView(LoginView):
    template_name = 'commons/forms/compact-dynamic-form.html'
    form_class = CustomisedAuthenticationForm

    def get(self, request, *args, **kwargs):
        self.object = None
        context = super().get_context_data(**kwargs)
        context['form'] = {
            'title': 'Sign In',
            'fields': self.form_class(),
            'url': reverse('signin'),
            'type': 'update'
        }

        return self.render_to_response(context)

    def form_valid(self, form):
        super().form_valid(form)
        return JsonResponse({'status': 200, 'redirect': reverse('frontpage')})

    def form_invalid(self, form):
        return JsonResponse({'status': 400, 'errors': form.errors.get_json_data(), 'message': 'Could not sign in'})
    
    
class SignoutView(LogoutView):
    success_url = reverse_lazy('core:frontpage')


class FullUserProfileView(DetailView):
    model = CustomUser
    template_name = 'users/full-user-profile.html'
    context_object_name = 'profile_user'