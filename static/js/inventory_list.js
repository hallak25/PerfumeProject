let currentFragranceId = null;
const sellModal = new bootstrap.Modal(document.getElementById('sellModal'));
let currentEditId = null;
const editModal = new bootstrap.Modal(document.getElementById('editModal'));

// --- SORTING LOGIC ---
let currentSortColumn = -1;
let isAscending = true;

/**
 * Sorts the fragrance table by a specific column index.
 * @param {number} n - The index of the column to sort by.
 */
function sortTable(n) {
    const table = document.getElementById("fragranceTable");
    let rows = Array.from(table.rows);

    // Toggle sort direction if clicking the same column
    if (currentSortColumn === n) {
        isAscending = !isAscending;
    } else {
        isAscending = true;
        currentSortColumn = n;
    }

    rows.sort((a, b) => {
        let valA, valB;

        if (n === 0) { // Perfumer Column
            valA = a.dataset.perfumer.toLowerCase();
            valB = b.dataset.perfumer.toLowerCase();
        } else if (n === 4) { // Purchase Date Column
            // Use the data-purchase_date attribute for accurate date sorting
            valA = new Date(a.dataset.purchase_date);
            valB = new Date(b.dataset.purchase_date);
        } else {
            return 0;
        }

        if (valA < valB) return isAscending ? -1 : 1;
        if (valA > valB) return isAscending ? 1 : -1;
        return 0;
    });

    // Re-append rows in the new order
    rows.forEach(row => table.appendChild(row));
}
// --- END SORTING LOGIC ---

 // Restore filter selections after page load
document.addEventListener('DOMContentLoaded', function() {
    // These values are pulled from the filter elements in your HTML
    const perfumerValue = document.getElementById('perfumerFilter').value;
    const fragranceValue = document.getElementById('fragranceFilter').value;
    const locationValue = document.getElementById('locationFilter').value;

    if (perfumerValue) document.getElementById('perfumerFilter').value = perfumerValue;
    if (fragranceValue) document.getElementById('fragranceFilter').value = fragranceValue;
    if (locationValue) document.getElementById('locationFilter').value = locationValue;

    // Apply filters
    updateDropdownOptions();
    filterTable();
});

function exportTableToCSV(filename) {
    const table = document.querySelector('.table-container table');
    const rows = table.querySelectorAll('tr');
    let csv = [];

    const headerRow = table.querySelector('thead tr');
    let header = [];
    headerRow.querySelectorAll('th').forEach((th, index) => {
        if (index < headerRow.querySelectorAll('th').length - 1) {
            header.push(`"${th.textContent.trim()}"`);
        }
    });
    csv.push(header.join(','));

    const bodyRows = table.querySelectorAll('#fragranceTable tr');
    bodyRows.forEach(row => {
        const isVisible = row.style.display !== 'none';
        if (isVisible) {
            let rowData = [];
            row.querySelectorAll('td').forEach((td, index) => {
                if (index < row.querySelectorAll('td').length - 1) {
                    let text = td.textContent.trim().replace(/"/g, '""');
                    rowData.push(`"${text}"`);
                }
            });
            csv.push(rowData.join(','));
        }
    });

    const csvFile = csv.join('\n');
    const blob = new Blob([csvFile], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement("a");

    if (link.download !== undefined) {
        const url = URL.createObjectURL(blob);
        link.setAttribute("href", url);
        link.setAttribute("download", filename);
        link.style.visibility = 'hidden';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    } else {
        window.open('data:text/csv;charset=utf-8,' + encodeURIComponent(csvFile));
    }
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function openEditDialog(id) {
    currentEditId = id;
    fetch(`/get-perfume/${id}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('editPerfumer').value = data.perfumer;
            document.getElementById('editFragrance').value = data.fragrance;
            document.getElementById('editPurchaseDate').value = data.purchase_date;
            document.getElementById('editPurchasePrice').value = data.price;
            document.getElementById('editOrigin').value = data.origin;
            document.getElementById('editLocation').value = data.location;
            document.getElementById('editBottle').value = data.bottle;
            document.getElementById('editPackage').value = data.package;
            document.getElementById('editListed_price_ruble').value = data.listed_price_ruble;
            document.getElementById('editListed_price_aed').value = data.listed_price_aed;
            loadPerfumeImages(id);
            editModal.show();
        })
        .catch(error => console.error('Error:', error));
}

function submitEdit() {
    const editData = {
        perfumer: document.getElementById('editPerfumer').value,
        fragrance: document.getElementById('editFragrance').value,
        purchase_date: document.getElementById('editPurchaseDate').value,
        purchase_price: document.getElementById('editPurchasePrice').value,
        origin: document.getElementById('editOrigin').value,
        package: document.getElementById('editPackage').value,
        bottle: document.getElementById('editBottle').value,
        location: document.getElementById('editLocation').value,
        listed_price_ruble:document.getElementById('editListed_price_ruble').value,
        listed_price_aed:document.getElementById('editListed_price_aed').value
    };

    fetch(`/update/${currentEditId}/`, {
        method: 'POST',
        body: JSON.stringify(editData),
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => console.error('Error:', error));
}

function filterTable() {
    const perfumer = document.getElementById('perfumerFilter').value;
    const fragrance = document.getElementById('fragranceFilter').value;
    const location = document.getElementById('locationFilter').value;

    const rows = document.querySelectorAll('#fragranceTable tr');
    let visibleCount = 0;
    let totalCostCount = 0.;

    rows.forEach(row => {
        const matchPerfumer = !perfumer || row.dataset.perfumer === perfumer;
        const matchFragrance = !fragrance || row.dataset.fragrance === fragrance;
        const matchLocation = !location || row.dataset.location === location;

        if (matchPerfumer && matchFragrance && matchLocation) {
            row.style.display = '';
            visibleCount++;
            totalCostCount += parseFloat(row.dataset.purchase_price_euro);
        } else {
            row.style.display = 'none';
        }
    });
    document.getElementById('totalItems').textContent = visibleCount;
    document.getElementById('totalCost').textContent = formatNumber(totalCostCount,2);
}

function openSellDialog(id) {
    currentFragranceId = id;
    fetch(`/get-perfume/${id}/`)
        .then(response => response.json())
        .then(data => {
            document.getElementById('salePrice').value = data.listed_price_ruble;
            document.getElementById('saleCurrency').addEventListener('change', function() {
                const salePriceField = document.getElementById('salePrice');
                salePriceField.value = (this.value === 'AED') ? data.listed_price_aed : data.listed_price_ruble;
            });
        })
        .catch(error => console.error('Error:', error));

    document.getElementById('saleDate').value = new Date().toISOString().split('T')[0];
    document.getElementById('saleCurrency').value = 'RUB';
    sellModal.show();
}

function submitSale() {
    const saleData = {
        sale_date: document.getElementById('saleDate').value,
        sale_price: document.getElementById('salePrice').value,
        sale_currency: document.getElementById('saleCurrency').value
    };

    fetch(`/sell/${currentFragranceId}/`, {
        method: 'POST',
        body: JSON.stringify(saleData),
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            const message = `Sale recorded successfully!\n
             ${data.body.perfumer} - ${data.body.fragrance} \n
            Date: ${formatDate(data.body.sale_date)} - Price: ${formatNumber(data.body.sale_price,0)} ${data.body.sale_currency} \n
            Exchange Rate: ${formatNumber(data.body.exch_rate,2)} - Price: ${formatNumber(data.body.sale_price_eur,2)} EUR \n
            Earning: ${formatNumber(data.body.earnings_eur,2)} EUR - Premium: ${formatNumber(data.body.premium*100.,0)} %`;
            alert(message);
            location.reload();
        } else {
            alert('Error: ' + data.message);
        }
    })
    .catch(error => alert('Error: ' + error));
}

function updateDropdownOptions() {
    const perfumerFilter = document.getElementById('perfumerFilter');
    const fragranceFilter = document.getElementById('fragranceFilter');
    const locationFilter = document.getElementById('locationFilter');

    const rows = document.querySelectorAll('#fragranceTable tr');

    const selectedPerfumer = perfumerFilter.value;
    const selectedFragrance = fragranceFilter.value;
    const selectedLocation = locationFilter.value;

    let availablePerfumers = new Set();
    let availableFragrances = new Set();
    let availableLocations = new Set();

    rows.forEach(row => {
        const rowPerfumer = row.dataset.perfumer;
        const rowFragrance = row.dataset.fragrance;
        const rowLocation = row.dataset.location;

        const matchPerfumer = !selectedPerfumer || rowPerfumer === selectedPerfumer;
        const matchFragrance = !selectedFragrance || rowFragrance === selectedFragrance;
        const matchLocation = !selectedLocation || rowLocation === selectedLocation;

        if ((!selectedFragrance && !selectedLocation) || (matchFragrance && matchLocation)) {
            availablePerfumers.add(rowPerfumer);
        }
        if ((!selectedPerfumer && !selectedLocation) || (matchPerfumer && matchLocation)) {
            availableFragrances.add(rowFragrance);
        }
        if ((!selectedPerfumer && !selectedFragrance) || (matchPerfumer && matchFragrance)) {
            availableLocations.add(rowLocation);
        }
    });

    updateOptions(perfumerFilter, availablePerfumers, selectedPerfumer);
    updateOptions(fragranceFilter, availableFragrances, selectedFragrance);
    updateOptions(locationFilter, availableLocations, selectedLocation);
}

function updateOptions(select, availableValues, currentValue) {
    const defaultOption = select.options[0];
    select.innerHTML = '';
    select.appendChild(defaultOption);

    Array.from(availableValues).sort().forEach(value => {
        const option = new Option(value, value);
        select.appendChild(option);
    });

    if (currentValue && availableValues.has(currentValue)) {
        select.value = currentValue;
    }
}

function loadPerfumeImages(perfumeId) {
    fetch(`/get-perfume-images/${perfumeId}/`)
        .then(response => response.json())
        .then(data => {
            const gallery = document.getElementById('imageGallery');
            gallery.innerHTML = data.images.map(image => `
                <div class="col-md-3 mb-3">
                    <div class="position-relative">
                        <img src="${image.url}" class="img-fluid rounded" alt="Perfume image">
                        <button class="btn btn-danger btn-sm position-absolute top-0 end-0"
                                onclick="deleteImage(${image.id})">×</button>
                    </div>
                </div>
            `).join('');
        });
}

function uploadImages(perfumeId) {
    const files = document.getElementById('imageUpload').files;
    const formData = new FormData();
    for (let file of files) {
        formData.append('images', file);
    }

    fetch(`/upload-images/${perfumeId}/`, {
        method: 'POST',
        body: formData,
        headers: { 'X-CSRFToken': getCookie('csrftoken') }
    })
    .then(response => response.json())
    .then(() => {
        loadPerfumeImages(perfumeId);
        document.getElementById('imageUpload').value = '';
    });
}

function deleteImage(imageId) {
    if (confirm('Delete this image?')) {
        fetch(`/delete-image/${imageId}/`, {
            method: 'POST',
            headers: { 'X-CSRFToken': getCookie('csrftoken') }
        })
        .then(response => response.json())
        .then(() => loadPerfumeImages(currentEditId));
    }
}

function formatNumber(input_value, FractionDigits) {
    return parseFloat(input_value).toLocaleString('en-US', {
        minimumFractionDigits: FractionDigits,
        maximumFractionDigits: FractionDigits
    });
}

function formatDate(date) {
    return new Date(date).toLocaleDateString('en-GB');
}

// Event Listeners
document.getElementById('perfumerFilter').addEventListener('change', () => {
    updateDropdownOptions();
    filterTable();
});

document.getElementById('fragranceFilter').addEventListener('change', () => {
    updateDropdownOptions();
    filterTable();
});

document.getElementById('locationFilter').addEventListener('change', () => {
    updateDropdownOptions();
    filterTable();
});

document.getElementById('imageUpload').addEventListener('change', () => {
    uploadImages(currentEditId);
});

// Initial load
updateDropdownOptions();
filterTable();
