from django.contrib import messages
from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.forms import inlineformset_factory

from accounts.models import Customer
from accounts.forms import CustomerForm
from rides.models import Destination
from rides.forms import DestinationForm, CreateHomeForm, UpdateHomeForm

