#########################################
# INFERENCES WITH WATERMARKed GAN
# ADAPT FOR 6G DEMONSTRATION
#########################################
import os
import sys
import random
import numpy as np

# Add utils directory to path
# sys.path.append("./utils")

# Pytorch and image tools
import torch
import torchvision.transforms as transforms

# Custom utilities and models
from .utils.utils_img import unnormalize_vqgan, normalize_img  # Meta functions
from .utils.models_64x64 import Generator, Discriminator
from .utils.loadmodels import load_generator_discriminator
from .utils.utils_hidden import load_hidden


class Content:
    def __init__(self):
        """Initialize models, parameters, and environment."""
        
        #######################################
        " Seed "
        self.requires_data=False
        manualseed = 999
        print(">>> Random Seed:", manualseed)
        random.seed(manualseed)
        torch.manual_seed(manualseed)
        torch.use_deterministic_algorithms(False)
        
        " Device/GPU "
        ngpu = 1
        self.device = torch.device("cuda:0" if (torch.cuda.is_available() and ngpu > 0) else "cpu")
        #######################################

        #######################################
        " Configuration des chemins et paramètres "
        self.config = {
            "device": self.device,
            "batch_size": 1,
            "latent_dim": 100,
            "img_shape": (3, 64, 64),
            "path_weight_generator" : '/app/add_files/weights/generator_best_49.pth',
            "path_weight_discriminator": 'None',
            "path_to_checkpoint": 'None',
            "path_key": '/app/add_files/utils/key.txt',
            "path_hidden_whitened": "/app/add_files/weights/hidden_replicate_whit.pth",
            "numb_bits": 48,
            "redundancy": 1,
            "decoder_depth": 8,
            "decoder_channels": 64
        }
        #######################################

        #######################################
        # Load models, hidden decoder and key
        self._load_models()
        #######################################

    def _load_models(self):
        print("current directory",os.getcwd())
        """Load generator, hidden model and key"""

        #######################################
        # Load Generator + Weights
        self.generator, _, _ = load_generator_discriminator(
            Generator(), Discriminator(),
            self.config["path_to_checkpoint"],
            self.config["path_weight_generator"],
            self.config["path_weight_discriminator"]
        )
        self.generator.to(self.device)
        self.generator.eval()
        for param in self.generator.parameters():
            param.requires_grad = False
        #######################################

        #######################################
        # Load Hidden Decoder
        print(">>> Building hidden decoder ...")
        self.msg_decoder = load_hidden(
            self.config["path_hidden_whitened"],
            self.config["numb_bits"],
            self.config["redundancy"],
            self.config["decoder_depth"],
            self.config["decoder_channels"],
            dataloader=None
        )
        self.msg_decoder.to(self.device)
        self.msg_decoder.eval()
        for param in self.msg_decoder.parameters():
            param.requires_grad = False
        #######################################

        #######################################
        # Load Watermarking Key
        with open(self.config["path_key"], "r") as f:
            key_str = f.read().strip()
        key = torch.tensor([int(bit) for bit in key_str], dtype=torch.float32, device=self.device).unsqueeze(0)
        self.config["key"] = key
        self.config["key_str"] = key_str
        #######################################

    def run(self):
        """Generate watermarked images and decode the watermark"""

        #######################################
        # Latent vector z
        z = torch.tensor(
            np.random.normal(0, 1, (self.config["batch_size"], self.config["latent_dim"])),
            dtype=torch.float32,
            device=self.device
        )
        #######################################

        #######################################
        # Image Generation
        print(">>> Generating images...")
        fake_imgs = self.generator(z)
        #######################################

        #######################################
        # Watermark Decoding
        keys = self.config["key"].repeat(self.config["batch_size"], 1)
        transform = transforms.Compose([unnormalize_vqgan, normalize_img])
        decoded = self.msg_decoder(transform(fake_imgs))
        diff = (~torch.logical_xor(decoded > 0, keys > 0))
        bit_accs = torch.sum(diff, dim=-1) / diff.shape[-1]
        print(">>> Inference completed.")
        #######################################

        #######################################
        # Retrieve image for visualization
        img_ori = (fake_imgs[0].detach().cpu() + 1) / 2.0
        return img_ori, bit_accs.mean().item()
        #######################################
