# MGP_Quiz

## Docker Environment Setup Guide

This guide provides instructions on setting up and managing the Docker environment for MGP_Quiz.

### 1. Launch & Check Docker
After launching Docker, verify whether a volume named `pg_data` exists. If it does, either:
- Remove the existing volume: `docker volume rm pg_data`
- Modify the volume name in the `docker-compose.yml` file to avoid conflicts.

### 2. Run `make build`
Execute the following command to build and launch the necessary Docker containers:

```
make build
```

### 3. View Documentation
To view the documentation, open your web browser and navigate to:

```
http://localhost:8000/docs
```

API endpoints can also be tested on this page.

### 4. Run `make stop`
To stop and remove running containers, execute:

```
make stop
```
