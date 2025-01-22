# Uploads Directory

This directory is intended for storing user-uploaded files.

**Important Notes:**

* This directory is mounted as a volume from your host machine. Any files placed here will persist even if the Docker container is stopped or removed.
* The exact location of the corresponding directory on your host machine depends on how you started the Docker container. Refer to the application's documentation for details.
* Do not manually modify files in this directory unless you know what you are doing.

**For Developers:**

* This directory is used by the application to store files uploaded by users.
* The application code expects this directory to exist at `/app/uploads` within the Docker container.
* Ensure that the appropriate permissions are set on this directory to allow the application to write files.
