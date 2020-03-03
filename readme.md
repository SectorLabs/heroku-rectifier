![](static/favicon.ico)

[![CircleCI](https://circleci.com/gh/SectorLabs/heroku-rectifier/tree/master.svg?style=svg)](https://circleci.com/gh/SectorLabs/heroku-rectifier/tree/master)

**heroku-rectifier** is a simple autoscaler built for Heroku.
It inspects your queues and the traffic they have, and blindly scales the consumers of the queues accordingly.
At the moment, **heroku-rectifier** only knows how to inspect RabbitMQ queues.

It *doesn't* take into consideration things like your DB load, so if you're worried about that, this might not be for you.

Also, you need to host **heroku-rectifier** yourself. If you're using Heroku, this is really easy, as a Procfile is provided.

## Configuration

You have to configure heroku-rectifier for it to actually do something.
The configuration is composed of two parts:

### Queues Configuration

This is made through a Flask endpoint ('/').

How often and how heroku-rectifier should update consumers, based on the queues stats, is configured
through a JSON file, editable at this endpoint.

Rectifier can watch as many queues as needed. An example of configuration looks like this:

```json
{
    "app_name": {
        "queue_name": {
            "intervals": [0, 100, 1000],
            "workers": [1, 2, 3],
            "cooldown": 30,
            "consumers_formation_name": "dyno_formation_name"
        }
    }
}
```

You specify the queues needed to be watched through the `queues` attribute.
Every queue **has** to have the following attributes set accordingly:

##### Intervals and workers

Together, these two attributes tell rectify how many workers should be used for certain intervals.
Rectify looks at the number of messages in every queue (let's call it `messageCount`), and based on this
configuration, decides on the number of workers it should scale to.

Take the above example:

```json
{
    "intervals": [0, 100, 1000],
    "workers": [1, 2, 3]
}
```

If `0 <= messageCount < 100`, Rectify will scale to 1 worker.

If `100 <= messageCount < 1000`, Rectify will scale to 2 workers.

If `1000 <= messageCount`, Rectify will scale to 3 workers.

If the number of the consumers already match the number needed to be scaled to,
no extra `scale` call will be made.

There are a couple of constraints for these attributes (if they're not respected, the configuration
will not be used):

* the `intervals` array should be sorted.
* the `intervals` array should start with 0
* all entries in the `intervals` array should be positive
* all entries in the `workers` array should be positive
* the length of the `intervals` array should match the length of the `workers` array.

##### Cooldown

The `cooldown` attribute (which should be a positive integer, expressing seconds), tells Rectifier how much
it should wait between succesive scales.

After one scale operation has been made, nothing else will be done until this cooldown
expires.

##### The consumers formation name

This is the key used for identifying a dyno formation on Heroku.

### Environment Variables

#### Redis

> REDIS_URL

The URL to be used for Redis storage of the configuration and the update times.
This is automatically provided by Heroku if you provide the app with Heroku Redis.
    
#### Flask

> SECRET_KEY

The secret key used by flask

> HOST (optional)

The host Flask should use

> PORT (optional)

the port flask should use

> BASIC_AUTH_USER

The user name to be used for basic auth.

> BASIC_AUTH_PASSWORD

The password to be used for basic auth.

#### Heroku

> HEROKU_API_KEY

The API key rectifier should use for accesing heroku.

#### Rectifier

> TIME_BETWEEN_REQUESTS

How often should Rectifier request RabbitMQ for stats.

> RABBIT_MQ_SECURE

Whether it should use `https` for rabbit MQ http calls.

> DRY_RUN

If true, the rectifier won't _actually_ scale.

## License
MIT License

Copyright (c) 2018 Sector Labs

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
