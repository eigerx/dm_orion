import numpy as np
from lsst.daf.butler import Butler
import lsst.meas.extensions.scarlet as mes
import yaml

butler = Butler(
    "/repo/main",
    collections=["u/eiger/DM-42258", "HSC/runs/RC2/w_2023_39/DM-40985"],
    skymap="hsc_rings_v1",
)

# Set these appropriately for the visits that you need.
# I don't know off hand how to find the visits that went into the
# coadd, but if you don't and can't find help on slack,
# ping me and I'l try to help.
detectors_visits = [(41, 26050), (51, 23888), (75, 24522), (18, 26036), (23, 26060),
                    (85, 424), (32, 36416), (74, 24494), (103, 27116), (102, 19712),
                    (96, 1324), (103, 11738)]

output_dict = {}
for detector, visit in detectors_visits:
    results = butler.registry.queryDataIds(dimensions=['tract', 'patch', 'band', 'visit', 'detector'],
                                           where=f"instrument='HSC' and skymap='hsc_rings_v1' "
                                           f"and detector={detector} and visit={visit} "
                                           f"and tract in (9615, 9813, 9697)",
                                           collections=["u/eiger/DM-42258", "HSC/runs/RC2/w_2023_39/DM-40985"],
                                           datasets='calexp'
                                          )
    for result in results:
        # Load the forced source catalog
        catalog = butler.get("deepCoadd_forced_src", result)
        # Load the ScarletModelData that contains all of the scarlet models
        modelData = butler.get("deepCoadd_scarletModelData", result)
        # Load the PSF model
        psfModel = butler.get("deepCoadd_calexp.psf", result)
        # Load the observed image
        image = butler.get("deepCoadd_calexp.image", result)
        # Update the footprints for all of the deblended sources.
        modelData.updateCatalogFootprints(catalog, result["band"], psfModel=psfModel,redistributeImage=image, updateFluxColumns=False)

        # Get all of the child footprints
        # (the parents are not HeavyFootprints so are irrelevant)
        footprints = [src.getFootprint() for src in catalog[catalog["parent"] != 0]]
        area = [fp.getArea() for fp in footprints]
        print(f"The minimum area is {np.min(area)} for {result}")
        if np.min(area) > 0:
            output_dict.extend({"detector": detector, "visit": visit, "tract": result["tract"], "patch": result["patch"],
                                "band": result["band"], "min_area":np.min(area)})


with open("results.yaml", "w") as stream:
    yaml.dump(output_dict, stream)
