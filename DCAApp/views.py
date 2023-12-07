from django.shortcuts import render
from .forms import InputDataForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout


@login_required
def landing_page(request):
    if request.method == 'POST':
        form = InputDataForm(request.POST)
        if form.is_valid():
            form.save()
            # Redirect or perform other actions upon successful form submission
    else:
        form = InputDataForm()
    return render(request, 'landing_page.html', {'form': form})
def logout_view(request):
    logout(request)
    return render(request, 'logged_out.html')  # Render a logged-out page or redirect to another view
