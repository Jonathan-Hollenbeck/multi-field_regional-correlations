import numpy as np
import random


# this hole algorithm is based on the paper: https://graphics.stanford.edu/courses/cs468-05-winter/Papers/Landmarks/Silva_landmarks5.pdf
# by Vin de Silva & Joshua B. Tenenbaum
def landmark_mds(dist_matrix, n, dim):
    # Select n landmarks (randomnly) by reordering the array randomnly
    landmark_sample = np.sort(random.sample(range(0, dist_matrix.shape[0], 1), n))
    d = dist_matrix[landmark_sample, :]
    d = d[:, landmark_sample]
    print("... ... selected landmarks")
    print("... ... matrix size: " + str(d.shape))

    # Apply classical mds on subset of points
    myn = np.mean(np.square(d), axis=0)

    print("... ... calculated myn")

    E = (-0.5 * d ** 2)

    # Use mat to get column and row means to act as column and row means.
    Er = np.mat(np.mean(E, 1))
    Es = np.mat(np.mean(E, 0))

    # From Principles of Multivariate Analysis: A User's Perspective (page 107).
    F = np.array(E - np.transpose(Er) - Es + np.mean(E))

    print("... ... start svd with dim: " + str(F.shape))

    [U, S, V] = np.linalg.svd(F)

    print("... ... calculated svd")

    # calculate embedding of landmarks
    Y = U[:, 0:dim] * np.sqrt(S[0:dim])
    print("... ... embedded landmarks")

    if len(S) < dim:
        return None
    if S[dim - 1] < 0:
        return None

    # distance based triangulation
    Lsharp = U[:, 0:dim] / np.sqrt(S[0:dim])

    X = np.zeros((dist_matrix.shape[0], dim))
    point_dist = np.transpose((np.square(dist_matrix[:, landmark_sample]) - myn) / 2)
    for i in range(dim):
        X[:, i] = np.matmul(- Lsharp[:, i], point_dist)
        # fix rotation error
        X_landmarks = X[landmark_sample, i]
        rotated = 0
        for j in range(len(X_landmarks)):
            if X_landmarks[j] < 0 < Y[j, i] or Y[j, i] < 0 < X_landmarks[j]:
                rotated += 1
        print("... ... rotation error in dim " + str(i) + ": " + str(round(rotated / X_landmarks.size, 2) * 100) + "%")
        if (rotated / X_landmarks.size) > 0.5:
            print("... ... ... rotating dim " + str(i))
            X[:, i] = -X[:, i]

    print("... ... embedded data")


    # pca normalisation
    # Xmean = np.mean(X, axis=0)
    # Xhat = X[:] - Xmean
    # XhatSquare = np.matmul(Xhat, np.transpose(Xhat))
    # w, v = np.linalg.eigh(XhatSquare)
    # Xpca = np.matmul(np.transpose(w), Xhat)
    return X, S
