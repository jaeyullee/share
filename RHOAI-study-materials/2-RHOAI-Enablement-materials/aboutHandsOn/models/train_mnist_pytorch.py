#!/usr/bin/env python3
"""
Day 2(PyTorch 모델 배포) — PyTorch(MNIST) 모델.

curriculum v0.9 Day 2: "PyTorch(MNIST) 모델 배포". CPU에서 1~2 epoch면 충분(경로 체득용).
TorchServe(.mar) 대신, KServe(Serverless 모드)에서 쓰기 쉬운 경로 2가지를 모두 출력:
  mnist/model.pt          # state_dict (참고/재학습용)
  mnist/1/model.onnx      # OVMS/ONNX 런타임으로 바로 서빙(권장, CPU 친화)
  mnist/sample_request.json

MNIST 데이터는 torchvision이 자동 다운로드(connected SNO 가정).
폐쇄망이면 datasets/ 아래로 미리 받아두고 root 경로를 바꾼다.
패키지: torch, torchvision, onnx
"""
import json
import os

OUTDIR = os.path.join(os.path.dirname(__file__), "mnist")


def main():
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    from torch.utils.data import DataLoader
    from torchvision import datasets, transforms

    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            self.conv1 = nn.Conv2d(1, 16, 3, 1)
            self.conv2 = nn.Conv2d(16, 32, 3, 1)
            self.fc1 = nn.Linear(32 * 12 * 12, 64)
            self.fc2 = nn.Linear(64, 10)

        def forward(self, x):
            x = F.relu(self.conv1(x))
            x = F.relu(self.conv2(x))
            x = F.max_pool2d(x, 2)
            x = torch.flatten(x, 1)
            x = F.relu(self.fc1(x))
            return self.fc2(x)

    tfm = transforms.Compose([transforms.ToTensor(),
                              transforms.Normalize((0.1307,), (0.3081,))])
    root = os.path.join(os.path.dirname(__file__), "../datasets/_mnist_cache")
    train = datasets.MNIST(root, train=True, download=True, transform=tfm)
    loader = DataLoader(train, batch_size=64, shuffle=True)

    model = Net()
    opt = torch.optim.Adam(model.parameters(), lr=1e-3)
    model.train()
    for epoch in range(1):  # CPU: 1 epoch ~ 충분히 동작 확인
        for i, (x, y) in enumerate(loader):
            opt.zero_grad()
            loss = F.cross_entropy(model(x), y)
            loss.backward()
            opt.step()
            if i % 200 == 0:
                print(f"epoch{epoch} step{i} loss={loss.item():.3f}")

    os.makedirs(os.path.join(OUTDIR, "1"), exist_ok=True)
    torch.save(model.state_dict(), os.path.join(OUTDIR, "model.pt"))

    model.eval()
    dummy = torch.randn(1, 1, 28, 28)
    torch.onnx.export(model, dummy, os.path.join(OUTDIR, "1", "model.onnx"),
                      input_names=["input"], output_names=["output"],
                      dynamic_axes={"input": {0: "batch"}, "output": {0: "batch"}},
                      opset_version=17)

    req = {"inputs": [{"name": "input", "shape": [1, 1, 28, 28],
                       "datatype": "FP32", "data": dummy.flatten().tolist()}]}
    json.dump(req, open(os.path.join(OUTDIR, "sample_request.json"), "w"))
    print(f"saved -> {OUTDIR}/model.pt, 1/model.onnx, sample_request.json")


if __name__ == "__main__":
    main()
