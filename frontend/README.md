# Frontend build system

Build the Docker image based on the official node image:

  ```
  (cd docker ; ./build.sh)
  ```

The frontend build uses [yarn](https://yarnpkg.com/) for package management,
dependencies are defined in `package.json` and locked in `yarn.lock`.

To run the frontend container invoke:

  ```
  ./run_docker.sh
  ```

The first run will take a bit longer because dependencies are downloaded with
`yarn`. The dependencies (`node_modules` directory) are stored in a docker
volume to avoid downloading them all again for every container restart.

To get rid of the `node_modules` you can just remove the volume:

  ```
  docker volume rm devdayhp_node_modules
  ```

Afterwards you'll be dropped into a shell where you can run:

  ```
  gulp
  ```

to build the frontend code.


Happy hacking!
