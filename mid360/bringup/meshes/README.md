# Livox MID-360S visual model

Source: Livox official MID-360S STEP model (2026-04-15).
- Download page: https://www.livoxtech.com/mid-360s/downloads
- STEP: https://terra-1-g.djicdn.com/65c028cd298f4669a7f0e40e50ba1131/Mid-360S/Mid-360S%203D%20Model/mid-360S.stp
- Coordinate and dimension reference: Livox MID-360S User Manual, pages 16 and 19.

The attached sensor reports the SDK device type Mid360s. Geometry was tessellated
from the manufacturer CAD and simplified to 69,067 triangles for RViz. The STL
uses metres and the Livox point-cloud frame; no URDF mesh scale is required.

CAD +X points toward the connector, +Y upward. The converted mesh uses
X=-CAD_X, Y=CAD_Z, Z=CAD_Y-0.02108289835 metres (after converting mm to m).
This puts the optical origin 47 mm above the bottom face, and +X away from the
connector, following the manufacturer's drawings. Body bounds are approximately
65 x 65 x 60 mm, with the connector extending in -X. See mid360s-metadata.json
for source and output hashes and the conversion matrix.

The mesh changes visual geometry only. Mounting TF remains in the robot config.
Original CAD rights remain with Livox; conversion does not relicense that asset.
