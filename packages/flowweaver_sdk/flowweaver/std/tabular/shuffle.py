import random
from flowweaver.std.datasets import Dataset, TabularDataset
from flowweaver.std.utils.validation import validate_dataset

def shuffle(dataset: Dataset, seed: int = 42) -> Dataset:
    """Randomly shuffle all rows."""
    validate_dataset(dataset)
    
    rows = list(dataset.to_list())
    rng = random.Random(seed)
    rng.shuffle(rows)
    
    res = TabularDataset(
        rows,
        columns=dataset.columns(),
        metadata=dataset.metadata,
        history=dataset.history
    )
    return res.with_history("shuffle", seed=seed)
