# hidden_utils.py

" Librairies "
import os
import torch
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from .loss_provider import LossProvider 
from . import utils_model

" Device/GPU "
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# Function which load the hidden whitened model

def load_hidden(path_hidden_whitened,num_bits,redundancy,decoder_depth,decoder_channels, dataloader):
    
    # If the whitened specific version extist
    if os.path.exists(path_hidden_whitened):
        msg_decoder = torch.jit.load(path_hidden_whitened).to(device)
        print(">>> TorchScript model loaded with whitening.")
   
   # Else generate it before loading
    else:
        print(f'>> Whitening Hidden % the dataset')
        msg_decoder = utils_model.get_hidden_decoder(num_bits=num_bits, redundancy=redundancy, num_blocks=decoder_depth, channels=decoder_channels).to(device)
        ckpt = utils_model.get_hidden_decoder_ckpt(msg_decoder_path)
        msg_decoder.load_state_dict(ckpt, strict=False)
        msg_decoder.eval()

        with torch.no_grad():
            ys = []
            for i, (x, _) in enumerate(dataloader):
                x = x.to(device)
                y = msg_decoder(x)
                ys.append(y.to('cpu'))
            ys = torch.cat(ys, dim=0)
            nbit = ys.shape[1]
            mean = ys.mean(dim=0, keepdim=True)
            ys_centered = ys - mean
            cov = ys_centered.T @ ys_centered
            e, v = torch.linalg.eigh(cov)
            L = torch.diag(1.0 / torch.pow(e, exponent=0.5))
            weight = torch.mm(L, v.T)
            bias = -torch.mm(mean, weight.T).squeeze(0)
            linear = nn.Linear(nbit, nbit, bias=True)
            linear.weight.data = np.sqrt(nbit) * weight
            linear.bias.data = np.sqrt(nbit) * bias
            msg_decoder = nn.Sequential(msg_decoder, linear.to(device))
            torchscript_m = torch.jit.script(msg_decoder)
            msg_decoder_path = msg_decoder_path.replace(".pth", "_whit.pth")
            print(f'>> Creating torchscript at {msg_decoder_path}...')
            torch.jit.save(torchscript_m, msg_decoder_path)
    return msg_decoder


# Function which initialize losses used for finetunning
def loss_initialization(loss_w, loss_i):
    if loss_w == 'mse':        
        loss_w = lambda decoded, keys, temp=10.0: torch.mean((decoded*temp - (2*keys-1))**2)
    elif loss_w == 'bce':
        loss_w = lambda decoded, keys, temp=10.0: F.binary_cross_entropy_with_logits(decoded*temp, keys, reduction='mean')
    else:
        raise NotImplementedError
    if loss_i == 'mse':
        loss_i = lambda imgs_w, imgs: torch.mean((imgs_w - imgs)**2)
    elif loss_i in ['watson-dft', 'watson-vgg', 'ssim']:
        provider = LossProvider()
        loss_percep = provider.get_loss_function(loss_i.replace('-', '-').upper(), colorspace='RGB', pretrained=True, reduction='sum')
        loss_percep = loss_percep.to(device)
        loss_i = lambda imgs_w, imgs: loss_percep((1+imgs_w)/2.0, (1+imgs)/2.0)/ imgs_w.shape[0]
    else:
        raise NotImplementedError
    return loss_w, loss_i





