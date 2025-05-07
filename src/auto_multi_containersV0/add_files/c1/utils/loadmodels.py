# loadmodels.py
import os
import torch


'''
Function for loading weights of GAN
'''

def load_generator_discriminator(generator, discriminator, path_to_checkpoint,path_weight_generator,path_weight_discriminator):
    print(f">>Loading Model")


    ext_ckpt = os.path.splitext(path_to_checkpoint)[1]
    ext_pth = os.path.splitext(path_weight_generator)[1]

    if ext_ckpt == '.ckpt':
        print(f">>Loading checkpoint")
        ckpt = torch.load(path_to_checkpoint, map_location='cpu')
        if 'G' in ckpt and 'D' in ckpt:
            generator.load_state_dict(ckpt['G'])
            discriminator.load_state_dict(ckpt['D'])
            start_epoch = ckpt.get('epoch', 0)
            print(f"Checkpoint loaded (epoch {start_epoch})")
        else:
            raise ValueError("Missing 'G' or 'D' keys in the checkpoint.")
    
    elif ext_pth == '.pth':
        print(f">>Loading pth")
        generator.load_state_dict(torch.load(path_weight_generator))
        print(f"Generator weights loaded from {path_weight_generator}")
        if path_weight_discriminator != 'None':
            discriminator.load_state_dict(torch.load(path_weight_discriminator))
            print(f"Discriminator weights loaded from {path_weight_discriminator}")
        start_epoch = 0  # Or None if epoch not tracked in .pth
    else:
        print("Training from scratch")
        start_epoch = 0 
    
    return generator, discriminator, start_epoch