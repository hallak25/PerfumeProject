        function formatDate(dateString) {
            const date = new Date(dateString);
            const day = date.getDate().toString().padStart(2, '0');
            const month = date.toLocaleString('en-GB', { month: 'short' });
            const year = date.getFullYear().toString().slice(-2);
            return `${day}-${month}-${year}`;
        }



        function formatNumber(number,decimals_nb) {
            return number.toFixed(decimals_nb).replace(/\B(?=(\d{3})+(?!\d))/g, ",");
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
                            <th>Purchase Price</th>
                            <th>Purchase Currency</th>
                            <th>Purchase Price (EUR)</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${transactions.map(t => `
                            <tr>
                                <td>${formatDate(t.purchase_date)}</td>
                                <td>${t.perfumer}</td>
                                <td>${t.fragrance}</td>
                                <td>${t.origin}</td>
                                <td>${t.bottle}</td>
                                <td>${t.package}</td>
                                <td>${formatNumber(t.price,2)}</td>
                                <td>${t.purchase_currency}</td>
                                <td>${formatNumber(t.purchase_price_euro,2)}</td>
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
                            <th>Sale Date</th>
                            <th>Perfumer</th>
                            <th>Fragrance</th>
                            <th>Purchase Date</th>
                            <th>Origin</th>
                            <th>Description</th>
                            <th>Sale Price</th>
                            <th>Exchange Rate</th>
                            <th>Sale Price (EUR)</th>
                            <th>Earnings (EUR)</th>
                            <th>Premium</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${transactions.map(t => `
                            <tr>
                                <td>${formatDate(t.sale_date)}</td>
                                <td>${t.perfumer}</td>
                                <td>${t.fragrance}</td>
                                <td>${formatDate(t.purchase_date)}</td>
                                <td>${t.origin}</td>
                                <td>${t.package}</td>
                                <td>${formatNumber(t.sale_price,0)}</td>
                                <td>${t.sale_exch_rate.toFixed(1)}</td>
                                <td>${formatNumber(t.sale_price_eur,2)}</td>
                                <td>${formatNumber(t.earnings_eur,2)}</td>
                                <td>${formatNumber(t.premium*100.,0)}%</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `;
        }

        function updateLists() {
            const yearMonth = document.getElementById('yearMonth').value;
            if (!yearMonth) return;

            fetch(`/monthly/transactions/?year_month=${yearMonth}`)
                .then(response => response.json())
                .then(data => {
                    updatePurchasesList(data.purchases);
                    updateSalesList(data.sales);
                });
        }

        function updatePurchasesList(purchases) {
            const purchasesList = document.getElementById('purchases-list');
            const purchasesSummary = document.getElementById('purchases-summary');

            purchases.sort((a, b) => new Date(a.purchase_date) - new Date(b.purchase_date));

            let html = createTablePurchases(purchases);
            purchasesList.innerHTML = html;

            const total = purchases.reduce((sum, p) => sum + parseFloat(p.purchase_price_euro), 0);
            purchasesSummary.innerHTML = `${purchases.length} purchases. ${formatNumber(total,0)} EUR`;
        }

        function updateSalesList(sales) {
            const salesList = document.getElementById('sales-list');
            const salesSummary = document.getElementById('sales-summary');

            sales.sort((a, b) => new Date(a.sale_date) - new Date(b.sale_date));

            let html = createTableSales(sales);
            salesList.innerHTML = html;

            const totals = sales.reduce((acc, s) => {
                return {
                    purchases: acc.purchases + parseFloat(s.purchase_price_euro),
                    sales: acc.sales + parseFloat(s.sale_price),
                    sales_eur: acc.sales_eur + parseFloat(s.sale_price_eur),
                    earnings: acc.earnings + parseFloat(s.earnings_eur),
                    premium: acc.premium + parseFloat(s.premium)
                };
            }, {purchases: 0, sales: 0, sales_eur: 0, earnings: 0, premium: 0 });
            const avgPremium = sales.length > 0 ? totals.earnings / totals.purchases : 0;

            salesSummary.innerHTML = `
                ${sales.length} sales.
                ${formatNumber(totals.sales,0)} RUB.
                ${formatNumber(totals.sales_eur,0)} EUR.
                Earnings: ${formatNumber(totals.earnings,0)} EUR.
                Average Premium: ${formatNumber(avgPremium*100.,0)}%
            `;
        }


        document.addEventListener('DOMContentLoaded', function()
         { const yearMonthSelect = document.getElementById('yearMonth');
          const options = Array.from(yearMonthSelect.options);
          if (options.length > 1) {
                // Get the latest year_month (excluding the default "Select Month" option)
                const latestYearMonth = options
                    .slice(1)
                    .map(opt => opt.value)
                    .sort()
                    .reverse()[0];

                yearMonthSelect.value = latestYearMonth;

            }

          updateLists()
          const selectedDate = new Date(document.getElementById('yearMonth').value + '-01');
          const formattedMonth = selectedDate.toLocaleString('en-GB', { month: 'long', year: '2-digit' });
          document.querySelector('.list:nth-child(2) h2').textContent = `${formattedMonth} - Purchases`;
          document.querySelector('.list:nth-child(3) h2').textContent = `${formattedMonth} - Sales`;
           });

          document.getElementById('yearMonth').addEventListener('change', function() {
                const selectedDate = new Date(this.value + '-01');
                const formattedMonth = selectedDate.toLocaleString('en-GB', { month: 'long', year: '2-digit' });

                document.querySelector('.list:nth-child(2) h2').textContent = `${formattedMonth} - Purchases`;
                document.querySelector('.list:nth-child(3) h2').textContent = `${formattedMonth} - Sales`;
                updateLists()
            });

          document.querySelectorAll('#yearMonth option').forEach(option => {
                if (option.value) {
                    const date = new Date(option.value + '-01');
                    option.textContent = date.toLocaleString('en-GB', { month: 'long', year: '2-digit' });
                }
            });
