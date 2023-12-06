import os
import json
import tkinter as tk
import time
from tkinter import ttk, messagebox
import pywaves as pw
import requests
import tksvg

# Global variable for params
results = []
fileName = ""
height_check_running = False


def load_defaults():
    defaults_file = "defaults.json"

    if os.path.exists(defaults_file):
        with open(defaults_file, "r") as file:
            defaults_data = json.load(file)
        return (
            defaults_data.get("address", "apple"),
            defaults_data.get("asset", ""),
            defaults_data.get("blocks_per", ""),
            defaults_data.get("dapp_address", ""),
            defaults_data.get("function_name", ""),
            defaults_data.get("default_to_asset", ""),
            defaults_data.get("private_key", ""),
            defaults_data.get("amount", ""),
            defaults_data.get("network", ""),
            defaults_data.get("max_invokes", ""),
            defaults_data.get("max_difference", "")
        )
    else:
        return "", "", "", "", "", "", "", "", "", "", ""

def save_defaults(address, asset, blocks_per, dapp_address, function_name, default_to_asset, private_key, amount, network, max_invokes, max_difference):
    defaults = {
        "address": address,
        "asset": asset,
        "blocks_per": blocks_per,
        "dapp_address": dapp_address,
        "function_name": function_name,
        "default_to_asset": default_to_asset,
        "private_key": private_key,
        "amount": amount,
        "network": network,
        "max_invokes": max_invokes,
        "max_difference": max_difference
    }
    with open("defaults.json", "w") as file:
        json.dump(defaults, file)

def validate_get_balance(address, private_key, asset):
    if not address.strip() and not private_key.strip():
        return False
    return True

def get_percision(asset_id="WAVES", network="TESTNET"):
    url = ""
    if asset_id == "WAVES":
        return 8
    if network == "MAINNET":
        url = f"https://nodes.wavesnodes.com/assets/details/{asset_id}"
    elif network == "STAGENET":
        url = f"https://nodes-stagenet.wavesnodes.com/assets/details/{asset_id}"
    elif network == "TESTNET":
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

def check_estimated_out(asset, to_asset, amount):
    if not asset.strip() or not to_asset.strip() or not amount.strip():
        messagebox.showerror("Validation Error", "Invalid input. Please check your entries.")
        return
    try:
        amount = int(amount) * (10 ** get_percision(asset, network_combobox.get()))
        params_data, estOut = generateParam(asset, to_asset, amount)
        if params_data is None:
            raise Exception("Error while getting the params.")
        estOut = estOut / (10 ** get_percision(to_asset, network_combobox.get()))
        messagebox.showinfo("Info", f"Estimated out: {estOut}")
    except Exception as e:
        messagebox.showerror("Error", e)
def save_results(results):
    if len(results) == 0:
        return
    if messagebox.askyesno("Save Results", "Do you want to save the results?"):
        timeNow = time.localtime()
        # Format the time
        timeNow = time.strftime("%Y-%m-%d %H-%M", timeNow)
        fileName = f"results-{timeNow}.json"
        # save the results to a file in the same directory
        with open(fileName, "w") as file:
            json.dump(results, file)
        messagebox.showinfo("Info", f"Results saved to {fileName}")
        
def validate_height_check(privateKey, asset, to_asset, blocks_per, dapp_address, function_name, amount, max_invokes, max_difference):
    if not privateKey.strip() or not blocks_per.strip() or not dapp_address.strip() or not function_name.strip() or not amount.strip() or not max_invokes.strip() or not asset.strip() or not to_asset.strip() or not max_difference.strip():
        return False
    if not blocks_per.isnumeric() or int(blocks_per) <= 0 or not amount.isnumeric() or int(amount) <= 0 or not max_invokes.isnumeric() or int(max_invokes) <= 0 or not max_difference.isnumeric() or float(max_difference) < 0 or float(max_difference) > 100:
        return False

    return True

    
def close_result_window(result_window):
    result_window.destroy()
    
    # Make the main window active again with deful
def heightCheck(address : pw.address, height_snapshot, asset, to_asset, blocks_per_value, dappAddress, functionName, amount, max_invokes, initialEstOut):
    global height_check_running, results
    current_height = pw.height()
    balance = address.balance(assetId=asset)
    if balance > 0 and int(balance) - int(amount) > 0 and height_check_running and max_invokes != 0:
        current_height = pw.height()
        print(f"current_height: {current_height} - height_snapshot: {height_snapshot} = {current_height - height_snapshot}")
        if current_height - height_snapshot >= int(blocks_per_value):
            height_snapshot = current_height
            try:
                params_data, _ = generateParam(asset, to_asset, amount, initialEstOut)
                if params_data is None:
                    raise Exception("Error while getting the params.")
                # Invoke the dapp
                returnVal = address.invokeScript(dappAddress, functionName, params_data, [{"amount": int(amount), "assetId": asset}])
                # format the return value
                returnVal = json.dumps(returnVal, indent=4)
                timeNow = time.localtime()
                # Format the time
                timeNow = time.strftime("%Y-%m-%d %H:%M:%S", timeNow)
                print("Invoke Result", f"{timeNow} Invoke result: \r\n{returnVal}")
                input_object = {"dappAddress": dappAddress, "functionName": functionName, "params": params_data, "amount": amount, "assetId": asset}
                results.append({"input": input_object,"time": timeNow, "result": returnVal})
                max_invokes -= 1
                change_current_invokes_number(1)
            except Exception as e:
                messagebox.showerror("Error", e)
                # Reset the flag when the height check is finished
                height_check_running = False

                # Change the button text back to "Start Height Check"
                height_check_button.config(text="Start")
                
                # Unlock all
                unlock_everything()                
                return
        # Call the function again after 30 seconds
        window.after(30000, heightCheck, address, height_snapshot, asset, to_asset, blocks_per_value, dappAddress, functionName, amount, max_invokes, initialEstOut)
            
    else:
        # Reset the flag when the height check is finished
        height_check_running = False
        user_stopped = False
        # If the balance is 0, stop the height check
        if balance == -1:
            messagebox.showerror("Error", "Invalid address or asset ID. Please check your entries.")
        elif balance == 0:
            messagebox.showinfo("Error", "The balance is 0.")
        elif max_invokes == 0:
            messagebox.showinfo("Info", "The max number of invokes has been reached.")
        else:
            # User stopped the height check
            user_stopped = True
        
        # Save the results
        if not user_stopped:
            save_results(results)
        
        # Change the button text back to "Start Height Check"
        height_check_button.config(text="Start")

        
        # Unlock all
        unlock_everything() 
        
def lock_everything():
    address_entry.config(state="disabled")
    asset_entry.config(state="disabled")
    asset_to_entry.config(state="disabled")
    blocks_per_entry.config(state="disabled")
    dapp_address_entry.config(state="disabled")
    function_name_entry.config(state="disabled")
    amount_entry.config(state="disabled")
    private_key_entry.config(state="disabled")
    max_invokes_entry.config(state="disabled")
    max_difference_entry.config(state="disabled")
    
    # Also the buttons
    test_button.config(state="disabled")
    save_defaults_button.config(state="disabled")
    one_time_height_check_button.config(state="disabled")
    
    # And the combobox
    network_combobox.config(state="disabled")
    
    change_current_invokes_number()

def change_current_invokes_number(number=0):
    if number == 0:
        current_invokes_number.config(text=number)
    else:
        # Add the number to the current number of invokes
        current_invokes_number.config(text=int(current_invokes_number.cget("text")) + number)
    
def unlock_everything():

    address_entry.config(state="normal")
    asset_entry.config(state="normal")
    asset_to_entry.config(state="normal")
    blocks_per_entry.config(state="normal")
    dapp_address_entry.config(state="normal")
    function_name_entry.config(state="normal")
    amount_entry.config(state="normal")
    private_key_entry.config(state="normal")
    max_invokes_entry.config(state="normal")
    max_difference_entry.config(state="normal")
    
    # Also the buttons
    test_button.config(state="normal")
    save_defaults_button.config(state="normal")
    one_time_height_check_button.config(state="normal")
    
    # And the combobox
    network_combobox.config(state="readonly")
    
    change_current_invokes_number()

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
    
def one_time_height_check(privateKey, asset, to_asset, blocks_per, dapp_address, function_name, amount):
    if not validate_height_check(privateKey, asset, to_asset, blocks_per, dapp_address, function_name, amount, "1", "1"):
        messagebox.showerror("Validation Error", "Invalid input. Please check your entries.")
        return
    # Set the network
    network_value = network_combobox.get()
    if network_value == "MAINNET":
        pw.setNode('https://nodes.wavesnodes.com/', chain='mainnet')
    elif network_value == "STAGENET":
        pw.setNode('https://nodes-stagenet.wavesnodes.com/', chain='stagenet')
    elif network_value == "TESTNET":
        pw.setNode('https://nodes-testnet.wavesnodes.com/', chain='testnet')
        
    # Lock all
    lock_everything()
    
    # Invoke once
    try:
        address = pw.Address(privateKey=privateKey)
        amount = int(amount) * (10 ** get_percision(asset, network_value))
        params_data, estOut = generateParam(asset, to_asset, amount)
        if params_data is None:
            raise Exception("Error while getting the params.")
        returnVal = address.invokeScript(dapp_address, function_name, params_data, [{"amount": int(amount), "assetId": asset}])
        # format the return value
        returnVal = json.dumps(returnVal, indent=4)
        timeNow = time.localtime()
        # Format the time
        timeNow = time.strftime("%Y-%m-%d %H:%M", timeNow)
        messagebox.showinfo("Invoke Result", f"{timeNow} Invoke result: \r\n{returnVal}")
    except Exception as e:
        messagebox.showerror("Error", e)
    # Unlock all
    unlock_everything()
    
def toggle_height_check():
    global height_check_running, results

    if not height_check_running:
        # Get the values from the text boxes and entry
        network_value = network_combobox.get()
        privateKey = private_key_entry.get()
        asset_value = asset_entry.get()
        to_asset_value = asset_to_entry.get()
        blocks_per_value = blocks_per_entry.get()
        dappAddress = dapp_address_entry.get()
        functionName = function_name_entry.get()
        amount = amount_entry.get()
        max_invokes = max_invokes_entry.get()
        max_difference = max_difference_entry.get()
        
        
        # Validate the input
        if not validate_height_check(privateKey, asset_value, to_asset_value, blocks_per_value, dappAddress, functionName, amount, max_invokes, max_difference):
            messagebox.showerror("Validation Error", "Invalid input. Please check your entries.")
            return
        # Lock all
        amount = int(amount) * (10 ** get_percision(asset_value, network_value))
        print(f"amount after percision: {amount}")
        if amount == 0:
            messagebox.showerror("Validation Error", "Invalid to asset ID. Please check your entries.")
            return
        lock_everything()
        
        max_invokes = int(max_invokes)
        results = []
            
        # Start the height check thread
        height_check_running = True
        if network_value == "MAINNET":
            pw.setNode('https://nodes.wavesnodes.com/', chain='mainnet')
        elif network_value == "STAGENET":
            pw.setNode('https://nodes-stagenet.wavesnodes.com/', chain='stagenet')
        elif network_value == "TESTNET":
            pw.setNode('https://nodes-testnet.wavesnodes.com/', chain='testnet')
        try:
            address = pw.Address(privateKey=privateKey)
        except Exception as e:
            messagebox.showerror("Error", e)
            # Reset the flag when the height check is finished
            height_check_running = False

            # Change the button text back to "Start Height Check"
            height_check_button.config(text="Start")
            
            # Unlock all
            unlock_everything()
            return
        height_snapshop = pw.height()
        _, estOut = generateParam(asset_value, to_asset_value, amount)
        initialEstOut = int(estOut) - int(int(estOut) * int(max_difference) / 100)
        print(f"initialEstOut: {initialEstOut} which is {max_difference}% less than {estOut}")
        window.after(0, heightCheck, address, height_snapshop, asset_value, to_asset_value, blocks_per_value, dappAddress, functionName, amount, max_invokes, initialEstOut)
        
        # Change the button text to "Stop Height Check"
        height_check_button.config(text="Stop")
        
    else:
        # Stop the height check
        height_check_running = False
        
        # Change the button text back to "Start Height Check"
        height_check_button.config(text="Start")
        
        save_results(results)       
        
        # Unlock all
        unlock_everything()


def testFunc(network, address, private_key, asset=None):
    # Validate the input
    if not validate_get_balance(address, private_key, asset):
        messagebox.showerror("Validation Error", "Invalid input. Please check your entries. (Address or private key is required and asset ID is WAVES when empty)")
        return
    # Set the network
    if network == "MAINNET":
        pw.setNode('https://nodes.wavesnodes.com/', chain='mainnet')
    elif network == "STAGENET":
        pw.setNode('https://nodes-stagenet.wavesnodes.com/', chain='stagenet')
    elif network == "TESTNET":
        pw.setNode('https://nodes-testnet.wavesnodes.com/', chain='testnet')

    try:
        if private_key.strip():
            myAddress = pw.Address(privateKey=private_key)
        else:
            myAddress = pw.Address(address)
        balance = myAddress.balance(assetId=asset)
        balance = balance / (10 ** get_percision(asset, network))
        result_message = f"Balance: {balance}"
        
        # Create a new window to display the result
        result_window = tk.Toplevel(window)
        result_window.title("Test Function Result")
        
        # Set the size of the result window
        result_window.geometry("400x200")
        
        # Display the result message in the new window
        result_label = tk.Label(result_window, text=result_message, padx=10, pady=10)
        result_label.pack()

        # Create an OK button to close the result window
        ok_button = tk.Button(result_window, text="OK", command=lambda: close_result_window(result_window))
        ok_button.pack(pady=10)

        # Make the result window modal (disable user interaction with other windows)
        result_window.grab_set()

        # Wait until the result window is closed
        result_window.wait_window()
        
    except Exception as e:
        messagebox.showerror("Error", e)


if __name__ == '__main__':
    # Create the main window
    window = tk.Tk()
    window.title("DCA bot")

    # Set the size of the main window
    window.geometry("850x300")

    # Set resizable to False
    window.resizable(False, False)


    # Load default values from "defaults.json"
    (
        default_address,
        default_asset,
        default_blocks_per,
        default_dapp_address,
        default_function_name,
        default_to_asset,
        default_private_key,
        default_amount,
        default_network,
        default_max_invokes,
        default_max_difference,
    ) = load_defaults()

    # Create entry widgets for address, asset, blocks per, dapp address, function name, and params file
    address_label = tk.Label(window, text="Address (used for 'Get Balance'):")
    address_label.grid(row=0, column=0, sticky="e", padx=10, pady=5)
    address_entry = tk.Entry(window)
    address_entry.grid(row=0, column=1, padx=10, pady=5)
    address_entry.insert(0, default_address)  # Set the default value

    # Create private key label
    private_key_label = tk.Label(window, text="Private Key:")
    private_key_label.grid(row=0, column=2, sticky="e", padx=10, pady=5)
    private_key_entry = tk.Entry(window)
    private_key_entry.grid(row=0, column=3, padx=10, pady=5)
    private_key_entry.insert(0, default_private_key)  # Set the default value

    asset_label = tk.Label(window, text="From asset ID:")
    asset_label.grid(row=1, column=0, sticky="e", padx=10, pady=5)
    asset_entry = tk.Entry(window)
    asset_entry.grid(row=1, column=1, pady=5)
    asset_entry.insert(0, default_asset)  # Set the default value
    # asset_svg = get_svg_by_asset_id(default_asset)
    # asset_svg_label = tk.Label(window, image=asset_svg)
    # asset_svg_label.grid(row=1, column=4, padx=10, pady=5)
    # # On value change of asset_entry, update the svg
    # asset_entry.bind("<KeyRelease>", lambda e: asset_svg_label.config(image=get_svg_by_asset_id(asset_entry.get())))

    asset_to_label = tk.Label(window, text="To asset ID:")
    asset_to_label.grid(row=1, column=2, sticky="e", padx=10, pady=5)
    asset_to_entry = tk.Entry(window)
    asset_to_entry.grid(row=1, column=3, pady=5)
    asset_to_entry.insert(0, default_to_asset)  # Set the default value

    blocks_per_label = tk.Label(window, text="Blocks Per:")
    blocks_per_label.grid(row=2, column=0, sticky="e", padx=10, pady=5)
    blocks_per_entry = tk.Entry(window)
    blocks_per_entry.grid(row=2, column=1, padx=10, pady=5)
    blocks_per_entry.insert(0, default_blocks_per)  # Set the default value

    # Label for max number of invokes
    max_invokes_label = tk.Label(window, text="Max number of Invokes: ")
    max_invokes_label.grid(row=2, column=2, sticky="e", padx=10, pady=5)
    max_invokes_entry = tk.Entry(window)
    max_invokes_entry.grid(row=2, column=3, padx=10, pady=5)
    max_invokes_entry.insert(0, default_max_invokes)  # Set the default value

    dapp_address_label = tk.Label(window, text="Dapp Address:")
    dapp_address_label.grid(row=3, column=0, sticky="e", padx=10, pady=5)
    dapp_address_entry = tk.Entry(window)
    dapp_address_entry.grid(row=3, column=1, padx=10, pady=5)
    dapp_address_entry.insert(0, default_dapp_address)  # Set the default value

    max_difference_label = tk.Label(window, text="Max Difference (as a %):")
    max_difference_label.grid(row=3, column=2, sticky="e", padx=10, pady=5)
    max_difference_entry = tk.Entry(window)
    max_difference_entry.grid(row=3, column=3, padx=10, pady=5)
    max_difference_entry.insert(0, default_max_difference)  # Set the default value

    function_name_label = tk.Label(window, text="Function Name:")
    function_name_label.grid(row=4, column=0, sticky="e", padx=10, pady=5)
    function_name_entry = tk.Entry(window)
    function_name_entry.grid(row=4, column=1, padx=10, pady=5)
    function_name_entry.insert(0, default_function_name)  # Set the default value

    # Current Number of Invokes labels
    current_invokes_label = tk.Label(window, text="Current Number of Invokes: ")
    current_invokes_label.grid(row=4, column=2, sticky="e", padx=10, pady=5)
    current_invokes_number = tk.Label(window, text="0")
    current_invokes_number.grid(row=4, column=3, sticky="w", padx=10, pady=5)

    # Amount label
    amount_label = tk.Label(window, text="Amount:")
    amount_label.grid(row=5, column=0, sticky="e", padx=10, pady=5)
    amount_entry = tk.Entry(window)
    amount_entry.grid(row=5, column=1, padx=10, pady=5)
    amount_entry.insert(0, default_amount)  # Set the default value

    # Create a combobox for the network
    network_label = tk.Label(window, text="Network:")
    network_label.grid(row=7, column=0, sticky="e", padx=10, pady=5)
    network_combobox = ttk.Combobox(window, values=["TESTNET", "MAINNET", "STAGENET"], state="readonly")
    network_combobox.grid(row=7, column=1, padx=10, pady=5)
    if default_network in ["TESTNET", "MAINNET", "STAGENET"]:
        network_combobox.set(default_network)  # Set the default value
    else:    
        network_combobox.set("TESTNET")

    # Create a button to trigger the testFunc
    test_button = tk.Button(window, text="Get Balance", command=lambda: testFunc(
        network_combobox.get(),
        address_entry.get(),
        private_key_entry.get(),
        asset_entry.get()
    ))
    test_button.grid(row=8, column=0, pady=10)

    # Create a button to save the default values
    save_defaults_button = tk.Button(window, text="Save Defaults", command=lambda: save_defaults(
        address_entry.get(),
        asset_entry.get(),
        blocks_per_entry.get(),
        dapp_address_entry.get(),
        function_name_entry.get(),
        asset_to_entry.get(),
        private_key_entry.get(),
        amount_entry.get(),
        network_combobox.get(),
        max_invokes_entry.get(),
        max_difference_entry.get()
    ))
    save_defaults_button.grid(row=8, column=1, pady=10)

    # Create a button to trigger the one time height check
    one_time_height_check_button = tk.Button(window, text="Invoke once", command=lambda: one_time_height_check(
        private_key_entry.get(),
        asset_entry.get(),
        asset_to_entry.get(),
        blocks_per_entry.get(),
        dapp_address_entry.get(),
        function_name_entry.get(),
        amount_entry.get()
    ))
    one_time_height_check_button.grid(row=8, column=2, pady=10)

    # Create a button to check the current estimated out
    check_estimated_out_button = tk.Button(window, text="Check estimated out", command=lambda: check_estimated_out(
        asset_entry.get(),
        asset_to_entry.get(),
        amount_entry.get()
    ))
    check_estimated_out_button.grid(row=8, column=4, pady=10)
    # Create a button to start/stop the height check
    height_check_running = False
    height_check_button = tk.Button(window, text="Start", command=toggle_height_check)
    height_check_button.grid(row=8, column=3, pady=10)

    # Run the Tkinter event loop
    window.mainloop()