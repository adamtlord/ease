from django.shortcuts import render
from django.contrib.auth.decorators import login_required


@login_required
def homepage(request, template='common/homepage.html'):
    return render(request, template, {})
