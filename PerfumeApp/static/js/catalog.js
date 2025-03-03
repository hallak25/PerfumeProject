document.addEventListener('DOMContentLoaded', function() {
    const perfumerSelect = document.getElementById('perfumerSelect');
    const fragranceSelect = document.getElementById('fragranceSelect');
    const locationSelect = document.getElementById('locationSelect');
    if (!isStaff) {
        locationSelect.value = userLocation;
        locationSelect.disabled = true;
    }

    function updateFilters() {

        if (!isStaff) {

            locationSelect.value = userLocation;
            locationSelect.disabled = true;
        }

        const selectedPerfumer = perfumerSelect.value;
        const selectedFragrance = fragranceSelect.value;
        const selectedLocation = locationSelect.value;

        fetch(`/get-filtered-options/?perfumer=${selectedPerfumer}&fragrance=${selectedFragrance}&location=${selectedLocation}`)
            .then(response => {

            return response.json();
            })
            .then(data => {

                updateSelect(perfumerSelect, data.perfumers, selectedPerfumer);
                updateSelect(fragranceSelect, data.fragrances, selectedFragrance);
                updateSelect(locationSelect, data.locations, selectedLocation);
                updatePerfumeList(data.perfumes);
            });
    }

    function updateSelect(select, options, selectedValue) {
        const currentValue = selectedValue || select.value;
        select.innerHTML = '<option value="">Select ' + select.id.replace('Select', '') + '</option>';
        options.forEach(option => {
            const optionElement = document.createElement('option');
            optionElement.value = option;
            optionElement.textContent = option;
            if (option === currentValue) {
                optionElement.selected = true;
            }
            select.appendChild(optionElement);
        });
    }

    perfumerSelect.addEventListener('change', updateFilters);
    fragranceSelect.addEventListener('change', updateFilters);
    locationSelect.addEventListener('change', updateFilters);

    // Initial load
    updateFilters();
});


function updatePerfumeList(perfumes) {
    const perfumeList = document.getElementById('perfumeList');
    perfumeList.innerHTML = '';

    perfumes.forEach(perfume => {
        const card = document.createElement('div');
        card.className = 'bg-white rounded-lg shadow p-4';
        card.innerHTML = `
            <h3 class="text-xl font-bold mb-2">${perfume.perfumer}</h3>
            <p class="text-gray-600">
                Location: <span onclick="makeFieldEditable(this, ${perfume.id}, 'location')">${perfume.location}</span>
            </p>
            <p class="text-gray-600">
                Bottle: <span onclick="makeFieldEditable(this, ${perfume.id}, 'bottle')">${perfume.bottle}</span>
            </p>
            <p class="text-gray-600">
                Package: <span onclick="makeFieldEditable(this, ${perfume.id}, 'package')">${perfume.package}</span>
            </p>
            <p class="text-gray-600">
                 Price:  ₽ <span onclick="makeFieldEditable(this, ${ perfume.id }, 'listed_price_ruble')">${ perfume.listed_price_ruble }</span>
             </p>
             <button onclick="viewPictures(${perfume.id})" class="mt-4 bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700">
                    View Pictures
                </button>
        `;
        perfumeList.appendChild(card);
    });
}

function viewPictures(perfumeId) {
    fetch(`/get-pictures/${perfumeId}/`)
        .then(response => response.json())
        .then(data => {
            const modal = document.createElement('div');
            modal.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center';
            modal.innerHTML = `
                <div class="bg-white p-6 rounded-lg max-w-4xl w-full mx-4">
                    <h2 class="text-2xl font-bold mb-4">Pictures</h2>
                    <div class="grid grid-cols-2 md:grid-cols-3 gap-4">
                        ${data.pictures.map(pic => `
                            <div class="aspect-square overflow-hidden rounded">
                                <img src="${pic.url}"
                                     alt="Perfume"
                                     class="w-full h-full object-cover hover:scale-105 transition-transform cursor-pointer"
                                     style="max-height: 300px;"
                                     onclick="window.open(this.src, '_blank')">
                            </div>
                        `).join('')}
                    </div>
                    ${data.is_admin ? `
                        <form id="uploadForm" class="mt-4">
                            <input type="file" multiple accept="image/*" class="mb-2">
                            <button type="submit" class="bg-green-600 text-white px-4 py-2 rounded mr-2">
                                Upload New Pictures
                            </button>
                        </form>
                    ` : ''}
                    <button onclick="this.parentElement.parentElement.remove()"
                            class="mt-4 bg-gray-600 text-white px-4 py-2 rounded">
                        Close
                    </button>
                </div>
        `   ;
            document.body.appendChild(modal);

            if (data.is_admin) {
                const form = modal.querySelector('#uploadForm');
                form.addEventListener('submit', (e) => {
                    e.preventDefault();
                    const formData = new FormData();
                    const files = form.querySelector('input[type="file"]').files;
                    for (let file of files) {
                        formData.append('images', file);
                    }
                    formData.append('perfume_id', perfumeId);

                    fetch('/upload-pictures/', {
                        method: 'POST',
                        body: formData,
                        headers: {
                            'X-CSRFToken': getCookie('csrftoken')
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        // Refresh the pictures display
                        viewPictures(perfumeId);
                    });
                });
            }
        });
}

// Helper function to get CSRF token
function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return parts.pop().split(';').shift();
}

function zoomImage(img) {
    const zoomModal = document.createElement('div');
    zoomModal.className = 'fixed inset-0 bg-black bg-opacity-90 flex items-center justify-center z-50';
    zoomModal.innerHTML = `
        <img src="${img.src}"
             class="max-h-screen max-w-screen p-4 cursor-zoom-out"
             onclick="this.parentElement.remove()">
    `;
    document.body.appendChild(zoomModal);
}
function makeFieldEditable(element, perfumeId, fieldName) {
    if (isStaff) {
        element.onclick = function() {
            const currentValue = this.textContent;

            if (fieldName === 'location') {
                const select = document.createElement('select');
                select.className = 'border rounded p-1';

                const locations = ['Paris', 'London', 'Moscow', 'Dubai'];
                locations.forEach(loc => {
                    const option = document.createElement('option');
                    option.value = loc;
                    option.text = loc;
                    if (loc === currentValue) {
                        option.selected = true;
                    }
                    select.appendChild(option);
                });

                select.onchange = function() {
                    updateField(perfumeId, fieldName, this.value, element);
                };

                this.parentNode.replaceChild(select, this);
                select.focus();
            } else {
                const input = document.createElement('input');
                input.value = currentValue;
                input.className = 'border rounded p-1';

                input.onblur = function() {
                    updateField(perfumeId, fieldName, this.value, element);
                };

                this.parentNode.replaceChild(input, this);
                input.focus();
            }
        };
    }
}

function updateField(perfumeId, field, value, element) {
    fetch('/update-perfume/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            perfume_id: perfumeId,
            field: field,
            value: value
        })
    })
    .then(response => response.json())
    .then(data => {
        element.textContent = value;
        element.parentNode.replaceChild(element, element.parentNode.firstChild);
    });
}
