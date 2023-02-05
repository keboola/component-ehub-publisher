eHUB Publisher Extractor
=============

eHub is an Internet marketing service. It is used for affiliate marketing

This component allows you to fetch data from the Publisher endpoints of the eHub API

**Table of contents:**

[TOC]

Supported endpoints
===================

* Campaigns
* Vouchers
* Creative
* Transactions

If you need more endpoints, please submit your request to
[ideas.keboola.com](https://ideas.keboola.com/)

Prerequisites
=============

Get the API token on the [API page of eHUB](https://pm.ehub.cz/api/), this page also contains the Publisher IDs of your
account

Configuration
=============

- API Key (#api_token) - [REQ] API key generated in eHUB
- Publisher IDs (publisher_ids) - [REQ] Comma separated list of Publisher IDs
- Fetch Campaigns (fetch_campaigns) - [REQ] boolean, if true fetch publisher campaign data
- Fetch Vouchers (fetch_vouchers) - [REQ] boolean, if true fetch publisher voucher data
- Fetch Creatives (fetch_creatives) - [REQ] boolean, if true fetch publisher creatives data
- Fetch Transactions (fetch_transactions) - [REQ] boolean, if true fetch publisher transaction data
- Transactions Fetching Options (transaction_options) - [OPT] Options on how to fetch transaction data
    - Fetch Mode (fetch_mode) - [OPT] either 'full_fetch'; get all historical, or 'incremental_fetch' to fetch data based on from and to date
    - Fetch From Date (date_from) - [OPT] Used for fetching the data with the dateInsertedFrom filter. The date should
      be in YYYY-MM-DD format or relative date i.e. 5 days ago, yesterday, etc.
    - Fetch To Date (date_to) - [OPT] Used for fetching the data with the dateInsertedTo filter. The date should be
      in YYYY-MM-DD format or relative date i.e. 5 days ago, yesterday, etc.
- Destination (destination_settings) - [OPT] description
    - Load Mode (load_mode) - [OPT] If Full load is used, the destination table will be overwritten every run. If
      incremental load is used, data will be upserted into the destination table. Tables with a primary key will have
      rows updated, tables without a primary key will have rows appended.

Sample Configuration
=============

```json
{
  "parameters": {
    "#api_token": "SECRET_VALUE",
    "publisher_ids": "SECRET_VALUE",
    "fetch_campaigns": true,
    "fetch_vouchers": true,
    "fetch_creatives": true,
    "fetch_transactions": true,
    "transaction_options": {
      "fetch_mode": "incremental_fetch",
      "date_from": "5 week ago",
      "date_to": "now"
    },
    "destination_settings": {
      "load_mode": "incremental_load"
    }
  }
}
```

Output
======

List of tables, foreign keys, schema.

Development
-----------

If required, change local data folder (the `CUSTOM_FOLDER` placeholder) path to your custom path in
the `docker-compose.yml` file:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    volumes:
      - ./:/code
      - ./CUSTOM_FOLDER:/data
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Clone this repository, init the workspace and run the component with following command:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
docker-compose build
docker-compose run --rm dev
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Run the test suite and lint check using this command:

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
docker-compose run --rm test
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Integration
===========

For information about deployment and integration with KBC, please refer to the
[deployment section of developers documentation](https://developers.keboola.com/extend/component/deployment/)