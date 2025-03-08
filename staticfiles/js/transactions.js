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
         // Sort purchases by date
        purchases.sort((a, b) => new Date(a.purchase_date) - new Date(b.purchase_date));

        let html = createTablePurchases(purchases);
        purchasesList.innerHTML = html;

        const total = purchases.reduce((sum, p) => sum + parseFloat(p.purchase_price_euro), 0);
        purchasesSummary.innerHTML = `Total: ${purchases.length} purchases, ${formatNumber(total)} EUR`;
    }

    function updateSalesList(sales) {
        const salesList = document.getElementById('sales-list');
        const salesSummary = document.getElementById('sales-summary');

        // Sort sales by purchase date
        sales.sort((a, b) => new Date(a.purchase_date) - new Date(b.purchase_date));

        let html = createTableSales(sales);
        salesList.innerHTML = html;

        const total = sales.reduce((sum, s) => sum + parseFloat(s.sale_price_eur), 0);
        const total_purchase_price = sales.reduce((sum, s) => sum + parseFloat(s.purchase_price_euro), 0);
        const total_earnings = sales.reduce((sum, s) => sum + parseFloat(s.earnings_eur), 0);
        const avg_premium = total_earnings/total_purchase_price*100.
        salesSummary.innerHTML = `Total: ${sales.length} sales, ${formatNumber(total)} EUR, Earnings: ${formatNumber(total_earnings)} EUR.  Avg Premium: ${avg_premium.toFixed(0)} % `;
    }

    function updateInventoryList(purchases) {
        const inventoryList = document.getElementById('inventory-list');
        const inventorySummary = document.getElementById('inventory-summary');

        purchases.sort((a, b) => new Date(a.purchase_date) - new Date(b.purchase_date));

        // Filter unsold items
        const inventoryItems = purchases.filter(p => p.sale_date === null);

        let html = createTablePurchases(inventoryItems);
        inventoryList.innerHTML = html;

        const total = inventoryItems.reduce((sum, p) => sum + parseFloat(p.purchase_price_euro), 0);
        inventorySummary.innerHTML = `Total: ${inventoryItems.length} perfumes, ${formatNumber(total)} EUR`;
    }

    function createTablePurchases(transactions) {
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
                    </tr>
                </thead>
                <tbody>
                    ${transactions.map(t => `
                        <tr class="${t.sale_date === null ? 'unsold' : ''}">
                            <td>${t.purchase_date}</td>
                            <td>${t.perfumer}</td>
                            <td>${t.fragrance}</td>
                            <td>${t.origin}</td>
                            <td>${t.bottle}</td>
                            <td>${t.package}</td>
                            <td>${t.purchase_price_euro.toFixed(2)}</td>
                            <td>${t.location}</td>
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
                        <th>Sale Date</th>
                        <th>Perfumer</th>
                        <th>Fragrance</th>
                        <th>Sale Price (EUR)</th>
                        <th>Earnings (EUR)</th>
                        <th>Premium (%)</th>
                    </tr>
                </thead>
                <tbody>
                    ${transactions.map(t => `
                        <tr>
                            <td>${t.purchase_date}</td>
                            <td>${t.sale_date}</td>
                            <td>${t.perfumer}</td>
                            <td>${t.fragrance}</td>
                            <td>${t.sale_price_eur.toFixed(2)}</td>
                            <td>${t.earnings_eur.toFixed(2)}</td>
                            <td>${(t.premium*100.).toFixed(0)}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    function formatNumber(number) {
        return number.toFixed(0).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
    }

    // Initial load
    updateLists();
});
