import random

from django.urls import reverse, reverse_lazy
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render

from .forms import SignupForm
from .models import CustomUser


class SignupView(TemplateView):
    template_name = 'users/signup.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['SignupForm'] = SignupForm()
        
        return context

    def post(self, request, *args, **kwargs):
        user_form = SignupForm(data=request.POST)
        username = request.POST.get('username')

        existing_username_ids = CustomUser.objects.filter(username=username).values_list('username_id', flat=True)
        free_ids = [value for value in range(0, 100) if value not in existing_username_ids]
        if not free_ids:
            user_form.add_error('username', f'All IDs for username {username} are taken, please choose a different username.')

        if user_form.is_valid():
            user = user_form.save(commit=False)
            user.username_id = random.choice(free_ids)
            user.save()
            return render(request, '', {'SignupForm': user_form})
            
        return render(request, self.template_name, {'SignupForm': user_form})
        

class SigninView(LoginView):
    template_name = 'users/signin.html'
    success_url = reverse_lazy('frontpage')
    
    def form_invalid(self, form):
        form.add_error('password', 'Invalid credentials, please check your email or password.')
        return render(self.request, self.template_name, self.get_context_data(form=form))

    def get_success_url(self):
        return self.request.GET.get('next') or reverse_lazy('frontpage')

class SignoutView(LogoutView):
    success_url = reverse_lazy('core:frontpage')
        

