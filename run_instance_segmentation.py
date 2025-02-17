import os
import argparse

# Some basic setup:
# Setup detectron2 logger
import detectron2
from detectron2.utils.logger import setup_logger
setup_logger()
setup_logger(name="mask2former")

# import some common libraries
import numpy as np
import cv2
import glob
from PIL import Image
import torch

# import some common detectron2 utilities
from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2.utils.visualizer import Visualizer, ColorMode
from detectron2.data import MetadataCatalog
from detectron2.projects.deeplab import add_deeplab_config
coco_metadata = MetadataCatalog.get("coco_2017_val_panoptic")

# import Mask2Former project
from mask2former import add_maskformer2_config
from pdb import set_trace


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--input", default="input", help="Input path (dir) for images.")
    parser.add_argument("-o", "--output", default="output", help="Output path for output maps.")
    parser.add_argument("-e", "--ext", default="jpg", help="Image extension.")
    parser.add_argument("-s", "--show", action="store_true", help="Image extension.")
    args = parser.parse_args()

    # select device
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print("device: %s" % device)

    # get input
    img_names = glob.glob(os.path.join(args.input, "*." + args.ext))
    num_images = len(img_names)
    print (f"Mask2Former::Debug:: number of images found: {num_images}")
    # set_trace()
    # create output folder
    os.makedirs(args.output, exist_ok=True)

    cfg = get_cfg()
    add_deeplab_config(cfg)
    add_maskformer2_config(cfg)
    cfg.merge_from_file("configs/coco/panoptic-segmentation/swin/maskformer2_swin_large_IN21k_384_bs16_100ep.yaml")
    # cfg.MODEL.WEIGHTS = 'https://dl.fbaipublicfiles.com/maskformer/mask2former/coco/panoptic/maskformer2_swin_large_IN21k_384_bs16_100ep/model_final_f07440.pkl'
    cfg.MODEL.WEIGHTS = '/gemini/data-1/scene-aware-3d-multi-human/tools/Mask2Former/model_final_f07440.pkl'
    cfg.MODEL.MASK_FORMER.TEST.SEMANTIC_ON = True
    cfg.MODEL.MASK_FORMER.TEST.INSTANCE_ON = True
    cfg.MODEL.MASK_FORMER.TEST.PANOPTIC_ON = True
    predictor = DefaultPredictor(cfg)

    print("start processing")
    for ind, img_name in enumerate(img_names):
        if os.path.isdir(img_name):
            continue

        sample_basename = os.path.splitext(os.path.basename(img_name))[0]
        if os.path.exists(os.path.join(args.output, f'{sample_basename}.png')):
            print(os.path.join(args.output, f'{sample_basename}.png'), 'exists...')
            continue
        print("  processing {} ({}/{})".format(img_name, ind + 1, num_images))

        img = cv2.imread(img_name)
        img_h, img_w = img.shape[:2]
        new_dim = (512, 512)
        resized_img = cv2.resize(img, new_dim, interpolation=cv2.INTER_AREA)

        outputs = predictor(resized_img)
        instances = outputs["instances"].to("cpu")
        pred_classes = instances.pred_classes.numpy()
        pred_masks = instances.pred_masks.numpy()   # 256
        scores = instances.scores.numpy()
        print(pred_masks.shape)

        idxs = np.array(range(len(pred_classes)))[pred_classes == 0] # select only "person"
        instances = np.zeros((img_h, img_w), dtype=np.uint8)
        # instances = np.zeros(new_dim, dtype=np.uint8)
        cls_ids = 0
        # set_trace()
        for i in idxs:
            pix_factor = 100 * pred_masks[i].sum() / np.prod(pred_masks[i].shape)
            if scores[i] > 0.7 and pix_factor > 0.5:    # 得分大于0.7且占比大于0.5%
                cls_ids += 1
                sm = (pred_masks[i] > 0).astype(np.uint8)
                #sm = cv2.erode(sm, np.ones((3, 3), sm.dtype))
                # cmask = 255 * sm # 
                cmask = cv2.resize(255 * sm, (img_w, img_h), interpolation=cv2.INTER_LINEAR) # cause grid
                instances[cmask > 127] = cls_ids

        if args.show:
            instances = (instances.astype('float32')* 255 / instances.max()).astype('uint8')
        instances_pil = Image.fromarray(instances)
        instances_pil.save(os.path.join(args.output, f'{sample_basename}.png'))

def getRandomColor(img):
    vmin, vmax = img.min(), img.max()
    r = np.random.randint(0, 256) / 255 * 2 - 1
    g = np.random.randint(0, 256) / 255 * 2 - 1
    b = np.random.randint(0, 256) / 255 * 2 - 1

    return r, g, b
