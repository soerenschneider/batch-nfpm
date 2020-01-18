# batch nfpm

## Problem statement

## Run example

```bash
DIR=/tmp/batchnfpm
if [ ! -d ${DIR} ]; then
    mkdir ${DIR}
    chcon -Rt svirt_sandbox_file_t ${DIR} || true
    chmod 777 -R ${DIR}
fi

NFPM_CONFIG=https://gitlab.com/soerenschneider/batch-nfpm/raw/master/example-config.yaml
podman run -v ${DIR}:${DIR} -e NFPM_CONFIG="${NFPM_CONFIG}" registry.gitlab.com/soerenschneider/batch-nfpm
```

## Example config

```yaml
builds:
  artifacts_path: /tmp/batchnfpm
  clone_path: /tmp/repositories
  nfpm_config:
    local_path: /tmp/nfpm-configs
    fetch_resource: https://gitlab.com/soerenschneider/nfpm-configs.git
  build_configurations:
    - hoster: github
      owner: prometheus
      project: prometheus
      commands:
        - make build
```

## Config parameters


## How does it work
