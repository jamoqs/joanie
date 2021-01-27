# Joanie – Power up Richie catalog 👛

Joanie aims to power up [Richie](https://github.com/openfun/richie)
catalog functionalities by delivering an API able to manage course
enrollment/subscription, payment and certificates delivery.

Joanie is built on top of [Django Rest Framework](https://www.django-rest-framework.org/).

## Getting started

### Prerequisite

Make sure you have a recent version of Docker and
[Docker Compose](https://docs.docker.com/compose/install) installed on your laptop:

```bash
$ docker -v
  Docker version 20.10.2, build 2291f61

$ docker-compose -v
  docker-compose version 1.27.4, build 40524192
```

>⚠️ You may need to run the following commands with `sudo` but this can be
>avoided by assigning your user to the `docker` group.

### Project bootstrap

The easiest way to start working on the project is to use our `Makefile` :
```bash
$ make bootstrap
```

This command builds the `app` container, installs dependencies, performs database migrations and
compile translations. It's a good idea to use this command each time you are pulling code from the
project repository to avoid dependency-releated or migration-releated issues.

Now that your Docker services are up, let's running them :

```bash
$ make run
```

You should be able to access to the API overview interface at [http://localhost:8060](http://localhost:8060).

Finally, you can see all available commands in our `Makefile` with :

```bash
$ make help
```

## Django admin

You can access the Django admin site at [http://localhost:8060/admin](http://localhost:8060).

You first need to create a superuser account :

```bash
$ make superuser
```

## Contributing

This project is intended to be community-driven, so please, do not hesitate to
get in touch if you have any question related to our implementation or design
decisions.

We try to raise our code quality standards and expect contributors to follow
the recommandations from our
[handbook](https://openfun.gitbooks.io/handbook/content).

## License

This work is released under the MIT License (see [LICENSE](./LICENSE)).
