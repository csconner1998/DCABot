from django.shortcuts import render, redirect, get_object_or_404
from .forms import DCASettingsEditForm, DCASettingsCreateForm
from .models import DCASettings
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout, update_session_auth_hash, authenticate, login
import threading
import time
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.forms import UserChangeForm, PasswordChangeForm
import os
from django.conf import settings  # Import Django settings module
import pywaves as pw
import requests
import csv
import json
from .forms import LoginForm



# Dictionary to store user-specific threads and status flags
bot_threads = {}
assets_data = {}  # Dictionary to store ID to name mappings
csv_file = os.path.join(settings.STATICFILES_DIRS[0], 'assets.csv')  # Use the appropriate index for your directory
with open(csv_file, 'r') as assets_file:
    reader = csv.DictReader(assets_file)
    for row in reader:
        assets_data[row['asset_id']]= row['asset_name']
        
def write_to_log_file(bot_id, user_id, text):
    log_file_path = os.path.join(settings.BASE_DIR, 'log', f'log{user_id}.txt')
    with open(log_file_path, 'a') as log_file:
        log_file.write(f'{time.strftime("%d/%m/%Y - %H:%M:%S")} - Bot ID: {bot_id} - {text}\n')
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
        return
    
    
    # Get parameter field of the response
    valueOfParam = response.json()["parameters"]
    valueOfEstOut = response.json()["estimatedOut"]
    
    json_data = [{"type": "string", "value": valueOfParam}, {"type": "integer", "value": minimum}]
    return json_data, valueOfEstOut

def get_percision(asset_id="WAVES", network="TESTNET"):
    url = ""
    if asset_id == "WAVES":
        return 8
    if network == "MainNet":
        url = f"https://nodes.wavesnodes.com/assets/details/{asset_id}"
    elif network == "Stagenet":
        url = f"https://nodes-stagenet.wavesnodes.com/assets/details/{asset_id}"
    elif network == "TestNet":
        url = f"https://nodes-testnet.wavesnodes.com/assets/details/{asset_id}"
    else:
        return
    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)
    if response.status_code != 200:
        return 0
    if "decimals" not in response.json():
        return 0
    return response.json()["decimals"]

def fake_start_invokes(instance):
    global bot_threads
    # Perform the startInvokes task here
    # This function will be run in a separate thread
    i = 0
    thread_id = instance.id
    while bot_threads.get(thread_id, False):
        # Simulate the task logic
        print(f"Task running for User ID: {instance.user}... {i}")
        write_to_log_file(thread_id, instance.user.id, f"Task running")
        time.sleep(3)
        i+=1
        if i >= 5:
            # Stop the task after 5 iterations
            break

    # Task completed or stopped
    instance.running = False
    instance.save()
def start_invokes(instance):
    global bot_threads
    # Perform the startInvokes task here
    # This function will be run in a separate thread
    try:
        if instance.network == 'MainNet':
            pw.setNode(node='https://nodes.wavesplatform.com', chain='mainnet')
        elif instance.network == 'TestNet':
            pw.setNode(node='https://nodes-testnet.wavesnodes.com', chain='testnet')
        elif instance.network == 'stagenet':
            pw.setNode(node='https://nodes-stagenet.wavesnodes.com', chain='stagenet')
        height_snapshot = pw.height()
        bot_id = instance.id
        user_id = instance.user.id
        amount = instance.amount * 10 ** get_percision(instance.from_asset_id, instance.network)
        _, estimatedOut = generateParam(instance.from_asset_id, instance.to_asset_id, amount)
        initialEstOut = int(estimatedOut) - int(int(estimatedOut) * (instance.max_difference_in_percent / 100))
        write_to_log_file(bot_id ,user_id, f"initialEstOut: {initialEstOut} which is {instance.max_difference_in_percent}% less than {estimatedOut}")
        try:
            address = pw.Address(privateKey=instance.private_key)
        except:
            raise Exception("Invalid private key")
        balance = address.balance(assetId=instance.from_asset_id)
        max_invokes = instance.max_invokes
        while bot_threads.get(instance.id, False) and balance > 0 and int(balance) - int(amount) > 0 and max_invokes > 0:
            # Simulate the task logic
            # write to log file
            current_height = pw.height()
            write_to_log_file(bot_id, user_id, f'current_height: {current_height} - height_snapshot: {height_snapshot} = {current_height - height_snapshot}')
            if current_height - height_snapshot >= int(instance.blocks_per_invoke):
                params_data, _ = generateParam(instance.from_asset_id, instance.to_asset_id, amount, initialEstOut)
                if params_data is None:
                    raise Exception("Error while getting the params.")
                returnVal = address.invokeScript(instance.dapp_address, instance.function_name, params_data, [{"amount": int(amount), "assetId": instance.from_asset_id}])
                returnVal = json.dumps(returnVal, indent=4)
                input_Object = {"dapp_address": instance.dapp_address, "function_name": instance.function_name, "params_data": params_data, "amount": int(amount), "assetId": instance.from_asset_id}
                write_to_log_file(bot_id, user_id, f'input_Object: {input_Object}')
                write_to_log_file(bot_id, user_id, f'returnVal: {returnVal}')
                max_invokes -= 1
                height_snapshot = current_height
            balance = address.balance(assetId=instance.from_asset_id)
            time.sleep(30)
#error
    except Exception as e:
        write_to_log_file(bot_id, user_id, f'Error: {e}')

    # Task completed or stopped
    bot_threads.pop(instance.id, None)  # Remove the thread from the dictionary
    instance.running = False
    instance.save()
    
@login_required
def dca_settings_create(request):
    form = DCASettingsCreateForm(request.POST or None)
    if form.is_valid():
        form.instance.user = request.user  # Set the current user as the owner of the settings
        form.save()
        #Redirect to edit of the settings
        return redirect('edit_dca_settings', pk=form.instance.pk)
    return render(request, 'dca_settings_create.html', {'form': form})
@login_required
def dca_settings_edit(request, pk):
    setting = get_object_or_404(DCASettings, pk=pk)
    # Check if the current user is the owner of the settings unless the user is a superuser
    if setting.user != request.user and not request.user.is_superuser:
        return HttpResponse('Unauthorized', status=401)
    form = DCASettingsEditForm(request.POST or None, instance=setting)
    if form.is_valid():
        form.save()
        #Redirect to view all settings
        return redirect('view_all_dca_settings')
    return render(request, 'dca_settings_edit.html', {'form': form, 'setting': setting})
@login_required
def dca_settings_edit_empty(request):
    # go to view all settings
    return redirect('view_all_dca_settings')
@login_required
def view_all_dca_settings(request):
    # Fetch settings for the current user ordered by ID
    settingss = DCASettings.objects.filter(user=request.user).order_by('id')
    # Replace from_asset_id and to_asset_id with corresponding names from the CSV data
    for setting in settingss:
        from_asset_id = str(setting.from_asset_id)
        if from_asset_id in assets_data:
            setting.from_asset_id = assets_data[from_asset_id]

        to_asset_id = str(setting.to_asset_id)
        if to_asset_id in assets_data:
            setting.to_asset_id = assets_data[to_asset_id]

    return render(request, 'view_all_dca_settings.html', {'settings': settingss})

@login_required
def delete_dca_settings(request, pk):
    # Fetch the specific DCASettings object by its ID (pk)
    setting = get_object_or_404(DCASettings, pk=pk)

    if request.method == 'POST':
        # If the request method is POST (from the form submission), delete the object
        if setting.running:
            # Tell user to stop the task before deleting the settings
            messages.error(request, 'Please stop the task before deleting the settings.')
            return redirect('view_all_dca_settings',)
        setting.delete()
        return redirect('view_all_dca_settings')  # Redirect to view all settings after deletion

    # If the request method is not POST (e.g., accessed directly via URL), handle as needed
    # You can add additional logic here if required for non-POST requests

@login_required
def stop_dca_settings(request, pk):
    # Fetch the specific DCASettings object by its ID (pk)
    setting = get_object_or_404(DCASettings, pk=pk)

    if request.method == 'POST':
        # Check if user is the owner of the settings
        if setting.user != request.user and not request.user.is_superuser:
            return HttpResponse('Unauthorized', status=401)
        # If the request method is POST (from the form submission), stop the task
        setting.running = False
        setting.save()
        # Stop the thread with the corresponding settings ID
        bot_threads[pk]= False
        return redirect('view_all_dca_settings')
    
@login_required
def start_dca_settings(request, pk):
    # Fetch the specific DCASettings object by its ID (pk)
    setting = get_object_or_404(DCASettings, pk=pk)

    if request.method == 'POST':
        # Check if user is the owner of the settings
        if setting.user != request.user and not request.user.is_superuser:
            return HttpResponse('Unauthorized', status=401)
        if setting.running:
            # Tell user to stop the task before starting it again
            messages.error(request, 'Please stop the task before starting it again.')
            return redirect('view_all_dca_settings',)
        # If the request method is POST (from the form submission), start the task
        setting.running = True
        setting.save()
        # Create a new thread for the task
        bot_threads[pk] = True
        thread = threading.Thread(target=start_invokes, args=(setting,))
        thread.start()
        return redirect('view_all_dca_settings')

@login_required
def logout_view(request):
    logout(request)
    return render(request, 'logged_out.html')  # Render a logged-out page or redirect to another view

@login_required
def user_specific_text(request):
    user_text = ""
  
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

@login_required
def bot_specific_specific(request, pk):
    user_text = ""
    if request.user.is_authenticated:
        user_id = request.user.id
        log_file_path = os.path.join(settings.BASE_DIR, 'log', f'log{user_id}.txt')

        if os.path.exists(log_file_path):
            if request.method == 'POST':
                # Clear log file content of the specific bot by opening the file in write mode
                with open(log_file_path, 'r') as log_file:
                    lines = log_file.readlines()
                    
                with open(log_file_path, 'w') as log_file:
                    for line in lines:
                        if f'Bot ID: {pk}' not in line:
                            log_file.write(line)
            else:
                with open(log_file_path, 'r') as log_file:
                    user_text = ""
                    if pk:
                        for line in log_file.readlines():
                            if f'Bot ID: {pk}' in line:
                                user_text += line.replace('\n', '<br>')    
    context = {'user_text': user_text, 'pk': pk}
    return render(request, 'user_specific_text.html', context)


@login_required
def account_settings(request):
    if request.method == 'POST':
        user_form = UserChangeForm(request.POST, instance=request.user)
        password_form = PasswordChangeForm(user=request.user, data=request.POST)
        
        if 'user_form_submit' in request.POST and user_form.is_valid():
            user_form.save()
            messages.success(request, 'Your account details have been updated successfully!')
            return redirect('account_settings')

        if 'password_form_submit' in request.POST and password_form.is_valid():
            user = password_form.save()
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully!')
            return redirect('account_settings')
    else:
        user_form = UserChangeForm(instance=request.user)
        password_form = PasswordChangeForm(user=request.user)
    return render(request, 'account_settings.html', {'user_form': user_form, 'password_form': password_form})

def get_balance(request):
    if request.method == 'GET':
        try:
            address = request.GET.get('address')
            asset_name = request.GET.get('asset_id')
            network = request.GET.get('network')
            
            # turn asset_name to asset_id
            asset_id = None
            for key, value in assets_data.items():
                if value == asset_name:
                    asset_id = key
                    break
            if asset_id is None:
                return JsonResponse({'error': 'Invalid asset name'}, status=400)            
            if network == 'MainNet':
                pw.setNode(node='https://nodes.wavesplatform.com', chain='mainnet')
            elif network == 'TestNet':
                pw.setNode(node='https://nodes-testnet.wavesnodes.com', chain='testnet')
            elif network == 'stagenet':
                pw.setNode(node='https://nodes-stagenet.wavesnodes.com', chain='stagenet')
            else:
                return JsonResponse({'error': 'Invalid network'}, status=400)
            address = pw.Address(address)
            if asset_id == 'WAVES':
                balance = address.balance()
            else:
                balance = address.balance(assetId=asset_id)
            balance = int(balance) / 10 ** get_percision(asset_id, network)
            return JsonResponse({'balance': balance})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

def calculate_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body.decode('utf-8'))
            from_id = data.get('from_id')
            to_id = data.get('to_id')
            amount = data.get('amount')
            network = data.get('network')
            
            amount = int(amount) * 10 ** get_percision(from_id, network)

            # Construct the PuzzleSwap API URL with parameters
            api_url = f"https://waves.puzzle-aggr-api.com/aggregator/calc?token0={from_id}&token1={to_id}&amountIn={amount}"

            # Make a GET request to the PuzzleSwap API
            response = requests.get(api_url, headers={
                'Referer': 'https://puzzleswap.org/',
                'Origin': 'https://puzzleswap.org/'
            })
            estimated_out = response.json().get('estimatedOut', 0)
            estimated_out = int(estimated_out) / 10 ** get_percision(to_id, network)
            return JsonResponse({'estimatedOut': estimated_out})
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=405)

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('view_all_dca_settings')  # Replace 'success_page' with your success URL name
            else:
                error_message = "Incorrect username or password."
                return render(request, 'login.html', {'form': form, 'error_message': error_message})
    else:
        form = LoginForm(initial={'username': request.POST.get('username', '')})  # Set initial username if available
    
    return render(request, 'login.html', {'form': form})