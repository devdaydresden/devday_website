# Going to production

This is the documentation for going to test/production.

## Clone the repository

```
git clone https://git.t-systems-mms.eu/scm/saec/devday_hp.git
```

## Build the images

Make sure that the following preconditions are met:

- `http_proxy` and `no_proxy` environment variables are matching the system
  network
- the docker daemon is running
- your user is in the docker group
- you have docker-compose installed
- put `MAILNAME`, `POSTFIX_ROOT_ALIAS` and `POSTFIX_RELAY_HOST` variables into
  `prod-env-postfix`

To build the images run:

```
./prod.sh build
```

which should work™. You might want to have a look into the generated
`prod-env`, `prod-env-db` and `prod-env-mail` files and adapt the environment
variables inside these files to fit your environment.

The build process creates a self signed certificate for Vault. You may also
create a CSR by running

```
openssl req -new -config docker/vault/openssl.cnf \
  -out docker/vault/vault.csr.pem \
  -key docker/vault/config/ssl/private/vault.key.pem
```

Let it sign by a CA and put the resulting certificate chain into
docker/vault/config/ssl/vault.crt.pem before running the build again.

The build process generates a random password for the postgres user in the db
container and puts it into prod-env-db

# Start Vault and initialize it

```
./prod.sh up -d vault
pushd docker/vault
./init_unseal_fill_vault.sh
popd
```

Save the generated `vault-YYYYMMDD-HHMMSS+TZ.json` (file name is written at the
top of the `init_unseal_fill_vault.sh` output. Keep the generated
`postgresql_password` as you will need it later.

# Start and initialize the database container

```
# start the db container
./prod.sh up -d db
./prod.sh exec db psql -U postgres -d postgres -c "ALTER USER devday PASSWORD '<password from above>'"
```

**Note:**

> If you want to work with a database dump (i.e. migrate from existing
> production) you should do this now:
>
> ```
> zcat "<database dump>.sql" | ./prod.sh exec -T db psql -U devday devday
> ```
>
> If you want to use a set of synthetic development data instead you can
> run the following instead:
>
> ```
> ./prod.sh manage devdata
> ```

# Start the application, the mail server and the reverse proxy

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
