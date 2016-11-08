from django.shortcuts import render
from django.contrib.auth.decorators import login_required


def homepage(request, template='marketing/homepage.html'):
    return render(request, template, {})
