function fetchBalance(address, asset_id, network) {
    $.ajax({
        url: '/get_balance/', // Replace with the URL for your Django view
        type: 'GET',
        data: {
            address: address,
            asset_id: asset_id,
            network: network
        },
        success: function(response) {
            alert('Balance is: ' + response.balance);
        },
        error: function(xhr, status, error) {
            alert('Error fetching balance.');
            console.error(xhr.responseText);
        }
    });
}
