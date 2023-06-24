import numpy as np
from sklearn.linear_model import LogisticRegression
from wasabi import Printer
from skops.io import dump, load
from pathlib import Path

msg = Printer() 


class SentenceModel:
    def __init__(self, encoder, tasks):
        self._encoder = encoder
        self._tasks = tasks
        self._models = {k: LogisticRegression(class_weight="balanced") for k in self._tasks}

    def update(self, examples):
        X = self._encoder.transform([ex["text"] for ex in examples])
        for task, model in self._models.items():
            xs = np.array([X[i] for i, ex in enumerate(examples) if task in ex])
            ys = np.array(
                [ex[task] for ex in examples if task in ex], dtype=int
            )
            model.fit(xs, ys)
            msg.good(f"Trained the {task} task, using {len(xs)} examples.")

    def __call__(self, text):
        result = {}
        X = self._encoder.transform([text])
        for task in self._tasks:
            proba = self._models[task].predict_proba(X)[0, 1]
            result[task] = float(proba)
        return result

    def to_disk(self, path):
        for name, clf in self._models.items():
            dump(clf, Path(path) / f"{name}.h5")

    @classmethod
    def from_disk(cls, path, encoder):
        models = {}
        for f in Path(path).glob("*.h5"):
            models[f.stem] = load(f, trusted=True)

        model = SentenceModel(encoder=encoder, tasks=models.keys())
        model._models = models
        return model
