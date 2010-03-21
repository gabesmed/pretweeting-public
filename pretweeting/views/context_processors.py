from django.conf import settings

def notice(request):

	context = {}

	if 'notice' in request.session:
		context['notice'] = request.session['notice']
		del request.session['notice']
  
	return context