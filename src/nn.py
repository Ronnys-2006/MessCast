"""Deep feed-forward network (MLP) for tabular demand forecasting, wrapped as a scikit-learn estimator.
Several members with different random initialisations are averaged (a small deep ensemble) because the
dataset is tiny and a single network is noisy."""
import warnings
import numpy as np
from sklearn.base import BaseEstimator, RegressorMixin
from sklearn.exceptions import ConvergenceWarning
from sklearn.neural_network import MLPRegressor


class MLPEnsemble(BaseEstimator, RegressorMixin):
    def __init__(self, hidden_layer_sizes=(64, 32), alpha=1e-3, learning_rate_init=3e-3,
                 n_members=5, max_iter=600, random_state=42):
        self.hidden_layer_sizes = hidden_layer_sizes
        self.alpha = alpha
        self.learning_rate_init = learning_rate_init
        self.n_members = n_members
        self.max_iter = max_iter
        self.random_state = random_state

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        y = np.asarray(y, dtype=float)
        self.mu_ = X.mean(axis=0)
        self.sd_ = X.std(axis=0) + 1e-8          # standardise inputs
        self.y_scale_ = 1000.0                    # keep targets around 0.2 - 1.0 for stable training
        Z = (X - self.mu_) / self.sd_
        self.members_ = []
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ConvergenceWarning)
            for i in range(self.n_members):
                m = MLPRegressor(hidden_layer_sizes=self.hidden_layer_sizes, activation="relu", solver="adam",
                                 alpha=self.alpha, learning_rate_init=self.learning_rate_init,
                                 max_iter=self.max_iter, n_iter_no_change=40, tol=1e-6,
                                 random_state=self.random_state + i)
                self.members_.append(m.fit(Z, y / self.y_scale_))
        return self

    def predict(self, X):
        Z = (np.asarray(X, dtype=float) - self.mu_) / self.sd_
        return np.mean([m.predict(Z) for m in self.members_], axis=0) * self.y_scale_

    @property
    def loss_curve_(self):
        return self.members_[0].loss_curve_
