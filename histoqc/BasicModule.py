import logging
import os
from histoqc.BaseImage import printMaskHelper
from skimage.morphology import remove_small_objects, binary_opening, disk
from skimage import io, color, img_as_ubyte

import matplotlib.pyplot as plt


def getBasicStats(s, params):
    logging.info(f"{s['filename']} - \tgetBasicStats")
    osh = s["metadata"]
    s.addToPrintList("type", osh['vendor'])
    s.addToPrintList("levels", osh['level_count'])
    s.addToPrintList("height", osh['level_dimensions'][0][1])
    s.addToPrintList("width", osh['level_dimensions'][0][0])
    s.addToPrintList("mpp_x", osh['mpp'][1])
    s.addToPrintList("mpp_y", osh['mpp'][0])
    s.addToPrintList("comment", "NA")
    return


def finalComputations(s, params):
    mask = s["img_mask_use"]
    s.addToPrintList("pixels_to_use", str(len(mask.nonzero()[0])))


def finalProcessingSpur(s, params):
    logging.info(f"{s['filename']} - \tfinalProcessingSpur")
    disk_radius = int(params.get("disk_radius", "25"))
    selem = disk(disk_radius)
    mask = s["img_mask_use"]
    mask_opened = binary_opening(mask, selem)
    mask_spur = ~mask_opened & mask

    io.imsave(s["outdir"] + os.sep + s["filename"] + "_spur.png", img_as_ubyte(mask_spur))

    prev_mask = s["img_mask_use"]
    s["img_mask_use"] = mask_opened

    s.addToPrintList("spur_pixels",
                     printMaskHelper(params.get("mask_statistics", s["mask_statistics"]), prev_mask, s["img_mask_use"]))

    if len(s["img_mask_use"].nonzero()[0]) == 0:  # add warning in case the final tissue is empty
        logging.warning(
            f"{s['filename']} - After BasicModule.finalProcessingSpur NO tissue remains detectable! Downstream modules likely to be incorrect/fail")
        s["warnings"].append(
            f"After BasicModule.finalProcessingSpur NO tissue remains detectable! Downstream modules likely to be incorrect/fail")


def finalProcessingArea(s, params):
    logging.info(f"{s['filename']} - \tfinalProcessingArea")
    area_thresh = int(params.get("area_threshold", "1000"))
    mask = s["img_mask_use"]

    mask_opened = remove_small_objects(mask, min_size=area_thresh)
    mask_removed_area = ~mask_opened & mask

    io.imsave(s["outdir"] + os.sep + s["filename"] + "_areathresh.png", img_as_ubyte(mask_removed_area))

    prev_mask = s["img_mask_use"]
    s["img_mask_use"] = mask_opened > 0

    s.addToPrintList("areaThresh",
                     printMaskHelper(params.get("mask_statistics", s["mask_statistics"]), prev_mask, s["img_mask_use"]))

    if len(s["img_mask_use"].nonzero()[0]) == 0:  # add warning in case the final tissue is empty
        logging.warning(
            f"{s['filename']} - After BasicModule.finalProcessingArea NO tissue remains detectable! Downstream modules likely to be incorrect/fail")
        s["warnings"].append(
            f"After BasicModule.finalProcessingArea NO tissue remains detectable! Downstream modules likely to be incorrect/fail")
