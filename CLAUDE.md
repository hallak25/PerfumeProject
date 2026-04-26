# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

All commands assume the virtualenv at `C:\Django\PErfumeEnv312\` is active.

```bash
# Run development server
python manage.py runserver

# Run on specific IP/port (used for LAN access)
python manage.py runserver 0.0.0.0:8000

# Apply migrations
python manage.py migrate

# Create new migrations after model changes
python manage.py makemigrations

# Collect static files (required before deploying or after adding new static assets)
python manage.py collectstatic

# Open Django shell
python manage.py shell
```

There are no tests and no linting configuration.

## Architecture

### Dual-audience design
The app serves two distinct user types:
- **Customers** (`/catalog/`, `/catalog_ru/`): Browse available inventory, filtered by location. Views use `@login_required`. Russian-language variants exist for `/ru/` and `/catalog_ru/`.
- **Staff** (`/inventory_list/`, `/all-transactions/`, `/financial_report/`, etc.): Full inventory and financial management. Views use `@staff_member_required`.

### Data model
`Fragrance` is a lookup catalog (perfumer + fragrance name pairs). It is the source of truth for valid perfumer/fragrance combinations and populates dropdowns throughout the app.

`PerfumeTransaction` is the core model (~46 fields). A single record represents one physical bottle. Its lifecycle:
1. **Purchase**: `price`, `purchase_currency`, `purchase_date`, `purchase_price_euro`, `origin`, `location`, etc. are set.
2. **Listed for sale**: `listed_price_ruble` and `listed_price_aed` are set (calculated from `purchase_price_euro` × exchange rate × `TARGET_PREMIUM`).
3. **Sold**: sale fields (`sale_date`, `sale_price`, `sale_currency`, `sale_exch_rate`, `sale_price_eur`, `earnings_eur`, `premium`) are populated. A null `sale_date` means the bottle is still in inventory.

`PerfumePicture` has a ForeignKey to `PerfumeTransaction` and stores uploaded bottle images.

### Utility modules
- **`GlobalParameters.py`**: App-wide constants — `EXCHANGE_RATES` (static fallback rates), `TARGET_PREMIUM` (0.65), and location names. Edit this when default rates or markup targets change.
- **`Tools.py`**: `CurrencyExchange` class fetches live rates from open.er-api.com with EUR as base. Used in `get_perfume_data` and `sell_perfume` to compute target prices and sale amounts.
- **`Transactions.py`**: Pure data functions operating on pandas DataFrames. `all_time_report()` aggregates `PerfumeTransaction` rows into monthly purchase/sale summaries with EUR normalization. Used by the financial report views.

### AJAX pattern
Many views are JSON endpoints consumed by dedicated JS files in `static/js/`. The pairing is:
- `inventory_list.js` ↔ `/inventory_list/` — uses `/get-perfume/<id>/`, `/update/<id>/`, `/sell/<id>/`, `/get-perfume-images/<id>/`, etc.
- `transactions.js` ↔ `/all-transactions/` — uses `/transactions/`, `/delete-transaction/<id>/`, `/reset-sale/<id>/`
- `add_transaction.js` ↔ `/start_add_transaction/` — uses `/add_transaction/`, `/get_unique_values/`, `/get_fragrances_2/`
- `monthly_financial.js` ↔ `/monthly/` — uses `/monthly/transactions/`

All mutating AJAX endpoints use `@require_POST` + `@staff_member_required` and expect `X-CSRFToken` in the request header. The CSRF token is embedded as `<meta name="csrf-token">` in standalone templates (those not extending `base_index.html`).

### Template structure
Most staff pages extend `base_index.html`. The `/all-transactions/` page (`transactions.html`) and `/inventory_list/` page are standalone HTML files that manage their own `<head>` and embed the CSRF token via `<meta name="csrf-token" content="{{ csrf_token }}">`.

### Database
SQLite (`db.sqlite3`) is used in development. A PostgreSQL config (AWS RDS) exists commented out in `settings.py` as `DATABASES_OLD`. Model fields use explicit `db_column` names with capitalised SQL column names (e.g. `db_column='Perfumer'`) — this is intentional for compatibility with the legacy schema and must be preserved on any new fields added to existing models.
