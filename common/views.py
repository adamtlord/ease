from django.shortcuts import render


def homepage(request, template='common/homepage.html'):
    return render(request, template, {})
