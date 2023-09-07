import numpy as np


def mds(d, dimensions=3):
    """
    Multidimensional Scaling - Given a matrix of interpoint distances,
    find a set of low dimensional points that have similar interpoint
    distances.
    """

    print("... ... matrix size: " + str(d.shape))

    E = (-0.5 * d ** 2)

    # Use mat to get column and row means to act as column and row means.
    Er = np.mat(np.mean(E, 1))
    Es = np.mat(np.mean(E, 0))

    # From Principles of Multivariate Analysis: A User's Perspective (page 107).
    F = np.array(E - np.transpose(Er) - Es + np.mean(E))

    print("... ... start svd with dim: " + str(F.shape))

    [U, S, V] = np.linalg.svd(F)

    print("... ... calculated svd")

    Y = U * np.sqrt(S)

    return (Y[:, 0:dimensions], S)
