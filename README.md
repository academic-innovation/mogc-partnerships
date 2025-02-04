# Michigan Online edX Partner Portal

This is the backend API for the Partner Portal, and the main entry point for starting development work within the MO Open edX instance.

## Tutor Dev Environment

The following steps will configure a local Tutor installation running edX with the custom Michigan Online Global Classroom backend API, MFE, and optionally, the legacy theme. The following is for Palm / Tutor v16.

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

### 4. Launch your dev instance:
```
tutor dev launch
```

This will guide you through introductory setup steps, build the necessary docker images, and start the services.

Confirm containers are running:
```
tutor dev status
```

### 5. Create a superuser for LMS Admin access:
```
tutor dev do createuser --staff --superuser <NAME> <EMAIL>
```

### 6. Install and enable the [MOGC Partnerships Extensions plugin](https://github.com/academic-innovation/tutor-mogc-partnerships):
```
pip install git+https://github.com/academic-innovation/tutor-mogc-partnerships
tutor plugins enable mogc_partnerships
```

**Note**: You can also clone this repo and install your local version for plugin development.

### 7. Clone backend API repo outside `tutor_root`
```
gh repo clone academic-innovation/mogc-partnerships
```
### 8. Add mount point
```
tutor mounts add ../mogc-partnerships
```

<!-- ### 6. Set up the [mogc-partnerships backend API](https://github.com/academic-innovation/mogc-partnerships):
```
cd $(tutor config printroot)/env/build/openedx/requirements && gh repo clone academic-innovation/mogc-partnerships
echo "-e ./mogc-partnerships/" >> $(tutor config printroot)/env/build/openedx/requirements/private.txt
```

### 7. Enable the plugin:
```
tutor plugins enable mogc_partnerships
``` -->

### 9. Clone [Partner Portal MFE repo](https://github.com/academic-innovation/frontend-app-mogc-partners) outside `tutor_root`:
```
gh repo clone academic-innovation/frontend-app-mogc-partners
```
And install dependencies:
```
npm install
```
*Note*: Ensure that you have the version of Node noted in the `.nvmrc` file installed and activated.

See the [nvm repo](https://github.com/nvm-sh/nvm) for installation and usage steps.

### 10. Add mount point for Partner Portal MFE:
```
tutor mounts add ../frontend-app-mogc-partners
```
*Note*: the mount point should match the directory where you cloned the repo above.

### 11. Save your config. This creates the necessary Docker files from Tutor templates:
```
tutor config save
```

### 12. Stop and launch again:

This step will bundle the mogc-partnerships backend API plugin and frontend-app-mogc-partners MFE into the Tutor Docker images and rebuild.
```
tutor dev stop && tutor dev launch
```

Once the build completes, Tutor will output a list of local URLs for LMS Admin, various MFEs and the Partner Portal.

See [Setup Troubleshooting](#setup-troubleshooting) if you encounter errors.

### Legacy Theme (Optional)

The [legacy theme](https://github.com/academic-innovation/mogc-theme) is where the HTML course certificates live. Follow the steps in that repo to install and activate the theme in your local dev environment.

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
