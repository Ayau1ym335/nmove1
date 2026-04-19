"""app/ml/autoencoder.py — Feedforward autoencoder for per-user gait anomaly detection.

Architecture (input dim = 12):
    Encoder: Linear(12→24) → ReLU → Linear(24→12) → ReLU → Linear(12→6)
    Decoder: Linear(6→12)  → ReLU → Linear(12→24) → ReLU → Linear(24→12)

The bottleneck (6-dim) is half the input, forcing the model to learn a compact
representation of the user's normal gait pattern.

Training:
    - Loss  : MSE reconstruction
    - Optim : Adam (lr=1e-3)
    - Epochs: up to 500, with early stopping at loss < 1e-5
    - Batch : full-batch (sessions fit in memory easily)

Persistence:
    - Model and scaler serialised with pickle via io.BytesIO
    - Uploaded to MinIO; never written to local disk

Anomaly scoring:
    reconstruction_error(x) = MSE(x, decoder(encoder(x)))
    Higher error → session looks anomalous relative to the user's baseline.
"""

from __future__ import annotations

import io
import logging
import pickle

import numpy as np
import torch
import torch.nn as nn
from torch.optim.adam import Adam

logger = logging.getLogger("nmove.ml.autoencoder")

INPUT_DIM      = 12   
HIDDEN_DIM_1   = 24     
HIDDEN_DIM_2   = 12    
BOTTLENECK_DIM = 6       

LR             = 1e-3
MAX_EPOCHS     = 500
EARLY_STOP_LOSS = 1e-5

class GaitAutoencoder(nn.Module):
    """Symmetric feedforward autoencoder for gait feature reconstruction.

    Architecture:
        Encoder: 12 → 24 → ReLU → 12 → ReLU → 6
        Decoder:  6 → 12 → ReLU → 24 → ReLU → 12
    """

    def __init__(self, input_dim: int = INPUT_DIM) -> None:
        super().__init__()
        hd1 = HIDDEN_DIM_1
        hd2 = HIDDEN_DIM_2
        bn  = BOTTLENECK_DIM

        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hd1),
            nn.ReLU(),
            nn.Linear(hd1, hd2),
            nn.ReLU(),
            nn.Linear(hd2, bn),
        )
        self.decoder = nn.Sequential(
            nn.Linear(bn, hd2),
            nn.ReLU(),
            nn.Linear(hd2, hd1),
            nn.ReLU(),
            nn.Linear(hd1, input_dim),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:  # type: ignore[override]
        return self.decoder(self.encoder(x))

    def reconstruction_error(self, x: torch.Tensor) -> torch.Tensor:
        """Per-sample MSE reconstruction error. Shape: (batch,)"""
        with torch.no_grad():
            recon = self.forward(x)
            return ((recon - x) ** 2).mean(dim=1)

def train_autoencoder(
    X_norm: np.ndarray,
) -> tuple[GaitAutoencoder, list[float]]:
    """Train a fresh GaitAutoencoder on *X_norm* (already normalised).

    Parameters
    ----------
    X_norm : np.ndarray, shape (n_sessions, 12), float32
        Normalised feature matrix from ``features.apply_scaler``.

    Returns
    -------
    model : GaitAutoencoder  — trained model in eval mode
    losses : list[float]     — training loss per epoch
    """
    device = torch.device("cpu")   # worker containers may lack GPU
    model = GaitAutoencoder(input_dim=X_norm.shape[1]).to(device)
    optimizer = Adam(model.parameters(), lr=LR)
    criterion = nn.MSELoss()

    X_tensor = torch.tensor(X_norm, dtype=torch.float32).to(device)

    losses: list[float] = []
    model.train()
    for epoch in range(MAX_EPOCHS):
        optimizer.zero_grad()
        recon = model(X_tensor)
        loss = criterion(recon, X_tensor)
        loss.backward()
        optimizer.step()

        loss_val = float(loss.item())
        losses.append(loss_val)

        if loss_val < EARLY_STOP_LOSS:
            logger.debug("Early stop at epoch %d, loss=%.6f", epoch, loss_val)
            break

    model.eval()
    logger.info(
        "Autoencoder trained: %d epochs, final_loss=%.6f, n_sessions=%d",
        len(losses), losses[-1], X_norm.shape[0],
    )
    return model, losses

def model_to_bytes(model: GaitAutoencoder) -> bytes:
    """Serialise model state_dict to a bytes object (pickle-compatible)."""
    buf = io.BytesIO()
    torch.save(model.state_dict(), buf, pickle_protocol=pickle.HIGHEST_PROTOCOL)
    return buf.getvalue()


def model_from_bytes(data: bytes) -> GaitAutoencoder:
    """Deserialise a GaitAutoencoder from bytes produced by :func:`model_to_bytes`."""
    buf = io.BytesIO(data)
    state_dict = torch.load(buf, map_location="cpu", weights_only=True)
    model = GaitAutoencoder()
    model.load_state_dict(state_dict)
    model.eval()
    return model


def scaler_to_bytes(scaler: np.ndarray) -> bytes:
    """Serialise the (2, FEATURE_DIM) numpy scaler array to bytes."""
    buf = io.BytesIO()
    np.save(buf, scaler)
    return buf.getvalue()


def scaler_from_bytes(data: bytes) -> np.ndarray:
    """Deserialise the numpy scaler array from bytes."""
    buf = io.BytesIO(data)
    return np.load(buf)


def score_session(
    feature_row: np.ndarray,
    model: GaitAutoencoder,
    scaler: np.ndarray,
) -> float:
    """Return the reconstruction error for a single session's feature vector.

    Parameters
    ----------
    feature_row : np.ndarray, shape (12,), raw (non-normalised)
    model       : trained GaitAutoencoder
    scaler      : (2, 12) numpy array from :func:`features.fit_scaler`

    Returns
    -------
    float — reconstruction MSE (higher = more anomalous)
    """
    from app.ml.features import apply_scaler

    row_norm = apply_scaler(feature_row[np.newaxis, :], scaler)   # (1, 12)
    x = torch.tensor(row_norm, dtype=torch.float32)
    error = model.reconstruction_error(x)
    return float(error.item())
