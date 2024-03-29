# Michigan Online edX Partner Portal

This is the backend API for the Partner Portal, and the main entry point for starting development work within The MO Open edX instance.

## Tutor Dev Environment

The following steps will configure a local Tutor installation running edX with the custom Michigan Online Global Classroom backend API, MFE, and legacy theme. The following is for Palm / Tutor v16. See [Nutmeg Setup](#nutmeg-setup) for Tutor v14.

Create and activate a new virtual environment:

```
python3 -m venv .venv
source .venv/bin/activate
```

Install [Tutor](https://github.com/overhangio/tutor/releases):
```
pip install "tutor[full]==<RELEASE VERSION>"
```

Create a root directory for Tutor:
```
mkdir tutor_root
export TUTOR_ROOT=$(pwd)/tutor_root
```

Set up the [mogc-partnerships backend API](https://github.com/academic-innovation/mogc-partnerships):
```
gh repo clone academic-innovation/mogc-partnerships $(tutor config printroot)/env/build/openedx/requirements
echo "-e ./mogc-partnerships/" >> $(tutor config printroot)/env/build/openedx/requirements/private.txt
```

Install the [legacy theme](https://github.com/academic-innovation/mogc-theme):
```
gh repo clone academic-innovation/mogc-theme $(tutor config printroot)/env/build/openedx/themes/mogc
-theme
```

Save your config. This creates the necessary docker files from Tutor templates:
```
tutor config save
```

Launch your dev instance:
```
tutor dev launch --interactive
```

This will guide you through introductory setup steps, build the necessary docker images, and start the services.

Confirm containers are running:
```
tutor dev status
```

Create a superuser for LMS Admin access:
```
tutor dev createuser --staff --superuser <NAME> <EMAIL>
```

Finally, enable the legacy theme:
```
tutor dev do settheme mogc-theme
```

Now you should be able to connect and login to the [LMS admin](http://local.overhang.io:8000/admin/)!

See [Setup Troubleshooting](#setup-troubleshooting) if you encounter errors.


### Nutmeg Setup

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

Now follow the steps in [MFE Setup](#mfe-setup) and [Legacy Theme Setup](#legacy-theme-setup).

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

### MFE Setup

#### Palm (Tutor v16)

As of Palm, the partner portal MFE is included as a plugin, so all you need to do is add the mount point:
```
tutor mounts add ../frontend-app-mogc-partners
```

Now you should be able to access the Partner Portal MFE at http://apps.local.overhang.io:1998.

#### Nutmeg (Tutor v14):

1. Clone the frontend app repository at the same directory level as your partner portal.
2. Add the following to `$(tutor config printroot)/config.yml`:
```
MFE_PARTNERS_MFE_APP:
  name: mogc-partners
  port: 1998
  repository: https://github.com/academic-innovation/frontend-app-mogc-partners.git
  version: master
```
3. Stop and restart your dev stack.
4. Restart tutor and start the app at the specified mount point:
```
tutor dev start -d mogc-partners --mount=../frontend-app-mogc-partners --skip-build
```

Now the Partner Portal can be accessed at http://apps.local.overhang.io:1998/mogc-partners.

### Legacy Theme Setup

Some pieces of the frontend use a legacy theme, such as the HTML course certificates, use the legacy edX theme.

1. Clone theme repository into `$(tutor config printroot)/env/build/openedx/themes`
2. Enable the theme: `tutor settheme <THEMENAME>`
3. In LMS Admin, go to themes and enable the theme in the UI.
