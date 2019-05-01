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

# experiment variables (TODO: expose them in plain text in workflow folder)
# {
experiment = "popper-examples"
node_img = "urn:publicid:IDN+emulab.net+image+emulab-ops:UBUNTU16-64-STD"
outdir = os.path.dirname(os.path.realpath(__file__))

# create variables to hold VTS and regular aggregate managers (AM). These can
# be assigned other VTSAM/AM values defined here:
#    https://bitbucket.org/barnstorm/geni-lib/src/1b480c83581207300f73679af6844d327794d45e/geni/aggregate/vts.py?at=0.9-DEV#lines-331:336
site1VTSAM = VTSAM.UKYPKS2
site2VTSAM = VTSAM.NPS
site1AM = IGAM.UKYPKS2
site2AM = IGAM.NPS
# }

# load context and create slice for experiment
ctx = geni.util.loadContext(key_passphrase=os.environ['GENI_KEY_PASSPHRASE'])

geni.util.createSlice(ctx, experiment)

# delete slivers if they already exist
print("-- Deleting any existing slivers")
for am in [site1VTSAM, site1AM, site2VTSAM, site2AM]:
    print("--  * " + am.name)
    try:
        am.deletesliver(ctx, experiment)
    except Exception as e:
        print("-- Error: {}".format(e))


############
# create VTS on site1
# {

# search circuit plane on site2's advertisement (by endpoint label) and create
# a WAN port so we can request a forwarding element
print("-- Getting VTS advertisement for " + site2VTSAM.name)
remote_ad = site2VTSAM.listresources(ctx)
remote_wan_port = None
for cp in remote_ad.circuit_planes:
    if cp.label == "geni-al2s":
        remote_wan_port = VTS.GRECircuit("geni-al2s", cp.endpoint)

if not remote_wan_port:
    raise Exception(
        "Could not find 'geni-al2s' circuit plane on " + site2VTSAM.name)

# create a vts non-OF OVS L2 image for our forwarding elements
vts_img = VTS.OVSL2Image()

# create a path with a local port (to connect to the node we will later below)
# and the WAN port we created above
dp = VTS.Datapath(vts_img, "fe0")
dp.attachPort(VTS.LocalCircuit())
dp.attachPort(remote_wan_port)

# create the request
site1_r = VTS.Request()
site1_r.addResource(dp)

# create sliver and wait for it to be ready (15 mins timeout)
print("-- Creating WAN tunnel on " + site1VTSAM.name)
site1vts_m = geni.util.createSliver(ctx, site1VTSAM, experiment, site1_r)
# }


############
# create VTS on site2
# {

# create an endpoint and stitch it to the wan port from site 1
dp = VTS.Datapath(vts_img, "fe0")
dp.attachPort(VTS.LocalCircuit())
dp.attachPort(
    VTS.GRECircuit(
        "geni-al2s",
        site1vts_m.findPort(remote_wan_port.clientid).local_endpoint))

site2_r = VTS.Request()
site2_r.addResource(dp)

print("-- Request VTS resource for {} (stitch to {})".format(site2VTSAM.name,
                                                             site1VTSAM.name))
site2vts_m = geni.util.createSliver(ctx, site2VTSAM, experiment, site2_r)
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
site1_r = PG.Request()
site1_r.addResource(node)
site1_r.addResource(lnk)

# request node
site1_m = geni.util.createSliver(ctx, site1AM, experiment, site1_r)

# same as above but for server node (on site2)
node = IGX.RawPC("server")
node.disk_image = node_img
intf = node.addInterface("if0")
intf.addAddress(PG.IPv4Address(server_ip, netmask))
lnk = PG.Link()
lnk.addInterface(intf)
lnk.connectSharedVlan(site2vts_m.local_circuits[0])
site2_r = PG.Request()
site2_r.addResource(node)
site2_r.addResource(lnk)
site2_m = geni.util.createSliver(ctx, site2AM, experiment, site2_r)
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
geni.util.toAnsibleInventory(
    site2_m, outdir+'/hosts', groups=group_vars, append=True)
# }
