import torch

flag = torch.cuda.is_available()
if flag:
    print("CUDA 可使用")
else:
    print("CUDA 不可用")

print(torch.cuda.is_available())

# pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118