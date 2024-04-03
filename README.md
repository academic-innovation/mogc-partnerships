# Michigan Online edX Partner Portal

This is the backend API for the Partner Portal, and the main entry point for starting development work within the MO Open edX instance.

## Tutor Dev Environment

The following steps will configure a local Tutor installation running edX with the custom Michigan Online Global Classroom backend API, MFE, and legacy theme. The following is for Palm / Tutor v16. See [Nutmeg Setup](#nutmeg-setup) for Tutor v14.

### 1. Create and activate a new virtual environment:

```
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install [Tutor](https://github.com/overhangio/tutor/releases):
```
pip install "tutor[full]==<RELEASE VERSION>"
```

### 3. Create a root directory for Tutor:
```
mkdir tutor_root
export TUTOR_ROOT=$(pwd)/tutor_root
```

### 4. Set up the [mogc-partnerships backend API](https://github.com/academic-innovation/mogc-partnerships):
```
gh repo clone academic-innovation/mogc-partnerships $(tutor config printroot)/env/build/openedx/requirements
echo "-e ./mogc-partnerships/" >> $(tutor config printroot)/env/build/openedx/requirements/private.txt
```

*Optional:* Install the [legacy theme](https://github.com/academic-innovation/mogc-theme).

### 5. Save your config. This creates the necessary Docker files from Tutor templates:
```
tutor config save
```

### 6. Launch your dev instance:
```
tutor dev launch --interactive
```

This will guide you through introductory setup steps, build the necessary docker images, and start the services.

Confirm containers are running:
```
tutor dev status
```

### 7. Create a superuser for LMS Admin access:
```
tutor dev createuser --staff --superuser <NAME> <EMAIL>
```

### 8. Install and enable the [MOGC MFE plugin](https://github.com/academic-innovation/tutor-mogc-partnerships):
```
pip install git+https://github.com/academic-innovation/tutor-mogc-partnerships
tutor plugins enable mogc_partnerships
```

Now you should be able to connect and login to the [LMS admin](http://local.overhang.io:8000/admin/)!

See [Setup Troubleshooting](#setup-troubleshooting) if you encounter errors.


### Nutmeg Setup

Older versions of Tutor have some additional steps required to get your dev environment up and running.

Initialize your local Tutor instance:
```
tutor config save --interactive
```

Due to [a change in git refs](https://discuss.openedx.org/t/please-update-your-git-urls-for-edx-platform-and-several-other-repos/12387), a plugin is required to change the git URL for `django-require`.

First set your plugins root:
```
export TUTOR_PLUGINS_ROOT=$(pwd)/tutor-plugins
```

Then [create a plugin](https://docs.tutor.edly.io/tutorials/plugin.html#getting-started) at `$(tutor plugins printroot)/django-require-edx-org-fix.yml` containing:
```
name: django-require-edx-org-fix
version: 0.2.0
patches:
  openedx-dockerfile-minimal: |
    #----------------------------------------------------DJANGO-REQUIRE-EDX-ORG-FIX----------------------------------------------------#
    RUN git config --global url."https://github.com/openedx/django-require.git".insteadOf "https://github.com/edx/django-require.git"
    #--------------------------------------------------END DJANGO-REQUIRE-EDX-ORG-FIX--------------------------------------------------#
  openedx-dockerfile: |
    #----------------------------------------------------DJANGO-REQUIRE-EDX-ORG-FIX----------------------------------------------------#
    RUN git config --global url."https://github.com/openedx/django-require.git".insteadOf "https://github.com/edx/django-require.git"
    #--------------------------------------------------END DJANGO-REQUIRE-EDX-ORG-FIX--------------------------------------------------#
```

Enable plugin, save config, and start your dev environment:
```
tutor plugins enable django-require-edx-org-fix
tutor config save
tutor dev start -d
```
And finally, run migrations:
```
tutor dev init -l lms
```

### Setup Troubleshooting

**NPM timeout**

Try using a build container limited to a single CPU:
```
cat >buildkitd.toml <<EOF
[worker.oci]
  max-parallelism = 1
EOF
docker buildx create --use --name=singlecpu --config=./buildkitd.toml
```
To remove it later:
```
docker buildx rm singlecpu
```

**Storage issue**

Increase the Docker virtual disk size.
