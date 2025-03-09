document.addEventListener('DOMContentLoaded', async () => {
    // Load initial data
    const response = await fetch('/get_unique_values/');
    const data = await response.json();

    // Populate dropdowns
    populateSelect('perfumer', data.perfumers);
    populateSelect('origin', data.origins);
    populateSelect('currency', data.currencies);
    populateSelect('location', data.locations);
    populateDatalist('bottleList', data.bottles);
    populateDatalist('packageList', data.packages);

    // Set default date to today
    document.getElementById('date').valueAsDate = new Date();

    // Add event listeners

    // Add this event listener after the other existing ones
    document.getElementById('origin').addEventListener('change', (e) => {
        if (e.target.value === 'Ebay UK') {
            document.getElementById('currency').value = 'GBP';
            document.getElementById('location').value = 'London';
        }
        if (e.target.value === 'Ebay FR') {
            document.getElementById('currency').value = 'EUR';
            document.getElementById('location').value = 'Paris';
        }
    });

    document.getElementById('perfumer').addEventListener('change', async (e) => {
        const response = await fetch(`/get_fragrances/?perfumer=${e.target.value}`);
        const data = await response.json();
        populateSelect('fragrance', data.fragrances);
    });

    document.getElementById('purchaseBtn').addEventListener('click', async () => {
         // Disable button immediately
        const purchaseBtn = document.getElementById('purchaseBtn');
        purchaseBtn.disabled = true;
        purchaseBtn.classList.add('opacity-50', 'cursor-not-allowed');
        const transaction = {
            perfumer: document.getElementById('perfumer').value,
            fragrance: document.getElementById('fragrance').value,
            origin: document.getElementById('origin').value,
            bottle: document.getElementById('bottle').value,
            package: document.getElementById('package').value,
            location: document.getElementById('location').value,
            price: document.getElementById('price').value,
            currency: document.getElementById('currency').value,
            date: document.getElementById('date').value
        };

        const response = await fetch('/add_transaction/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(transaction)
        });

        const result = await response.json();
        const messageDiv = document.getElementById('message');
        messageDiv.classList.remove('hidden');

        if (result.status === 'success') {
            messageDiv.className = 'mt-4 p-4 rounded-lg bg-green-100 text-green-700';
        } else {
            messageDiv.className = 'mt-4 p-4 rounded-lg bg-red-100 text-red-700';
        }
        messageDiv.textContent = result.message;
    });
});

function populateSelect(id, options) {
    const select = document.getElementById(id);
    select.innerHTML = '<option value="">Select...</option>';
    options.forEach(option => {
        const el = document.createElement('option');
        el.textContent = option;
        el.value = option;
        select.appendChild(el);
    });
}

function populateDatalist(id, options) {
    const datalist = document.getElementById(id);
    options.forEach(option => {
        const el = document.createElement('option');
        el.value = option;
        datalist.appendChild(el);
    });
}
