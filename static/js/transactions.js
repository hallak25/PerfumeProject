document.addEventListener('DOMContentLoaded', function() {
    const perfumerSelect = document.getElementById('perfumer');
    const fragranceSelect = document.getElementById('fragrance');

    perfumerSelect.addEventListener('change', function() {
        updateFragrances();
        updateLists();
    });

    fragranceSelect.addEventListener('change', function() {
        updateLists();
    });

    function updateFragrances() {
        const perfumer = perfumerSelect.value;
        fetch(`/get-fragrances/?perfumer=${perfumer}`)
            .then(response => response.json())
            .then(fragrances => {
                fragranceSelect.innerHTML = '<option value="">Select Fragrance</option>';
                fragrances.forEach(fragrance => {
                    const option = document.createElement('option');
                    option.value = fragrance;
                    option.textContent = fragrance;
                    fragranceSelect.appendChild(option);
                });
            });
    }

    function updateLists() {
        const perfumer = perfumerSelect.value;
        const fragrance = fragranceSelect.value;

        fetch(`/transactions/?perfumer=${perfumer}&fragrance=${fragrance}`)
            .then(response => response.json())
            .then(data => {
                updatePurchasesList(data.purchases);
                updateSalesList(data.sales);
                updateInventoryList(data.purchases);
            });
    }

    function updatePurchasesList(purchases) {
        const purchasesList = document.getElementById('purchases-list');
        const purchasesSummary = document.getElementById('purchases-summary');
        purchases.sort((a, b) => new Date(a.purchase_date) - new Date(b.purchase_date));

        purchasesList.innerHTML = createTablePurchases(purchases);

        const total = purchases.reduce((sum, p) => sum + parseFloat(p.purchase_price_euro), 0);
        purchasesSummary.innerHTML = `Total: ${purchases.length} purchases, ${formatNumber(total)} EUR`;
    }

    function updateSalesList(sales) {
        const salesList = document.getElementById('sales-list');
        const salesSummary = document.getElementById('sales-summary');

        sales.sort((a, b) => new Date(a.purchase_date) - new Date(b.purchase_date));

        salesList.innerHTML = createTableSales(sales);

        const total = sales.reduce((sum, s) => sum + parseFloat(s.sale_price_eur), 0);
        const total_purchase_price = sales.reduce((sum, s) => sum + parseFloat(s.purchase_price_euro), 0);
        const total_earnings = sales.reduce((sum, s) => sum + parseFloat(s.earnings_eur), 0);
        const avg_premium = total_earnings / total_purchase_price * 100;
        salesSummary.innerHTML = `Total: ${sales.length} sales, ${formatNumber(total)} EUR, Earnings: ${formatNumber(total_earnings)} EUR.  Avg Premium: ${avg_premium.toFixed(0)} % `;
    }

    function updateInventoryList(purchases) {
        const inventoryList = document.getElementById('inventory-list');
        const inventorySummary = document.getElementById('inventory-summary');

        purchases.sort((a, b) => new Date(a.purchase_date) - new Date(b.purchase_date));

        const inventoryItems = purchases.filter(p => p.sale_date === null);

        inventoryList.innerHTML = createTablePurchases(inventoryItems, false);

        const total = inventoryItems.reduce((sum, p) => sum + parseFloat(p.purchase_price_euro), 0);
        inventorySummary.innerHTML = `Total: ${inventoryItems.length} perfumes, ${formatNumber(total)} EUR`;
    }

    function createTablePurchases(transactions, showDelete = true) {
        if (transactions.length === 0) return '<p>No transactions found</p>';

        return `
            <table>
                <thead>
                    <tr>
                        <th>Purchase Date</th>
                        <th>Perfumer</th>
                        <th>Fragrance</th>
                        <th>Origin</th>
                        <th>Bottle</th>
                        <th>Description</th>
                        <th>Purchase Price (EUR)</th>
                        <th>Location</th>
                        ${showDelete ? '<th></th>' : ''}
                    </tr>
                </thead>
                <tbody>
                    ${transactions.map(t => `
                        <tr class="${t.sale_date === null ? 'unsold' : ''}">
                            <td>${formatDate(t.purchase_date)}</td>
                            <td>${t.perfumer}</td>
                            <td>${t.fragrance}</td>
                            <td>${t.origin}</td>
                            <td>${t.bottle}</td>
                            <td>${t.package}</td>
                            <td>${t.purchase_price_euro.toFixed(2)}</td>
                            <td>${t.location}</td>
                            ${showDelete ? `<td><button class="btn-delete" onclick="deleteTransaction(${t.id}, '${escapeHtml(t.perfumer)} – ${escapeHtml(t.fragrance)}')">Delete</button></td>` : ''}
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    function createTableSales(transactions) {
        if (transactions.length === 0) return '<p>No transactions found</p>';

        return `
            <table>
                <thead>
                    <tr>
                        <th>Purchase Date</th>
                        <th style="white-space: nowrap">Sale Date</th>
                        <th>Perfumer</th>
                        <th>Fragrance</th>
                        <th>Sale Price</th>
                        <th>Exchange Rate</th>
                        <th>Sale Price (EUR)</th>
                        <th>Earnings (EUR)</th>
                        <th>Premium (%)</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    ${transactions.map(t => `
                        <tr>
                            <td>${formatDate(t.purchase_date)}</td>
                            <td style="white-space: nowrap">${formatDate(t.sale_date)}</td>
                            <td>${t.perfumer}</td>
                            <td>${t.fragrance}</td>
                            <td>${formatNumber(t.sale_price)}</td>
                            <td>${t.sale_exch_rate.toFixed(1)}</td>
                            <td>${t.sale_price_eur.toFixed(2)}</td>
                            <td>${t.earnings_eur.toFixed(2)}</td>
                            <td>${(t.premium * 100).toFixed(0)}</td>
                            <td><button class="btn-reset-sale" onclick="resetSale(${t.id}, '${escapeHtml(t.perfumer)} – ${escapeHtml(t.fragrance)}')">Delete</button></td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    function formatNumber(number) {
        return number.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }

    function formatDate(dateString) {
        const date = new Date(dateString);
        const day = date.getDate().toString().padStart(2, '0');
        const month = date.toLocaleString('en-GB', { month: 'short' });
        const year = date.getFullYear().toString().slice(-2);
        return `${day}-${month}-${year}`;
    }

    function escapeHtml(str) {
        return String(str).replace(/'/g, "\\'");
    }

    // Initial load
    updateLists();
});

function getCsrfToken() {
    return document.querySelector('meta[name="csrf-token"]').getAttribute('content');
}

function deleteTransaction(id, label) {
    if (!confirm(`Permanently delete "${label}"?\n\nThis cannot be undone.`)) return;
    fetch(`/delete-transaction/${id}/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrfToken() }
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') location.reload();
        else alert('Delete failed.');
    })
    .catch(() => alert('Delete failed.'));
}

function resetSale(id, label) {
    if (!confirm(`Reset sale fields for "${label}"?\n\nThe purchase record will be kept but all sale data will be cleared.`)) return;
    fetch(`/reset-sale/${id}/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': getCsrfToken() }
    })
    .then(r => r.json())
    .then(data => {
        if (data.status === 'success') location.reload();
        else alert('Reset failed.');
    })
    .catch(() => alert('Reset failed.'));
}
