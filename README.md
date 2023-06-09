# dcrx-api
[![PyPI version](https://img.shields.io/pypi/v/dcrx-api?color=gre)](https://pypi.org/project/dcrx-api/)
[![License](https://img.shields.io/github/license/scorbettUM/dcrx-api)](https://github.com/scorbettUM/dcrx-api/blob/main/LICENSE)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](https://github.com/scorbettUM/dcrx-api/blob/main/CODE_OF_CONDUCT.md)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/dcrx-api)](https://pypi.org/project/dcrx-api/)

Dcrx-api is a RESTful implementation of the dcrx library, allowing you to create Docker images on request! Dcrx-api extends dcrx, providing integrations with the Docker API and dcrx that allow images to be built by making REST requests.

Dcrx-api also includes basic JWT authorization and user management (no-RBAC), and is intended to be deployed as an internal-facing service. dcrx also provides OpenAPI documentation to make getting started intuitive, and features integrations with SQLite, Postgres, and MySQL for storing and managing users.


# Setup and Installation

DCRX is available both as a Docker image and as a PyPi package. For local use, we recommend using PyPi, Python 3.10+, and a virtual environment. To install, run:

```bash
python -m venv ~/.dcrx && \
source ~/.dcrx/bin/activate && \
pip install dcrx-api
```

To get the Docker image, run:

```
docker pull adalundhe/dcrx-api:latest
```


# Getting Started

Dcrx requires a slew of environmental variables in order to run correctly. These include:

```
DCRX_API_WORKERS=10 # Number of workers to use for Job executor. Default is the number os OS threads.

DCRX_API_TOKEN_EXPIRATION_MINUTES=10 # Time in minutes for JWT authorization token to expire. Default is 30.

DCRX_API_SECRET_KEY=testingthis # Initial secret used to hash user passwords.

DCRX_API_AUTH_ALGORITHM=HS256 # Algorithm to use for hashing user passwords.

DCRX_API_DATABASE_TYPE=sqlite # Type of database to use. Default is sqlite and options are mysql, asyncpg, and sqlite.

DCRX_API_DATABASE_USER=admin # Username used for database connection authentication

DCRX_API_DATABASE_PASSWORD=test1234 # Password used for database connection authentrication

DCRX_API_DATABASE_NAME=dcrx # Name of database to use for storing users. Default is dcrx.

DCRX_API_DATABASE_URI=sqlite+aiosqlite:///dcrx # URL/URI of SQL database for storing users

DOCKER_REGISTRY_URI=https://docker.io/v1/myrepo/test-images # Docker image registry to push images to.

DOCKER_REGISTRY_USERNAME=test # Username to authenticate Docker pushes to the provided registry.

DOCKER_REGISTRY_PASSWORD=test-repo-password # Password to authenticate Docker pushes to the provided registry.
```

Prior to starting the server, we recommend seeding the database with an initial user. To do so, run the command:

```bash
dcrx-api database initialize --username $USERNAME --password $PASSWORD --first-name $FIRST_NAME --last-name $LAST_NAME --email $EMAIL
```

If you've chosen to run the Docker image, this step is taken care of for you, with the default user being:

```
username: admin
password: dcrxadmin1*
first-name: admin
last-name: user
email: admin@admin.com
```

Next run:

```bash
dcrx-api server run
```

and navigate to `localhost:2277/docs`, where you'll find dcrx-api's OpenAPI documentation.


# Authenticating and Building an Image

From here, we'll need to authenticate using the initial user we created above. Open the tab for `/users/login`, and for the `username` and `password` fields enter the username and password of the initial user, then click `Execute`. A `200` status response containg the initial user's username and id should return.

Next navigate to the `/jobs/images/create` tab. As before, we'll need to fill out some data. Go ahead and copy paste the below into the input for the request body:

```json
{
  "name": "hello-world",
  "tag": "latest",
  "layers": [
    {
      "layer_type": "stage",
      "base": "python",
      "tag": "3.11-slim",
    },
    {
        "layer_type": "entrypoint",
        "command": [
            "echo",
            "Hello world!"
        ]
    }
  ]
}
```

A dcrx-api image build request requires, at-minimum, a `name`, `tag` and one or more `layer` objects, which will be processed and build in-order of appearance. Note that each layer object almost exactly corresponds to its `dcrx` call. The above corresponds exactly to:

```python

from dcrx import Image

hello_world = Image('hello-world')

hello_world.stage(
    'python',
    '3.11-slim'
).entrypoint([
    'echo',
    'Hello world!'
])
```

Go ahead and submit the request via the `Execute` button. This will start a job to build the specified image and push it to the repository specified in dcrx-api's environmental variables.

Note that dcrx-api doesn't wait for the image to be built, instead returning a `JobMetadata` response with a status code of `200`, including the `job_id`. Building images is time-intensive and could potentially bog down a server, so dcrx-api builds and pushes images in the background. We can use the `job_id` of a Job to make further `GET` requests to the `/jobs/images/{job_id}/get` endpoint to monitor and check how our job is progressing. If we need to cancel a job for any reason, we can simple make a `DELETE` request to `/jobs/images/{job_id}/cancel`.


# Running the Docker Image

To run the Docker image, we recommend first creating a `.env` file with the required environment variables noted above. Then run the image:

```bash
docker run -p 2277:2277 --env-file .env --privileged dcrx-api:latest
```


# Notes and Gotchas

1. Does dcrx-api require a volume to run? - Yes. While dcrx-api builds images in-memory, Docker still (frustratingly) requires that a physical file be present in the build directory. This means that, if running dcrx-api in Docker or via Kubernetes, you will need to have a volume with the correct permissions mounted.

2. Does the dcrx-api Docker image require root? - Currently yes. The dcrx-api image is based on the latest version of Docker's `dind` image, which runs as and requires root privlidges. We're working on getting the rootless version of `dind` working though!