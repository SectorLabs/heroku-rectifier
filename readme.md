**Rectifier** is an autoscaler. It inspects queues and the traffic they have, and scales the consumers of the queues
accordingly.

No fancy logo available.

## Configuration

You have to configure Rectifier for it to actually do something.
The configuration is made in two parts:

### Queues Configuration

This is made through a Flask endpoint ('/').

How often and how Rectifier should update consumers, based on the queues stats, is configured
through a JSON file, editable at this endpoint.

Rectifier can watch as many queues as needed. An example of configuration looks like this:

```json
{
    "bayut-development": {
        "photos": {
            "intervals": [0, 100, 1000],
            "workers": [1, 2, 3],
            "cooldown": 30,
            "consumers_formation_name": "worker_photos"
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
