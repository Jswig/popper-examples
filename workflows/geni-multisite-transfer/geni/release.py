import os

import geni.aggregate.instageni as IGAM
import geni.aggregate.vts as VTSAM
import geni.util


ctx = geni.util.loadContext(key_passphrase=os.environ['GENI_KEY_PASSPHRASE'])

experiment = 'popper-examples'
site1VTSAM = VTSAM.UKYPKS2
site1AM = IGAM.UKYPKS2
site2VTSAM = VTSAM.UKYPKS2
site2AM = IGAM.NPS

print("Available slices: {}".format(ctx.cf.listSlices(ctx).keys()))

if geni.util.sliceExists(ctx, experiment):
    print('Slice exists.')
    print('Removing existing slivers on site 1 and 2 (errors are ignored)')
    for am in [site1VTSAM, site1AM, site2VTSAM, site2AM]:
        geni.util.deleteSliverExists(am, ctx, experiment)
else:
    print("Slice does not exist.")
