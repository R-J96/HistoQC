import logging
import os
import numpy as np
import inspect
import zlib, dill
from distutils.util import strtobool

#os.environ['PATH'] = 'C:\\research\\openslide\\bin' + ';' + os.environ['PATH'] #can either specify openslide bin path in PATH, or add it dynamically
import openslide
from tiatoolbox.wsicore.wsireader import get_wsireader


def printMaskHelper(type, prev_mask, curr_mask):
    if type == "relative2mask":
        if len(prev_mask.nonzero()[0]) == 0:
            return str(-100)
        else:
            return str(1 - len(curr_mask.nonzero()[0]) / len(prev_mask.nonzero()[0]))
    elif type == "relative2image":
        return str(len(curr_mask.nonzero()[0]) / np.prod(curr_mask.shape))
    elif type == "absolute":
        return str(len(curr_mask.nonzero()[0]))
    else:
        return str(-1)


# this function is seperated out because in the future we hope to have automatic detection of
# magnification if not present in open slide, and/or to confirm openslide base magnification
def getMag(s, params):
    logging.info(f"{s['filename']} - \tgetMag")
    # TODO: refactor variable names here
    osh = s["metadata"]
    # osh = s["os_handle"]
    # mag = osh.properties.get("openslide.objective-power", "NA")
    mag = osh["objective_power"]
    if (
            mag == "NA"):  # openslide doesn't set objective-power for all SVS files: https://github.com/openslide/openslide/issues/247
        mag = osh.properties.get("aperio.AppMag", "NA")
    if (mag == "NA" or strtobool(
            params.get("confirm_base_mag", "False"))):
        # do analysis work here
        logging.warning(f"{s['filename']} - Unknown base magnification for file")
        s["warnings"].append(f"{s['filename']} - Unknown base magnification for file")
    else:
        mag = float(mag)

    return mag


class BaseImage(dict):

    def __init__(self, fname, fname_outdir, params):
        dict.__init__(self)

        self.in_memory_compression = strtobool(params.get("in_memory_compression", "False"))

        self["warnings"] = ['']  # this needs to be first key in case anything else wants to add to it
        self["output"] = []

        # these 2 need to be first for UI to work
        self.addToPrintList("filename", os.path.basename(fname))
        self.addToPrintList("comments", " ")

        self["outdir"] = fname_outdir
        self["dir"] = os.path.dirname(fname)

        self["os_handle"] = get_wsireader(fname)
        self["metadata"] = self["os_handle"].info.as_dict()
        self["image_base_size"] = self["metadata"]['slide_dimensions']
        self["image_work_size"] = params.get("image_work_size", "1.25x")
        self["mask_statistics"] = params.get("mask_statistics", "relative2mask")
        self["base_mag"] = getMag(self, params)
        self.addToPrintList("base_mag", self["base_mag"])

        mask_statistics_types = ["relative2mask", "absolute", "relative2image"]
        if (self["mask_statistics"] not in mask_statistics_types):
            logging.error(
                f"mask_statistic type '{self['mask_statistics']}' is not one of the 3 supported options relative2mask, absolute, relative2image!")
            exit()

        self["img_mask_use"] = np.ones(self.getImgThumb(self["image_work_size"]).shape[0:2], dtype=bool)
        self["img_mask_force"] = []

        self["completed"] = []

    def __getitem__(self, key):
        value = super(BaseImage, self).__getitem__(key)
        if hasattr(self,"in_memory_compression") and  self.in_memory_compression and key.startswith("img"):
            value = dill.loads(zlib.decompress(value))
        return value

    def __setitem__(self, key, value):
        if hasattr(self,"in_memory_compression") and self.in_memory_compression and key.startswith("img"):
            value = zlib.compress(dill.dumps(value), level=5)

        return super(BaseImage, self).__setitem__(key,value)

    def addToPrintList(self, name, val):
        self[name] = val
        self["output"].append(name)

    def getImgThumb(self, dim):
        key = "img_" + str(dim)
        if key not in self:
            osh = self["os_handle"]
            if dim.replace(".", "0", 1).isdigit(): #check to see if dim is a number
                dim = float(dim)
            elif "X" in dim.upper():  # specifies a desired operating magnification

                base_mag = self["base_mag"]
                if base_mag != "NA":  # if base magnification is not known, it is set to NA by basic module
                    base_mag = float(base_mag)
                else:  # without knowing base mag, can't use this scaling, push error and exit
                    logging.error(
                        f"{self['filename']}: Has unknown or uncalculated base magnification, cannot specify magnification scale: {base_mag}! Did you try getMag?")
                    return -1

                target_mag = float(dim.upper().split("X")[0])
                
                output = osh.slide_thumbnail(resolution=float(dim.replace("x","",1)))
                self[key] = output
            else:
                logging.error(
                    f"{self['filename']}: Unknown image level setting: {dim}!")
                return -1
        return self[key]
    
# if __name__ == '__main__':
#     import configparser
#     file_name = "/data/UHCW/WSIs_jp2/wsi_test/H05-20260_A1LEV1-3_1.jp2"
#     fname_outdir = "./test/output"
#     config_test = configparser.ConfigParser()
#     config_test.read_file(open('/home/robj/Projects/HistoQC/histoqc/config/config_first.ini'))
#     # config_test = [('image_work_size', '1.25x'), ('mask_statistics', 'relative2mask'), ('confirm_base_mag', 'False')]
#     test = BaseImage(file_name, fname_outdir, dict(config_test.items("BaseImage.BaseImage")))
#     print(test['base_mag'])
