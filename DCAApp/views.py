from django.shortcuts import render, redirect
from .forms import DCASettingsForm
from .models import DCASettings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
import threading
import time
from django.contrib import messages
from django.http import HttpResponse
import os
from django.conf import settings  # Import Django settings module
import pywaves as pw

# Dictionary to store user-specific threads and status flags
user_threads = {}
def generateParam(from_asset, to_asset, amount, minimum=0):
    url = f"https://waves.puzzle-aggr-api.com/aggregator/calc?token0={from_asset}&token1={to_asset}&amountIn={amount}"

    payload = {}
    headers = {
    'Referer': 'https://puzzleswap.org/',
    'Origin': 'https://puzzleswap.org/'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    
    # Error handling
    if response.status_code != 200:
        return
    
    # Make sure response has "params" field
    if "parameters" not in response.json():
        print(response.text)
        return
    
    
    # Get parameter field of the response
    valueOfParam = response.json()["parameters"]
    valueOfEstOut = response.json()["estimatedOut"]
    
    json_data = [{"type": "string", "value": valueOfParam}, {"type": "integer", "value": minimum}]
    return json_data, valueOfEstOut

def start_invokes(instance, user_id):
    global user_threads
    # Perform the startInvokes task here
    # This function will be run in a separate thread
    try:
        if instance.network == 'MainNet':
            pw.setNode(node='https://nodes.wavesplatform.com', chain='mainnet')
        elif instance.network == 'TestNet':
            pw.setNode(node='https://nodes-testnet.wavesnodes.com', chain='testnet')
        elif instance.network == 'stagenet':
            pw.setNode(node='https://nodes-stagenet.wavesnodes.com', chain='stagenet')
        current_height = pw.height()
        while user_threads.get(user_id, False):
            # Simulate the task logic
            # write to log file
            log_file_path = os.path.join(settings.BASE_DIR, 'log', f'log{user_id}.txt')
            with open(log_file_path, 'a') as log_file:
                log_file.write(f'{time.strftime("%H:%M:%S")} - Performing startInvokes task...\n')
            i+=1
            if i >= 5:
                # Stop the task after 5 iterations
                break
            time.sleep(1)
    #error
    except Exception as e:
        with open(log_file_path, 'a') as log_file:
            log_file.write(f'{time.strftime("%H:%M:%S")} - Error: {e}\n')

    # Task completed or stopped
    user_threads[user_id] = False  # Signal the thread to stop
    instance.running = False
    instance.save()
    
@login_required
def landing_page(request):
    global stop_thread
    current_user_settings = DCASettings.objects.filter(user=request.user).first()
    running_status = current_user_settings.running if current_user_settings else False

    if request.method == 'POST':
        if current_user_settings:
            # Update existing entry
            form = DCASettingsForm(request.POST, instance=current_user_settings, user=request.user)
        else:
            form = DCASettingsForm(request.POST, user=request.user)
        if form.is_valid():
            # Save the form without committing to the database
            instance = form.save(commit=False)
            instance.user_id = request.user.id  # Assign the currently logged-in user
            user_id = instance.user_id
            if running_status:
                if user_threads.get(user_id, False):
                    user_threads[user_id] = False  # Signal the thread to stop
                instance.running = False
                instance.save()
                return redirect('/stopped')  # Redirect to a success page or desired URL
            else:
                # Start a new thread for startInvokes task if not already running
                if not user_threads.get(user_id, False):
                    user_threads[user_id] = True  # Set flag for the user
                    thread = threading.Thread(target=start_invokes, args=(instance, user_id))
                    thread.daemon = True  # Daemonize the thread
                    thread.start()
                instance.running = True
                instance.save()  # Save the instance with 'running' set to True
                return redirect('/success')  # Redirect to a success page or desired URL
    else:
        form = DCASettingsForm(user=request.user)
        
    context = {
        'form': form,
        'running': running_status,
    }

    return render(request, 'landing_page.html', context)
def logout_view(request):
    logout(request)
    return render(request, 'logged_out.html')  # Render a logged-out page or redirect to another view
def success_page_view(request):
    return render(request, 'success_page.html')
def stopped_page_view(request):
    return render(request, 'stopped_page.html')

def user_specific_text(request):
    user_text = ""
    if request.method == 'POST':
        if request.user.is_authenticated:
            user_id = request.user.id
            log_file_path = os.path.join(settings.BASE_DIR, 'log', f'log{user_id}.txt')

            if os.path.exists(log_file_path):
                # Clear log file content by opening the file in write mode
                with open(log_file_path, 'w') as log_file:
                    log_file.write('')
    
    if request.user.is_authenticated:
        user_id = request.user.id
        log_file_path = os.path.join(settings.BASE_DIR, 'log', f'log{user_id}.txt')

        if os.path.exists(log_file_path):
            if request.method == 'POST':
                with open(log_file_path, 'w') as log_file:
                    log_file.write('')
            else:
                with open(log_file_path, 'r') as log_file:
                    user_text = log_file.read().replace('\n', '<br>')  # Replace newline with <br>
    
    context = {'user_text': user_text}
    return render(request, 'user_specific_text.html', context)