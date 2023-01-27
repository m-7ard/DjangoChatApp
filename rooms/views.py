from django.views.generic import TemplateView

from core.models import News


class DashboardView(TemplateView):
	template_name = 'rooms/dashboard.html'

	def get_context_data(self, **kwargs):
		context = super().get_context_data(**kwargs)
		context['site_news'] = News.objects.all()
		return context