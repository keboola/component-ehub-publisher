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
- Fetch Campaigns (fetch_campaigns) - [REQ] Fetch all publisher campaign data
- Fetch Vouchers (fetch_vouchers) - [REQ] Fetch all publisher voucher data
- Fetch Creatives (fetch_creatives) - [REQ] Fetch all publisher creatives data
- Fetch Transactions (fetch_transactions) - [REQ] Fetch all publisher transaction data

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
    "fetch_transactions": true
  },
  "action": "run"
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