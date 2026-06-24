import torch
import torch.nn as nn
import torch.optim as optim

class IntrusionNN(nn.Module):
    def __init__(self, input_dim):
        super(IntrusionNN, self).__init__()
        self.layer1 = nn.Linear(input_dim, 16)
        self.layer2 = nn.Linear(16, 8)
        self.output = nn.Linear(8, 1)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x):
        x = torch.relu(self.layer1(x))
        x = torch.relu(self.layer2(x))
        x = self.sigmoid(self.output(x))
        return x

def train_pytorch_model(X_train, y_train):
    # Μετατροπή σε tensors
    X = torch.tensor(X_train.values, dtype=torch.float32)
    y = torch.tensor(y_train.values, dtype=torch.float32).view(-1, 1)
    
    model = IntrusionNN(X.shape[1])
    criterion = nn.BCELoss()
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    for epoch in range(10): # Quick test
        optimizer.zero_grad()
        outputs = model(X)
        loss = criterion(outputs, y)
        loss.backward()
        optimizer.step()
        print(f"Epoch {epoch+1}, Loss: {loss.item():.4f}")
    
    return model