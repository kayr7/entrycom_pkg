"""Handle 2n Entrycom doorbell."""

import asyncio
import async_timeout
import aiohttp
import logging

import json
import sys

DEFAULT_NAME = "2n keycard_validator"
CONF_USERNAME = "username"
CONF_PASSWORD = "password"
CONF_URL = "entrycom_url"



class Entrycom(object):
    """Representation of a Sensor."""

    def __init__(self, username, password, url):
        """Initialize the sensor."""
        self._uname = username
        self._passw = password
        self._base_url = '{}api/'.format(url)
        self._state = None
        self._subscribe_url = "{}log/subscribe?filter=KeyPressed,CardEntered".format(
            self._base_url
        )
        self._id = None
        self._event_url = "unset"
        self._unsubscribe_url = "unset"

    async def setId(self, websession):
        self._id = None
        if self._id == None:
            try:
                with async_timeout.timeout(10):
                    response = await websession.get(
                        self._subscribe_url,
                        auth=aiohttp.BasicAuth(self._uname, self._passw),
                        verify_ssl=False,
                    )

                    if response.status == 200:
                        text = await response.text()
                        jData = json.loads(text)
                        print(jData)
                        self._id = jData["result"]["id"]
                        self._event_url = "{}log/pull?id={}&timeout=600".format(
                            self._base_url, self._id
                        )
                        self._unsubscribe_url = "{}log/unsubscribe?id={}".format(
                            self._base_url, self._id
                        )
                    else:
                        print(response)

            except Exception as e:
                    print("exception when setting up subscription: {}".format(e))

        if self._id is None:
            print("error subscribing to 2n! retrying in 5min!")


    async def async_get_state(self, websession):
        """Get state of doorbell."""

        while True:
            resp = None
            try:
                with async_timeout.timeout(10):
                    print('listening for an event')
                    resp = await websession.get(
                        self._event_url,
                        auth=aiohttp.BasicAuth(self._uname, self._passw),
                        verify_ssl=False,
                    )

                    text = await resp.text()

                    if resp.status == 200:
                        jData = json.loads(text)
                        if (
                            "success" in jData
                            and jData["success"]
                            and "result" in jData
                            and len(jData["result"]["events"]) > 0
                        ):
                            if (
                                jData["result"]["events"][0]["event"]
                                == "CardEntered"
                            ):
                                if jData["result"]["events"][0]["params"]["valid"]:
                                    self._state = "ValidCardEntered"
                                else:
                                    self._state = "InvalidCardEvent: {}".format(
                                        jData["result"]["events"][0]["params"][
                                            "uid"
                                        ]
                                    )
                            elif (
                                jData["result"]["events"][0]["event"]
                                == "KeyPressed"
                            ):
                                self._state = "KeyPress: {}".format(
                                    jData["result"]["events"][0]["params"]["key"]
                                )
                            elif (
                                jData["result"]["events"][0]["event"]
                                == "MotionDetected"
                            ):
                                if (
                                    jData["result"]["events"][0]["params"]["state"]
                                    == "in"
                                ):
                                    self._state = "StartOfMotion"
                                else:
                                    self._state = "EndOfMotion"
                            elif (
                                jData["result"]["events"][0]["event"]
                                == "NoiseDetected"
                            ):
                                if (
                                    jData["result"]["events"][0]["params"]["state"]
                                    == "in"
                                ):
                                    self._state = "StartOfNoise"
                                else:
                                    self._state = "EndOfNoise"
                        else:
                            self._state = False
                        return self._state

            except (asyncio.TimeoutError) as e:
                print("timeout")
                continue

            if resp is None or resp.status != 200:
                self._state = False
                print("unsubscribing from stream to reinitialize")
                try:
                    with async_timeout.timeout(10):
                        resp = await websession.get(
                            self._unsubscribe_url,
                            auth=aiohttp.BasicAuth(self._uname, self._passw),
                            verify_ssl=False,
                        )
                except Exception as e:
                    print("exception while trying to end subscription")
                    print("exception: {}".format(e))
                break
                return False




async def main(entrycom):
    async with aiohttp.ClientSession() as session:
        await entrycom.setId(session)
        while True:
            html = await entrycom.async_get_state(session)
            print(html)


entrycom = Entrycom(sys.argv[1], sys.argv[2], sys.argv[3])

loop = asyncio.get_event_loop()
loop.run_until_complete(main(entrycom))
