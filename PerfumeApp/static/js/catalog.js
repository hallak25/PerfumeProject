window.addEventListener('unhandledrejection', event => {
    console.log('Promise rejection:', event.reason);
});

document.addEventListener('DOMContentLoaded', function() {
    const perfumerSelect = document.getElementById('perfumerSelect');
    const fragranceSelect = document.getElementById('fragranceSelect');
    const locationSelect = document.getElementById('locationSelect');


    function updateFilters() {


        const selectedPerfumer = perfumerSelect.value;
        const selectedFragrance = fragranceSelect.value;
        const selectedLocation = locationSelect.value;

        // Filter perfumes using client-side data
        let filteredPerfumes = allPerfumes;

        if (selectedPerfumer) {
            filteredPerfumes = filteredPerfumes.filter(p => p.perfumer === selectedPerfumer);
        }
        if (selectedFragrance) {
            filteredPerfumes = filteredPerfumes.filter(p => p.fragrance === selectedFragrance);
        }
        if (selectedLocation) {
            filteredPerfumes = filteredPerfumes.filter(p => p.location === selectedLocation);
        }

        // Get unique values for dropdowns
        const perfumers = [...new Set(filteredPerfumes.map(p => p.perfumer))].sort();
        const fragrances = [...new Set(filteredPerfumes.map(p => p.fragrance))].sort();
        const locations = [...new Set(filteredPerfumes.map(p => p.location))];

        // Update dropdowns and perfume list

        updateSelect(perfumerSelect, perfumers, selectedPerfumer);
        updateSelect(fragranceSelect, fragrances, selectedFragrance);
        updateSelect(locationSelect, locations, selectedLocation);
        updatePerfumeList(filteredPerfumes);

    }

    function updateFilters_old() {

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
            optionElement.value = decodeURIComponent(option.replace(/&#x27;/g, "'"));
            optionElement.textContent = decodeURIComponent(option.replace(/&#x27;/g, "'"));
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
    perfumeList.className = 'flex flex-col w-full'; // Make it a column layout
    perfumeList.innerHTML = '';

    perfumes.forEach((perfume, index) => {
        const listItem = document.createElement('div');

        // Alternate between white and light gray backgrounds
        const bgColor = index % 2 === 0 ? 'bg-white' : 'bg-gray-50';
        listItem.className = `flex w-full border-b p-4 ${bgColor}`;


        const imageContainer = document.createElement('div');
        imageContainer.className = 'relative w-96 flex-shrink-0 ml-24';

        const imageScroll = document.createElement('div');
        imageScroll.className = 'flex overflow-x-hidden';

        if (perfume.pictures && perfume.pictures.length > 0) {

            perfume.pictures.forEach(picture => {
                const img = document.createElement('img');
                img.src = picture;
                img.alt = 'Perfume';
                img.className = 'w-48 h-48 object-cover';
                img.ondblclick = () => window.open(img.src, '_blank');
                imageScroll.appendChild(img);
            });

            if (perfume.pictures.length > 1) {
                const leftArrow = document.createElement('button');
                leftArrow.className = 'absolute left-0 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 text-white p-2 rounded-r';
                leftArrow.textContent = '←';
                leftArrow.onclick = () => scrollImages(imageContainer, 'left');

                const rightArrow = document.createElement('button');
                rightArrow.className = 'absolute right-0 top-1/2 transform -translate-y-1/2 bg-black bg-opacity-50 text-white p-2 rounded-l';
                rightArrow.textContent = '→';
                rightArrow.onclick = () => scrollImages(imageContainer, 'right');

                imageContainer.appendChild(leftArrow);
                imageContainer.appendChild(rightArrow);
            }
        }

        imageContainer.appendChild(imageScroll);

        const perfumerColumn = document.createElement('div');
        perfumerColumn.className = 'w-96 ml-48  mr-24';
        perfumerColumn.innerHTML = `
            <h3 class="text-xl font-bold">${perfume.perfumer}</h3>
            <p class="text-l"> ${perfume.fragrance}</p>
            <p class="text-gray-600">${perfume.location === 'Dubai' ?
                `AED ${parseInt(perfume.listed_price_aed).toLocaleString()}` :
                `₽ ${parseInt(perfume.listed_price_ruble).toLocaleString()}`}</p>

        `;

        const specsColumn = document.createElement('div');
        specsColumn.className = 'w-96 space-y-2';
        specsColumn.innerHTML = `
            <p class="text-gray-600">Location: ${perfume.location}</p>
            <p class="text-gray-600">Bottle: ${perfume.bottle}</p>
            <p class="text-gray-600">${perfume.package}</p>

        `;

        listItem.appendChild(perfumerColumn);
        listItem.appendChild(specsColumn);
        listItem.appendChild(imageContainer);
        perfumeList.appendChild(listItem);
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




function scrollImages(container, direction) {
    const scrollAmount = 192; // width of image + padding
    if (direction === 'left') {
        container.querySelector('.flex').scrollLeft -= scrollAmount;
    } else {
        container.querySelector('.flex').scrollLeft += scrollAmount;
    }
}
