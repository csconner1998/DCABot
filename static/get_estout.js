function getEstimatedOutput() {
    const from_id = document.getElementById('id_from_asset_id').value;
    const to_id = document.getElementById('id_to_asset_id').value;
    const amount = document.getElementById('id_amount').value;
    const network = document.getElementById('id_network').value;
    const formData = new FormData(document.getElementById('DCAForm'));
    

    // Check if any input value is null or empty
    if (!from_id || !to_id || !amount || !network) {
      document.getElementById('outputDiv').innerText = 'Estimated Output: 0';
      return;
    }
    fetch('/api/calculate', {
      method: 'POST',
      headers: {
        'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
        'X-Requested-With': 'XMLHttpRequest' // Include X-Requested-With header
    },
      body: JSON.stringify({ from_id, to_id, amount, network })
    })
      .then((response) => response.json())
      .then((data) => {
        const estimatedOut = data && data.estimatedOut ? data.estimatedOut : 0;
        document.getElementById('outputDiv').innerText = `Estimated Output: ${estimatedOut}`;
      })
      .catch((error) => {
        console.error('Error fetching estimated output from server:', error);
        document.getElementById('outputDiv').innerText = 'Estimated Output: 0';
      });
  }
  
  document.getElementById('id_from_asset_id').addEventListener('input', getEstimatedOutput);
  document.getElementById('id_to_asset_id').addEventListener('input', getEstimatedOutput);
  document.getElementById('id_amount').addEventListener('input', getEstimatedOutput);
  document.getElementById('id_network').addEventListener('input', getEstimatedOutput);
  getEstimatedOutput(); // Call getEstimatedOutput() once on page load
  