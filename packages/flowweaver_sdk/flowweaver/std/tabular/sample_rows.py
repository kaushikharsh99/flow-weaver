import random
from flowweaver.std.datasets import Dataset, TabularDataset
from flowweaver.std.utils.validation import validate_dataset

def sample_rows(dataset: Dataset, n: int = 100, seed: int = 42) -> Dataset:
    """Randomly sample N rows from dataset."""
    validate_dataset(dataset)
    
    rows = dataset.to_list()
    rng = random.Random(seed)
    
    sampled = rng.sample(rows, min(n, len(rows)))
    
    res = TabularDataset(
        sampled,
        columns=dataset.columns(),
        metadata=dataset.metadata,
        history=dataset.history
    )
    return res.with_history("sample_rows", n=n, seed=seed)
