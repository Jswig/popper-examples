workflow "run http transfer test" {
  resolves = "plot results"
}

action "build context" {
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

action "request resources" {
  needs = "build context"
  uses = "popperized/geni/exec@master"
  args = "workflows/geni-multisite-transfer/geni/request.py"
  secrets = ["GENI_KEY_PASSPHRASE"]
}

action "run test" {
  needs = "request resources"
  uses = "popperized/ansible@master"
  args = "-i workflows/geni-multisite-transfer/geni/hosts workflows/geni-multisite-transfer/ansible/playbook.yml"
  env = {
    ANSIBLE_HOST_KEY_CHECKING = "False"
  }
  secrets = ["ANSIBLE_SSH_KEY_DATA"]
}

action "teardown" {
  needs = "run test"
  uses = "popperized/geni/exec@master"
  args = "workflows/geni-multisite-transfer/geni/release.py"
  secrets = ["GENI_KEY_PASSPHRASE"]
}

action "plot results" {
  needs = "teardown"
  uses = "docker://ivotron/gnuplot:5.0"
  runs = ["sh", "-c", "$GITHUB_WORKSPACE/workflows/geni-multisite-transfer/scripts/plot.sh"]
}
