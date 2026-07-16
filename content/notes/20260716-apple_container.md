---
title: "A minimal working setup for apple container"
date: 2026-07-16
summary: "A minimal drop-in replacement for docker desktop on macos"
tags: ["apple-container"]
audience: "Software Engineers"
---

With macOS 26, Apple released an open-source `container` CLI. It aims at providing a lightweight solution to run Linux containers on Mac. Instead of running every container inside a single shared Linux VM (as Docker Desktop and Colima do), the Apple framework gives each container its own lightweight Linux VM, which isolates containers and optimizes performance on macOS.

## A minimal `container compose` setup

I was curious to try it out, but the apple framework does not support the `compose` feature yet. There is quite some demand on the official github repository, but it would require some work to ship the framework with a fully compatible `compose` service.

For my purposes, I don't need that many features from `compose` to run a container. In most of my projects, I would usually create a slim `docker-compose.yml` with a service, a few volumes and an environment file attached to it. A typical docker compose file would look like:

```yml
services:
  api-server:
    image: connectors-api-server
    build:
      context: .
      dockerfile: ./docker/api-server/Dockerfile
    volumes:
      - ./data:/data
    env_file:
      - aws.env
    ports:
      - "8000:8000"
```

The goal for me, was then to create a small python script that would parse the yml file, extract the volumes, environment files and ports, and map them correctly to the `container` CLI. It is relatively straightforward to write and allows a drop-in replacement of `docker compose` in most of my personal projects.

The script would simply map `container-compose-build api-server` to the corresponding `container build` call. Alternatively, I also use `container-compose-run api-server bash` that would run `container run -v ./data:/data --env-file aws.env -p 8000:8000 api-server-image bash`.

You can find a working example in my [dotfiles](https://github.com/tywr/dotfiles/blob/main/.config/zsh/scripts/container_compose.py).

## Conclusion

With some minor scripting, apple container can be used in some trivial `compose` use cases, and can definitely be used in simple projects. For more complex projects which require a greater number of `compose` features, I'm afraid I'll have to fall back to my docker `colima` setup.

I am however quite happy with the performance of apple container, I usually find the building and running of containers to be faster, and the memory footprint of the docker system running in the background has been reduced.
