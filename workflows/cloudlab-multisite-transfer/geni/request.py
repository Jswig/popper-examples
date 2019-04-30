# Creates a multi-site link between two GENI sites
# Adapted from:
#   https://bitbucket.org/barnstorm/geni-lib/src/1b480c83581207300f73679af6844d327794d45e/docs/source/tutorials/wanvts.rst?at=0.9-DEV#wanvts.rst
import os

import geni.rspec.pg as PG
import geni.rspec.igext as IGX
import geni.rspec.vts as VTS

import geni.aggregate.instageni as IGAM
import geni.aggregate.vts as VTSAM

import geni.util

# experiment variables (TODO: expose them in plain text)
# {
experiment = "popper-examples"
node_img = "urn:publicid:IDN+emulab.net+image+emulab-ops:UBUNTU16-64-STD"
outdir = os.path.dirname(os.path.realpath(__file__))

# create variables to hold VTS and regular aggregate managers (AM). These can
# be modified based on the available VTS AMs. See here for a list:
#    https://bitbucket.org/barnstorm/geni-lib/src/1b480c83581207300f73679af6844d327794d45e/geni/aggregate/vts.py?at=0.9-DEV#lines-331:336
site1VTSAM = VTSAM.UKYPKS2
site1AM = IGAM.UKYPKS2
site2VTSAM = VTSAM.UKYPKS2
site2AM = IGAM.NPS
# }

# load context and create slice for experiment
ctx = geni.util.loadContext(key_passphrase=os.environ['GENI_KEY_PASSPHRASE'])
geni.util.createSlice(ctx, experiment)

# delete slivers if they already exist
print("-- Deleting any existing slivers")
for am in [site1VTSAM, site1AM, site2VTSAM, site2AM]:
    geni.util.deleteSliverExists(am, ctx, experiment)

############
# create site1 VTS
# {

# search remote advertisement for endpoint description of for circuit plane
print("-- Getting VTS advertisements")
remote_ad = site1VTSAM.listresources(ctx)
for cp in remote_ad.circuit_planes:
    if cp.label == "geni-al2s":
        remote_endpoint = cp.endpoint

# create a vts non-OF OVS L2 learning image for our forwarding elements
vts_img = VTS.OVSL2Image()

# and create a forwarding element
felement = VTS.Datapath(vts_img, "fe0")
felement.attachPort(VTS.LocalCircuit())
wan_port = felement.attachPort(VTS.GRECircuit("geni-al2s", remote_endpoint))

# create the request
site1r = VTS.Request()
site1r.addResource(felement)

# create sliver and wait for it to be ready (15 mins timeout)
print("-- Creating sliver on ")
site1vts_m = geni.util.createSliver(ctx, site1VTSAM, experiment, site1r)
# }


############
# create site2 VTS
# {

# similarly to how we did it above, but stitch it to site1 VTS
felement = VTS.Datapath(vts_img, "fe0")
felement.attachPort(VTS.LocalCircuit())

# attach a port that connects to the site1 forwarding element
felement.attachPort(
    VTS.GRECircuit(
        "geni-al2s", site1vts_m.findPort(wan_port.clientid).local_endpoint))

site2r = VTS.Request()
site2r.addResource(felement)

site2vts_m = geni.util.createSliver(ctx, site2VTSAM, experiment, site2r)
# }


############
# request nodes
# {
netmask = "255.255.255.0"
client_ip = "10.50.1.1"
server_ip = "10.50.1.2"

# create client node (on site1)
node = IGX.RawPC("client")
node.disk_image = node_img
intf = node.addInterface("if0")
intf.addAddress(PG.IPv4Address(client_ip, netmask))

# create link
lnk = PG.Link()
lnk.addInterface(intf)
lnk.connectSharedVlan(site1vts_m.local_circuits[0])

# create request
site1r = PG.Request()
site1r.addResource(node)
site1r.addResource(lnk)

# request node
site1_m = geni.util.createSliver(ctx, site1AM, experiment, site1r)

# same as above but for server node (on site2)
node = IGX.RawPC("server")
node.disk_image = node_img
intf = node.addInterface("if0")
intf.addAddress(PG.IPv4Address(server_ip, netmask))
lnk = PG.Link()
lnk.addInterface(intf)
lnk.connectSharedVlan(site2vts_m.local_circuits[0])
site2r = PG.Request()
site2r.addResource(node)
site2r.addResource(lnk)
site2_m = geni.util.createSliver(ctx, site2AM, experiment, site1r)
# }


#########
# generate output files
# {
site1vts_m.writeXML(outdir+'/vts-site1-manifest.xml')
site2vts_m.writeXML(outdir+'/vts-site2-manifest.xml')
site1_m.writeXML(outdir+'/site1-manifest.xml')
site2_m.writeXML(outdir+'/site2-manifest.xml')
group_vars = {
    'client:vars': ['client_internal_ip={}'.format(client_ip)],
    'server:vars': ['server_internal_ip={}'.format(server_ip)],
}
geni.util.toAnsibleInventory(site1_m, outdir+'/hosts')
geni.util.toAnsibleInventory(site2_m, outdir+'/hosts', groups=group_vars,
                             append=True)
# }
