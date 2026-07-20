import random
from typing import Tuple
from flowweaver.std.datasets import Dataset, TabularDataset
from flowweaver.std.utils.validation import validate_dataset

def split_dataset(dataset: Dataset, ratio: float = 0.8, seed: int = 42) -> Tuple[Dataset, Dataset]:
    """Split dataset into train/test by ratio. Returns (train_dataset, test_dataset)."""
    validate_dataset(dataset)
    
    if not (0 <= ratio <= 1):
        raise ValueError(f"Ratio must be between 0 and 1, got {ratio}")

    rows = list(dataset.to_list())
    rng = random.Random(seed)
    rng.shuffle(rows)
    
    split_idx = int(len(rows) * ratio)
    train_rows = rows[:split_idx]
    test_rows = rows[split_idx:]
    
    train_dataset = TabularDataset(
        train_rows,
        columns=dataset.columns(),
        metadata=dataset.metadata,
        history=dataset.history
    ).with_history("split_dataset", split="train", ratio=ratio, seed=seed)
    
    test_dataset = TabularDataset(
        test_rows,
        columns=dataset.columns(),
        metadata=dataset.metadata,
        history=dataset.history
    ).with_history("split_dataset", split="test", ratio=ratio, seed=seed)
    
    return train_dataset, test_dataset
