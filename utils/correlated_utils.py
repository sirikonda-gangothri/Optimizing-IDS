import pandas as pd
import numpy as np

def CORRELATED(df1):
    X = df1.drop('Label', axis=1)

    # Step 1: Remove features with zero standard deviation
    zero_std_features = [col for col in X.columns if X[col].std() == 0]
    X = X.drop(columns=zero_std_features)

    # Step 2: Remove highly correlated features
    correlation_matrix = X.corr().abs()
    upper_triangle = correlation_matrix.where(np.triu(np.ones(correlation_matrix.shape), k=1).astype(bool))

    highly_correlated_features = set()
    for column in upper_triangle.columns:
        correlated_cols = upper_triangle.index[upper_triangle[column] == 1].tolist()
        for col in correlated_cols:
            if col not in highly_correlated_features:
                highly_correlated_features.add(column)

    X = X.drop(columns=highly_correlated_features)

    # Step 3: Remove redundant features (identical columns)
    # duplicate_features = X.T.duplicated()
    # redundant_features = X.columns[duplicate_features].tolist()
    # X = X.loc[:, ~duplicate_features]

    # Keep the label column
    X['Label'] = df1['Label']

    removed_features = {
        "zero_std": zero_std_features,
        "highly_correlated": list(highly_correlated_features),
        
    }
    return X, removed_features