# Going to production

This is the documentation for going to test/production.

## Clone the repository

```
git clone https://git.t-systems-mms.eu/scm/saec/devday_hp.git
```

## Generate a strong postgresql password

```
(echo -n "POSTGRES_PASSWORD=" ; dd if=/dev/urandom bs=32 count=1 2>/dev/null | base64 -w 0) > prod-env-db
```

## Build the images

Make sure that the following preconditions are met:

- `http_proxy` and `no_proxy` environment variables are matching the system network
- the docker daemon is running
- your user is in the docker group
- you have docker-compose installed

To build the images run:

```
./prod.sh build
```

which should work™.

# Start Vault and initialize it

```
./prod.sh up -d vault
popd docker/vault
./init_unseal_fill_vault.sh
pushd
```

Save the generated `vault-YYYYMMDD-HHMMSS+TZ.json` (file name is written at the
top of the `init_unseal_fill_vault.sh` output. Keep the generated
`postgresql_password` as you will need it later.

# Start and initialize the database container

```
# start the db container
./prod.sh up -d db
echo "ALTER USER devday PASSWORD '<password from above>'"|./prod.sh exec -T db psql -U postgres -d postgres
```

**Note:**

> If you want to work with a database dump (i.e. migrate from existing
> production) you should do this now:
>
> ```
> zcat "<database dump>.sql" | ./prod.sh exec -T db psql -U devday devday
> ```

# Start the application and the reverse proxy

```
./prod.sh up -d
```

You can follow the application startup logs with:

```
./prod.sh logs -f app
```

**Note:**

> To import a media backup you can perform:
>
> ```
> cat "<media dump>.tar.gz" | ./prod.sh exec -T app tar xz -C /srv/devday/media
> ```

The application is now available on Port 8080 of the host system.
