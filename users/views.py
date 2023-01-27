from django.urls import reverse, reverse_lazy
from django.views.generic.edit import CreateView
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from .forms import UserAttributes_SignupForm, ProfileAttributes_SignupForm


class SignupView(TemplateView):
    model = User
    template_name = 'users/signup.html'
    form_class = UserAttributes_SignupForm # technically doesn't do anything here

    def get_context_data(self, **kwargs):
        context = super(SignupView, self).get_context_data(**kwargs)
        context['ProfileAttributes_SignupForm'] = ProfileAttributes_SignupForm()
        context['UserAttributes_SignupForm'] = UserAttributes_SignupForm()
        
        return context

    def post(self, request, *args, **kwargs):
        profile_form = ProfileAttributes_SignupForm(data=request.POST)
        user_form = UserAttributes_SignupForm(data=request.POST)
        if profile_form.is_valid() and user_form.is_valid():
            print(profile_form.cleaned_data, '*' * 100)
            user = user_form.save()
            # creates a blank profile with the signals at models.py
            user.profile.birthday = profile_form.cleaned_data.get('birthday')
            user.save()

        return HttpResponseRedirect(reverse_lazy('frontpage'))

    """
    def form_valid(self, form):
        print('entering form_valid')
        context = self.get_context_data()
        profile_form = context['ProfileAttributes_SignupForm']

        if form.is_valid() and profile_form.is_valid():
            profile = profile_form.save(commit=False)
            user = form.save()
            profile.user = user
            profile.save()
        
        return super().form_valid(form)
    """

class SigninView(LoginView):
    template_name = 'users/signin.html'
    success_url = reverse_lazy('frontpage')
    
    def form_invalid(self, form):
        """If the form is invalid, render the invalid form."""
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        return self.request.GET.get('next') or reverse_lazy('frontpage')

class SignoutView(LogoutView):
    success_url = reverse_lazy('core:frontpage')
        

