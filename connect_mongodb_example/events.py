# -*- coding: utf-8 -*-
#
# Copyright (c) 2023, CloudBlue Connect
# All rights reserved.
#
import urllib.parse

import httpx
import motor.motor_asyncio

from connect.eaas.core.decorators import (
    event,
)
from connect.eaas.core.extension import EventsApplicationBase
from connect.eaas.core.responses import (
    BackgroundResponse,
)


class ConnectExtensionMongodbExampleEventsApplication(EventsApplicationBase):
    @event(
        'asset_purchase_request_processing',
        statuses=[
            'pending', 'approved', 'failed',
            'inquiring', 'scheduled', 'revoking',
            'revoked',
        ],
    )
    async def handle_asset_purchase_request_processing(self, request):
        await self.save_subscription_event_via_http_api_to_mongo_db(request)
        await self.save_subscription_event_via_motor_to_mongo_db(request)

        return BackgroundResponse.done()

    async def save_subscription_event_via_http_api_to_mongo_db(self, request):
        base_api_endpoint = self.config['DATA_API_ENDPOINT']

        async with httpx.AsyncClient() as client:
            r = await client.post(
                f'{base_api_endpoint}/action/insertOne',
                headers={
                    'Content-Type': 'application/json',
                    'Access-Control-Request-Headers': '*',
                    'api-key': self.config['API_KEY'],
                },
                json={
                    'collection': self.config['HTTP_COLLECTION'],
                    'database': self.config['DB'],
                    'dataSource': self.config['CLUSTER'],
                    'document': request,
                },
            )
            self.logger.info(r)

    async def save_subscription_event_via_motor_to_mongo_db(self, request):
        db_host = self.config['DB_HOST']
        db_user = urllib.parse.quote(self.config['DB_USER'])
        db_password = urllib.parse.quote(self.config['DB_PASSWORD'])

        connection_str = f'mongodb+srv://{db_user}:{db_password}@{db_host}/'
        client = motor.motor_asyncio.AsyncIOMotorClient(
            connection_str, serverSelectionTimeoutMS=5000,
        )

        db = client[self.config['DB']]
        collection = db[self.config['DRIVER_COLLECTION']]

        r = await collection.insert_one(request)
        self.logger.info(r)
