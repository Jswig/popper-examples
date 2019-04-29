workflow "run http transfer test" {
  resolves = "plot results"
}

action "build cloudlab context" {
  uses = "popperized/geni/build-context@master"
  env = {
    GENI_FRAMEWORK = "cloudlab"
  }
  secrets = [
    "GENI_PROJECT",
    "GENI_USERNAME",
    "GENI_PASSWORD",
    "GENI_PUBKEY_DATA",
    "GENI_CERT_DATA"
  ]
}

action "request cloudlab resources" {
  needs = "build cloudlab context"
  uses = "popperized/geni/exec@master"
  args = "workflows/cloudlab-multisite-transfer/geni/request.py"
  secrets = ["GENI_KEY_PASSPHRASE"]
}

action "run test" {
  needs = "request cloudlab resources"
  uses = "popperized/ansible@master"
  args = "-i workflows/cloudlab-multisite-transfer/geni/hosts workflows/cloudlab-multisite-transfer/ansible/playbook.yml"
  env = {
    ANSIBLE_HOST_KEY_CHECKING = "False"
  }
  secrets = ["ANSIBLE_SSH_KEY_DATA"]
}

action "teardown" {
  needs = "run test"
  uses = "popperized/geni/exec@master"
  args = "workflows/cloudlab-multisite-transfer/geni/release.py"
  secrets = ["GENI_KEY_PASSPHRASE"]
}

action "plot results" {
  needs = "teardown"
  uses = "docker://ivotron/gnuplot:5.2"
  runs = "$GITHUB_WORKSPACE/workflows/cloudlab-multisite-transfer/scripts/plot.sh"
}
